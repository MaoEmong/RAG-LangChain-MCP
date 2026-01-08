# services/db_query_validator.py
from __future__ import annotations

from typing import Tuple
from ..schemas.db_query import DBQueryRequest
from ..services.db_service import DB_ALLOWED_QUERIES


def validate_db_query(req: DBQueryRequest) -> Tuple[bool, str]:
    """
    DB 쿼리 요청이 미리 정의된 허용 규격(화이트리스트)에 맞는지 검증합니다.

    검증 항목:
    - 쿼리 식별자(query)가 허용 목록에 있는지
    - 필수 파라미터(required)가 모두 존재하는지
    - 허용되지 않은 추가 파라미터가 없는지

    Args:
        req (DBQueryRequest): 파싱된 DB 쿼리 요청 객체

    Returns:
        Tuple[bool, str]: (ok, reason) - ok False일 때 reason에 상세 설명
    """
    if req.query not in DB_ALLOWED_QUERIES:
        return False, f"Query not allowed: {req.query}"

    spec = DB_ALLOWED_QUERIES[req.query]
    args = req.args or {}

    # required 체크
    for k in spec.required:
        if k not in args or args[k] in (None, ""):
            return False, f"Missing required param: {k}"

    # extra param 차단 (화이트리스트)
    allowed_keys = set(spec.required) | set(spec.optional)
    extra = set(args.keys()) - allowed_keys
    if extra:
        return False, f"Unexpected params: {sorted(extra)}"

    return True, "ok"
