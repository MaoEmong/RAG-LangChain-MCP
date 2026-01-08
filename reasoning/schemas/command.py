"""
reasoning/schemas/command.py
============================================================
LLM이 생성하는 명령(명령 제안) JSON 구조를 검증하는 Pydantic 스키마.

설명:
- 이 스키마는 LLM이 반환한 명령 JSON을 안전하게 파싱/검증하기 위해 사용됩니다.
- 실제 실행은 `actions`에 명시된 함수 이름과 인자를 서버 쪽 화이트리스트/검증을
  거쳐 수행되어야 합니다.
"""

from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field


class CommandAction(BaseModel):
    """
    단일 실행 액션을 표현하는 스키마.

    필드:
    - name: 호출할 함수 이름(화이트리스트에 등록된 것만 허용해야 함)
    - args: 함수에 전달할 인자 딕셔너리(없으면 빈 dict)
    """
    # 실행할 함수 이름 (예: "OpenUrl", "ShowNotification")
    name: str = Field(..., description="실행할 함수 이름")

    # 함수 인자 딕셔너리 (인자가 없으면 빈 딕셔너리 {})
    args: Dict[str, Any] = Field(default_factory=dict)


class CommandResponse(BaseModel):
    """
    전체 명령 응답 스키마.

    필드:
    - type: 항상 "command"
    - speech: 사용자에게 보여줄 한 줄 안내 문구
    - actions: 실행할 액션 목록(순차 실행 가능)
    """
    # 타입은 항상 "command"로 고정 (다른 타입과 구분)
    type: Literal["command"] = "command"

    # 사용자에게 보여줄/말해줄 한 문장
    # 예: "URL을 열었습니다", "알림을 표시했습니다"
    speech: str

    # 실행할 액션 목록 (여러 액션을 순차적으로 실행 가능)
    # 빈 배열이면 실행할 액션 없음 (설명/질문에 가까운 경우)
    actions: List[CommandAction] = Field(default_factory=list)
