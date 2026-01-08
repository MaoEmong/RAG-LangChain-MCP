"""
reasoning/services/db_fallback_summary.py
============================================================
LLM 요약이 실패했을 때 규칙 기반으로 안전하게 생성할 수 있는 폴백
요약 텍스트를 만드는 유틸리티입니다.

설명:
- LLM 기반 DB 요약이 파싱 실패나 품질 문제로 사용 불가능할 때, 이 모듈은
  서버가 제공한 원본 `rows`와 `query` 식별자를 기반으로 사람이 읽기 좋은
  텍스트 요약을 생성합니다. 핵심은 예측 가능성과 안전성입니다.
"""

from __future__ import annotations
from typing import Any, Dict, List


def _fmt_value(v: Any) -> str:
    if v is None:
        return "-"
    return str(v)


def build_fallback_summary(
    *,
    question: str,
    query: str,
    params: Dict[str, Any],
    rows: List[Dict[str, Any]],
) -> str:
    """
    규칙 기반 폴백 요약을 생성합니다.

    Args:
        question (str): 원래 사용자 질문(디버깅/문구용)
        query (str): 쿼리 식별자
        params (Dict[str, Any]): 쿼리 파라미터
        rows (List[Dict[str, Any]]): DB에서 반환된 원본 행 목록

    Returns:
        str: 사람이 읽기 좋은 텍스트 요약
    """
    if not rows:
        return "조회 결과가 없습니다."

    # 랭킹류
    if query in ("GetTopScores", "GetTopScoresByModeAndDays"):
        limit = params.get("limit", len(rows))
        lines = [f"랭킹 TOP {limit} (요약 생성 실패로 원본 기반 표시)"]
        for i, r in enumerate(rows, start=1):
            username = _fmt_value(r.get("username"))
            score = _fmt_value(r.get("score"))
            mode = _fmt_value(r.get("mode"))
            created = _fmt_value(r.get("created_at"))
            lines.append(f"{i}) {username} - {score} ({mode}) / {created}")
        return "\n".join(lines)

    # 유저 최근 기록
    if query == "GetUserRecentScores":
        username = _fmt_value(rows[0].get("username") or params.get("username") or "user")
        lines = [f"{username} 최근 점수 (요약 생성 실패로 원본 기반 표시)"]
        for i, r in enumerate(rows, start=1):
            score = _fmt_value(r.get("score"))
            mode = _fmt_value(r.get("mode"))
            created = _fmt_value(r.get("created_at"))
            lines.append(f"{i}) {score} ({mode}) / {created}")
        return "\n".join(lines)

    # 유저 요약
    if query == "GetUserScoreSummary":
        r = rows[0]
        username = _fmt_value(r.get("username") or params.get("username") or "user")
        games = _fmt_value(r.get("games"))
        avg_score = _fmt_value(r.get("avg_score"))
        best_score = _fmt_value(r.get("best_score"))
        return (
            f"{username} 점수 요약 (요약 생성 실패로 원본 기반 표시)\n"
            f"- 플레이 수: {games}\n"
            f"- 평균 점수: {avg_score}\n"
            f"- 최고 점수: {best_score}"
        )

    # 기타: 첫 행 키 일부만 보여주기
    keys = list(rows[0].keys())[:5]
    lines = [f"조회 결과 {len(rows)}건 (요약 생성 실패로 일부 키 표시)"]
    for i, r in enumerate(rows[:10], start=1):
        parts = [f"{k}={_fmt_value(r.get(k))}" for k in keys]
        lines.append(f"{i}) " + ", ".join(parts))
    return "\n".join(lines)
