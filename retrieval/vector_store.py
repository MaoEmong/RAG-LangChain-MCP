"""
retrieval/vector_store.py
============================================================
벡터 저장소(ChromaDB) 생성 및 초기화 헬퍼 모듈.

설명:
- OpenAI 임베딩 함수를 초기화하고 이를 사용해 Chroma 컬렉션을 생성하거나
    존재하는 저장소를 로드합니다.

함수 `create_vector_store`는 아래를 책임집니다:
- 임베딩 인스턴스 초기화
- Chroma 컬렉션 연결(없으면 생성)

포트폴리오 포인트:
- 벡터 인덱스 초기화는 RAG 파이프라인의 핵심이며, 이 모듈은 해당 책임을
    한 곳에 모아 재사용성과 테스트 편의성을 제공합니다.
"""

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

def create_vector_store(
    api_key,
    embed_model,
    persist_dir,
    collection_name,
):
    """
    ChromaDB 벡터 저장소를 생성하고 반환합니다.
    
    이 함수는:
    1. OpenAI 임베딩 모델을 초기화
    2. ChromaDB 벡터 저장소를 생성/로드
    3. 지정된 컬렉션에 연결
    
    Args:
        api_key (str): OpenAI API 키
        embed_model (str): 임베딩 모델 이름 (예: "text-embedding-3-small")
        persist_dir (str): 벡터DB 저장 디렉토리 경로
        collection_name (str): ChromaDB 컬렉션 이름
    
    Returns:
        Chroma: ChromaDB 벡터 저장소 객체
        
    Note:
        - persist_dir에 이미 벡터DB가 있으면 자동으로 로드됩니다
        - 없으면 새로 생성됩니다
        - ingest_langchain.py로 문서를 먼저 저장해야 합니다
    """
    # OpenAI 임베딩 모델 초기화
    # 텍스트를 벡터로 변환하는 데 사용
    embeddings = OpenAIEmbeddings(
        model=embed_model,
        api_key=api_key,
    )

    # ChromaDB 벡터 저장소 생성/로드
    # - collection_name: 저장소 내부의 컬렉션 이름
    # - embedding_function: 벡터 변환 함수 (OpenAI 임베딩)
    # - persist_directory: 벡터DB 파일 저장 경로
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
