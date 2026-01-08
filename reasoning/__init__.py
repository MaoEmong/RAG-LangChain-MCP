"""reasoning 패키지
============================================================
LLM 기반 추론 체인, 프롬프트, 스키마, 서비스를 포함하는 패키지입니다.

주요 서브패키지:
- chains: RAG, SQL 쿼리, DB 요약, 명령 등 LLM 체인 구현
- prompts: 각 체인에 사용되는 프롬프트 템플릿
- schemas: LLM 출력 구조화를 위한 Pydantic 스키마
- services: DB 조회, SQL 검증, 의도 분류 등 지원 서비스

흐름:
1. 사용자 요청이 들어옴
2. intent_classifier가 요청 의도 분류 (RAG/SQL/명령)
3. 해당 체인 실행 (rag_chain, sql_query_chain 등)
4. LLM 결과를 파싱하여 최종 응답 생성
"""