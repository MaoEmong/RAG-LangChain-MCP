"""
reasoning/services/confidence.py
============================================================
검색 결과(벡터 검색)의 신뢰도를 계산하는 유틸리티 모듈.

설명:
- ChromaDB와 같은 벡터 DB는 distance(거리) 기반 점수를 반환하므로,
  이 모듈은 거리 점수를 0.0~1.0 범위의 신뢰도(score)로 정규화하고,
  좋은 품질의 히트 수에 따른 보너스를 더해 최종 신뢰도를 산출합니다.

사용처:
- `rag_server` 등에서 검색 결과의 guardrail 판별(충분한 근거 여부)에 사용됩니다.
"""

from config import CONF_SCORE_MIN, CONF_SCORE_MAX


def normalize_score(score: float) -> float:
    """
    distance 기반 점수를 0.0(최저 신뢰)~1.0(최고 신뢰) 범위로 정규화합니다.

    Args:
        score (float): 벡터 검색의 distance 점수

    Returns:
        float: 정규화된 기본 신뢰도
    """
    # 매우 좋은 점수 이하면 최대 신뢰도
    if score <= CONF_SCORE_MIN:
        return 1.0

    # 최악의 점수 이상이면 최소 신뢰도
    if score >= CONF_SCORE_MAX:
        return 0.0

    # 선형 보간: 점수가 낮을수록 신뢰도 높음
    return 1.0 - (score - CONF_SCORE_MIN) / (CONF_SCORE_MAX - CONF_SCORE_MIN)


def hits_bonus(good_hits: int) -> float:
    """
    좋은 품질의 문서 개수에 따른 보너스 점수를 계산합니다.

    여러 개의 좋은 문서가 있으면 검색의 일관성이 높다고 판단하여
    소폭의 보너스를 부여합니다.

    Returns:
        float: 보너스 점수 (0.0 ~ 0.15)
    """
    if good_hits >= 3:
        return 0.15  # 3개 이상이면 최대 보너스
    if good_hits == 2:
        return 0.10  # 2개면 중간 보너스
    if good_hits == 1:
        return 0.05  # 1개면 작은 보너스
    return 0.0       # 없으면 보너스 없음


def calculate_confidence(top_score: float, good_hits: int) -> dict:
    """
    검색 결과의 종합 신뢰도를 계산하여 레벨과 점수, 상세 내역을 반환합니다.

    Args:
        top_score (float): 최상위 문서의 distance 점수
        good_hits (int): 기준(GOOD_HIT_SCORE_MAX) 이하로 간주되는 문서 수

    Returns:
        dict: {"level": str, "score": float, "details": {"base": float, "bonus": float}}
    """
    # 기본 신뢰도: 최상위 문서 점수 기반
    base = normalize_score(top_score)

    # 보너스: 좋은 문서 개수 기반
    bonus = hits_bonus(good_hits)

    # 최종 신뢰도 (1.0을 넘지 않도록 제한)
    final = min(base + bonus, 1.0)

    # 신뢰도 레벨 분류
    if final >= 0.75:
        level = "high"
    elif final >= 0.5:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "score": round(final, 3),
        "details": {
            "base": round(base, 3),      # 기본 신뢰도
            "bonus": round(bonus, 3),    # 보너스 점수
        },
    }
