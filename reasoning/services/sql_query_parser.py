"""
reasoning/services/sql_query_parser.py
------------------------------------------------------------
LLM이 생성한 SQL 요청(JSON)을 파싱하고 Pydantic 스키마로 검증하는 유틸리티.

설명:
- LLM의 출력은 항상 JSON 형식이라고 가정할 수 없으므로 방어적으로
  파싱을 시도하고, 성공 시 내부 `SQLQueryRequest` 객체로 변환합니다.
- 실패 시 None을 반환하여 상위 로직에서 폴백 전략을 선택할 수 있게 합니다.
"""

from __future__ import annotations

import json
from pydantic import ValidationError

from ..schemas.sql_query import SQLQueryRequest


def parse_sql_query_json(text: str) -> SQLQueryRequest | None:
    """
    LLM이 생성한 JSON 문자열을 파싱하여 `SQLQueryRequest`로 변환합니다.

    Args:
        text (str): LLM이 반환한 JSON 텍스트

    Returns:
        SQLQueryRequest | None: 파싱 및 검증이 성공하면 객체 반환, 실패하면 None
    """
    try:
        data = json.loads(text)
        return SQLQueryRequest.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        return None
