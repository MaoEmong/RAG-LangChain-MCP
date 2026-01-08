"""
chains/db_query_chain.py
============================================================
DB 질의를 위해 LLM에 전달할 메시지를 생성하는 헬퍼 모듈.

설명:
- 이 모듈은 허용된 쿼리 목록(화이트리스트)과 사용자의 질문을 프롬프트에
  주입하여 LLM이 안전하게 DB 쿼리(JSON)를 생성하도록 돕습니다.

주의:
- 생성된 출력은 반드시 파싱 및 화이트리스트 검증을 거쳐야 합니다.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from ..prompts.db_query_prompt import DB_QUERY_PROMPT_TEMPLATE


def build_db_query_messages(*, allowed_queries: str, question: str):
    """
    DB 질의용 메시지를 생성합니다.

    Args:
        allowed_queries (str): 허용되는 쿼리 목록 또는 스펙(프롬프트용)
        question (str): 사용자 질문

    Returns:
        list: LangChain 형식의 메시지 리스트
    """
    prompt = ChatPromptTemplate.from_template(DB_QUERY_PROMPT_TEMPLATE)
    return prompt.format_messages(allowed_queries=allowed_queries, question=question)
