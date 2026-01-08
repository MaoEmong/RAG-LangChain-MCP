"""
reasoning/services/command_parser.py
============================================================
LLM이 생성한 명령(JSON 텍스트)을 안전하게 파싱하고 Pydantic 스키마로
검증하는 유틸리티 모듈.

설명:
- LLM은 항상 정확한 JSON을 반환하지 않을 수 있으므로 방어적으로 파싱합니다.
- 이 모듈은 파싱 실패나 스키마 불일치가 발생하면 None을 반환하여
    상위 로직에서 폴백 또는 오류 응답을 처리할 수 있게 합니다.
"""

import json
from ..schemas.command import CommandResponse
from pydantic import ValidationError

def parse_command_json(text: str) -> CommandResponse | None:
    """
    LLM 응답(JSON 텍스트)을 `CommandResponse`로 파싱하여 반환합니다.

    동작:
    1. JSON 파싱
    2. Pydantic 검증(CommandResponse 모델)
    3. 검증 실패 시 None 반환

    Args:
        text (str): LLM이 반환한 텍스트(예상 JSON)

    Returns:
        CommandResponse | None: 파싱 및 검증 성공 시 객체, 실패 시 None
    """
    try:
        # JSON 문자열을 Python 딕셔너리로 파싱
        data = json.loads(text)
        
        # Pydantic 모델로 검증 및 변환
        # - 필수 필드 확인
        # - 타입 검증
        # - 스키마 규칙 검증
        return CommandResponse.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        # JSON 파싱 오류 또는 스키마 검증 실패 시 None 반환
        return None
