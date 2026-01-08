"""
reasoning/schemas/db_query.py
============================================================
LLM이 선택하도록 설계된 허용 쿼리 식별자와 해당 파라미터를 표현하는 스키마.

설명:
- 서버는 미리 등록된 `DB_ALLOWED_QUERIES`(화이트리스트)를 보유하고,
  LLM은 실제 SQL이 아닌 해당 쿼리의 키와 필요한 인자(args)를 채워 반환합니다.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class DBQueryRequest(BaseModel):
    """
    DB 쿼리 호출을 표현하는 요청 스키마.

    필드:
    - type: 항상 "db_query"
    - query: 허용된 쿼리 이름(화이트리스트 키와 동일해야 함)
    - args: 쿼리에 필요한 파라미터 딕셔너리
    - speech: 사용자에게 보여줄 짧은 설명(선택)
    """
    type: Literal["db_query"] = "db_query"

    # DB_ALLOWED_QUERIES의 key와 동일해야 함
    query: str = Field(..., description="Allowed query name from DB registry")

    # query별 파라미터
    args: Dict[str, Any] = Field(default_factory=dict)

    # 사용자에게 보여줄 짧은 설명(선택)
    speech: Optional[str] = None
