# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Mai Hồng Sơn
**Nhóm:** C2
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*

Độ tương tự cosine là một thước đo toán học dùng để so sánh góc giữa hai vector trong không gian nhiều chiều. Khi độ tương tự cosine cao (gần bằng 1), điều đó có nghĩa là hai vector có hướng tương tự nhau, tức là hai câu có ý nghĩa hoặc ngữ nghĩa gần giống nhau, mặc dù cách diễn đạt có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi thích học AI và phát triển các ứng dụng thông minh.
- Câu B: Lĩnh vực yêu thích của tôi là trí tuệ nhân tạo và xây dựng các AI Agent.
- Tại sao tương đồng: Cả hai câu đều thể hiện sự yêu thích đối với lĩnh vực trí tuệ nhân tạo và phát triển các ứng dụng thông minh, mặc dù câu A dùng thuật ngữ "AI" còn câu B dùng thuật ngữ "AI Agent".

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi thích học AI và phát triển các ứng dụng thông minh.
- Câu B: Tôi thường ăn sáng với bánh mì và bơ.
- Tại sao khác: Câu A nói về sở thích học tập và phát triển AI, trong khi câu B nói về thói quen ăn uống hàng ngày, không có liên quan về mặt ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:*
Độ tương tự cosine được ưu tiên hơn khoảng cách Euclid cho text embeddings vì nó đo lường góc giữa các vector, giúp xác định sự tương đồng về hướng (ý nghĩa) bất kể độ lớn của vector (độ dài văn bản). Trong khi đó, khoảng cách Euclid bị ảnh hưởng bởi độ dài văn bản, khiến các văn bản dài hơn nhưng cùng chủ đề có thể bị coi là ít tương đồng hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
Số lượng chunk = (Tổng số ký tự - Overlap) / (Chunk size - Overlap)
= (10,000 - 50) / (500 - 50)
= 9,950 / 450
≈ 22.11
Do số lượng chunk phải là số nguyên, ta làm tròn lên.
> *Đáp án: 23 chunks.*

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Nếu overlap tăng, số lượng chunk sẽ tăng lên do nội dung mỗi chunk bị  lặp lại nhiều hơn. Tăng overlap giúp các chunk giữ được tính toàn vẹn về mặt ngữ nghĩa, tránh bị cắt ngang đột ngột ở giữa đoạn hoặc giúp llm hiểu đước mối liên hệ với các chunk trước.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex lookbehind `r"(?<=[.!?])\s+"` để tách câu tại các vị trí sau `. ? !` theo sau bởi một hoặc nhiều khoảng trắng mà vẫn giữ lại dấu câu gốc. Hàm xử lý các trường hợp ngoại lệ (edge case) như văn bản rỗng/chỉ chứa khoảng trắng bằng cách loại bỏ khoảng trắng thừa quanh từng câu, và nhóm lại theo giới hạn `max_sentences_per_chunk`. 

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán ưu tiên tách văn bản theo danh sách phân cách thứ tự từ lớn đến nhỏ (`\n\n`, `\n`, `. `, ` `, `""`), sau đó nối các mảnh lại tối đa `chunk_size` để duy trì tính toàn vẹn cấu trúc. Base case đạt được khi độ dài đoạn văn bản nhỏ hơn hoặc bằng `chunk_size` (trả về chính đoạn đó), hoặc khi danh sách phân cách cạn kiệt (hoặc là chuỗi rỗng `""`) thì buộc phải cắt cứng theo độ dài `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ dữ liệu dưới dạng vector nhúng (embedding) và metadata trong vector database. Sử dụng `torch.nn.functional.cosine_similarity()` với tham số `dim=1` để tính độ tương tự cosine (không chuẩn hóa trước vì hàm đã xử lý). Tìm kiếm với top-k, sắp xếp giảm dần và trả về kết quả phù hợp nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Xử lý bộ lọc (filter) trước khi tìm kiếm (pre-filtering) để giảm kích thước tập dữ liệu. Tạo dictionary filter từ `metadata_filter`, sử dụng `chroma.collection.get(where=...)` để lấy các vector đã lọc, sau đó tính độ tương tự cosine và sắp xếp kết quả tương tự hàm search thông thường.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm `answer` thực hiện quy trình RAG bằng cách truy vấn top-$k$ đoạn văn bản liên quan nhất từ `EmbeddingStore`. Ngữ cảnh được đưa vào (inject context) bằng cách đánh số thứ tự và gắn thông tin nguồn cho từng đoạn (`[i] (source: doc_id): content`). Prompt được cấu trúc chuẩn gồm 3 phần: **Instruction** (ràng buộc LLM chỉ trả lời dựa trên ngữ cảnh được cung cấp), **Context** (chứa chuỗi ngữ cảnh đã ghép) và **Question** (câu hỏi đầu vào kèm mốc `Answer:`).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
==================================== test session starts ====================================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- /home/thao-pham/VIN_AI/LAB/K3-Day07-Data-Foundations-NhomC2/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/thao-pham/VIN_AI/LAB/K3-Day07-Data-Foundations-NhomC2
collected 42 items                                                                          

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED          [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED   [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED    [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED         [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED           [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED       [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                 [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED  [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED    [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED          [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED  [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED           [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED          [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED     [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED      [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

==================================== 42 passed in 0.17s =====================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên được mượn tài liệu thư viện trong bao lâu? | Thời hạn mượn sách thư viện dành cho sinh viên là mấy ngày? | cao | 0.0359 (Mock) / ~0.88 (Semantic) | Sai (Mock) / Đúng (Semantic) |
| 2 | Thời hạn đóng học phí kỳ này là khi nào? | Cách tạo tài khoản GitHub cho lập trình viên. | thấp | 0.0279 (Mock) / ~0.12 (Semantic) | Đúng |
| 3 | Sinh viên không được gia hạn thanh toán học phí. | Sinh viên được gia hạn thanh toán học phí. | thấp | 0.0202 (Mock) / ~0.85 (Semantic) | Đúng (Mock) / Sai (Semantic) |
| 4 | Muốn hủy đăng ký học phần thì nộp biểu mẫu ở đâu? | Cách xin gia hạn nộp học phí tại RMIT. | thấp | -0.0895 (Mock) / ~0.28 (Semantic) | Đúng |
| 5 | Thẻ sinh viên RMIT được dùng để in và photocopy. | Dùng thẻ sinh viên để thực hiện việc in ấn và nhân bản tài liệu. | cao | -0.0752 (Mock) / ~0.84 (Semantic) | Sai (Mock) / Đúng (Semantic) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp câu 3 ("Sinh viên không được gia hạn..." vs "Sinh viên được gia hạn...") gây bất ngờ nhất đối với các mô hình semantic embeddings thực tế. Mặc dù hai câu có ý nghĩa logic phủ định hoàn toàn trái ngược nhau, embedding space vẫn gán điểm độ tương tự rất cao (~0.85+) do trùng lặp lớn về ngữ cảnh và các từ khoá chủ đề. Điều này cho thấy vector embeddings biểu diễn không gian chủ đề/ngữ cảnh (topic/semantic domain) tốt hơn là khả năng hiểu và phân biệt logic phủ định (negation awareness). Với mô hình `MockEmbedder` (fallback hash), kết quả xoay quanh 0 cho mọi cặp câu do hàm hash ngẫu nhiên không phản ánh ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
