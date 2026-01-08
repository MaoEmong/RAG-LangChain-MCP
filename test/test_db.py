"""
test_db.py
============================================================
간단한 데이터베이스 호출 테스트 스크립트

설명:
- `reasoning.services.db_service.MySqlService`를 사용해
  사전 정의된 쿼리(`GetTopScores`)를 실행하고 결과 행 수를 출력합니다.

주의:
- 실제 DB 연결 정보는 `config.MYSQL`에서 로드되므로,
  로컬 환경에 맞는 설정이 필요합니다.

사용법:
    python test_db.py
"""

from config import MYSQL
from reasoning.services.db_service import MySqlConfig, MySqlService


def main():
    """DB 연결 및 샘플 쿼리 실행

    - `MYSQL` 설정으로 `MySqlConfig` 객체 생성
    - `MySqlService`로 연결 후 `GetTopScores` 쿼리를 실행
    """
    cfg = MySqlConfig(**MYSQL)
    db = MySqlService(cfg)

    rows = db.run_query("GetTopScores", {"limit": 5})
    print("OK rows:", len(rows))
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
