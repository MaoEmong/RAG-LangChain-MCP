"""reasoning/prompts 패키지
============================================================
LLM 프롬프트 템플릿들을 포함합니다.

주요 프롬프트:
- intent_prompt.py: 사용자 요청의 의도 분류 (RAG/SQL/명령)
- rag_prompt.py: RAG 체인용 컨텍스트 기반 응답 생성
- sql_query_prompt.py: 자연어 → SQL 쿼리 생성
- db_query_prompt.py: 저장된 쿼리 선택 및 파라미터 추출
- db_summary_prompt.py: DB 결과 자연어 요약
- hybrid_prompt.py: RAG와 DB 결과 합산 프롬프트
- hybrid_onecall_prompt.py: 단일 LLM 호출 하이브리드 프롬프트
- command_prompt.py: 명령 파라미터 추출

특징:
- 모든 프롬프트는 JSON 형식의 구조화된 출력을 명시
- reasoning/schemas 의 Pydantic 스키마와 연동
- Few-shot 예제 포함으로 LLM 성능 향상
"""