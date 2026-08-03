# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Thị Linh
**Nhóm:** C2
**Ngày:** 93/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao (gần 1) nghĩa là hai vector embedding gần như cùng hướng trong không gian nhiều chiều, cho thấy hai đoạn văn bản mang ý nghĩa hoặc chủ đề tương đồng nhau, bất kể độ dài văn bản khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Sinh viên có thể mượn tối đa 25 tài liệu trong 30 ngày."
- Câu B: "Số lượng sách được mượn tối đa là 25 cuốn, thời hạn 30 ngày."
- Tại sao tương đồng: Cả hai câu diễn đạt cùng một nội dung (quy định mượn tài liệu thư viện) chỉ khác cách dùng từ, nên embedding của chúng nằm gần nhau về hướng trong không gian vector.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Sinh viên có thể mượn tối đa 25 tài liệu trong 30 ngày."
- Câu B: "Để hủy đăng ký chương trình, sinh viên cần nộp Program Cancellation form."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau (mượn tài liệu thư viện và hủy đăng ký chương trình), nên vector embedding của chúng có hướng khác biệt rõ rệt trong không gian.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity chỉ quan tâm đến **hướng** của vector, không bị ảnh hưởng bởi độ dài (magnitude) của vector — điều này quan trọng vì độ dài văn bản khác nhau có thể tạo ra embedding với magnitude khác nhau dù ý nghĩa giống nhau. Euclidean distance lại bị ảnh hưởng bởi magnitude, nên hai câu cùng ý nghĩa nhưng độ dài khác nhau có thể bị đánh giá là "xa nhau" một cách sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Bước nhảy (step) giữa các chunk = chunk_size − overlap = 500 − 50 = 450 ký tự.
> Chunk đầu tiên bắt đầu tại vị trí 0, các chunk tiếp theo bắt đầu tại 450, 900, 1350, ...
> Cần tìm vị trí bắt đầu nhỏ nhất sao cho `start + chunk_size ≥ 10000`, tức `start ≥ 9500`.
> `9500 / 450 ≈ 21.11` → làm tròn lên → chunk cuối bắt đầu tại vị trí `22 × 450 = 9900`.
> Tổng số chunk = số giá trị `start` từ 0 đến 9900 (bước 450) = `9900/450 + 1 = 23`.
>
> **Đáp án: 23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi overlap tăng lên 100, step = 500 − 100 = 400, số chunk tăng lên thành 25 (tính tương tự: cần `start ≥ 9500`, `9500/400 = 23.75` → chunk cuối bắt đầu tại `24×400=9600`, tổng = `24+1=25` chunk). Overlap lớn hơn giúp giữ được ngữ cảnh liên tục giữa các chunk liền kề, tránh trường hợp một câu hoặc ý quan trọng bị cắt đứt ngay tại ranh giới giữa hai chunk, đánh đổi bằng việc tạo ra nhiều chunk hơn (tốn thêm dung lượng lưu trữ và thời gian tính embedding).

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng regex với lookbehind `(?<=\. )|(?<=! )|(?<=\? )|(?<=\.\n)` để tách văn bản ngay sau các dấu kết thúc câu, nhờ đó dấu câu và khoảng trắng vẫn thuộc về câu trước thay vì bị cắt mất hoặc lẫn sang câu sau. Edge case xử lý: văn bản rỗng hoặc chỉ chứa khoảng trắng trả về danh sách rỗng, và các câu rỗng phát sinh sau khi strip (do nhiều khoảng trắng liên tiếp) được lọc bỏ trước khi gộp thành chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán thử tách văn bản theo từng separator trong danh sách ưu tiên (`\n\n`, `\n`, `. `, ` `, `""`); nếu một mảnh sau khi tách vẫn dài hơn `chunk_size`, hàm tiếp tục đệ quy xuống bằng separator kế tiếp trong danh sách còn lại. Base case gồm hai trường hợp: mảnh đã ≤ `chunk_size` thì dừng lại và giữ nguyên, hoặc đã hết separator để thử thì cắt cứng theo độ dài `chunk_size`. Sau khi tách xong, các mảnh nhỏ liền kề được gộp lại (`_merge`) để tạo thành chunk gần đầy `chunk_size` nhất có thể, tránh sinh ra quá nhiều chunk vụn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Mỗi `Document` được chuyển thành một record gồm `id`, `content`, `embedding` (tính từ `embedding_fn`) và `metadata`, sau đó lưu vào danh sách `self._store` trong bộ nhớ (hoặc collection ChromaDB nếu có sẵn). Khi search, embedding của câu truy vấn được tính rồi so sánh với từng embedding đã lưu bằng dot product; vì các embedding đều đã được chuẩn hóa (normalize) sẵn nên dot product tương đương với cosine similarity, kết quả được sắp xếp giảm dần và lấy top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Lọc **trước** khi tính độ tương tự: các record được lọc theo `metadata_filter` (khớp toàn bộ key-value bằng `all()`), sau đó mới chạy similarity search trên tập đã lọc — cách này giúp giảm không gian tìm kiếm và tránh nhiễu từ các document không liên quan, như thấy rõ trong benchmark khi query có filter đạt điểm tuyệt đối. Xóa document được thực hiện bằng cách rebuild lại `self._store`, loại bỏ mọi record có `metadata["doc_id"]` (hoặc `id`) khớp với `doc_id` cần xóa.\*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Agent gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất, sau đó nối nội dung (`content`) của các chunk lại bằng dấu xuống dòng kép để tạo thành context. Context này được chèn vào một template prompt cố định gồm 3 phần: Context, Question, Answer; prompt hoàn chỉnh được truyền vào `llm_fn` (được inject từ ngoài) để sinh câu trả lời — cách thiết kế này giúp dễ dàng thay thế LLM thật hoặc mock LLM khi test mà không cần sửa logic của agent.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\admin\Documents\AITHUCHIEN\LAB\K3-Day07-Data-Foundations-NhomC2\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\admin\Documents\AITHUCHIEN\LAB\K3-Day07-Data-Foundations-NhomC2
plugins: anyio-4.14.2
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                              [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                       [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                 [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                      [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                      [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                            [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                             [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                           [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                             [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                             [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                        [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                    [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                              [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                     [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                         [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                   [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                         [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                             [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                               [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                 [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                       [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                            [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                              [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                  [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                               [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                        [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                       [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                  [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                              [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                         [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                             [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                   [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                             [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                          [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                        [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                       [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                           [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                      [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                               [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                     [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                         [100%]

========================================================== 42 passed in 1.65s ===========================================================
```

**Số lượng bài test vượt qua (pass):** _42_ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                                                             | Câu B                                                                                             | Dự đoán | Điểm thực tế   | Đúng? |
| --- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------- | -------------- | ----- |
| 1   | Sinh viên có thể mượn tối đa 25 tài liệu trong 30 ngày.                                           | Số lượng sách được mượn tối đa là 25 cuốn, thời hạn 30 ngày.                                      | cao     | -0.2237 (thấp) | Không |
| 2   | Sinh viên có thể mượn tối đa 25 tài liệu trong 30 ngày.                                           | Để hủy đăng ký chương trình, sinh viên cần nộp Program Cancellation form.                         | thấp    | 0.2025 (thấp)  | Có    |
| 3   | Thẻ sinh viên RMIT có thể dùng để mượn sách trong thư viện.                                       | Thẻ sinh viên RMIT được dùng để vào khu vực an ninh như phòng máy và studio.                      | cao     | -0.1097 (thấp) | Không |
| 4   | Để xin gia hạn thanh toán, sinh viên cần nộp đơn trước Payment Date.                              | Muốn hủy toàn bộ đăng ký chương trình, sinh viên phải nộp Program Cancellation form trong myRMIT. | thấp    | -0.1000 (thấp) | Có    |
| 5   | Sau Census Date, nếu sinh viên không tham gia lớp học vẫn phải trả học phí và các khoản phí khác. | Sinh viên vẫn phải chịu họcphí và các khoản phí khác dù không tham gia lớp học.                   | cao     | 0.1071 (thấp)  | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất là cặp 1 và cặp 5 có nội dung rất giống nhau nhưng điểm lần lượt chỉ là -0.2237 và 0.1071. Điều này cho thấy `MockEmbedder` đang tạo vector giả lập gần như ngẫu nhiên, nên chưa biểu diễn đúng quan hệ ngữ nghĩa; muốn rút ra kết luận đáng tin cậy cần chạy lại với model embedding local đa ngôn ngữ.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| 1 | Hạn mức mượn, thời hạn mượn, số lần và thời lượng gia hạn (SV đại học/sau đại học)? | rmit-library-borrowing-returning, chunk=3, score=0.6089 — "Details on how to log in... Borrowing for students, staff and alumni... Loan quota - 25 items, Loan period - 30 days" | 2/2 | Có | Agent trích đúng "Loan quota - 25 items" và "Renewals last 15 days (maximum renewal period = 45 days)" — trả lời đầy đủ, có căn cứ (grounded). |
| 2 | Điều kiện xin gia hạn thanh toán cho Standard Course? | rmit-defer-payment, chunk=16, score=0.6334 — "Proof of capacity to pay... submit application to student.billing@rmit.edu.vn before Payment Date" | 0/2 | Không | Agent trả lời về hồ sơ chứng minh tài chính và deadline nộp đơn, nhưng thiếu 2 mốc số liệu chính ("dưới 5 triệu VNĐ", "tối đa 45 ngày") — chunk đúng (7,8) không nằm trong top-3. |
| 3 | Muốn hủy toàn bộ đăng ký chương trình, nộp biểu mẫu nào và ở đâu? | rmit-change-cancel-enrolment, chunk=10, score=0.5627 — "RMIT may cancel a student's enrolment under specific circumstances..." | 0/2 | Không | Agent trả lời về các lý do RMIT có thể hủy đăng ký (chiều ngược), không nêu được "Program Cancellation form" — retrieval lấy đúng document nhưng sai chunk (10 thay vì đúng chunk mong đợi cũng là 10 nhưng nội dung preview khác góc). |
| 4 | Thẻ sinh viên RMIT dùng cho những mục đích nào? | rmit-student-support, chunk=6, score=0.5797 — "Blended learning experience... Guidelines for photography and filming on campus" | 0/2 | Không | Agent trả lời lạc đề hoàn toàn (nói về blended learning, không phải công dụng thẻ sinh viên) — retrieval lấy sai document (rmit-student-support thay vì rmit-student-cards). |
| 5 | Hủy đăng ký sau Census Date nhưng không học, có phải trả học phí không? | rmit-change-cancel-enrolment, chunk=10, score=0.5614 — "RMIT may cancel a student's enrolment under specific circumstances..." | 1/2 | Có (top-3) | Chunk đúng (9) xuất hiện ở rank 2, có chứa "still liable for tuition and other fees" — agent trả lời đúng nội dung này nhưng lẫn thêm đoạn không liên quan (lý do hủy từ phía RMIT) ở đầu câu trả lời. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> So với mock embedding (1/10), local embedding cải thiện rõ (3/10) — chứng minh chất lượng embedding ảnh hưởng trực tiếp đến retrieval, đúng như cảnh báo trong output ban đầu.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------- |
| Khởi động (Warm-up)                             | 5/ 5             |
| Hướng tiếp cận của tôi (My Approach)            | 10/ 10           |
| Hoàn thiện code (Core Implementation — tests)   | 30/ 30           |
| Dự đoán độ tương tự (Similarity Predictions)    | 5/ 5             |
| Kết quả truy xuất của tôi (Competition Results) | 3/ 10            |
| **Tổng phần cá nhân**                           | **53/ 60**       |
