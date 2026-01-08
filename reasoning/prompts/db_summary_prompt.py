"""
reasoning/prompts/db_summary_prompt.py
============================================================
DB 조회 결과(행 목록)를 사람이 읽기 좋은 요약 텍스트로 변환하는
프롬프트 템플릿입니다.

설명:
- 이 템플릿은 서버에서 이미 정렬/limit이 적용된 `RESULT_ROWS`를 그대로
  받아 요약을 생성하도록 설계되었습니다. LLM이 임의로 값을 추가하거나
  순서를 변경하지 않도록 엄격히 지시합니다.
- 출력은 구조화된 JSON 한 건으로 한정되어야 하며, 상위 로직에서 이 JSON을
  파싱하여 사용자 응답으로 사용합니다.
"""

DB_SUMMARY_PROMPT_TEMPLATE = r"""
너는 DB 조회 결과(RESULT_ROWS)를 사용자에게 보여줄 "요약 텍스트"를 만드는 역할이다.

최우선 규칙(반드시 준수):
- 근거는 RESULT_ROWS에만 있다. 추측/상상/추가 정보 생성 금지.
- 출력은 반드시 JSON 하나만 출력한다. (설명, 마크다운, 코드블럭 금지)
- summary는 사람이 읽기 좋은 텍스트이며 줄바꿈(\n)을 포함해도 된다.
- 사용자가 요청한 TOP N을 반드시 지킨다. (PARAMS.limit 또는 질문의 'top N' 의미를 따른다)
- RESULT_ROWS에 있는 순서를 바꾸지 말고 그대로 요약한다. (이미 서버가 정렬/limit 처리함)

포맷 규칙:
- summary 첫 줄: 한 문장 요약(예: "상위 랭킹 TOP 5입니다.")
- summary 두 번째 줄부터: 랭킹/리스트를 "1) ...", "2) ..." 형식으로 작성
- 각 줄 형식(가능하면 동일하게 유지):
  "{{순위}}) {{username}} - {{score}}점 ({{mode}}) / {{created_at}}"
- created_at은 RESULT_ROWS에 들어있는 값을 그대로 사용한다(변형 최소화).
- username/score/mode/created_at 중 누락된 값이 있으면 "-"로 표기한다.

speech 규칙:
- speech는 한 문장(짧게). summary 첫 줄과 비슷해도 된다.
- speech는 없어도 된다.

입력:
[QUESTION]
{question}

[QUERY]
{query}

[PARAMS]
{params}

[RESULT_ROWS]
{rows_json}

출력 JSON 형식(반드시 이 형태로만):
{
  "type": "db_summary",
  "summary": "...",
  "speech": "..."
}
"""
