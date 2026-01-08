# LangChain 기반 하이브리드 RAG 서버 (MCP)

문서 기반 QA, 명령 JSON 생성, DB 연동을 통합한 FastAPI RAG 서버입니다.  
Parent-Document Retriever, FlashRank Re-Ranking, DB+문서 하이브리드 응답, intent 자동 분기, MCP(Model Context Protocol) 지원을 포함합니다.

**문서화 상태**: 모든 Python 파일에 한국어 도큐스트링 및 상세 주석 추가됨 (포트폴리오 공개용)

## 주요 기능

- **다중 포맷 문서 로딩** → 청킹 → 벡터 적재 (`ingest_langchain.py`)
  - PDF (텍스트 PDF / 스캔 PDF 자동 구분)
  - 텍스트 파일 (TXT, MD)
  - Word 문서 (DOCX)
  - HTML 파일
- **PDF 자동 처리**:
  - 텍스트 PDF: PyMuPDF로 직접 텍스트 추출
  - 스캔 PDF: Tesseract OCR을 사용한 이미지 텍스트 인식 (한국어/영어 지원)
- **DB + 문서 하이브리드 QA** (`/ask`):
  - MySQL 화이트리스트 쿼리를 LLM이 선택·검증 후 실행
  - DB 결과와 문서 검색 컨텍스트를 합쳐 `hybrid_answer`로 응답
- Parent-Document Retriever: child는 검색/랭킹, parent는 LLM 컨텍스트 (Chroma + SQLite)
- 2단계 검색: 벡터 검색 → FlashRank Re-Ranking
- Guardrail & Confidence: top score 컷, good hit 개수, 신뢰도 점수/레벨 반환
- Intent 분류(`/ask`): explain/command로 자동 라우팅
- 명령 JSON 생성 + 파싱 + 화이트리스트 검증(`/command`)
- 출처/score/미리보기 포함 RAG 응답(`/chat`)

## 기술 스택

- Python 3, FastAPI, Uvicorn
- LangChain(OpenAI, Chroma, Text Splitters, Community)
- Parent-Document Retriever 패턴 (Chroma child + SQLite parent)
- FlashRank Re-Ranker
- Pydantic
- PyMuPDF (PDF 텍스트 추출)
- Tesseract OCR (스캔 PDF 이미지 인식)
- MySQL + mysql-connector-python (DB 랭킹/점수 조회)

## 폴더 구조

```
.
├── api/                  # FastAPI 서버 관련 파일
│   └── rag_server.py     # FastAPI 엔트리포인트 (/chat, /command, /ask)
├── chains/               # LLM 체인 구현 (RAG/SQL/DB/하이브리드)
│   ├── __init__.py
│   ├── rag_chain.py
│   ├── sql_query_chain.py
│   ├── db_query_chain.py
│   ├── db_summary_chain.py
│   ├── hybrid_chain.py
│   ├── hybrid_onecall_chain.py
│   └── command_chain.py
├── commands/             # 명령 화이트리스트
│   ├── __init__.py
│   └── registry.py       # 허용 명령 목록 및 파라미터 정의
├── docs/                 # 원본 문서 저장 폴더
├── ingest/               # 문서 수집 및 벡터DB 구축
│   ├── __init__.py
│   ├── ingest_langchain.py   # 문서 적재 스크립트
│   ├── docstore_sqlite.py    # SQLite 기반 Parent 문서 저장소
│   └── debug_chroma_scan.py  # ChromaDB 디버깅 스크립트
├── loaders/              # 문서 로더 (다중 포맷 지원)
│   ├── auto_loader.py    # 자동 문서 로더 (PDF 자동 구분)
│   ├── pdf_detector.py   # PDF 종류 판별기 (텍스트/스캔)
│   ├── pdf_text_loader.py # 텍스트 PDF 로더
│   ├── pdf_scan_loader.py # 스캔 PDF 로더 (OCR)
│   └── rules.py          # 파일 확장자별 로더 규칙
├── ocr/                  # OCR 엔진
│   ├── __init__.py
│   ├── base.py           # OCR 베이스 클래스
│   ├── tesseract_ocr.py  # Tesseract OCR 구현
│   └── dummy_ocr.py      # 더미 OCR (테스트용)
├── preprocess/           # 전처리 유틸리티
│   └── text_cleaner.py   # 텍스트 정리
├── prompts/              # LLM 프롬프트 템플릿
│   ├── __init__.py
│   ├── command_prompt.py
│   ├── intent_prompt.py
│   ├── rag_prompt.py
│   ├── sql_query_prompt.py
│   ├── db_query_prompt.py
│   ├── db_summary_prompt.py
│   ├── hybrid_onecall_prompt.py
│   └── hybrid_prompt.py
├── reasoning/            # LLM 기반 추론 모듈
│   ├── __init__.py
│   ├── chains/          # LLM 체인들
│   ├── prompts/         # 프롬프트 템플릿
│   ├── schemas/         # Pydantic 스키마
│   └── services/        # 검색/파싱/검증 서비스
├── retrieval/            # 검색 및 벡터화
│   ├── retrieval.py      # Parent-Child 검색 + FlashRank re-ranking
│   ├── vector_store.py   # ChromaDB 벡터 저장소
│   └── rerank_flashrank.py # FlashRank 재정렬 엔진
├── schemas/              # Pydantic 스키마 정의
│   ├── __init__.py
│   ├── command.py
│   ├── intent.py
│   ├── rag_answer.py
│   ├── sql_query.py
│   ├── db_query.py
│   ├── db_summary.py
│   └── hybrid_answer.py
├── services/             # 비즈니스 로직 서비스
│   ├── __init__.py
│   ├── retrieval.py      # Parent-Child 검색
│   ├── vector_store.py   # 벡터 저장소 관리
│   ├── intent_classifier.py        # 의도 분류
│   ├── command_parser.py           # 명령 JSON 파싱
│   ├── command_validator.py        # 명령 검증
│   ├── db_service.py               # MySQL 연결 및 쿼리 실행
│   ├── db_router.py                # DB 질문 판별
│   ├── db_schema_provider.py       # DB 스키마 정보 제공
│   ├── db_query_parser.py          # DB 쿼리 JSON 파싱
│   ├── db_query_validator.py       # DB 쿼리 검증
│   ├── db_summary_parser.py        # DB 요약 결과 파싱
│   ├── db_fallback_summary.py      # DB 요약 폴백
│   ├── sql_query_parser.py         # SQL 쿼리 파싱
│   ├── sql_validator.py            # SQL SELECT 전용 검증
│   ├── hybrid_parser.py            # 하이브리드 답변 파싱
│   └── confidence.py               # 신뢰도 계산
├── test/                 # 테스트 스크립트
│   ├── test_loaders.py   # 로더 테스트
│   ├── test_retrieval.py # 검색 기능 테스트
│   └── test_db.py        # DB 연결 테스트
├── config.py             # 전역 설정 파일
├── query_test.py         # 검색 단독 테스트
├── requirements.txt      # 프로젝트 의존성
├── chroma_db/            # ChromaDB 벡터 저장소 (자동 생성)
└── README.md             # 이 파일
```

## 주요 파일 설명

### 루트 디렉토리

#### FastAPI 서버

- **`api/rag_server.py`**: FastAPI 서버 메인 파일
  - `/chat`, `/command`, `/ask` 엔드포인트 제공
  - 2단계 검색 파이프라인 (벡터 검색 + FlashRank Re-Ranking) 실행
  - Guardrail 및 Confidence 계산
  - 모든 엔드포인트에 상세 한국어 도큐스트링 포함

#### 문서 수집 및 테스트

- **`ingest/ingest_langchain.py`**: 문서 수집 및 벡터DB 구축 스크립트
  - `docs/` 폴더의 문서를 읽어서 ChromaDB에 저장
  - Parent-Child 구조로 저장 (검색은 child, LLM 컨텍스트는 parent)
  - 문서 청킹 및 임베딩 변환
  - 상세한 한국어 도큐스트링 포함

- **`query_test.py`**: 벡터 검색 기능만 단독으로 테스트하는 스크립트
  - 서버 실행 없이 검색 결과 확인 가능
  - 한국어 사용법 주석 포함

- **`config.py`**: 프로젝트 전역 설정 파일
  - OpenAI API 키, 모델 설정, Guardrail 파라미터 등
  - 민감한 정보는 플레이스홀더로 표시
  - 상세 한국어 설명 추가

### loaders/

- **`auto_loader.py`**: 자동 문서 로더
  - 폴더 내 모든 문서를 자동으로 감지하고 적절한 로더 선택
  - PDF 파일의 경우 텍스트 PDF와 스캔 PDF를 자동 구분하여 처리
  - 문서 메타데이터 자동 추가 (doc_id, source, kind, domain 등)
- **`pdf_detector.py`**: PDF 종류 판별기
  - 텍스트 레이어 존재 여부를 확인하여 텍스트 PDF/스캔 PDF 자동 판별
- **`pdf_text_loader.py`**: 텍스트 PDF 로더
  - PyMuPDF를 사용하여 텍스트 레이어에서 직접 텍스트 추출
  - 파일당 Document 1개로 통합 로드
- **`pdf_scan_loader.py`**: 스캔 PDF 로더
  - Tesseract OCR을 사용하여 이미지에서 텍스트 추출
  - 한국어/영어 다국어 지원
  - 파일당 Document 1개로 통합 로드
- **`rules.py`**: 파일 확장자별 로더 규칙
  - TXT, MD, PDF, DOCX, HTML 등의 로더 매핑

### ocr/

- **`base.py`**: OCR 베이스 클래스
  - OCR 엔진의 공통 인터페이스 정의
- **`tesseract_ocr.py`**: Tesseract OCR 구현
  - PDF를 이미지로 렌더링한 후 OCR 수행
  - 다국어 지원 (한국어, 영어 등)
- **`dummy_ocr.py`**: 더미 OCR (테스트용)

### preprocess/

- **`text_cleaner.py`**: 텍스트 정리 유틸리티
  - 개행 문자 통일, 과도한 공백 제거 등

### reasoning/ 패키지

#### `reasoning/chains/` - LLM 체인 구현
- **`rag_chain.py`**: RAG 체인
  - 벡터 검색된 문서를 컨텍스트로 변환
  - LangChain 체인으로 질문 → 검색 → 답변 생성 파이프라인 구성
  - 모든 함수에 한국어 도큐스트링 포함

- **`sql_query_chain.py`**: SQL 쿼리 생성 체인
  - 자연어 → SQL 쿼리 변환
  - SELECT 전용 검증으로 보안 강화

- **`db_query_chain.py`**: DB 쿼리 선택 체인
  - 허용된 DB 쿼리 목록 중 하나를 선택하도록 LLM 가이드

- **`db_summary_chain.py`**: DB 요약 체인
  - DB 조회 결과를 자연어로 요약

- **`hybrid_chain.py`**: 2단계 하이브리드 체인
  - DB 요약 + 문서 컨텍스트를 합쳐 최종 답변 생성

- **`hybrid_onecall_chain.py`**: 단일 호출 하이브리드 체인
  - DB rows + 문서 컨텍스트를 한 번에 처리

- **`command_chain.py`**: 명령 생성 체인
  - 자연어 명령을 JSON 형식으로 변환

#### `reasoning/prompts/` - LLM 프롬프트 템플릿
- **`intent_prompt.py`**: 의도 분류 프롬프트
  - 사용자 입력을 "command" 또는 "explain"으로 분류

- **`rag_prompt.py`**: RAG 응답 프롬프트
  - 검색된 문서 컨텍스트 기반 응답 생성

- **`sql_query_prompt.py`**: SQL 생성 프롬프트
  - 자연어 → SQL 변환 프롬프트

- **`db_query_prompt.py`**: DB 쿼리 선택 프롬프트
  - 허용 쿼리 목록 중 선택

- **`db_summary_prompt.py`**: DB 요약 프롬프트
  - 결과 요약 프롬프트

- **`hybrid_onecall_prompt.py`**: 하이브리드 단일 호출 프롬프트
  - DB + 문서 통합 프롬프트

- **`hybrid_prompt.py`**: 하이브리드 2단계 프롬프트
  - 폴백용 하이브리드 프롬프트

- **`command_prompt.py`**: 명령 생성 프롬프트
  - JSON 명령 생성 프롬프트

#### `reasoning/schemas/` - Pydantic 스키마
- **`intent.py`**: 의도 분류 결과 스키마
  - `IntentResult` 모델

- **`rag_answer.py`**: RAG 답변 스키마
  - 검색 기반 응답 구조

- **`sql_query.py`**: SQL 쿼리 스키마
  - 생성된 SQL 쿼리 구조

- **`db_query.py`**: DB 쿼리 요청 스키마
  - `DBQueryRequest` 모델

- **`db_summary.py`**: DB 요약 결과 스키마
  - `DBSummaryResult` 모델

- **`hybrid_answer.py`**: 하이브리드 답변 스키마
  - DB + 문서 통합 응답 구조

- **`command.py`**: 명령 스키마
  - `CommandResponse`, `CommandAction` 모델

#### `reasoning/services/` - 비즈니스 로직 서비스
모든 서비스는 단일 책임 원칙(SRP)을 따르며 상세한 한국어 도큐스트링 포함:

**검색 및 순위 매김**
- **`retrieval.py`**: Parent-Child 검색 + FlashRank re-ranking
  - 2단계 검색 파이프라인 구현
  - OCR 키워드 바이어스

- **`rerank_flashrank.py`**: FlashRank 재정렬 엔진
  - 검색 결과 의미적 관련성 기반 재정렬

**의도 분류 및 라우팅**
- **`intent_classifier.py`**: 사용자 의도 분류
  - Rule 기반 + LLM 기반 하이브리드
  - "command" 또는 "explain" 분류

- **`db_router.py`**: DB 질문 판별
  - 사용자 질문이 DB 관련인지 판별

**명령 처리**
- **`command_parser.py`**: 명령 JSON 파싱
  - LLM 생성 명령 JSON 파싱

- **`command_validator.py`**: 명령 화이트리스트 검증
  - `commands/registry.py` 기반 검증

**SQL 쿼리 처리**
- **`sql_query_parser.py`**: SQL 쿼리 파싱
  - LLM 생성 SQL 파싱

- **`sql_validator.py`**: SQL SELECT 전용 검증
  - DML(INSERT, UPDATE, DELETE) 차단

**DB 쿼리 처리**
- **`db_service.py`**: MySQL 연결 및 쿼리 실행
  - 허용 쿼리 화이트리스트 기반 실행

- **`db_schema_provider.py`**: DB 스키마 정보 제공
  - LLM에 제공할 DB 구조 정보

- **`db_query_parser.py`**: DB 쿼리 JSON 파싱
  - LLM이 생성한 DB 쿼리 JSON 파싱

- **`db_query_validator.py`**: DB 쿼리 검증
  - 허용 쿼리 및 파라미터 검증

**DB 요약**
- **`db_summary_parser.py`**: DB 요약 결과 파싱
  - LLM 요약 결과 파싱

- **`db_fallback_summary.py`**: DB 요약 폴백
  - LLM 실패 시 규칙 기반 요약 생성

**하이브리드 답변**
- **`hybrid_parser.py`**: 하이브리드 답변 파싱
  - DB + 문서 통합 응답 파싱

**신뢰도 및 guardrail**
- **`confidence.py`**: 신뢰도 계산
  - 검색 점수 + 좋은 문서 개수 기반 신뢰도 계산
  - high/medium/low 레벨 분류

### 테스트 파일 (test/ 폴더)

- **`test/test_loaders.py`**: 문서 로더 테스트 스크립트
  - PDF 종류 판별 테스트
  - 텍스트 PDF 추출 샘플 출력
  - 스캔 PDF OCR 샘플 출력
  - AutoLoader 전체 요약
  - 한국어 도큐스트링 포함

- **`test/test_retrieval.py`**: 검색 기능 테스트 스크립트
  - ChromaDB에서 Child 문서 검색
  - doc_id별 랭킹
  - SQLiteDocStore에서 Parent 문서 복원
  - 상세한 한국어 함수 설명

- **`test/test_db.py`**: DB 연결 및 쿼리 테스트
  - MySQL 연결 확인
  - 샘플 쿼리 실행
  - 한국어 도큐스트링 포함

- **`query_test.py`** (루트): ParentDocumentRetriever 동작 테스트
  - 대화형 질의응답 테스트

## 설치 & 환경 설정

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. Tesseract OCR 설치 (스캔 PDF 처리용)

스캔 PDF 파일을 처리하려면 Tesseract OCR이 필요합니다.

**Windows:**

1. [Tesseract OCR 설치 프로그램](https://github.com/UB-Mannheim/tesseract/wiki) 다운로드 및 설치
2. 기본 설치 경로: `C:\Program Files\Tesseract-OCR\tesseract.exe`
3. `loaders/auto_loader.py`와 `ocr/tesseract_ocr.py`에서 경로 확인/수정

**Linux (Ubuntu/Debian):**

```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-kor  # 한국어 지원
```

**macOS:**

```bash
brew install tesseract
brew install tesseract-lang  # 다국어 지원
```

**참고:**

- 한국어 지원을 위해 한국어 언어팩 설치 권장
- 설치 후 언어 코드: `"eng+kor"` (영어+한국어)

## 환경 변수(.env 권장)

```
OPENAI_API_KEY=your-api-key
EMBED_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini
CHROMA_DIR=./chroma_db
COLLECTION_NAME=my_rag_docs
TOP_K=4
DOCSTORE_PATH=./parent_docstore.sqlite

# 선택사항 - MySQL 설정 (DB 질문 사용 시)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_db

# 선택사항 - Tesseract OCR 설정 (스캔 PDF 처리)
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
OCR_LANGUAGE=eng+kor
```

**보안 권장사항:**
- 민감한 정보는 환경 변수나 비밀 관리 서비스 사용
- Git에 `.env` 파일 커밋 금지 (`.gitignore`에 추가)

## 데이터 적재(ingest)

문서를 `docs/`에 넣고 실행:

```bash
python ingest/ingest_langchain.py
```

### 지원 파일 형식

- **PDF**: 텍스트 PDF와 스캔 PDF 자동 구분
  - 텍스트 PDF: PyMuPDF로 직접 텍스트 추출
  - 스캔 PDF: Tesseract OCR로 이미지 텍스트 인식
- **텍스트 파일**: TXT, MD
- **Word 문서**: DOCX
- **HTML 파일**: HTML, HTM

### 처리 방식

- **청크 설정**: 기본 800자, 오버랩 100자 (`config.py` / `ingest/ingest_langchain.py`)
- **저장 방식**: child→Chroma, parent→SQLite(`parent_docstore.sqlite`)
- **PDF 처리**: 파일당 Parent 문서 1개로 통합 (페이지별 분할 없음)
- **메타데이터**: 각 문서에 자동 추가
  - `doc_id`: 파일별 고유 ID
  - `source`: 파일 경로
  - `kind`: 문서 종류 (pdf_text, pdf_scan_ocr, txt, md 등)
  - `domain`: 도메인 태그
  - `page`: 페이지 번호 (해당시)
- **재실행**: 원본 문서 변경 시 재실행

### 처리 흐름

```python
# ingest/ingest_langchain.py 실행
# 1. docs/ 폴더 스캔
# 2. PDF 자동 구분 (텍스트 vs 스캔)
# 3. 텍스트 추출 (PyMuPDF 또는 Tesseract OCR)
# 4. 파일별 Parent 문서 생성 및 SQLite 저장
# 5. Child 청크 생성 및 ChromaDB 벡터 저장
# 6. 진행 상황 콘솔 출력
```

## 서버 실행

### 1. 문서 적재 (처음 한 번만)

```bash
python ingest/ingest_langchain.py
```

### 2. FastAPI 서버 시작

```bash
uvicorn api.rag_server:app --reload --port 8000
```

또는 내장 테스트:

```bash
python -m uvicorn api.rag_server:app --reload --port 8000
```

### 3. API 테스트

브라우저에서 대화형 API 문서 보기:
```
http://localhost:8000/docs
```

## API 엔드포인트

### `/chat` - RAG 기반 Q&A

**요청:**
```json
{
  "question": "질문 내용"
}
```

**응답:**
```json
{
  "answer": "응답 텍스트",
  "sources": [
    {
      "source": "문서 경로",
      "score": 0.95,
      "preview": "미리보기 텍스트..."
    }
  ],
  "guard": {
    "reason": "ok",
    "top_score": 0.85,
    "good_hits": 3
  },
  "confidence": {
    "level": "high",
    "score": 0.92,
    "details": {
      "base": 0.85,
      "bonus": 0.07
    }
  }
}
```

### `/command` - 명령 JSON 제안

**요청:**
```json
{
  "question": "어떤 작업을 하고 싶은지"
}
```

**응답:**
```json
{
  "speech": "요약 음성",
  "actions": [
    {
      "action": "명령이름",
      "params": {
        "param1": "값1"
      }
    }
  ],
  "confidence": 0.9,
  "guard": {
    "reason": "ok"
  }
}
```

### `/ask` - 의도 기반 통합 인터페이스

**요청:**
```json
{
  "question": "질문 또는 명령"
}
```

**응답 (DB 질문인 경우):**
```json
{
  "type": "hybrid_answer",
  "question": "...",
  "speech": "...",
  "db_summary": "DB 조회 결과 요약",
  "doc_notes": "관련 문서 추가 설명",
  "answer": "최종 통합 답변",
  "query": "GetTopScores",
  "params": { "limit": 10 },
  "rows": [ ... ],
  "sources": [ ... ],
  "guard": { "reason": "ok" }
}
```

**응답 (일반 질문인 경우):**
```json
{
  "type": "rag_answer",
  "answer": "...",
  "sources": [ ... ],
  "guard": { "reason": "ok" },
  "confidence": { "level": "high", "score": 0.9 }
}
```

### 호출 예시

```bash
# RAG 질문
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "RAG 파이프라인 설명"}'

# 명령 요청
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"question": "화면 밝기 올려줘"}'

# 통합 인터페이스 (의도 자동 판별)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "지난주 상위 점수는?"}'
```

## 동작 흐름

### 1. 문서 수집 (Ingest)

1. `docs/` 폴더에서 문서 자동 탐색
2. PDF 파일: 텍스트 PDF/스캔 PDF 자동 판별
   - 텍스트 PDF: PyMuPDF로 텍스트 추출
   - 스캔 PDF: Tesseract OCR로 이미지 텍스트 인식
3. 각 파일에 `doc_id` 부여 (파일별 고유 ID)
4. 파일당 Parent 문서 1개 생성 (모든 페이지 통합)
5. Parent 문서를 Child 청크로 분할 (800자, 오버랩 100자)
6. Parent는 SQLite 저장, Child는 ChromaDB에 벡터로 저장

### 2. 검색 요청 (문서)

1. Child 문서 similarity 검색 (initial_k=20)
   - OCR 키워드 질의 시 OCR 문서 우선 검색 (키워드 바이어스)
2. FlashRank Re-ranking으로 결과 재정렬
3. Parent 문서 복원 및 중복 제거
4. Parent별 최소 distance score 계산
5. Guardrail 및 신뢰도 계산

### 3. `/chat` 엔드포인트

1. Parent 컨텍스트 포맷 (문서별 900자, 전체 3,500자)
2. `_trim_context`로 최대 12,000자 제한
3. LLM 응답 생성 + 출처 정보 반환

### 4. `/command` 엔드포인트

1. 동일 컨텍스트 사용
2. LLM이 JSON 형식 명령 생성
3. JSON 파싱 및 화이트리스트 검증
4. 신뢰도 낮으면 차단

### 5. `/ask` 엔드포인트 (DB + 문서 하이브리드)

1. 질문이 DB 관련이면:
   - 허용 쿼리 목록(DB 화이트리스트) 중 하나를 LLM이 선택해 JSON 생성
   - 서버에서 검증 후 MySQL 실행 (rows 최대 50건 사용)
   - 문서 검색 컨텍스트와 합쳐 `hybrid_answer`로 응답
   - 실패 시: 기본 쿼리 `GetTopScores` + 규칙 기반 요약으로 폴백
2. DB 관련이 아니면:
   - intent 분류(`command`/`explain`) 후 `/command` 또는 `/chat` 로직 실행

## 주요 설정 포인트

- `ingest_langchain.py`: Parent/Child split(`build_parent_retriever`), `COLLECTION_NAME`
- `config.py`: `CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`, `TOP_K`, `TOP_SCORE_MAX`, `MIN_GOOD_HITS`, `GOOD_HIT_SCORE_MAX`, `CONF_SCORE_MIN/MAX`, `DOCSTORE_PATH`
- `rag_server.py`: `INITIAL_K=20`, `_trim_context` 최대 12,000자
- `services/retrieval.py`: `fetch_multiplier=3`로 rerank 범위를 top_k보다 넓혀 parent dedupe 손실 완화
- `commands/registry.py`: 허용 명령/필수 args 정의

## 아키텍처 메모 (Parent-Document Retriever)

- 검색은 child 청크(Chroma), LLM 컨텍스트는 parent(SQLite)
- 흐름: child 검색 → FlashRank rerank → parent 복원/중복 제거 → parent별 최소 distance score → guard/confidence → 컨텍스트 컷 → LLM

## 운영/보안 팁

- API 키는 환경 변수/비밀 관리 서비스 사용
- `chroma_db/`는 필요 시 재생성 가능(ingest 재실행)
- PDF 파일 처리:
  - 텍스트 PDF는 빠르게 처리 가능
  - 스캔 PDF는 OCR 처리로 시간이 오래 걸릴 수 있음 (파일 크기 및 페이지 수에 비례)
  - OCR 정확도를 높이려면 고해상도 PDF 사용 권장
- 문제 발생 시 `docs/troubleshooting.txt` 참고

## 주요 특징

### PDF 자동 구분

- 텍스트 레이어 존재 여부를 자동으로 판별
- 텍스트 PDF: 빠른 직접 추출
- 스캔 PDF: OCR을 통한 이미지 텍스트 인식

### OCR 키워드 검색 최적화

- 운송장 번호, 트래킹 코드 등의 키워드 검색 시 OCR 문서 우선 검색
- 키워드 바이어스를 통한 검색 정확도 향상

### Parent-Child 구조

- 검색은 작은 Child 청크로 정확도 향상
- LLM 컨텍스트는 전체 Parent 문서로 제공하여 컨텍스트 유지
