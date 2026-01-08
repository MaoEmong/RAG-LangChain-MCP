"""
reasoning/schemas/intent.py
============================================================
사용자 입력의 의도 분류 결과를 표현하는 Pydantic 스키마 모듈.

설명:
- 이 스키마는 룰 기반 또는 LLM 기반의 의도 분류 결과를 표준화하여
  상위 로직에서 일관되게 처리할 수 있게 합니다. `reason`은 디버깅/로그용
  간단한 근거 문자열입니다.
"""

from typing import Literal
from pydantic import BaseModel


class IntentResult(BaseModel):
    """
    의도 분류 결과 스키마

    필드:
    - intent: "command" 또는 "explain"
    - reason: 분류 근거(짧은 설명)
    """
    # 분류된 의도: "command" 또는 "explain"
    intent: Literal["command", "explain"]

    # 분류 근거 (예: "rule_match:해줘", "llm_parse_failed")
    reason: str