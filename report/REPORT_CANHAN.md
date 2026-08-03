# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nhữ Trọng Thành
**Nhóm:** C2
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có cosine similarity cao khi chúng hướng gần giống nhau trong không gian vector. Điều này thường cho thấy hai đoạn văn có ý nghĩa hoặc ngữ cảnh gần nhau, dù không nhất thiết dùng cùng từ ngữ.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên có thể xin gia hạn thời hạn đóng học phí.
- Câu B: Người học được phép đề nghị lùi hạn thanh toán học phí.
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng cùng diễn đạt việc sinh viên yêu cầu kéo dài hạn thanh toán học phí.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên được mượn tài liệu từ thư viện trong 30 ngày.
- Câu B: Dự báo thời tiết cho biết ngày mai có mưa lớn.
- Tại sao khác: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau: dịch vụ thư viện và thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào góc giữa hai vector, nên đánh giá hướng biểu diễn ngữ nghĩa và ít bị ảnh hưởng bởi độ lớn của vector. Khoảng cách Euclid phụ thuộc cả độ lớn, vì vậy hai embedding cùng hướng nhưng khác độ dài vẫn có thể bị xem là xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Phép tính:* `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.111...)`.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng lên 25 vì `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = 25`. Overlap lớn hơn giữ được nhiều ngữ cảnh tại ranh giới chunk và giảm nguy cơ tách rời thông tin liên quan, nhưng làm tăng nội dung trùng lặp, dung lượng lưu trữ và chi phí embedding/truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng ngay sau dấu kết thúc câu, nhờ đó dấu câu vẫn nằm ở câu phía trước. Text rỗng trả về `[]`; các phần được `strip`, bỏ phần rỗng rồi ghép theo từng nhóm không vượt quá `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử separator theo thứ tự đoạn, dòng, câu, từ và cuối cùng là ký tự; các phần liền nhau được gộp cho đến trước khi vượt `chunk_size`. Base case là text đã đủ ngắn; nếu hết separator hoặc gặp separator rỗng thì cắt fixed-size. Mỗi lần đệ quy đều bỏ separator hiện tại nên luôn tiến gần điều kiện dừng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi dùng store in-memory; mỗi `Document` được chuẩn hóa thành record gồm ID chunk duy nhất, content, bản sao metadata, `doc_id` gốc và embedding. `search` chỉ tạo query embedding một lần, tính dot product với embedding của từng record, sắp xếp score giảm dần rồi lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc metadata trước rồi mới xếp hạng trên tập ứng viên còn lại; như vậy các tài liệu hợp lệ không bị loại chỉ vì không nằm trong top-k toàn cục. `delete_document` loại tất cả record có `metadata['doc_id']` trùng ID tài liệu gốc và trả `True` khi thực sự xóa được ít nhất một record.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent gọi `store.search`, đánh số từng chunk `[1]`, `[2]`, ... và đưa kèm `doc_id` cùng `source_url` hoặc đường dẫn nguồn vào context. Prompt yêu cầu chỉ dùng context, dẫn nguồn bằng số thứ tự và nói rõ khi thiếu thông tin; nếu store không trả kết quả thì agent trả thông báo ngay mà không gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ python -m pytest tests -v
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1
rootdir: D:\workSpace\VinAI\K3-Day07-Data-Foundations-NhomC2
collected 42 items

tests/test_solution.py::TestProjectStructure (2 tests) PASSED
tests/test_solution.py::TestClassBasedInterfaces (2 tests) PASSED
tests/test_solution.py::TestFixedSizeChunker (7 tests) PASSED
tests/test_solution.py::TestSentenceChunker (4 tests) PASSED
tests/test_solution.py::TestRecursiveChunker (4 tests) PASSED
tests/test_solution.py::TestEmbeddingStore (8 tests) PASSED
tests/test_solution.py::TestKnowledgeBaseAgent (2 tests) PASSED
tests/test_solution.py::TestComputeSimilarity (4 tests) PASSED
tests/test_solution.py::TestCompareChunkingStrategies (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument (3 tests) PASSED

============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên có thể xin gia hạn thời hạn đóng học phí. | Người học được phép đề nghị lùi hạn thanh toán học phí. | Cao | 0.6858 | Đúng |
| 2 | Sinh viên được mượn 25 tài liệu trong 30 ngày. | Undergraduate students may borrow 25 library items for 30 days. | Cao | 0.8712 | Đúng |
| 3 | Để hủy chương trình, sinh viên nộp Program Cancellation form trên myRMIT. | Students must complete the Program Cancellation form in the Submit Request tile in myRMIT. | Cao | 0.7973 | Đúng |
| 4 | Thẻ sinh viên được dùng để mượn sách và vào khu vực an ninh. | RMIT student cards can be used to borrow library items and access secure areas. | Cao | 0.7002 | Đúng |
| 5 | Sinh viên được mượn tài liệu từ thư viện trong 30 ngày. | Dự báo thời tiết cho biết ngày mai có mưa lớn. | Thấp | 0.0194 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 2 có score cao nhất (0.8712) dù hai câu khác ngôn ngữ, cao hơn cặp diễn đạt lại bằng tiếng Việt ở cặp 1 (0.6858). Điều này cho thấy local multilingual model ánh xạ tốt hai câu Việt–Anh có cùng số liệu và ý nghĩa; đồng thời score phụ thuộc cách model học biểu diễn chứ không chỉ số từ trùng nhau. Cặp khác chủ đề ở câu 5 chỉ đạt 0.0194, phù hợp dự đoán thấp.

> Các score trên được đo bằng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, với embedding đã normalize và `compute_similarity()` của dự án.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hạn mức, thời hạn và gia hạn mượn | `rmit-library-borrowing-returning:3` — hạn mức 25 tài liệu/30 ngày (`0.6089`) | 2/2 | Có; hai evidence marker nằm trong top-3 | Context chứa hạn mức, thời hạn và quy định gia hạn 15 ngày; agent có đủ bằng chứng để trả lời. |
| 2 | Điều kiện gia hạn thanh toán Standard Course | `rmit-defer-payment:16` — chứng minh khả năng thanh toán (`0.6334`) | 0/2 | Không; đúng chủ đề nhưng sai section | Top-3 thiếu cả mức nợ dưới 5 triệu và giới hạn thanh toán không quá 45 ngày, nên context không đủ. |
| 3 | Biểu mẫu và nơi hủy chương trình | `rmit-change-cancel-enrolment:10` — Program Cancellation form trong myRMIT (`0.5974`) | 2/2 | Có; evidence đứng top-1 | Agent có thể trả lời đúng biểu mẫu và nơi nộp từ chunk top-1. |
| 4 | Công dụng thẻ sinh viên | `rmit-student-support:6` — blended learning/support (`0.5797`) | 0/2 | Không | Top-3 không chứa “print, scan and photocopy” hoặc “access secure areas”, nên không đủ bằng chứng. |
| 5 | Phí khi hủy sau Census Date | `rmit-change-cancel-enrolment:9` — vẫn chịu học phí sau Census Date (`0.5777`) | 2/2 | Có; evidence đứng top-1 | Agent có đủ context để trả lời rằng sinh viên vẫn phải chịu học phí và các khoản phí khác. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 — tổng điểm 6/10.

### Nhận xét benchmark và failure analysis

**Embedder và phép đo:** Benchmark chính thức sử dụng local multilingual embedder `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, chạy trên CPU. Corpus chủ yếu bằng tiếng Anh trong khi query bằng tiếng Việt, nên multilingual semantic embedding phù hợp hơn MockEmbedder. Cùng `RecursiveChunker(chunk_size=400)`, hệ thống nạp 103 chunks và đạt 6/10, tăng từ baseline kỹ thuật 0/10 của MockEmbedder.

**Precision và chunk coherence:** Ba query Q1, Q3 và Q5 có evidence trong top-3; Q3 và Q5 giữ được biểu mẫu/quy trình hoặc điều kiện/ngoại lệ trong một chunk top-1. Q2 cho thấy đúng `doc_id` vẫn chưa đủ: hai kết quả đầu đều thuộc tài liệu hoãn thanh toán nhưng sai section và không chứa hai điều kiện định lượng. Q4 không retrieve được tài liệu thẻ sinh viên trong top-3.

**A/B metadata filter:** Ở Q1, có filter `audience=all` trả `[library:3, library:6, library:4]`, cả ba chunk đều thuộc tài liệu thư viện và chứa đủ hai evidence marker. Không filter trả `[library:3, defer-payment:8, fees-payments:4]`: hai slot bị tài liệu thanh toán chiếm và chỉ còn một phần evidence. Filter trước rồi rank giúp Q1 đạt 2/2; lượt không filter chỉ đạt mức một phần 1/2.

**Grounding:** Agent offline chỉ trích context đã retrieve và giữ citation `[1]`, `[2]`, `[3]`, nên có thể truy vết về `doc_id`/chunk. Q1, Q3 và Q5 có context đủ evidence; Q2 và Q4 thiếu bằng chứng nên không được xem là trả lời đúng. Similarity cao vẫn chỉ là tín hiệu xếp hạng, không phải bằng chứng nội dung đúng.

**Failure case rõ nhất — Q2:** Top-1 `rmit-defer-payment:16` đạt 0.6334 và top-2 `rmit-defer-payment:4` đạt 0.6045, nhưng không chunk nào chứa `less than five million VND` hoặc `no more than 45 days`. Đây là lỗi “đúng document nhưng sai section”: embedding nhận đúng chủ đề thanh toán nhưng không đo trực tiếp mật độ bằng chứng trả lời. Đề xuất là làm sạch navigation/footer, tách theo heading trước rồi recursive với section dài, gắn lại heading vào chunk con và thử overlap nhỏ để điều kiện có thêm cơ hội lọt top-k.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> So sánh baseline cho thấy không có chunker tốt tuyệt đối: fixed-size có overlap nhưng dễ cắt giữa ý, sentence chunker giữ câu nhưng có thể tạo chunk quá dài, còn recursive giữ ranh giới tự nhiên nhưng hiện không overlap. Bài học quan trọng là phải giữ nguyên corpus, query và embedder khi so sánh strategy, đồng thời chấm ở mức evidence trong chunk thay vì chỉ kiểm tra `doc_id`.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 |
| **Tổng phần cá nhân** | **56 / 60** |
