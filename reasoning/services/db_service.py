"""
reasoning/services/db_service.py
============================================================
MySQL 접근을 추상화한 간단한 서비스 레이어.

설명 및 책임:
- 데이터베이스 연결 생성/종료를 관리합니다.
- 상위 레이어에서 검증된 SELECT 쿼리(보수적 권장)를 실행하고
    결과를 `List[Dict]` 형태로 반환합니다.
- 보안 원칙상 이 모듈은 쿼리의 안전성(예: SELECT-only 검증)을 수행하지 않습니다.
    해당 검증은 호출자(상위 로직)에서 수행되어야 합니다.

포트폴리오 포인트:
- 이 레이어는 단일 책임 원칙(SRP)을 따르며, 테스트 및 모킹이 용이하도록
    디자인되어 있습니다. 실제 운영 환경에서는 커넥션 풀링과 타임아웃,
    로깅/모니터링을 추가해야 합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursorDict


# ============================================================
# Config
# ============================================================
@dataclass(frozen=True)
class MySqlConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


# ============================================================
# Service
# ============================================================
class MySqlService:
    def __init__(self, cfg: MySqlConfig):
        self.cfg = cfg

    # --------------------------------------------------------
    # Internal
    # --------------------------------------------------------
    def _connect(self) -> MySQLConnection:
        """
        MySQL 커넥션 생성
        """
        return mysql.connector.connect(
            host=self.cfg.host,
            port=self.cfg.port,
            user=self.cfg.user,
            password=self.cfg.password,
            database=self.cfg.database,
            autocommit=True,
            connection_timeout=5,
        )

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def run_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        SELECT SQL 실행

        Args:
            sql    : SELECT 쿼리 (서버 상위 레이어에서 검증 완료된 상태)
            params : 파라미터(dict), 없으면 {}

        Returns:
            List[Dict[str, Any]] : row 단위 dict 결과
        """
        params = params or {}

        conn: Optional[MySQLConnection] = None
        cursor: Optional[MySQLCursorDict] = None

        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return rows

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
