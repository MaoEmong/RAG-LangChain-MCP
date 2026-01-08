"""reasoning/schemas 패키지
============================================================
LLM 출력 구조화를 위한 Pydantic 스키마들을 포함합니다.

주요 스키마:
- intent.py: 의도 분류 결과 (type: rag/sql/command)
- rag_answer.py: RAG 응답 구조
- sql_query.py: SQL 쿼리 생성 결과 (쿼리 + 설명)
- db_query.py: DB 저장 쿼리 선택 결과 (쿼리명 + 파라미터)
- db_summary.py: DB 결과 요약 (제목 + 상세내용)
- hybrid_answer.py: 하이브리드 응답 (RAG결과 + DB결과 + 최종답변)
- command.py: 명령 파라미터 (명령명 + 파라미터)

특징:
- 모든 스키마는 Pydantic BaseModel 상속
- type hint를 통한 자동 검증
- JSON 직렬화 가능
- LLM 함수 호출(OpenAI function calling)에 자동 변환
"""