"""
rag_server.py
============================================================
FastAPI로 구성된 데모 RAG(Retrieval-Augmented Generation) 및 DB 하이브리드
질의응답 서버입니다. 포트폴리오에서 서버 아키텍처와 라우팅 설계를 보여주기
위해 작성된 예제 코드입니다.

엔드포인트 요약:
- POST /chat    : 문서 기반 RAG 답변 반환 (문서 검색 → LLM 요약/응답)
- POST /command : 문서에서 명령 후보 추출 → JSON 파싱 → 화이트리스트 검증
- POST /ask     : DB 질의 식별 시 LLM으로 SQL(SELECT) 생성 → 안전성 검사 → 실행
                                    → 문서 컨텍스트와 결합한 하이브리드 응답 생성

안전성 및 설계 원칙:
- DB 쿼리는 서버 측에서 "SELECT 전용"으로 엄격히 제한하여 임의 명령 실행을 방지합니다.
- 문서 기반 응답은 검색 결과의 신뢰도(거리 기반 점수)와 재랭킹 과정을 거쳐
    충분한 근거가 있는 경우에만 LLM에 전달됩니다.
- 다양한 폴백(예: 안전 SQL, 규칙 기반 요약)을 통해 실패 시에도 안전한 응답을 제공합니다.

포트폴리오 작성 포인트:
- 이 모듈은 RAG와 데이터베이스 질의를 결합한 하이브리드 시스템 설계를
    명확히 보여주며, 신뢰도 계산·가드레일(guardrail)·원콜/폴백 전략이 구현되어 있습니다.
"""

import json
from typing import List, Tuple

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from config import (
    OPENAI_API_KEY,
    EMBED_MODEL,
    CHAT_MODEL,
    CHROMA_DIR,
    COLLECTION_NAME,
    TOP_K,
    TOP_SCORE_MAX,
    MIN_GOOD_HITS,
    GOOD_HIT_SCORE_MAX,
    DOCSTORE_PATH,
    MYSQL,
)

# -----------------------------
# reasoning/* 경로(네가 쓰는 구조)
# -----------------------------
from reasoning.chains.sql_query_chain import build_sql_query_messages
from reasoning.services.sql_query_parser import parse_sql_query_json
from reasoning.services.sql_validator import validate_select_only
from reasoning.services.db_fallback_summary import build_fallback_summary

from reasoning.chains.hybrid_chain import build_hybrid_messages
from reasoning.chains.hybrid_onecall_chain import build_hybrid_onecall_messages
from reasoning.services.hybrid_parser import parse_hybrid_json
from reasoning.chains.db_summary_chain import build_db_summary_messages
from reasoning.services.db_summary_parser import parse_db_summary_json
from reasoning.services.intent_classifier import classify_intent
from reasoning.services.db_router import is_db_question

# -----------------------------
# 기존 RAG/Command 쪽 (네 프로젝트 기존 모듈)
# -----------------------------
from reasoning.chains.rag_chain import format_docs
from reasoning.prompts.command_prompt import COMMAND_PROMPT_TEMPLATE

from retrieval.vector_store import create_vector_store
from retrieval.retrieval import retrieve_parents_with_rerank
from retrieval.rerank_flashrank import FlashRankReranker
from reasoning.services.confidence import calculate_confidence

from reasoning.services.command_parser import parse_command_json
from reasoning.services.command_validator import validate_commands

from ingest.docstore_sqlite import SQLiteDocStore

from reasoning.services.db_service import MySqlConfig, MySqlService


# ============================================================
# FastAPI
# ============================================================
app = FastAPI()


# ============================================================
# Vector DB / DocStore
# ============================================================
vector_db = create_vector_store(
    OPENAI_API_KEY,
    EMBED_MODEL,
    CHROMA_DIR,
    COLLECTION_NAME,
)

docstore = SQLiteDocStore(DOCSTORE_PATH)
DocumentScore = Tuple[Document, float]


# ============================================================
# LLM
# ============================================================
llm = ChatOpenAI(
    model=CHAT_MODEL,
    api_key=OPENAI_API_KEY,
    temperature=0.2,
)


# ============================================================
# DB
# ============================================================
db_service = MySqlService(MySqlConfig(**MYSQL))
MAX_DB_LIMIT = 50


# ============================================================
# Prompt templates
# ============================================================
rag_prompt = ChatPromptTemplate.from_template(
    """
너는 문서 기반 RAG QA 시스템이다.
반드시 아래 CONTEXT에 있는 정보만 사용해서 답해라.

규칙:
1) CONTEXT에 질문과 관련된 정보가 있으면, 그 내용을 요약해서 답해야 한다.
2) CONTEXT에 정말 아무 근거가 없을 때만 "문서에서 근거를 찾지 못했습니다."라고 답한다.
3) 답변의 핵심 문장 끝에는 근거로 사용한 DOC 번호를 (DOC 1)처럼 붙여라.
4) 과장/추측/상상 금지. 문서에 있는 표현을 우선 사용하되, 자연스럽게 풀어서 설명해라.

[CONTEXT]
{context}

[QUESTION]
{question}

[ANSWER]
"""
)

command_prompt = ChatPromptTemplate.from_template(COMMAND_PROMPT_TEMPLATE)


# ============================================================
# ReRank
# ============================================================
INITIAL_K = 20
reranker = FlashRankReranker(model="ms-marco-MiniLM-L-12-v2")


# ============================================================
# Request schema
# ============================================================
class ChatRequest(BaseModel):
    question: str


# ============================================================
# Helpers
# ============================================================
MAX_CONTEXT_CHARS = 12000

def _trim_context(context: str, limit: int = MAX_CONTEXT_CHARS) -> str:
    if len(context) <= limit:
        return context
    cut = context.rfind("\n\n[DOC", 0, limit)
    if cut == -1 or cut < limit * 0.5:
        return context[:limit]
    return context[:cut].rstrip()

def _retrieve(question: str) -> List[DocumentScore]:
    return retrieve_parents_with_rerank(
        vector_db=vector_db,
        docstore=docstore,
        query=question,
        initial_k=INITIAL_K,
        top_k=TOP_K,
        reranker=reranker,
        parent_id_key="doc_id",
    )

def _guard_and_conf(results: List[DocumentScore]):
    if not results:
        return None, None, None
    top_score = float(results[0][1])
    good_hits = sum(1 for _, s in results if float(s) <= GOOD_HIT_SCORE_MAX)
    confidence = calculate_confidence(top_score, good_hits)
    return top_score, good_hits, confidence

def _sources_from_results(results: List[DocumentScore]):
    sources = []
    for d, score in results:
        sources.append({
            "source": d.metadata.get("source"),
            "score": float(score),
            "preview": d.page_content[:180],
        })
    return sources

def _doc_context_for_hybrid(question: str) -> tuple[str, list]:
    results = _retrieve(question)
    sources = _sources_from_results(results)

    if not results:
        return "", sources

    top_score, good_hits, _ = _guard_and_conf(results)

    # 문서 관련성이 낮으면 컨텍스트 제거
    if (top_score is not None and top_score > TOP_SCORE_MAX) or (good_hits is not None and good_hits < MIN_GOOD_HITS):
        return "", sources

    docs_only = [d for d, _ in results]
    ctx = _trim_context(format_docs(docs_only))
    return ctx, sources


# ============================================================
# /chat
# ============================================================
@app.post("/chat")
def chat(req: ChatRequest):
    results = _retrieve(req.question)

    if not results:
        return {
            "type": "rag_answer",
            "question": req.question,
            "answer": "문서에서 근거를 찾지 못했습니다.",
            "sources": [],
            "guard": {"reason": "no_results"},
        }

    top_score, good_hits, confidence = _guard_and_conf(results)

    if top_score is not None and top_score > TOP_SCORE_MAX:
        return {
            "type": "rag_answer",
            "question": req.question,
            "answer": "문서에서 충분한 근거를 찾지 못했습니다.",
            "sources": _sources_from_results(results),
            "guard": {"reason": "low_confidence", "top_score": top_score, "good_hits": good_hits},
            "confidence": confidence,
        }

    has_parent_context = any(len(d.page_content) > 300 for d, _ in results)
    if good_hits is not None and good_hits < MIN_GOOD_HITS and not has_parent_context:
        return {
            "type": "rag_answer",
            "question": req.question,
            "answer": "문서에서 충분한 근거를 찾지 못했습니다.",
            "sources": _sources_from_results(results),
            "guard": {"reason": "insufficient_good_hits", "top_score": top_score, "good_hits": good_hits},
            "confidence": confidence,
        }

    docs_only = [d for d, _ in results]
    context = _trim_context(format_docs(docs_only))

    messages = rag_prompt.format_messages(context=context, question=req.question)
    answer = llm.invoke(messages).content

    return {
        "type": "rag_answer",
        "question": req.question,
        "answer": answer,
        "sources": _sources_from_results(results),
        "guard": {"reason": "ok", "top_score": top_score, "good_hits": good_hits},
        "confidence": confidence,
    }


# ============================================================
# /command
# ============================================================
@app.post("/command")
def command(req: ChatRequest):
    results = _retrieve(req.question)

    if not results:
        return {
            "type": "command",
            "speech": "실행 가능한 명령을 찾지 못했습니다.",
            "actions": [],
            "confidence": {"level": "low", "score": 0.0, "details": {"base": 0.0, "bonus": 0.0}},
            "guard": {"reason": "no_results"},
        }

    top_score, good_hits, confidence = _guard_and_conf(results)

    # 명령은 보수적으로
    if confidence["level"] == "low" and confidence["score"] < 0.5:
        return {
            "type": "command",
            "speech": "확신이 부족하여 명령을 실행할 수 없습니다.",
            "actions": [],
            "confidence": confidence,
            "sources": _sources_from_results(results),
            "guard": {"reason": "low_confidence", "top_score": top_score, "good_hits": good_hits},
        }

    docs_only = [d for d, _ in results]
    context = _trim_context(format_docs(docs_only))

    messages = command_prompt.format_messages(context=context, question=req.question)
    raw_text = llm.invoke(messages).content

    parsed = parse_command_json(raw_text)
    if not parsed:
        return {
            "type": "command",
            "speech": "명령을 해석하지 못했습니다.",
            "actions": [],
            "confidence": confidence,
            "sources": _sources_from_results(results),
            "guard": {"reason": "parse_failed"},
            "raw": raw_text,
        }

    ok, reason = validate_commands(parsed)
    if not ok:
        return {
            "type": "command",
            "speech": "허용되지 않은 명령입니다.",
            "actions": [],
            "confidence": confidence,
            "sources": _sources_from_results(results),
            "guard": {"reason": "command_not_allowed", "detail": reason},
        }

    return {
        "type": "command",
        "speech": parsed.speech,
        "actions": [a.model_dump() for a in parsed.actions],
        "confidence": confidence,
        "sources": _sources_from_results(results),
        "guard": {"reason": "ok"},
    }


# ============================================================
# /ask  (DB + 문서 하이브리드, DB는 LLM이 SQL 생성)
# ============================================================
@app.post("/ask")
def ask(req: ChatRequest):
    # DB 질문이면: LLM이 SQL+params 생성 → 서버는 SELECT만 확인 → 실행 → hybrid
    if is_db_question(req.question):
        # 1) LLM SQL 생성(JSON)
        messages = build_sql_query_messages(
            question=req.question,
            max_limit=MAX_DB_LIMIT,  # 프롬프트에 들어가는 값 (강제는 안 함)
        )
        raw = llm.invoke(messages).content

        parsed = parse_sql_query_json(raw)

        # 폴백 SQL (데모 DB: users/scores 기준)
        safe_sql = """
SELECT u.username, s.score, s.mode, s.created_at
FROM scores s
JOIN users u ON u.user_id = s.user_id
ORDER BY s.score DESC
LIMIT 10
""".strip()

        if not parsed:
            rows = db_service.run_sql(safe_sql, {})
            rows = rows[:MAX_DB_LIMIT]
            rows_json = json.dumps(rows, ensure_ascii=False, default=str)

            doc_context, doc_sources = _doc_context_for_hybrid(req.question)
            if not doc_context.strip():
                doc_sources = []

            # 원콜 시도
            hy_messages = build_hybrid_onecall_messages(
                question=req.question,
                query="RawSQL(fallback)",
                params={"sql": safe_sql, "limit": 10},
                rows_json=rows_json,
                doc_context=doc_context,
            )
            raw_hybrid = llm.invoke(hy_messages).content
            hy_parsed = parse_hybrid_json(raw_hybrid)

            if hy_parsed:
                return {
                    "type": "hybrid_answer",
                    "question": req.question,
                    "speech": hy_parsed.speech,
                    "db_summary": hy_parsed.db_summary,
                    "doc_notes": hy_parsed.doc_notes,
                    "answer": hy_parsed.answer,
                    "sql": safe_sql,
                    "params": {},
                    "rows": rows,
                    "sources": doc_sources,
                    "guard": {"reason": "sql_query_parse_failed_fallback_ok"},
                    "raw": raw,
                }

            # 최후 폴백(룰 기반 요약)
            fallback_db_summary = build_fallback_summary(
                question=req.question,
                query="RawSQL(fallback)",
                params={"sql": safe_sql, "limit": 10},
                rows=rows,
            )
            return {
                "type": "hybrid_answer",
                "question": req.question,
                "speech": "요청하신 정보를 조회했습니다.",
                "db_summary": fallback_db_summary,
                "doc_notes": "관련 문서 근거 없음",
                "answer": fallback_db_summary,
                "sql": safe_sql,
                "params": {},
                "rows": rows,
                "sources": doc_sources,
                "guard": {"reason": "sql_query_parse_failed_fallback_summary"},
                "raw": raw,
            }

        # 2) SELECT-only 검사
        ok, reason = validate_select_only(parsed.sql)
        if not ok:
            return {
                "type": "hybrid_answer",
                "question": req.question,
                "speech": "요청하신 쿼리는 실행할 수 없습니다.",
                "db_summary": "",
                "doc_notes": "관련 문서 근거 없음",
                "answer": "SELECT 쿼리만 허용됩니다.",
                "sql": parsed.sql,
                "params": parsed.params,
                "rows": [],
                "sources": [],
                "guard": {"reason": "sql_not_select_only", "detail": reason},
                "raw": raw,
                "parsed": parsed.model_dump(),
            }

        # 3) SQL 실행
        try:
            rows = db_service.run_sql(parsed.sql, parsed.params or {})
        except Exception as e:
            return {
                "type": "hybrid_answer",
                "question": req.question,
                "speech": "DB 조회 중 오류가 발생했습니다.",
                "db_summary": "",
                "doc_notes": "관련 문서 근거 없음",
                "answer": "DB 조회 중 오류가 발생했습니다.",
                "sql": parsed.sql,
                "params": parsed.params,
                "rows": [],
                "sources": [],
                "guard": {"reason": "db_execute_failed", "detail": str(e)},
                "raw": raw,
                "parsed": parsed.model_dump(),
            }

        rows = rows[:MAX_DB_LIMIT]
        rows_json = json.dumps(rows, ensure_ascii=False, default=str)

        # 4) 문서 컨텍스트도 같이
        doc_context, doc_sources = _doc_context_for_hybrid(req.question)
        if not doc_context.strip():
            doc_sources = []

        # 5) 하이브리드 원콜
        hy_messages = build_hybrid_onecall_messages(
            question=req.question,
            query="RawSQL",
            params={"sql": parsed.sql, **(parsed.params or {})},
            rows_json=rows_json,
            doc_context=doc_context,
        )
        raw_hybrid = llm.invoke(hy_messages).content
        hy_parsed = parse_hybrid_json(raw_hybrid)

        if hy_parsed:
            return {
                "type": "hybrid_answer",
                "question": req.question,
                "speech": hy_parsed.speech,
                "db_summary": hy_parsed.db_summary,
                "doc_notes": hy_parsed.doc_notes,
                "answer": hy_parsed.answer,
                "sql": parsed.sql,
                "params": parsed.params,
                "rows": rows,
                "sources": doc_sources,
                "guard": {"reason": "ok"},
                "raw": raw,
            }

        # 6) 원콜 실패 → DB 요약(LLM) → hybrid(LLM) 폴백
        raw_sum = None
        sum_parsed = None
        try:
            sum_messages = build_db_summary_messages(
                question=req.question,
                query="RawSQL",
                params={"sql": parsed.sql, **(parsed.params or {})},
                rows_json=rows_json,
            )
            raw_sum = llm.invoke(sum_messages).content
            sum_parsed = parse_db_summary_json(raw_sum)
        except Exception:
            sum_parsed = None

        if sum_parsed and sum_parsed.summary and sum_parsed.summary.strip():
            db_summary_text = sum_parsed.summary
        else:
            db_summary_text = build_fallback_summary(
                question=req.question,
                query="RawSQL",
                params={"sql": parsed.sql, **(parsed.params or {})},
                rows=rows,
            )

        speech_text = (sum_parsed.speech.strip() if (sum_parsed and sum_parsed.speech) else "") or (
            parsed.speech or "요청하신 정보를 조회했습니다."
        )

        try:
            hy2_messages = build_hybrid_messages(
                question=req.question,
                db_summary=db_summary_text,
                doc_context=doc_context,
            )
            raw_hybrid2 = llm.invoke(hy2_messages).content
            hy2_parsed = parse_hybrid_json(raw_hybrid2)
        except Exception:
            hy2_parsed = None
            raw_hybrid2 = None

        if hy2_parsed:
            return {
                "type": "hybrid_answer",
                "question": req.question,
                "speech": hy2_parsed.speech or speech_text,
                "db_summary": db_summary_text,
                "doc_notes": hy2_parsed.doc_notes,
                "answer": hy2_parsed.answer,
                "sql": parsed.sql,
                "params": parsed.params,
                "rows": rows,
                "sources": doc_sources,
                "guard": {"reason": "hybrid_onecall_failed_used_2call_fallback"},
                "raw": raw,
                "raw_summary": raw_sum,
                "raw_hybrid": raw_hybrid,
                "raw_hybrid2": raw_hybrid2,
            }

        # 7) 최후 폴백
        return {
            "type": "hybrid_answer",
            "question": req.question,
            "speech": speech_text,
            "db_summary": db_summary_text,
            "doc_notes": "관련 문서 근거 없음",
            "answer": db_summary_text,
            "sql": parsed.sql,
            "params": parsed.params,
            "rows": rows,
            "sources": doc_sources,
            "guard": {"reason": "hybrid_failed_all_fallbacks"},
            "raw": raw,
            "raw_summary": raw_sum,
        }

    # DB가 아니면 기존대로 intent 분류 후 라우팅
    intent = classify_intent(req.question, llm)
    if intent.intent == "command":
        return command(req)
    return chat(req)
