"""
reasoning/services/db_router.py
============================================================
사용자 질문이 데이터베이스 조회가 필요한지 판별하는 라우터.

설명:
- LLM 기반 판별을 통해 자연어 질문이 실제 테이블 조회(DB query)를 필요로
    하는지 판단합니다. 판별 결과는 상위 로직에서 SQL 생성 또는 문서 기반
    처리로 라우팅하는 데 사용됩니다.

디자인 원칙:
- 판별은 판단 오류가 발생할 수 있으므로, 실패 시 안전하게 "DB 아님"으로
    처리하여 임의의 DB 실행을 방지합니다.
"""

from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel, ValidationError
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY, CHAT_MODEL


# ============================================================
# LLM 출력 스키마
# ============================================================
class DBRouteResult(BaseModel):
    is_db_question: bool
    reason: Optional[str] = None


# ============================================================
# Prompt
# ============================================================
DB_ROUTE_PROMPT = """
너는 질문을 분류하는 라우터다.
사용자의 질문이 "데이터베이스 조회(DB query)가 필요한 질문"인지 판단하라.

DB 질문의 예:
- 현재 랭킹 top 5 보여줘
- alice 점수 기록 알려줘
- hard 모드 최고 점수는?
- 최근 7일간 최고 점수

DB 질문이 아닌 예:
- 이 시스템은 어떻게 동작해?
- 랭킹 산정 방식 설명해줘
- 점수는 어떻게 계산돼?
- SQL이 뭐야?

판단 기준:
- 실제 테이블 데이터를 조회해야 답할 수 있으면 DB 질문
- 개념 설명/규칙 설명/문서 요약이면 DB 질문 아님

출력은 반드시 JSON 하나만:
{
  "is_db_question": true | false,
  "reason": "간단한 판단 이유"
}
""".strip()


# ============================================================
# Router
# ============================================================
_llm: Optional[ChatOpenAI] = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=CHAT_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.0,  # 판별은 deterministic 하게
        )
    return _llm


def is_db_question(question: str) -> bool:
    """
    질문이 DB 조회가 필요한지 여부를 LLM으로 판별한다.
    실패 시 안전하게 False로 처리한다.
    """
    llm = _get_llm()

    messages = [
        SystemMessage(content=DB_ROUTE_PROMPT),
        HumanMessage(content=question),
    ]

    try:
        raw = llm.invoke(messages).content
        data = json.loads(raw)
        parsed = DBRouteResult.model_validate(data)
        return bool(parsed.is_db_question)
    except (json.JSONDecodeError, ValidationError, Exception):
        # 판별 실패 시 보수적으로 DB 아님 처리
        return False
