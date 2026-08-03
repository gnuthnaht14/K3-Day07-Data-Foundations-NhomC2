from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if hasattr(self.store, "get_collection_size") and self.store.get_collection_size() == 0:
            return "No context available in knowledge base to answer the question."

        chunks = self.store.search(question, top_k=top_k)
        if not chunks:
            return "No relevant context found in knowledge base to answer the question."

        context_parts = []
        for idx, chunk in enumerate(chunks, start=1):
            doc_id = chunk.get("metadata", {}).get("doc_id", chunk.get("id", "unknown"))
            content = chunk.get("content", "")
            context_parts.append(f"[{idx}] (doc_id: {doc_id}): {content}")
        context_str = "\n".join(context_parts)

        prompt = (
            "Instruction: Answer the question using ONLY the provided context below. "
            "If the context does not contain enough information, state clearly that the information is insufficient.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        return self.llm_fn(prompt)
