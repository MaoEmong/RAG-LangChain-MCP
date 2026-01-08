"""
chains/hybrid_chain.py
============================================================
하이브리드(문서 + DB 요약) 응답을 생성하기 위한 메시지 빌더.

설명:
- DB에서 요약된 정보(`db_summary`)와 문서 기반 컨텍스트(`doc_context`)를
  결합하여 LLM에 전달할 프롬프트 메시지를 생성합니다.
- 주로 DB 질의 후 원콜이 실패했을 때 2단계 폴백으로 사용되는 흐름에 적합합니다.

함수:
- `build_hybrid_messages`: 질문, DB 요약, 문서 컨텍스트를 받아 ChatPromptTemplate로
  메시지를 생성합니다.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from ..prompts.hybrid_prompt import HYBRID_PROMPT_TEMPLATE


def build_hybrid_messages(*, question: str, db_summary: str, doc_context: str):
    """
    2단계 하이브리드 메시지를 생성합니다.

    Args:
        question (str): 사용자 질문
        db_summary (str): DB 조회 결과를 LLM이 요약한 텍스트
        doc_context (str): 문서 기반 컨텍스트(문서에서 추출한 근거)

    Returns:
        list: LangChain 형식의 메시지 리스트
    """
    prompt = ChatPromptTemplate.from_template(HYBRID_PROMPT_TEMPLATE)
    return prompt.format_messages(
        question=question,
        db_summary=db_summary,
        doc_context=doc_context,
    )
