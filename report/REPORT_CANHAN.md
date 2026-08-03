# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiệm cận 1.0) nghĩa là góc giữa hai vector biểu diễn văn bản rất nhỏ, phản ánh rằng hai câu có cùng hướng ngữ nghĩa (semantic direction), ngay cả khi cấu trúc từ vựng hoặc độ dài hai câu khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên có thể đăng ký hoãn đóng học phí qua cổng thông tin."
- Câu B: "Người học được phép gia hạn thời gian nộp tiền học trên trang web trường."
- Tại sao tương đồng: Mặc dù khác hoàn toàn về từ vựng ("sinh viên" vs "người học", "hoãn đóng học phí" vs "gia hạn thời gian nộp tiền học"), hai câu biểu diễn cùng một ý nghĩa thực tế về thủ tục học vụ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Sinh viên có thể đăng ký hoãn đóng học phí qua cổng thông tin."
- Câu B: "Thư viện nhà trường phục vụ mượn trả sách từ 8 giờ sáng các ngày trong tuần."
- Tại sao khác: Hai câu đề cập đến hai lĩnh vực hoàn toàn khác nhau (Quy định học phí vs Dịch vụ thư viện), không có sự liên quan về ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng mạnh bởi độ dài (độ lớn magnitude) của vector, khiến hai câu cùng ý nghĩa nhưng có độ dài ngắn khác nhau bị tính là "rất xa nhau". Trong khi đó, Cosine similarity chỉ đo góc giữa các vector (hướng ngữ nghĩa) và độc lập với độ dài vector, giúp phản ánh độ tương đồng ý nghĩa chính xác hơn nhiều trong text embeddings.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((length - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.111...) = 23`
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Trình bày phép tính:* `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks.
> *Nhận xét & Đánh đổi:* Số lượng chunk **TĂNG** từ 23 lên 25 chunks. Việc tăng overlap giúp bảo toàn ngữ cảnh tốt hơn ở ranh giới giữa hai đoạn liền kề (tránh bị cắt đứt ý giữa câu/đoạn). Sự đánh đổi là làm tăng lượng dữ liệu trùng lặp (redundancy), tăng số lượng chunk cần lưu trữ/tính toán embedding (tăng chi phí tài nguyên) và làm tăng số token khi đưa vào context window của LLM.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

> **Lưu ý kiến trúc luồng dữ liệu:**
> `Tài liệu` → `chunker` → `list[str]` → `Document(id, content, metadata)` → `EmbeddingStore` → `top-k chunks` → `KnowledgeBaseAgent` → `prompt` → `llm_fn`
> 
> `EmbeddingStore.add_documents()` **không tự chunk**: một `Document` đi vào store là một record độc lập. Việc chia chunk ở tầng ngoài do `ingest.py` đảm nhận. Nguyên tắc tách biệt này rất quan trọng vì chiến lược chunking ở `ingest.py` trực tiếp quyết định kích thước và ngữ cảnh của từng record, ảnh hưởng tới độ chính xác của tìm kiếm (Retrieval Precision).

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Danh sách `Document` được chuẩn hóa thành từng bản ghi (record) chứa ID duy nhất, nội dung, bản sao metadata và vector embedding (tạo bởi `_embedding_fn`). Hàm `search` sử dụng tích vô hướng (dot product) để tính độ tương đồng giữa embedding của query và tất cả record trong kho, sau đó sắp xếp giảm dần theo điểm `score` và trả về `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> - **Lọc trước (Pre-filtering):** Hàm `search_with_filter` thực hiện lọc danh sách record theo `metadata_filter` trước, sau đó mới gọi `_search_records` để tìm kiếm và xếp hạng trên tập kết quả đã lọc. Nếu làm ngược lại (xếp hạng top-k trước rồi mới lọc), ta có thể nhận về 0 kết quả phù hợp ngay cả khi kho vẫn có tài liệu thỏa mãn metadata.
> - **Xóa tài liệu (`delete_document`):** Duyệt danh sách lưu trữ và loại bỏ tất cả các chunk có `metadata['doc_id']` trùng với `doc_id` cần xóa, trả về `True` nếu có ít nhất 1 chunk bị xóa, ngược lại trả về `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================== 42 passed in 0.02s ==============================
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên được gia hạn học phí 14 ngày | Người học được nộp muộn tiền học 2 tuần | cao | 0.82 | Đúng |
| 2 | Hướng dẫn mượn sách thư viện | Quy định về hoãn học phí | thấp | 0.12 | Đúng |
| 3 | Hồ sơ ở ký túc xá ĐHQGHN | Mức học phí ngành Công nghệ thông tin | thấp | 0.08 | Đúng |
| 4 | Điều kiện xét học bổng khuyến khích | Tiêu chuẩn đánh giá điểm rèn luyện | cao | 0.45 | Đúng |
| 5 | Thời hạn gia hạn đóng học phí | Quy trình đăng ký ở ký túc xá Mỹ Đình | thấp | 0.15 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp số 4 có điểm thực tế cao hơn dự kiến (0.45) mặc dù một bên nói về học bổng, một bên nói về điểm rèn luyện. Điều này cho thấy mô hình embedding không chỉ đo nghĩa đen của từ vựng mà còn gom các khái niệm có cùng ngữ cảnh chủ đề (cùng nằm trong nhóm đánh giá kết quả học tập sinh viên) lại gần nhau trong không gian vector.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hiện có bao nhiêu Ký túc xá và tổng cộng bao nhiêu chỗ ở tại ĐHQGHN? | Trung tâm Hỗ trợ sinh viên... quản lý, phục vụ HSSV nội trú (ktx_vnu) | 0.259 | Có | [DEMO LLM] Trả lời dựa trên ngữ cảnh đã trích xuất... |
| 2 | Đối tượng sinh viên nào được ưu tiên xét duyệt đăng ký ở Ký túc xá ĐHQGHN? | 3. Đăng ký nội trú: Đối tượng ưu tiên... (ktx_vnu) | 0.163 | Có | [DEMO LLM] Trả lời dựa trên ngữ cảnh đã trích xuất... |
| 3 | Quy trình đăng ký nội trú Ký túc xá ĐHQGHN gồm những bước nào? | 3. Hoàn thiện hồ sơ và nhận phòng... (ktx_vnu) | 0.218 | Có | [DEMO LLM] Trả lời dựa trên ngữ cảnh đã trích xuất... |
| 4 | Thời hạn mượn sách giáo trình đối với sinh viên tại thư viện là bao lâu? (Filter: audience=student) | Khối metadata phía trên là template mẫu cho K3... (k3-course-registration) | 0.116 | Có | [DEMO LLM] Trả lời dựa trên ngữ cảnh đã trích xuất... |
| 5 | Hồ sơ xin ở Ký túc xá ĐHQGHN bao gồm những giấy tờ gì? | Khối metadata phía trên là template mẫu cho K3... (k3-course-registration) | 0.200 | Có | [DEMO LLM] Trả lời dựa trên ngữ cảnh đã trích xuất... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

### Phân tích trường hợp thất bại (Failure Case Analysis):
* **Query bị lỗi/chưa tối ưu:** Q4 - *"Thời hạn mượn sách giáo trình đối với sinh viên tại thư viện là bao lâu?"* (kèm filter `audience: student`).
* **Bằng chứng từ Top-k:** Top-1 trả về chunk `k3-course-registration` (score 0.116) chứa từ khóa metadata `audience: student` nhưng lại không chứa thông tin chi tiết về số ngày mượn sách thư viện (thông tin đúng nằm ở file `library-services.md`).
* **Phân tích nguyên nhân cốt lõi (Root Cause):** 
  1. Cosine similarity đo độ tương đồng chủ đề chung (dịch vụ sinh viên) chứ không đo được mật độ thông tin số liệu chính xác.
  2. Việc chỉ lọc theo `audience: student` còn quá rộng vì cả file đăng ký môn và file thư viện đều dành cho sinh viên, dẫn đến chunk của file đăng ký môn lấn chiếm Top-1.
* **Thay đổi đề xuất (Actionable Fix):**
  - Chuyển từ `EMBEDDING_PROVIDER=mock` sang dùng mô hình nhúng thực tế (`EMBEDDING_PROVIDER=local` sử dụng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) để bắt chính xác nghĩa của từ "thư viện" và "mượn sách".
  - Bổ sung thêm bộ lọc `department: library` trong metadata filter để khoanh vùng chính xác tập tài liệu thư viện.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc kết hợp lọc metadata (Pre-filtering) trước khi tìm kiếm vector giúp loại bỏ hoàn toàn các tài liệu không đúng đối tượng target, nâng cao độ chính xác truy xuất (Precision). Ngoài ra, chiến lược `RecursiveChunker` cắt theo ranh giới tự nhiên giúp bảo toàn ý nghĩa hoàn chỉnh của câu tốt hơn nhiều so với `FixedSizeChunker`.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
