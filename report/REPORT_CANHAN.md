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
> Hai vector embedding có góc giữa chúng gần 0° (cosine gần 1) — nghĩa là hai đoạn văn bản mang **cùng hướng ngữ nghĩa**, dù có thể khác nhau về độ dài hoặc cách diễn đạt. Nói cách khác, hai văn bản đang "nói về cùng một điều" theo cách mô hình embedding hiểu.

**Ví dụ có độ tương tự CAO:**
- Câu A:"Sinh viên cần đăng ký học phần trước khi học kỳ mới bắt đầu."
- Câu B:"Trước khi bước vào học kỳ, sinh viên phải hoàn tất việc đăng ký môn học."
- Tại sao tương đồng:hai câu diễn đạt khác từ ngữ (đăng ký học phần / đăng ký môn học, trước khi học kỳ mới bắt đầu / trước khi bước vào học kỳ) nhưng cùng một ý nghĩa — cùng chủ thể (sinh viên), cùng hành động (đăng ký), cùng mốc thời gian (trước học kỳ).

**Ví dụ có độ tương tự THẤP:**
- Câu A:"Sinh viên cần đăng ký học phần trước khi học kỳ mới bắt đầu."
- Câu B:"Thư viện mở cửa từ 7h đến 21h các ngày trong tuần."
- Tại sao khác:khác chủ đề hoàn toàn (đăng ký học phần vs. giờ mở cửa thư viện), không chia sẻ khái niệm ngữ nghĩa cốt lõi nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo **hướng** của vector, bỏ qua độ lớn (magnitude) — trong khi độ lớn của embedding thường bị ảnh hưởng bởi độ dài văn bản hoặc số token, không phản ánh ý nghĩa. Nhờ vậy, một câu ngắn và một đoạn dài hơn nhưng cùng chủ đề vẫn có thể cho cosine similarity cao, trong khi Euclidean distance có thể bị "lệch" chỉ vì khác độ dài, dù ngữ nghĩa gần nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> số lượng chunk = ceil((length - overlap) / (chunk_size - overlap))
>                = ceil((10000 - 50) / (500 - 50))
>                = ceil(9950 / 450)
>                = ceil(22.11)
>                = 23
> ```

> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với `overlap=100`: `ceil((10000-100)/(500-100)) = ceil(9900/400) = ceil(24.75) = 25` chunks — **tăng từ 23 lên 25**. Overlap càng lớn thì phần "bước tiến" thực sự giữa hai chunk liên tiếp (`chunk_size - overlap`) càng nhỏ, nên cần nhiều chunk hơn để phủ hết văn bản. Đánh đổi: overlap lớn giúp **giữ ngữ cảnh** tốt hơn ở ranh giới giữa các chunk (một câu/ý bị cắt ở chunk này vẫn xuất hiện trọn vẹn ở chunk kế tiếp, tránh mất thông tin khi retrieval), nhưng đổi lại tốn nhiều dung lượng lưu trữ hơn, chunk trùng lặp nội dung nhiều hơn, và tăng chi phí tính embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
>Mình dùng re.split(r"(?<=[.!?])\s+|(?<=\.)\n", text) với lookbehind để tách văn bản ngay sau dấu ., !, ? mà vẫn giữ dấu câu ở lại phần trước (không mất dấu câu như split thường). Sau khi split, mình strip() từng câu và lọc bỏ chuỗi rỗng để tránh trường hợp có nhiều khoảng trắng liên tiếp hoặc câu rỗng ở đầu/cuối text sinh ra phần tử rác. Cuối cùng nhóm các câu theo từng lô kích thước max_sentences_per_chunk bằng slicing sentences[index:index+limit] rồi join bằng dấu cách.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy thử lần lượt các separator theo thứ tự ưu tiên (\n\n → \n → .  →   → ""): nếu separator hiện tại không xuất hiện trong text thì gọi đệ quy với phần separator còn lại, nếu có thì split theo separator đó rồi gộp các phần liền kề cho đến sát ngưỡng chunk_size. Base case gồm hai trường hợp: (1) text đã đủ ngắn (len <= chunk_size) thì trả về nguyên text, và (2) hết separator hoặc separator là chuỗi rỗng thì cắt cố định theo chunk_size — đây là điều kiện dừng đảm bảo đệ quy luôn tiến gần hơn tới việc thoát, tránh lặp vô hạn khi gọi lại với đúng input/separator cũ.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi Document được chuẩn hoá thành một record dict (id, content, metadata đã copy, embedding) qua _make_record, rồi append vào list self._store trong bộ nhớ (đồng thời mirror sang ChromaDB nếu thư viện có sẵn). Việc tính độ tương tự dùng dot product (_dot) giữa embedding của query (chỉ tính một lần) và embedding của từng record, sau đó sort giảm dần theo score và cắt lấy top_k — logic này được tách riêng thành helper _search_records để tái sử dụng ở các hàm search khác.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Mình lọc theo metadata trước, sau đó mới đưa tập con đã lọc vào _search_records để rank — nếu làm ngược lại (rank top-k trước rồi mới lọc) thì có thể mất kết quả hợp lệ dù store vẫn còn tài liệu khớp filter. delete_document duyệt qua self._store và giữ lại các record có metadata['doc_id'] != doc_id (fallback về chính doc.id nếu record đó không được gán doc_id tường minh), trả True/False tuỳ vào việc kích thước store có giảm sau khi lọc hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent gọi self.store.search(question, top_k=top_k) để lấy các chunk liên quan nhất, sau đó ghép chúng thành context với mỗi chunk được đánh số [1], [2]... kèm nguồn (doc_id lấy từ metadata) để có thể truy vết lại đúng file gốc. Prompt được dựng theo cấu trúc cố định gồm 4 phần: Instruction (chỉ dùng context, nói rõ khi thiếu thông tin) → Context (các chunk đã đánh số) → Question → Answer:, rồi gửi cho llm_fn; nếu không retrieve được chunk nào (store rỗng), agent trả thông báo rõ ràng thay vì gọi LLM một cách vô ích.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
================================================== test session starts ===================================================
platform win32 -- Python 3.12.2, pytest-9.1.1, pluggy-1.6.0 -- D:\AITHUCCHIEN\LAB\K3-Day07-Data-Foundations-NhomC2\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\AITHUCCHIEN\LAB\K3-Day07-Data-Foundations-NhomC2
collected 42 items                                                                                                        

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                               [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                        [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                 [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                  [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                       [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                       [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                             [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                              [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                            [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                              [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                              [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                         [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                     [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                               [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                      [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                          [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                    [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                          [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                              [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                  [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                        [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                             [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                               [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                   [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                         [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                        [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                   [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                               [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                          [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                              [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                    [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                              [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED           [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                         [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                        [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED            [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                       [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED      [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED          [100%]

=================================================== 42 passed in 0.18s ===================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên cần đăng ký học phần trước khi học kỳ bắt đầu. | Sinh viên phải hoàn tất đăng ký môn học trước khi vào học kỳ mới. | Cao | 0.94 | ✔ |
| 2 | Thư viện mở cửa từ 7h đến 21h. | Sinh viên phải đóng học phí trước hạn. | Thấp | 0.19 | ✔ |
| 3 | Sinh viên có thể gia hạn mượn sách nếu chưa quá hạn. | Có thể gia hạn thời gian mượn tài liệu khi sách chưa bị đặt giữ. | Cao | 0.89 | ✔ |
| 4 | Thẻ sinh viên được dùng để vào phòng máy. | Thẻ sinh viên dùng để xác minh danh tính và sử dụng các dịch vụ trong trường. | Cao | 0.78 | ✔ |
| 5 | RMIT hỗ trợ sinh viên gặp khó khăn tài chính. | Sinh viên có thể xin gia hạn thanh toán khi đáp ứng đủ điều kiện. | Cao | 0.72 | ✔ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Cặp số 5 là kết quả mình thấy bất ngờ nhất vì hai câu sử dụng từ ngữ khác nhau nhưng vẫn có độ tương đồng khá cao. Điều này cho thấy embedding không chỉ so khớp từ khóa mà còn biểu diễn ý nghĩa ngữ nghĩa của câu, giúp nhận diện được các nội dung liên quan dù cách diễn đạt khác nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Query                | Top-1                     | Score  | Relevant | Agent                                    |
| - | -------------------- | ------------------------- | ------ | -------- | ---------------------------------------- |
| 1 | Hạn mức mượn         | Library borrowing chunk 3 | 0.5754 | Có       | Trả lời đúng                             |
| 2 | Gia hạn thanh toán   | Defer payment chunk 3     | 0.6475 | Không    | Thiếu evidence                           |
| 3 | Program Cancellation | Change enrolment chunk 3  | 0.6147 | Không    | Không lấy được Program Cancellation form |
| 4 | Student Card         | Student support chunk 5   | 0.5888 | Không    | Sai tài liệu                             |
| 5 | Sau Census Date      | Change enrolment chunk 8  | 0.5563 | Có       | Trả lời đúng                             |


**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Với SentenceChunker(max_sentences_per_chunk=2), hệ thống tạo ra 86 chunk, ít hơn FixedSize nhưng nhiều hơn SentenceChunker(3). Strategy này hoạt động tốt đối với các truy vấn cần một đoạn thông tin ngắn và tập trung như Q1 và Q5. Tuy nhiên, các câu hỏi yêu cầu tổng hợp nhiều điều kiện hoặc thông tin trải trên nhiều đoạn vẫn còn hạn chế, khiến retrieval chỉ đạt 4/10.

---

## Tự Đánh Giá (Phần Cá Nhân)

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
