from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

# 1. Chọn thư mục dữ liệu (mặc định data/k3_university)
DATA_DIR = os.getenv("LAB_DATA_DIR", "data/k3_university")


def get_embedder():
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            print("Local embedder không sẵn sàng; tạm dùng mock.")
            return _mock_embed
    elif provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            print("OpenAI embedder không sẵn sàng; tạm dùng mock.")
            return _mock_embed
    return _mock_embed


# 2. Bộ 5 Benchmark Queries cố định của nhóm K3
BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "question": "Sinh viên được gia hạn đóng học phí tối đa bao nhiêu ngày kể từ ngày hết hạn?",
        "filter": None,
        "note": "Quy định về thời gian đóng học phí và gia hạn",
    },
    {
        "id": "Q2",
        "question": "Thời hạn mượn sách giáo trình đối với sinh viên tại thư viện là bao lâu?",
        "filter": {"audience": "student"},
        "note": "Bắt buộc K3: Có dùng metadata_filter audience=student",
    },
    {
        "id": "Q3",
        "question": "Địa chỉ và hotline liên hệ của Ký túc xá Mỹ Đình ĐHQGHN là gì?",
        "filter": {"department": "student-support-center"},
        "note": "Thông tin liên hệ KTX Mỹ Đình",
    },
    {
        "id": "Q4",
        "question": "Sinh viên muốn xin hủy học phần muộn nhất là vào tuần thứ mấy của học kỳ?",
        "filter": {"audience": "student"},
        "note": "Quy trình điều chỉnh/hủy học phần của sinh viên",
    },
    {
        "id": "Q5",
        "question": "Hồ sơ đăng ký nội trú Ký túc xá ĐHQGHN bao gồm những giấy tờ gì?",
        "filter": None,
        "note": "Thủ tục và hồ sơ xin ở KTX",
    },
]


def run_benchmark() -> None:
    print("=" * 65)
    print("🚀 CHẠY BENCHMARK STRATEGY CÁ NHÂN")
    print(f"📁 Thư mục dữ liệu: {DATA_DIR}")

    embedder = get_embedder()

    # -----------------------------------------------------------------
    # STRATEGY CỦA BẠN (Dòng duy nhất khác biệt với các thành viên nhóm)
    # Ví dụ: RecursiveChunker(chunk_size=400)
    # -----------------------------------------------------------------
    chunker = RecursiveChunker(chunk_size=400)
    strategy_name = "RecursiveChunker(chunk_size=400)"

    print(f"⚙️ Strategy cá nhân: {strategy_name}")
    print("=" * 65)

    # 1. Nạp cơ sở tri thức bằng ingest.py
    store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=chunker)
    total_chunks = store.get_collection_size()
    print(f"📦 Tổng số chunks đã nạp: {total_chunks}")
    print("=" * 65)

    # 2. Khởi tạo tác tử RAG Agent
    agent = KnowledgeBaseAgent(
        store=store,
        llm_fn=lambda prompt: "[DEMO LLM] Trả lời dựa trên ngữ cảnh đã trích xuất."
    )

    # 3. Chạy 5 câu hỏi Benchmark Query
    for item in BENCHMARK_QUERIES:
        q_id = item["id"]
        question = item["question"]
        m_filter = item["filter"]
        note = item["note"]

        print(f"\n❓ [{q_id}] {question}")
        print(f"   📌 Mục tiêu: {note} | Metadata Filter: {m_filter}")

        # Retrieval top-3
        if m_filter:
            results = store.search_with_filter(question, top_k=3, metadata_filter=m_filter)
        else:
            results = store.search(question, top_k=3)

        print("   🔍 Top-3 Kết Quả Truy Xuất (Retrieval):")
        for idx, res in enumerate(results, start=1):
            doc_id = res["metadata"].get("doc_id", res["id"])
            preview = res["content"][:100].replace("\n", " ")
            print(f"      [{idx}] Score={res['score']:.3f} | doc_id={doc_id} | Preview=\"{preview}...\"")

        # Agent câu trả lời
        ans = agent.answer(question, top_k=3)
        print(f"   🤖 Agent Response: {ans[:150]}...")


if __name__ == "__main__":
    run_benchmark()
