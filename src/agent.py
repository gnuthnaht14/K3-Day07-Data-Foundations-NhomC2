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
            return "Store rỗng: Không có dữ liệu trong cơ sở tri thức."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy ngữ cảnh phù hợp trong cơ sở tri thức."

        context_blocks = []
        for i, res in enumerate(results, start=1):
            doc_id = res.get("metadata", {}).get("doc_id") or res.get("metadata", {}).get("source") or res.get("id", f"doc_{i}")
            content = res.get("content", "")
            context_blocks.append(f"[{i}] (source: {doc_id}): {content}")

        context_str = "\n".join(context_blocks)

        prompt = (
            "Instruction: Chỉ sử dụng thông tin trong phần Context dưới đây để trả lời câu hỏi. "
            "Nếu ngữ cảnh không đủ thông tin, hãy nói rõ rằng không đủ thông tin để trả lời.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        return self.llm_fn(prompt)
