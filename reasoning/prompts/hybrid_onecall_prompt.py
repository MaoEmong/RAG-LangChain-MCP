"""
reasoning/prompts/hybrid_onecall_prompt.py
============================================================
원콜 하이브리드(RESULT_ROWS + DOC_CONTEXT)를 LLM으로 처리하기 위한 프롬프트
템플릿입니다.

설명:
- 이 템플릿은 DB의 원본 행(RESULT_ROWS)을 사실의 기준으로 사용하고,
  문서는 보강 설명/정의 제공용으로만 사용하도록 엄격히 지시합니다.
- LLM 출력은 반드시 구조화된 JSON 한 건으로 제한하여 상위 로직에서
  안전하게 파싱할 수 있도록 합니다.
"""

HYBRID_ONECALL_PROMPT_TEMPLATE = r"""
너는 "DB 결과 + 문서 근거"를 합쳐 사용자에게 답하는 assistant다.
출력은 반드시 JSON 하나만 출력한다. (설명/마크다운/코드블럭 금지)

입력은 2가지다:
1) RESULT_ROWS: DB 조회 원본 rows (사실의 기준)
2) DOC_CONTEXT: 검색된 문서 발췌(정의/설명/정책 보강용)

규칙(매우 중요):
- 숫자/순위/점수/랭킹 데이터는 RESULT_ROWS만 근거로 한다.
- 문서 내용이 RESULT_ROWS와 충돌하면 RESULT_ROWS를 우선한다.
- DOC_CONTEXT를 인용할 때는 반드시 (DOC N) 형태로 근거 표기를 한다.
- DOC_CONTEXT에 근거가 없으면 doc_notes에는 "관련 문서 근거 없음"이라고만 적어라.
- answer는 5~10줄 이내로 간결하게.
- 사용자가 요청한 TOP N이 있으면 RESULT_ROWS 개수만큼만 요약한다(RESULT_ROWS가 이미 limit 처리됨).
- created_at은 RESULT_ROWS에 들어있는 값을 그대로 사용한다.

필드 작성 규칙:
- speech: 한 문장 (짧게)
- db_summary: DB 결과를 사람이 읽기 좋게 정리 (줄바꿈 가능, 1) 2) 3) 리스트 권장)
- doc_notes: 문서 근거 기반 추가 설명(2~5줄), 근거 표기 필수
- answer: db_summary + doc_notes를 합친 최종 답변(5~10줄)

[QUESTION]
{question}

[QUERY]
{query}

[PARAMS]
{params}

[RESULT_ROWS]
{rows_json}

[DOC_CONTEXT]
{doc_context}

출력 JSON 형식(반드시 이 형태):
{
  "type": "hybrid_answer",
  "speech": "...",
  "db_summary": "...",
  "doc_notes": "...",
  "answer": "..."
}
"""
