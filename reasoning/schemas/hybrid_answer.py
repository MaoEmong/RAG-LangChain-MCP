"""
reasoning/schemas/hybrid_answer.py
============================================================
DB 조회 결과와 문서 근거를 결합한 하이브리드 응답의 표준 스키마.

설명:
- `HybridAnswerResult`는 DB 요약(`db_summary`)을 사실 기준으로 삼고,
  문서 기반 보강 설명(`doc_notes`)을 추가한 뒤 최종 `answer` 텍스트를
  포함합니다. `speech`는 요약형 한 줄 응답입니다.
"""

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class HybridAnswerResult(BaseModel):
    """
    DB + 문서 하이브리드 응답 스키마.

    필드 요약:
    - speech: 한 문장 요약
    - db_summary: DB 결과 요약
    - doc_notes: 문서 근거 기반 보강 설명
    - answer: 사용자가 보게 될 최종 답변
    """

    type: Literal["hybrid_answer"] = "hybrid_answer"
    speech: str
    db_summary: str
    doc_notes: str
    answer: str
