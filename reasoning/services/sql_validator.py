# services/sql_validator.py
from __future__ import annotations

from typing import Tuple


def validate_select_only(sql: str) -> Tuple[bool, str]:
    """
    SQL 안전성 검사(간단한 내부 가드).

    설명:
    - 상위 레이어에서 LLM이 생성한 SQL이 실제로 SELECT 문인지 간단히 검사합니다.
    - 이 함수는 매우 기본적인 검사만 수행하므로, 추가 보안(화이트리스트, 파서 기반
      검사 등)은 상위 레이어에서 보완되어야 합니다.

    Args:
        sql (str): 검사할 SQL 문자열

    Returns:
        Tuple[bool, str]: (ok, reason) - ok가 False이면 reason에 에러 원인 설명이 담깁니다.
    """
    s = (sql or "").strip().lower()
    if not s.startswith("select "):
        return False, "only SELECT is allowed"
    return True, "ok"
