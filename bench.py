"""Run the locked RMIT benchmark with one personal chunking strategy."""

from __future__ import annotations

from typing import Any

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed


DATA_DIR = "data/k3_university"
BENCHMARK_VERSION = "rmit-v1-2026-08-03"
TOP_K = 3

# This is the only strategy-specific line teammates should change.
chunker = RecursiveChunker(chunk_size=450)

BENCHMARKS: list[dict[str, Any]] = [
    {
        "type": "số liệu + metadata filter",
        "query": (
            "Đối với sinh viên đại học và sau đại học, hạn mức mượn, "
            "thời hạn mượn, số lần và thời lượng gia hạn là bao nhiêu?"
        ),
        "metadata_filter": {"audience": "all"},
        "gold_answer": (
            "Được mượn 25 tài liệu trong 30 ngày, gia hạn 1 lần thêm 15 ngày "
            "(tổng thời gian tối đa 45 ngày), nếu tài liệu chưa quá hạn và "
            "không bị người khác đặt giữ."
        ),
        "expected_doc_id": "rmit-library-borrowing-returning",
        "expected_chunks": [3, 4],
        "evidence_markers": ["Loan quota - 25 items", "Renewals last 15 days"],
    },
    {
        "type": "điều kiện",
        "query": (
            "Sinh viên cần đáp ứng những điều kiện nào để được xin gia hạn "
            "thanh toán cho Standard Course?"
        ),
        "metadata_filter": None,
        "gold_answer": (
            "Sinh viên không ở học kỳ đầu; nợ cũ dưới 5 triệu đồng; chứng minh "
            "hoàn cảnh bất ngờ ảnh hưởng khả năng trả ngắn hạn; chứng minh có thể "
            "trả đủ trong tối đa 45 ngày từ Payment Date; và đã tuân thủ các hạn "
            "gia hạn từng được phê duyệt trước đó."
        ),
        "expected_doc_id": "rmit-defer-payment",
        "expected_chunks": [7, 8],
        "evidence_markers": [
            "less than five million VND",
            "no more than 45 days",
        ],
    },
    {
        "type": "quy trình",
        "query": "Muốn hủy toàn bộ đăng ký chương trình, sinh viên phải nộp biểu mẫu nào và ở đâu?",
        "metadata_filter": None,
        "gold_answer": (
            "Hoàn thành Program Cancellation form trong mục Submit Request của myRMIT."
        ),
        "expected_doc_id": "rmit-change-cancel-enrolment",
        "expected_chunks": [10],
        "evidence_markers": ["Program Cancellation form"],
    },
    {
        "type": "liệt kê",
        "query": "Thẻ sinh viên RMIT có thể được sử dụng cho những mục đích nào?",
        "metadata_filter": None,
        "gold_answer": (
            "Dùng để mượn tài liệu thư viện; in, scan và photocopy; vào khu vực "
            "an ninh như phòng máy và studio; xác minh tại kỳ đánh giá và các "
            "điểm dịch vụ RMIT; đồng thời nhận một số ưu đãi."
        ),
"expected_doc_id": "rmit-student-cards",
        "expected_chunks": [3, 4],
        "evidence_markers": ["print, scan and photocopy", "access secure areas"],
    },
    {
        "type": "ngoại lệ",
        "query": (
            "Nếu hủy đăng ký sau Census Date nhưng không tham gia lớp học, "
            "sinh viên có còn phải trả học phí và các khoản phí khác không?"
        ),
        "metadata_filter": None,
        "gold_answer": (
            "Có. Sinh viên vẫn phải chịu học phí và các khoản phí khác dù không tham gia lớp học."
        ),
        "expected_doc_id": "rmit-change-cancel-enrolment",
        "expected_chunks": [9],
        "evidence_markers": ["still liable for tuition and other fees"],
    },
]


class FilteredStoreView:
    """Expose the store search interface with one fixed metadata filter."""

    def __init__(self, store, metadata_filter: dict[str, Any]) -> None:
        self.store = store
        self.metadata_filter = metadata_filter

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        return self.store.search_with_filter(
            query,
            top_k=top_k,
            metadata_filter=self.metadata_filter,
        )

    def get_collection_size(self) -> int:
        return self.store.get_collection_size()


def offline_extractive_llm(prompt: str) -> str:
    """Return a traceable context excerpt when no external LLM is configured."""
    context = prompt.split("Context:\n", 1)[-1].split("\n\nQuestion:", 1)[0]
    return "[OFFLINE EXTRACTIVE ANSWER]\n" + context


def preview(text: str, limit: int = 180) -> str:
    return " ".join(text.split())[:limit]


def contains_marker(text: str, marker: str) -> bool:
    return marker.casefold() in text.casefold()


def evaluate(
    results: list[dict[str, Any]],
    evidence_markers: list[str],
    agent_answer: str,
) -> dict[str, Any]:
    """Grade retrieved chunks by answer evidence, not merely by document ID."""
    evidence_ranks = {
        marker: [
            rank
            for rank, result in enumerate(results, start=1)
            if contains_marker(result["content"], marker)
        ]
        for marker in evidence_markers
    }
    relevant_ranks = sorted(
        {rank for ranks in evidence_ranks.values() for rank in ranks}
    )
    all_evidence_retrieved = all(evidence_ranks.values())
    answer_grounded = all(
        contains_marker(agent_answer, marker) for marker in evidence_markers
    )
    if all_evidence_retrieved and answer_grounded and 1 in relevant_ranks:
        score = 2
    elif relevant_ranks:
        score = 1
    else:
        score = 0
    return {
        "score": score,
        "evidence_ranks": evidence_ranks,
        "relevant_ranks": relevant_ranks,
        "all_evidence_retrieved": all_evidence_retrieved,
        "answer_grounded": answer_grounded,
    }


def result_signature(results: list[dict[str, Any]]) -> list[tuple[str | None, Any]]:
    return [
        (result["metadata"].get("doc_id"), result["metadata"].get("chunk_index"))
        for result in results
]


def main() -> int:
    store = build_knowledge_base(DATA_DIR, _mock_embed, chunker=chunker)
    print(f"Benchmark: {BENCHMARK_VERSION}")
    print("Embedding: mock embeddings fallback (shared offline baseline)")
    print("Strategy: RecursiveChunker(chunk_size=400)")
    print(f"Loaded chunks: {store.get_collection_size()}")
    scores = []

    for number, benchmark in enumerate(BENCHMARKS, start=1):
        query = benchmark["query"]
        metadata_filter = benchmark["metadata_filter"]
        if metadata_filter is None:
            results = store.search(query, top_k=TOP_K)
            agent_store = store
        else:
            results = store.search_with_filter(
                query,
                top_k=TOP_K,
                metadata_filter=metadata_filter,
            )
            agent_store = FilteredStoreView(store, metadata_filter)

        print(f"\nQ{number} [{benchmark['type']}]: {query}")
        print(f"Filter: {metadata_filter}")
        print(f"Gold: {benchmark['gold_answer']}")
        print(
            "Expected: "
            f"{benchmark['expected_doc_id']} chunks={benchmark['expected_chunks']}"
        )
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            relevant = any(
                contains_marker(result["content"], marker)
                for marker in benchmark["evidence_markers"]
            )
            print(
                f"  top-{rank}: score={result['score']:.4f} "
                f"doc_id={metadata.get('doc_id')} "
                f"chunk={metadata.get('chunk_index')} "
                f"relevant={'YES' if relevant else 'NO'} "
                f"preview={preview(result['content'])}"
            )

        agent = KnowledgeBaseAgent(agent_store, offline_extractive_llm)
        agent_answer = agent.answer(query, top_k=TOP_K)
        print("Agent answer:")
        print(agent_answer)
        evaluation = evaluate(
            results,
            benchmark["evidence_markers"],
            agent_answer,
        )
        scores.append(evaluation["score"])
        print(
            "Evaluation: "
            f"score={evaluation['score']}/2 "
            f"evidence_ranks={evaluation['evidence_ranks']} "
            f"all_evidence={evaluation['all_evidence_retrieved']} "
            f"grounded={evaluation['answer_grounded']}"
        )

        if metadata_filter is not None:
            unfiltered = store.search(query, top_k=TOP_K)
            filtered_signature = result_signature(results)
            unfiltered_signature = result_signature(unfiltered)
            print("A/B metadata filter:")
            print(f"  with_filter={filtered_signature}")
            print(f"  without_filter={unfiltered_signature}")
            print(f"  identical={filtered_signature == unfiltered_signature}")

    print(f"\nBenchmark total: {sum(scores)}/{len(scores) * 2}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())