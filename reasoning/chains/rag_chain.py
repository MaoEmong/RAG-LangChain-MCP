"""
chains/rag_chain.py
============================================================
RAG(Retrieval-Augmented Generation) 파이프라인 구성 모듈.

설명:
- 이 모듈은 검색기(retriever)로부터 문서를 받아 LLM에 들어갈 컨텍스트를
    생성하고, 프롬프트와 결합하여 LLM으로부터 최종 텍스트 응답을 얻는
    LangChain runnable 체인을 구성합니다.

핵심 컴포넌트:
- `format_docs`: Document 리스트를 컨텍스트 문자열로 정리하여 LLM에 입력
- `build_rag_chain`: retriever → format_docs → prompt → llm → parser 흐름을
    연결하는 LangChain runnable 반환

포트폴리오 포인트:
- 컨텍스트 길이 관리(truncation), 문서별 컷오프, 그리고 문서 출처 표기
    처리를 통해 LLM에 제공되는 프롬프트 품질을 보장하는 구현을 보여줍니다.
"""

from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ============================================================
# Helper 함수: Document 리스트를 컨텍스트 문자열로 변환
# ============================================================
def format_docs(
    docs,
    *,
    max_chars_per_doc: int = 900,     # 문서 1개당 최대 글자수
    max_context_chars: int = 3500,    # 전체 컨텍스트 최대 글자수
) -> str:
    """
    검색된 Document들을 LLM에 넣기 좋은 문자열로 변환합니다.
    - 각 문서별 길이 제한
    - 전체 컨텍스트 길이 제한
    """

    blocks = []
    total = 0

    for i, d in enumerate(docs, start=1):
        src = (d.metadata or {}).get("source", "unknown")
        text = d.page_content or ""

        # 1) 문서별 컷
        if len(text) > max_chars_per_doc:
            text = text[:max_chars_per_doc].rstrip() + "\n…[TRUNCATED]"

        block = f"[DOC {i}] source={src}\n{text}"

        # 2) 전체 컨텍스트 컷
        if total + len(block) > max_context_chars:
            remain = max_context_chars - total
            if remain <= 0:
                break
            block = block[:remain].rstrip() + "\n…[CONTEXT TRUNCATED]"
            blocks.append(block)
            break

        blocks.append(block)
        total += len(block) + 2  # \n\n 정도 여유

    return "\n\n".join(blocks)

# ============================================================
# RAG 체인 빌더
# ============================================================
def build_rag_chain(retriever, llm, prompt):
    """
    RAG 체인을 구성하고 반환합니다.
    
    파이프라인 흐름:
    1. retriever: 질문으로 관련 문서 검색
    2. format_docs: 검색된 문서를 컨텍스트 문자열로 변환
    3. prompt: 컨텍스트와 질문을 프롬프트에 삽입
    4. llm: LLM이 답변 생성
    5. StrOutputParser: LLM 출력을 문자열로 파싱
    
    Args:
        retriever: 벡터DB 검색기 (LangChain Retriever)
        llm: 언어 모델 (ChatOpenAI 등)
        prompt: 프롬프트 템플릿 (ChatPromptTemplate)
    
    Returns:
        Runnable: LangChain Runnable 체인 객체
    """
    return (
        {
            # "context" 키: retriever로 문서 검색 후 format_docs로 변환
            "context": retriever | format_docs,
            # "question" 키: 입력 질문을 그대로 전달
            "question": RunnablePassthrough(),
        }
        | prompt      # 프롬프트에 context와 question 삽입
        | llm         # LLM이 답변 생성
        | StrOutputParser()  # LLM 출력을 문자열로 변환
    )
