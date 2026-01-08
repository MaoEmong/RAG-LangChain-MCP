"""
reasoning/services/hybrid_parser.py
------------------------------------------------------------
LLM이 생성한 하이브리드 응답(hybrid_answer) JSON을 파싱하는 유틸리티.

설명:
- LLM의 원콜/원콜-폴백 응답은 JSON 형태로 하이브리드 응답 구조를 반환하도록
  설계되어 있습니다. 이 모듈은 해당 JSON을 안전하게 파싱하여
  `HybridAnswerResult` Pydantic 객체로 변환합니다.

동작 원칙:
- 파싱 실패(형식 불일치, JSON 오류 등) 시 None을 반환하여 상위 로직에서
  폴백 전략을 수행할 수 있도록 합니다.
"""

from __future__ import annotations

import json
from typing import Optional
from ..schemas.hybrid_answer import HybridAnswerResult


def parse_hybrid_json(text: str) -> Optional[HybridAnswerResult]:
    """
    LLM이 반환한 텍스트(예상 JSON)를 파싱하여 `HybridAnswerResult`로 변환합니다.

    Args:
        text (str): LLM의 응답 텍스트

    Returns:
        HybridAnswerResult | None: 파싱 성공 시 객체, 실패 시 None
    """
    try:
        data = json.loads(text)
        return HybridAnswerResult.model_validate(data)
    except Exception:
        return None
