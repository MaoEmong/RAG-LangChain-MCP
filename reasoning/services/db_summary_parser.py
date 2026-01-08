"""
reasoning/services/db_summary_parser.py
------------------------------------------------------------
LLM이 생성한 DB 요약(JSON)을 파싱하여 `DBSummaryResult`로 변환합니다.

설명:
- DB 조회 결과를 LLM으로 요약할 때 LLM은 JSON 형식의 요약 구조를 반환하도록
  설계됩니다. 이 모듈은 해당 출력을 안전하게 파싱하고 검증합니다.

실패 처리:
- 파싱/검증 실패 시 None을 반환하여 상위 레이어에서 규칙 기반 폴백 요약으로
  대체할 수 있도록 합니다.
"""

from __future__ import annotations

import json
from typing import Optional
from ..schemas.db_summary import DBSummaryResult


def parse_db_summary_json(text: str) -> Optional[DBSummaryResult]:
    """
    LLM이 반환한 JSON 텍스트를 파싱하여 `DBSummaryResult` 반환.

    Args:
        text (str): LLM 응답 텍스트

    Returns:
        DBSummaryResult | None: 파싱 성공 시 객체, 실패 시 None
    """
    try:
        data = json.loads(text)
        return DBSummaryResult.model_validate(data)
    except Exception:
        return None
