"""
chains/hybrid_onecall_chain.py
============================================================
하이브리드 원콜(One-call) 메시지 생성 유틸리티.

설명:
- 이 함수는 DB에서 실행된 실제 행(rows)과 문서 컨텍스트를 함께 LLM에
  전달하여, 한 번의 LLM 호출로 DB+문서 기반의 통합 응답을 생성하려는
  시나리오에 사용됩니다.
- 원콜 방식은 네트워크/비용 측면에서 효율적이지만, LLM의 출력 포맷이
  불안정할 수 있으므로 상위 로직에서 파싱/검증 폴백을 반드시 수행해야 합니다.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from ..prompts.hybrid_onecall_prompt import HYBRID_ONECALL_PROMPT_TEMPLATE


def build_hybrid_onecall_messages(*, question: str, query: str, params: dict, rows_json: str, doc_context: str):
    """
    원콜 하이브리드 메시지를 생성합니다.

    Args:
        question (str): 사용자 질문
        query (str): 실행된 SQL 또는 쿼리 식별자(디버깅용)
        params (dict): SQL 파라미터
        rows_json (str): 실행 결과 행을 JSON 문자열로 직렬화한 값
        doc_context (str): 문서 컨텍스트

    Returns:
        list: LangChain 형식의 메시지 리스트
    """
    prompt = ChatPromptTemplate.from_template(HYBRID_ONECALL_PROMPT_TEMPLATE)
    return prompt.format_messages(
        question=question,
        query=query,
        params=params,
        rows_json=rows_json,
        doc_context=doc_context,
    )
