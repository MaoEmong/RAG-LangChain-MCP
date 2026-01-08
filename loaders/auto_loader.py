"""
loaders/auto_loader.py
============================================================
디렉터리 내 다양한 형식의 문서를 자동으로 탐색하고 적절한 로더를
선택하여 LangChain `Document` 리스트로 반환하는 유틸리티입니다.

동작 개요:
1. 폴더를 재귀적으로 탐색하여 파일을 발견합니다.
2. 확장자/규칙 기반으로 적절한 로더를 선택합니다 (rules.get_loader_rules).
3. PDF는 `is_text_pdf` 검사로 텍스트 PDF와 스캔 PDF를 구분하여
     각각 `load_pdf_text` 또는 `load_pdf_scan`으로 처리합니다.
4. 각 문서에 `source`, `doc_id`, `kind`, `domain`, `is_scan` 등 메타데이터를
     일관되게 추가합니다.

디자인 포인트 (포트폴리오 설명용):
- 모든 파일을 일괄 처리할 수 있어 대량 문서 수집 파이프라인의
    초기 단계로 적합합니다.
- `doc_id`는 파일 경로 기반의 안정적인 식별자를 생성하여 재처리 시
    동일한 ID를 보장하도록 설계되어 있습니다.

성능/운영 주의:
- OCR은 비용이 많이 드는 작업이므로 대규모 처리 시 병렬화/큐잉이
    필요합니다. Tesseract는 로컬에서 간단히 사용 가능하지만, 대규모는
    클라우드 OCR(Managed OCR) 고려를 권장합니다.
"""

import os
import glob
import uuid
from typing import List, Dict
from langchain_core.documents import Document

from preprocess.text_cleaner import clean_text
from loaders.rules import get_loader_rules

from loaders.pdf_detector import is_text_pdf
from loaders.pdf_text_loader import load_pdf_text
from loaders.pdf_scan_loader import load_pdf_scan

from ocr.dummy_ocr import DummyOCR
from ocr.tesseract_ocr import TesseractOCR

def _stable_doc_id_for_source(source_abs_path: str, cache: Dict[str, str]) -> str:
    """
    파일 경로에 대해 안정적인 doc_id를 생성/반환합니다.
    
    같은 파일 경로에 대해서는 항상 같은 doc_id를 반환하여,
    문서 재처리 시에도 일관된 ID를 유지합니다.
    
    Args:
        source_abs_path: 파일의 절대 경로
        cache: doc_id 캐시 딕셔너리 (경로 -> doc_id 매핑)
    
    Returns:
        str: UUID 형식의 doc_id
    """
    if source_abs_path not in cache:
        cache[source_abs_path] = str(uuid.uuid4())
    return cache[source_abs_path]


def load_docs_from_folder(folder: str) -> List[Document]:
    """
    지정된 폴더 내의 모든 문서를 로드합니다.
    
    처리 방식:
    1. PDF 파일: 텍스트 PDF와 스캔 PDF를 자동 판별하여 처리
       - 텍스트 PDF: PyMuPDF로 직접 텍스트 추출
       - 스캔 PDF: OCR을 사용하여 텍스트 추출
    2. 기타 파일: 확장자 기반으로 적절한 로더 선택
    
    Args:
        folder: 문서가 있는 폴더 경로
    
    Returns:
        List[Document]: 로드된 문서 리스트
        각 문서는 다음 메타데이터를 포함:
        - source: 파일 절대 경로
        - doc_id: 파일별 고유 ID
        - kind: 문서 종류 (pdf_text, pdf_scan_ocr, txt, md 등)
        - domain: 도메인 태그 (pdf_text, ocr_scan 등)
        - is_scan: 스캔 문서 여부 (PDF만)
    """
    docs: List[Document] = []
    rules = get_loader_rules()
    doc_id_cache: Dict[str, str] = {}

    # OCR 엔진 초기화 (스캔 PDF 처리용)
    # Tesseract OCR을 사용하여 한국어와 영어 모두 지원
    ocr = TesseractOCR(
        tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        lang="eng+kor"
    )

    # 폴더 내 모든 파일 재귀적으로 탐색
    for path in glob.glob(os.path.join(folder, "**/*"), recursive=True):
        if not os.path.isfile(path):
            continue

        ext = os.path.splitext(path)[1].lower()
        abs_path = os.path.abspath(path)

        # ===== PDF 파일 처리 (별도 라우팅) =====
        if ext == ".pdf":
            try:
                # PDF 종류 판별 후 적절한 로더 사용
                if is_text_pdf(path):
                    # 텍스트 PDF: 텍스트 레이어가 있는 PDF
                    loaded_docs = load_pdf_text(path)
                else:
                    # 스캔 PDF: 이미지 기반 PDF, OCR 필요
                    loaded_docs = load_pdf_scan(path, ocr=ocr)
        
                # 파일당 하나의 doc_id 생성 (안정적 ID 유지)
                doc_id = _stable_doc_id_for_source(abs_path, doc_id_cache)
                is_scan = not is_text_pdf(path)

                # 각 문서에 메타데이터 추가
                for d in loaded_docs:
                    d.metadata["source"] = abs_path
                    d.metadata["doc_id"] = doc_id  # 파일당 1개 doc_id

                    if is_scan:
                        # 스캔 PDF 메타데이터
                        d.metadata["kind"] = "pdf_scan_ocr"
                        d.metadata["domain"] = "ocr_scan"   # 키워드 바이어스용 핵심 태그
                        d.metadata["is_scan"] = True
                    else:
                        # 텍스트 PDF 메타데이터
                        d.metadata["kind"] = "pdf_text"
                        d.metadata["domain"] = "pdf_text"
                        d.metadata["is_scan"] = False

                    # 텍스트 정리 (공백 정리, 개행 통일 등)
                    d.page_content = clean_text(d.page_content)
        
                docs.extend(loaded_docs)
        
            except Exception as e:
                print(f"[WARN] failed to load PDF: {path} ({e})")
        
            continue
        
        # ===== 기타 파일 처리 (rules 기반) =====
        # 확장자에 따라 적절한 로더 선택
        for rule_ext, make_loader in rules:
            if ext != rule_ext:
                continue

            try:
                # 로더 생성 및 문서 로드
                loader = make_loader(path)
                loaded_docs = loader.load()

                # 파일당 하나의 doc_id 생성
                doc_id = _stable_doc_id_for_source(abs_path, doc_id_cache)

                # 각 문서에 메타데이터 추가
                for d in loaded_docs:
                    d.metadata["source"] = abs_path
                    d.metadata["doc_id"] = doc_id
                    d.metadata["kind"] = ext.lstrip(".")  # 확장자에서 . 제거
                    d.page_content = clean_text(d.page_content)

                docs.extend(loaded_docs)

            except Exception as e:
                print(f"[WARN] failed to load: {path} ({e})")

            break

    return docs
