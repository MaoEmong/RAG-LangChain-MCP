"""reasoning/services 패키지
============================================================
LLM 체인을 지원하는 서비스 모듈들을 포함합니다.

주요 서비스:
- intent_classifier.py: 사용자 요청 의도 분류
- db_service.py: MySQL 연결 및 쿼리 실행
- db_schema_provider.py: DB 스키마 정보 제공
- db_router.py: 요청이 DB 관련인지 판별
- db_query_parser.py: LLM 출력 파싱 (DB 쿼리)
- db_query_validator.py: DB 파라미터 검증
- db_summary_parser.py: LLM 요약 출력 파싱
- db_fallback_summary.py: LLM 요약 실패 시 규칙 기반 폴백
- sql_query_parser.py: SQL 쿼리 생성 결과 파싱
- sql_validator.py: SQL SELECT 전용 검증 (DML 차단)
- hybrid_parser.py: 하이브리드 응답 파싱
- command_parser.py: 명령 파라미터 파싱
- command_validator.py: 명령 화이트리스트 검증
- confidence.py: 검색 신뢰도 계산

특징:
- 각 서비스는 단일 책임 원칙(SRP) 준수
- 에러 처리 및 로깅 포함
- LLM 결과의 안전한 파싱 및 검증
"""