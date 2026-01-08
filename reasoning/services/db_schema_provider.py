"""
reasoning/services/db_schema_provider.py
------------------------------------------------------------
데이터베이스의 스키마(테이블/컬럼/외래키 등)를 INFORMATION_SCHEMA에서
추출하여 LLM 프롬프트에 넣기 적합한 텍스트로 생성하는 유틸리티입니다.

주요 목적:
- LLM이 SQL을 생성하거나 조인 힌트를 이해하도록 DB 구조를 프롬프트에
  포함시키기 위한 요약 텍스트를 자동으로 만듭니다.

캐시:
- 서버 실행 중 동일한 DB에 대해 중복 쿼리를 피하기 위해 간단한 메모리 캐시를 유지합니다.

주의:
- 이 모듈은 읽기 전용 메타데이터 생성 목적이며, 보안 민감 정보는 포함하지 않습니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import mysql.connector


@dataclass(frozen=True)
class MySqlConnInfo:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class DBSchemaContext:
    schema_text: str


# 간단 캐시(서버 실행 중 1회 생성)
_SCHEMA_CACHE: Dict[str, DBSchemaContext] = {}


def get_db_schema_context(conn: MySqlConnInfo, *, refresh: bool = False) -> DBSchemaContext:
    """
    주어진 MySQL 연결 정보로부터 스키마 요약 텍스트를 반환합니다.

    Args:
        conn (MySqlConnInfo): DB 연결 정보
        refresh (bool): True이면 캐시를 무시하고 재조회합니다.

    Returns:
        DBSchemaContext: 프롬프트에 넣기 적합한 `schema_text`를 포함한 컨텍스트
    """
    cache_key = f"{conn.host}:{conn.port}/{conn.database}"
    if not refresh and cache_key in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[cache_key]

    schema_text = _build_schema_text(conn)
    ctx = DBSchemaContext(schema_text=schema_text)
    _SCHEMA_CACHE[cache_key] = ctx
    return ctx


def _build_schema_text(conn: MySqlConnInfo) -> str:
    db = conn.database

    con = mysql.connector.connect(
        host=conn.host,
        port=conn.port,
        user=conn.user,
        password=conn.password,
        database=db,
        autocommit=True,
        connection_timeout=5,
    )
    try:
        cur = con.cursor(dictionary=True)

        # 1) 테이블 목록
        cur.execute(
            """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
            """,
            (db,),
        )
        tables = [r["TABLE_NAME"] for r in cur.fetchall()]

        # 2) 컬럼 목록
        cur.execute(
            """
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """,
            (db,),
        )
        cols = cur.fetchall()

        table_to_cols: Dict[str, List[dict]] = {}
        for r in cols:
            table_to_cols.setdefault(r["TABLE_NAME"], []).append(r)

        # 3) FK 정보(조인 힌트용)
        cur.execute(
            """
            SELECT
              kcu.TABLE_NAME,
              kcu.COLUMN_NAME,
              kcu.REFERENCED_TABLE_NAME,
              kcu.REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            WHERE kcu.TABLE_SCHEMA = %s
              AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY kcu.TABLE_NAME, kcu.COLUMN_NAME
            """,
            (db,),
        )
        fks = cur.fetchall()

        fk_lines: List[str] = []
        for r in fks:
            fk_lines.append(
                f"- {r['TABLE_NAME']}.{r['COLUMN_NAME']} -> {r['REFERENCED_TABLE_NAME']}.{r['REFERENCED_COLUMN_NAME']}"
            )

        # 4) schema_text 생성
        lines: List[str] = []
        lines.append(f"DB: {db}")
        lines.append("")
        lines.append("TABLES & COLUMNS:")

        for t in tables:
            lines.append(f"\nTABLE {t}")
            for c in table_to_cols.get(t, []):
                col = c["COLUMN_NAME"]
                dtype = c["DATA_TYPE"]
                nullable = c["IS_NULLABLE"]
                key = c["COLUMN_KEY"]  # PRI, MUL, UNI 등
                extra = c["EXTRA"] or ""

                meta = []
                if key == "PRI":
                    meta.append("PK")
                elif key == "UNI":
                    meta.append("UNIQUE")
                elif key == "MUL":
                    meta.append("INDEXED")

                if nullable == "NO":
                    meta.append("NOT NULL")
                if extra:
                    meta.append(extra.upper())

                meta_str = f" ({', '.join(meta)})" if meta else ""
                lines.append(f"- {col}: {dtype}{meta_str}")

        if fk_lines:
            lines.append("\nFOREIGN KEYS (JOIN HINTS):")
            lines.extend(fk_lines)

        lines.append(
            "\nNOTE: Use JOIN when needed. Prefer selecting only necessary columns."
        )

        return "\n".join(lines).strip()

    finally:
        try:
            con.close()
        except Exception:
            pass
