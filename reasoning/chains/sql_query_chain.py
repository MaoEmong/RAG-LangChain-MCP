"""
reasoning/chains/sql_query_chain.py
============================================================
LLM으로부터 안전한 SELECT 전용 SQL을 생성하도록 메시지를 빌드하는 유틸리티.

설명:
- 상위 로직은 사용자의 자연어 질문을 받아 LLM으로부터 SQL(JSON)을 얻어야 할 때,
  이 모듈의 `build_sql_query_messages`를 사용해 시스템/사용자 메시지를 구성합니다.
- 데이터베이스 스키마 요약(`get_db_schema_context`)을 프롬프트에 주입하여
  LLM이 테이블/컬럼을 참고해 올바른 SELECT 쿼리를 생성하도록 돕습니다.

안전성 주의:
- 실제 SQL 실행 전에는 반드시 `validate_select_only` 같은 검증기를 통과시켜야 합니다.
  이 모듈은 메시지 구성 책임만 담당합니다.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from reasoning.prompts.sql_query_prompt import SQL_QUERY_PROMPT_TEMPLATE
from reasoning.services.db_schema_provider import get_db_schema_context


def build_sql_query_messages(question: str, max_limit: int = 50):
    """
    LLM에 전달할 메시지 리스트를 생성합니다.

    Args:
        question (str): 사용자 자연어 질문
        max_limit (int): 프롬프트에 포함될 최대 반환 로우 수(안내용)

    Returns:
        list: SystemMessage와 HumanMessage로 구성된 메시지 리스트
    """
    schema_context = get_db_schema_context()

    system_text = "You are a careful SQL generator. Return ONLY valid JSON."
    prompt = SQL_QUERY_PROMPT_TEMPLATE.format(
        schema_context=schema_context,
        max_limit=max_limit,
        question=question,
    )

    return [
        SystemMessage(content=system_text),
        HumanMessage(content=prompt),
    ]
