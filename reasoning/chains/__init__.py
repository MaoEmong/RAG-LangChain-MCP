"""reasoning/chains 패키지
============================================================
LLM 기반 추론 체인들을 포함합니다.

주요 체인:
- rag_chain.py: 벡터 검색 기반 RAG (Retrieval-Augmented Generation)
- sql_query_chain.py: 자연어 → SQL 변환 + SELECT만 실행 (DML 차단)
- db_query_chain.py: 저장된 쿼리(GetTopScores 등) 실행
- db_summary_chain.py: DB 결과를 자연어로 요약
- hybrid_chain.py: RAG와 DB 결과를 모두 활용한 하이브리드 응답
- hybrid_onecall_chain.py: 단일 LLM 호출로 RAG와 DB 결과 통합
- command_chain.py: 명령 화이트리스트 검증 및 실행

특징:
- 모든 체인은 LLM 입력에 guardrail을 적용하여 보안 강화
- 구조화된 JSON 출력을 위해 Pydantic 스키마 사용
- 에러 처리 및 폴백 로직 포함
"""