from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from backend.config import settings


def get_pinecone_vector_store():
    """
    Create pinecone vector store using langchain tooling
    :return:
    """
    embeddings = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDINGS_MODEL, api_key=settings.OPENAI_API_KEY)
    pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
    pinecone_index = pinecone_client.Index(settings.PINECONE_INDEX_NAME)
    vector_store = PineconeVectorStore(index=pinecone_index, embedding=embeddings)

    return vector_store



class Retriever:
    def __init__(self, vector_store: PineconeVectorStore):
        self.vector_store = vector_store

    def sim_search(self, prompt: str, namespace: str | None):
        top_matched_docs = self.vector_store.similarity_search(prompt, k=6, namespace=namespace if namespace else "")
        return self._rerank_docs(top_matched_docs)

    @staticmethod
    def _rerank_docs(docs: list[Document]):
        return sorted(docs, key=lambda d: d.metadata["score"], reverse=True)