"""
reasoning/services/db_query_parser.py
------------------------------------------------------------
LLM이 생성한 DB 쿼리(JSON)를 파싱하고 `DBQueryRequest`로 검증합니다.

주요 설계:
- LLM 출력은 언제든 형식이 어긋날 수 있으므로 방어적으로 파싱합니다.
- 파싱 실패 시 None을 반환하여 상위 로직이 안전한 폴백 경로를 사용하게 합니다.
"""

from __future__ import annotations

import json
from typing import Optional
from ..schemas.db_query import DBQueryRequest


def parse_db_query_json(text: str) -> Optional[DBQueryRequest]:
    """
    LLM이 반환한 텍스트(예상 JSON)를 파싱하여 `DBQueryRequest`로 변환합니다.

    Args:
        text (str): LLM의 응답 텍스트

    Returns:
        DBQueryRequest | None: 파싱 및 검증이 성공하면 객체, 실패 시 None
    """
    try:
        data = json.loads(text)
        return DBQueryRequest.model_validate(data)
    except Exception:
        return None
