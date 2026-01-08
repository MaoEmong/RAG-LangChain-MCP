"""
loaders/pdf_scan_loader.py
============================================================
이미지 기반(텍스트 레이어 없음) PDF를 OCR 처리하여 LangChain `Document`
형태로 반환하는 로더입니다.

설명:
- Tesseract 등의 OCR 엔진을 통해 각 페이지를 텍스트로 변환한 뒤,
    모든 페이지 텍스트를 하나의 Parent 문서로 결합합니다.
- 반환된 Document는 이후 ingest 단계에서 청크화되어 벡터 인덱스로
    저장될 수 있습니다.

파라미터 설명:
- `ocr`: OCR 엔진 인터페이스(예: `TesseractOCR`) - 엔진의 `ocr_pdf` 메서드를 사용
- `zoom`: 렌더링 배율(기본 2.5)로, 값이 클수록 OCR 정확도가 올라가지만
    처리 시간과 메모리 사용량이 증가합니다.

메타데이터 예시:
- `kind`: "pdf_scan_ocr"
- `domain`: "ocr_scan"
- `is_scan`: True
"""

import os
from langchain_core.documents import Document
from preprocess.text_cleaner import clean_text

def load_pdf_scan(path: str, ocr, zoom: float = 2.5) -> list[Document]:
    """
    스캔 PDF 파일을 OCR로 처리하여 Document 리스트로 반환합니다.
    
    이미지 기반 PDF의 각 페이지를 OCR로 처리하여 텍스트를 추출하고,
    모든 페이지의 텍스트를 하나의 Document로 통합합니다.
    
    Args:
        path: PDF 파일 경로
        ocr: OCR 엔진 객체 (TesseractOCR 등)
        zoom: PDF 렌더링 확대 배율 (기본값: 2.5)
            - 클수록 OCR 정확도 상승, 속도/메모리 사용량 증가
            - 작을수록 빠르지만 정확도 감소
    
    Returns:
        list[Document]: Document 1개를 포함한 리스트
            - page_content: 모든 페이지 OCR 결과가 합쳐진 전체 텍스트
            - metadata:
                - source: 파일 절대 경로
                - page: None (parent 문서이므로 페이지 의미 없음)
                - kind: "pdf_scan_ocr"
                - n_pages: 총 페이지 수
    
    Note:
        - 빈 페이지는 제외됩니다
        - 텍스트는 clean_text()로 정리됩니다
        - zoom 값은 OCR 정확도와 성능 사이의 트레이드오프를 조절합니다
    """
    # OCR로 모든 페이지 처리
    pages = ocr.ocr_pdf(path, zoom=zoom)

    # 각 페이지의 텍스트 추출
    texts = []
    for p in pages:
        t = (p.text or "").strip()
        if t:
            texts.append(t)

    # 모든 페이지 텍스트 합치기
    full_text = "\n\n".join(texts).strip()
    full_text = clean_text(full_text)

    abs_path = os.path.abspath(path)
    return [
        Document(
            page_content=full_text,
            metadata={
                "source": abs_path,
                "page": None,
                "kind": "pdf_scan_ocr",
                "n_pages": len(pages),
            },
        )
    ]
