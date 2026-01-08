"""
reasoning/schemas/sql_query.py
============================================================
LLM이 생성한 SELECT 전용 SQL과 파라미터를 표현하는 스키마.

설명:
- 이 스키마는 LLM이 반환한 SQL을 구조화하여 상위 로직이 안전하게
    검증하고 실행할 수 있도록 돕습니다. 파라미터는 dict 형태로 전달됩니다.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class SQLQueryRequest(BaseModel):
        """
        SELECT 전용 SQL 요청을 표현하는 스키마.

        필드:
        - type: 항상 "sql_query"
        - sql: 실행할 SELECT 문 (파라미터화 권장)
        - params: SQL 파라미터 딕셔너리
        - speech: 사용자에게 보여줄 간단한 안내(선택)
        """
        type: Literal["sql_query"] = "sql_query"

        # SELECT-only SQL, pyformat placeholders 권장: %(param)s
        sql: str = Field(..., description="SELECT-only SQL query")

        # placeholder에 들어갈 파라미터
        params: Dict[str, Any] = Field(default_factory=dict)

        # 사용자에게 보여줄 짧은 설명(선택)
        speech: Optional[str] = None
