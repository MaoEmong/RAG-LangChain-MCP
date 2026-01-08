"""
reasoning/services/intent_classifier.py
============================================================
사용자 질의의 의도를 판별하는 하이브리드(룰+LLM) 분류기.

설명:
- 빠른 룰 기반 매칭으로 명확한 명령(예: "재생해줘", "켜줘")을 탐지하고,
  애매한 입력은 LLM을 호출해 보다 정확하게 분류합니다.
- 비용과 성능을 고려해 룰 우선, LLM 보조 패턴을 사용합니다.

결과 모델:
- `IntentResult`(intent: "command"|"explain", reason: str)를 반환합니다.
"""

import re
import json
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..schemas.intent import IntentResult
from ..prompts.intent_prompt import INTENT_PROMPT_TEMPLATE

# ============================================================
# Rule 기반 분류: 빠른 패턴 매칭
# ============================================================
# "행동"을 나타내는 대표적인 표현들 (정규식 패턴)
# 필요하면 계속 추가 가능
COMMAND_HINTS = [
    r"해줘", r"해주세요", r"해봐", r"해봐줘",
    r"켜줘", r"꺼줘",
    r"열어줘", r"닫아줘",
    r"재생해줘", r"틀어줘",
    r"저장해줘", r"복사해줘",
    r"이동해줘", r"바꿔줘", r"변경해줘",
    r"실행해줘", r"눌러줘", r"검색해줘",
]

# "설명/질문"을 나타내는 대표적인 표현들
EXPLAIN_HINTS = [
    r"뭐야", r"무슨", r"설명", r"원리", r"왜", r"어떻게",
    r"차이", r"정의", r"의미", r"개념",
]

def rule_intent(question: str) -> Optional[IntentResult]:
    """
    룰 기반 의도 분류.

    - 즉각적으로 명령 패턴이 감지되면 `IntentResult(intent="command")`를 반환합니다.
    - 설명/질문 패턴이 감지되면 `IntentResult(intent="explain")`를 반환합니다.
    - 불명확한 경우 `None`을 반환하여 LLM 분류를 수행하게 합니다.
    """
    q = question.strip()

    # 너무 짧은 입력은 안전하게 explain으로 처리
    if len(q) <= 2:
        return IntentResult(intent="explain", reason="too_short")

    # 명령 힌트 패턴 체크 (우선순위 높음)
    for pat in COMMAND_HINTS:
        if re.search(pat, q):
            return IntentResult(intent="command", reason=f"rule_match:{pat}")

    # 설명 힌트 패턴 체크
    for pat in EXPLAIN_HINTS:
        if re.search(pat, q):
            return IntentResult(intent="explain", reason=f"rule_match:{pat}")

    # 확신 없으면 None 반환 → LLM 분류로 넘김
    return None

# ============================================================
# LLM 기반 분류: 애매한 경우 정확한 분류
# ============================================================
def llm_intent(question: str, llm) -> IntentResult:
    """
    LLM을 이용한 의도 분류.

    - 프롬프트 템플릿을 통해 LLM이 JSON 형태로 의도와 근거를 반환한다고 기대합니다.
    - 반환값 파싱이 실패하면 안전하게 `explain`으로 처리합니다.
    """
    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_template(INTENT_PROMPT_TEMPLATE)
    
    # LangChain 체인 구성: 프롬프트 -> LLM -> 문자열 파싱
    chain = prompt | llm | StrOutputParser()

    # LLM 호출하여 분류 결과 받기
    raw = chain.invoke({"question": question}).strip()

    # LLM이 JSON을 깔끔히 안 주는 경우 대비 (방어 코드)
    try:
        # JSON 파싱
        data = json.loads(raw)
        # IntentResult 객체로 변환
        return IntentResult(**data)
    except Exception:
        # 파싱 실패 시 안전하게 explain로 처리
        return IntentResult(intent="explain", reason="llm_parse_failed")

# ============================================================
# 메인 분류 함수: 하이브리드 방식
# ============================================================
def classify_intent(question: str, llm) -> IntentResult:
    """
    하이브리드 의도 분류 엔트리 포인트.

    - 우선 룰 기반으로 빠르게 판별하고, 룰로 분류되지 않으면 LLM을 사용합니다.
    - 이 함수는 포트폴리오에서 비용-성능 균형을 고려한 설계 예시로 설명하기 좋습니다.
    """
    # 1단계: Rule 기반 분류 시도
    r = rule_intent(question)
    if r:
        return r  # 명확하게 분류되면 바로 반환

    # 2단계: 애매하면 LLM 분류
    return llm_intent(question, llm)