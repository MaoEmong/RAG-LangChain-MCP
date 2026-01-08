"""ocr 패키지
============================================================
OCR(광학 문자 인식) 기능을 제공하는 패키지입니다.

주요 모듈:
- base.py: OCR 엔진의 추상 베이스 클래스 (BaseOCR)
- tesseract_ocr.py: Tesseract OCR 구현 (TesseractOCR)
- dummy_ocr.py: 테스트용 더미 OCR 구현 (DummyOCR)

사용처:
- loaders/pdf_scan_loader.py: 스캔 PDF에서 텍스트 추출

특징:
- 다국어 지원 (한국어, 영어 등)
- 추상 인터페이스를 통한 확장성
- PDF 페이지별 처리
"""