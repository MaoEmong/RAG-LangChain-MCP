"""
reasoning/schemas/db_summary.py
============================================================
DB 조회 결과를 사람이 읽기 좋은 요약 형태로 표현하는 스키마.

설명:
- `DBSummaryResult`는 DB 조회 결과(서버가 이미 정렬/limit 처리한)를
    읽기 좋은 텍스트로 변환한 결과를 표준화합니다. `summary`는 리스트 형식
    또는 여러 줄 텍스트를 포함할 수 있습니다.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel


class DBSummaryResult(BaseModel):
        type: Literal["db_summary"] = "db_summary"
        summary: str
        speech: Optional[str] = None
