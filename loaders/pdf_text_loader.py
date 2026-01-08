"""
loaders/pdf_text_loader.py
============================================================
텍스트 레이어가 포함된 PDF 파일을 로드하여 LangChain `Document` 객체로
변환하는 유틸리티.

설명:
- PyMuPDF(fitz)를 사용해 PDF의 텍스트 레이어를 추출합니다.
- 각 페이지의 텍스트를 합쳐 하나의 Parent 문서로 반환하므로,
    이후 chunking/ingest 단계에서 적절히 분할하여 벡터 인덱스에 저장합니다.

반환되는 Document의 메타데이터 예시:
- `source`: 파일 절대 경로
- `page`: None (Parent 문서이므로 개별 페이지 정보 없음)
- `kind`: "pdf_text"
- `n_pages`: 총 페이지 수

사용 시 주의:
- 텍스트 레이어가 없는 스캔 PDF는 이 로더로는 처리되지 않습니다.
    스캔 PDF는 OCR 로더(`loaders.pdf_scan_loader`)를 사용하세요.
"""

import os
import fitz  # PyMuPDF
from langchain_core.documents import Document
from preprocess.text_cleaner import clean_text

def load_pdf_text(path: str) -> list[Document]:
    """
    텍스트 PDF 파일을 로드하여 Document 리스트로 반환합니다.
    
    텍스트 레이어가 있는 PDF에서 모든 페이지의 텍스트를 추출하여
    하나의 Document로 통합합니다. 페이지별로 분할하지 않습니다.
    
    Args:
        path: PDF 파일 경로
    
    Returns:
        list[Document]: Document 1개를 포함한 리스트
            - page_content: 모든 페이지 텍스트가 합쳐진 전체 텍스트
            - metadata:
                - source: 파일 절대 경로
                - page: None (parent 문서이므로 페이지 의미 없음)
                - kind: "pdf_text"
                - n_pages: 총 페이지 수 (참고용)
    
    Note:
        - 빈 페이지는 제외됩니다
        - 텍스트는 clean_text()로 정리됩니다
    """
    doc = fitz.open(path)
    pages = []
    
    # 모든 페이지에서 텍스트 추출
    for pno in range(len(doc)):
        text = doc.load_page(pno).get_text("text") or ""
        text = text.strip()
        if text:
            pages.append(text)

    # 모든 페이지 텍스트 합치기
    full_text = "\n\n".join(pages).strip()
    full_text = clean_text(full_text)

    abs_path = os.path.abspath(path)
    return [
        Document(
            page_content=full_text,
            metadata={
                "source": abs_path,
                "page": None,          # parent 문서이므로 페이지 의미 없음
                "kind": "pdf_text",
                "n_pages": len(doc),   # 참고용 페이지 수
            },
        )
    ]
