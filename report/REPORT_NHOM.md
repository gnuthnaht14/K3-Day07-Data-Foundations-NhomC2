# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** C2
**Thành viên:** Nhữ Trọng Thành, Mai Hồng Sơn, Lê Thị Linh, Vũ Thu Huyền, Lường Thị Hảo
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> Quy định đăng ký học, học phí và các dịch vụ hỗ trợ sinh viên tại Đại học RMIT Việt Nam, gồm thư viện và thẻ sinh viên.

### Kết quả kiểm tra dữ liệu

| Điều kiện | Kết quả | Bằng chứng |
|-----------|---------|------------|
| Có 5–10 tài liệu | Đạt | 7 file Markdown trong `data/k3_university/` |
| Mọi file đủ metadata | Đạt | 7/7 file có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version` và `audience` |
| `sources.csv` khớp một–một | Đạt | 7 dòng dữ liệu tương ứng đúng 7 `doc_id` và 7 đường dẫn file tồn tại |
| Trường phân vai có ít nhất hai giá trị | Đạt | `audience`: `student` (6 tài liệu), `all` (1 tài liệu) |

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Change or cancel your enrolment | [RMIT Vietnam](https://www.rmit.edu.vn/students/my-studies/enrolment/change-or-cancel-your-enrolment) | 2026-08-03 / `not-stated` | 6,024 | `audience=student`; `department=registrar`; `category=enrolment-policy`; `language=en` |
| 2 | Defer a payment | [RMIT Vietnam](https://www.rmit.edu.vn/students/my-studies/fees-and-payments/defer-a-payment) | 2026-08-03 / `not-stated` | 7,553 | `audience=student`; `department=student-administration`; `category=payment-extension`; `language=en` |
| 3 | Enrolment at RMIT Vietnam | [RMIT Vietnam](https://www.rmit.edu.vn/students/my-studies/enrolment) | 2026-08-03 / `not-stated` | 4,079 | `audience=student`; `department=registrar`; `category=enrolment`; `language=en` |
| 4 | Fees and payments | [RMIT Vietnam](https://www.rmit.edu.vn/students/my-studies/fees-and-payments) | 2026-08-03 / `not-stated` | 4,583 | `audience=student`; `department=student-administration`; `category=tuition-fees`; `language=en` |
| 5 | Borrowing and returning | [RMIT Vietnam](https://www.rmit.edu.vn/libraryvn/borrowing-and-resources/borrowing-and-returning) | 2026-08-03 / `not-stated` | 6,485 | `audience=all`; `department=library`; `category=borrowing-policy`; `language=en` |
| 6 | RMIT student cards | [RMIT Vietnam](https://www.rmit.edu.vn/students/support/admin-support/rmit-student-cards) | 2026-08-03 / `not-stated` | 7,108 | `audience=student`; `department=student-administration`; `category=student-id`; `language=en` |
| 7 | Student support | [RMIT Vietnam](https://www.rmit.edu.vn/students/support) | 2026-08-03 / `not-stated` | 4,368 | `audience=student`; `department=student-services`; `category=support-services`; `language=en` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | Chuỗi định danh duy nhất | `rmit-defer-payment` | Truy vết chunk về đúng tài liệu gốc và đối chiếu với `sources.csv`. |
| `title` | Chuỗi | `Defer a payment` | Hiển thị và nhận diện tài liệu trong kết quả truy xuất. |
| `source_url` | URL công khai | `https://www.rmit.edu.vn/students/...` | Kiểm chứng nội dung và minh bạch nguồn. |
| `retrieved_at` | Ngày ISO `YYYY-MM-DD` | `2026-08-03` | Đánh giá độ mới của bản dữ liệu đã thu thập. |
| `document_version` | Chuỗi phiên bản/ngày hoặc `not-stated` | `not-stated` | Phân biệt các phiên bản chính sách và tránh suy đoán khi nguồn không nêu phiên bản. |
| `audience` | Enum | `student`, `all` | Lọc tài liệu theo nhóm đối tượng; có hai giá trị để chứng minh metadata filtering. |
| `department` | Enum | `registrar`, `library`, `student-administration` | Thu hẹp tìm kiếm theo đơn vị phụ trách dịch vụ hoặc quy định. |
| `category` | Enum | `enrolment-policy`, `tuition-fees`, `borrowing-policy` | Lọc theo nghiệp vụ cụ thể trước khi xếp hạng semantic. |
| `language` | Mã ngôn ngữ | `en` | Chọn tài liệu theo ngôn ngữ khi corpus được mở rộng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Defer a payment | FixedSizeChunker (`fixed_size`, size=400, overlap=50) | 20 | 392.8 | Có overlap nhưng có thể cắt giữa điều kiện. |
| Defer a payment | SentenceChunker (`by_sentences`, 3 câu/chunk) | 13 | 527.5 | Giữ trọn câu nhưng chunk khá dài. |
| Defer a payment | RecursiveChunker (`recursive`, size=400) | 20 | 343.2 | Giữ tốt ranh giới đoạn/dòng của danh sách điều kiện. |
| Borrowing and returning | FixedSizeChunker (`fixed_size`, size=400, overlap=50) | 17 | 388.4 | Có thể cắt rời hạn mức và quy tắc gia hạn. |
| Borrowing and returning | SentenceChunker (`by_sentences`, 3 câu/chunk) | 9 | 641.7 | Các dòng số liệu ít dấu câu làm chunk quá dài. |
| Borrowing and returning | RecursiveChunker (`recursive`, size=400) | 16 | 360.7 | Giữ các dòng hạn mức/thời hạn gần nhau. |
| RMIT student cards | FixedSizeChunker (`fixed_size`, size=400, overlap=50) | 19 | 387.4 | Có overlap nhưng đôi khi cắt giữa danh sách công dụng. |
| RMIT student cards | SentenceChunker (`by_sentences`, 3 câu/chunk) | 12 | 533.6 | Danh sách không có dấu chấm làm chunk dài. |
| RMIT student cards | RecursiveChunker (`recursive`, size=400) | 19 | 337.8 | Phù hợp cấu trúc dòng và mục của trang dịch vụ. |

> Baseline dùng phần thân tài liệu do `load_documents()` đã bỏ YAML front matter; các số liệu trên không tính metadata.

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nhữ Trọng Thành**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=400)` với separator mặc định `\n\n → \n → . → khoảng trắng → ký tự`.
- **Mô tả & lý do chọn cho chủ đề này:** Corpus là các trang quy định/dịch vụ có nhiều mục và danh sách theo dòng. Recursive chunking ưu tiên giữ các ranh giới tự nhiên này, đồng thời vẫn hạ xuống từ hoặc ký tự khi một mục vượt 400 ký tự.
- **Kết quả Checkpoint 5:** `bench.py` nạp 103 chunks và in top-3 cùng câu trả lời có nguồn cho đủ 5 query đã khóa.
- **Code snippet (nếu custom):**
```python
chunker = RecursiveChunker(chunk_size=400)
```

**Thành viên 2 — Mai Hồng Sơn**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=400, overlap=50)`.
- **Mô tả & lý do chọn cho chủ đề này:** Chia đều theo cửa sổ 400 ký tự và lặp lại 50 ký tự giữa hai chunk liên tiếp. Overlap cho bằng chứng nằm sát ranh giới thêm một cơ hội xuất hiện trong top-k, phù hợp làm đối chứng với Recursive-400 không overlap.
- **Kết quả benchmark local:** Nạp 105 chunks, đạt **4/10**: Q1=1, Q2=0, Q3=1, Q4=0, Q5=2. Q1 lấy đủ evidence nhưng chunk liên quan đầu tiên chỉ đứng hạng 2; Q3 lấy được `Program Cancellation form` ở hạng 2; Q5 lấy đúng ngoại lệ Census Date ở hạng 1.
- **Code snippet:**
```python
chunker = FixedSizeChunker(chunk_size=400, overlap=50)
```

**Thành viên 3 — Lê Thị Linh**
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)`.
- **Mô tả & lý do chọn cho chủ đề này:** Gom tối đa ba câu hoàn chỉnh vào một chunk để hạn chế cắt giữa câu và giữ mệnh đề điều kiện–kết luận gần nhau. Đây là đối chứng theo đơn vị ngôn ngữ thay vì số ký tự.
- **Kết quả benchmark local:** Nạp 58 chunks, đạt **3/10**: Q1=2, Q2=0, Q3=1, Q4=0, Q5=0. Q1 giữ cả hạn mức và gia hạn trong chunk top-1; Q3 có biểu mẫu ở hạng 3; Q5 thất bại vì câu ngoại lệ không vào top-3.
- **Code snippet:**
```python
chunker = SentenceChunker(max_sentences_per_chunk=3)
```

**Thành viên 4 — Vũ Thu Huyền:** Chưa cung cấp strategy và output benchmark local tại thời điểm cập nhật report.

**Thành viên 5 — Lường Thị Hảo**

- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=2)` kết hợp local embedding `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

- **Mô tả & lý do chọn cho chủ đề này:**
Mình giảm số câu trong mỗi chunk từ 3 xuống còn 2 nhằm tạo các chunk nhỏ hơn và tập trung hơn về ngữ nghĩa. Với corpus gồm nhiều quy định, điều kiện và hướng dẫn của RMIT, chunk nhỏ giúp embedding biểu diễn rõ hơn từng ý chính và giảm việc nhiều chủ đề khác nhau nằm trong cùng một vector.

- **Kết quả benchmark local:**
Chạy `bench.py` trên corpus `data/rmit`, tạo **86 chunks** và đạt **4/10**. Strategy truy xuất tốt các câu hỏi yêu cầu thông tin tập trung (Q1 và Q5), nhưng gặp khó khăn với những câu hỏi mà bằng chứng nằm rải rác ở nhiều đoạn hoặc nhiều điều kiện cần xuất hiện đồng thời (Q2, Q3, Q4).

- **Code snippet:**

```python
chunker = SentenceChunker(max_sentences_per_chunk=2)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nhữ Trọng Thành | RecursiveChunker (`chunk_size=400`) | 6/10 với local multilingual embedding | Đạt 2/2 ở Q1, Q3, Q5; giữ tốt biểu mẫu, số liệu và ngoại lệ trong các chunk thành công; metadata/provenance đầy đủ. | Q2 đúng document nhưng sai section; Q4 sai cả tài liệu. Recursive hiện không overlap và raw data còn navigation/footer. |
| Mai Hồng Sơn | FixedSizeChunker (`size=400`, `overlap=50`) | 4/10 với local multilingual embedding | Overlap giúp Q1 có đủ hai evidence marker và Q5 đạt top-1 với similarity 0.7483. | Cắt theo ký tự nên có thể phá vỡ câu/section; Q2 và Q4 không có evidence, Q3 chỉ đứng hạng 2. |
| Lê Thị Linh | SentenceChunker (`3 câu/chunk`) | 3/10 với local multilingual embedding | Chỉ tạo 58 chunks; giữ trọn câu và đạt 2/2 ở Q1 khi evidence nằm top-1. | Các danh sách ít dấu câu tạo chunk dài; Q2, Q4, Q5 không có evidence trong top-3. |
| Lường Thị Hảo | SentenceChunker (2 câu/chunk) | 4/10 với local multilingual embedding | Chunk nhỏ hơn nên tập trung ngữ nghĩa, Q1 và Q5 truy xuất đúng evidence. | Ngữ cảnh bị chia nhỏ nên Q2, Q3 và Q4 không đưa được đầy đủ evidence vào top-3. |

> Ba strategy trong bảng đã được chạy trên cùng 7 tài liệu, 5 query khóa và local embedder `paraphrase-multilingual-MiniLM-L12-v2`. Hai thành viên còn lại chưa có output benchmark trong phạm vi báo cáo này.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Trong ba strategy đã đo công bằng, Recursive-400 của Nhữ Trọng Thành tốt nhất với **6/10**, so với FixedSize-400-overlap-50 đạt **4/10** và Sentence-3 đạt **3/10**. Recursive thắng nhờ đạt trọn điểm ở Q1, Q3 và Q5; nó giữ tốt ranh giới đoạn/dòng của corpus quy định. Tuy nhiên đây là kết luận trong phạm vi ba strategy đã chạy, dựa trên evidence ở mức chunk chứ không chỉ dựa vào `doc_id`.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | **[Số liệu + filter]** Đối với sinh viên đại học và sau đại học, hạn mức mượn, thời hạn mượn, số lần và thời lượng gia hạn là bao nhiêu? Dùng filter `audience=all`. | 25 tài liệu trong 30 ngày; gia hạn 1 lần thêm 15 ngày, tối đa 45 ngày, nếu chưa quá hạn và không bị đặt giữ. | `rmit-library-borrowing-returning`, Recursive-400 chunks 3–4. |
| 2 | **[Điều kiện]** Sinh viên cần đáp ứng những điều kiện nào để được xin gia hạn thanh toán cho Standard Course? | Không ở học kỳ đầu; nợ cũ dưới 5 triệu đồng; chứng minh hoàn cảnh bất ngờ và khả năng trả đủ trong tối đa 45 ngày; đã tuân thủ các hạn gia hạn trước. | `rmit-defer-payment`, Recursive-400 chunks 7–8. |
| 3 | **[Quy trình]** Muốn hủy toàn bộ đăng ký chương trình, sinh viên phải nộp biểu mẫu nào và ở đâu? | Hoàn thành Program Cancellation form trong mục Submit Request của myRMIT. | `rmit-change-cancel-enrolment`, Recursive-400 chunk 10. |
| 4 | **[Liệt kê]** Thẻ sinh viên RMIT có thể được sử dụng cho những mục đích nào? | Mượn tài liệu; in/scan/photocopy; vào khu vực an ninh; xác minh tại kỳ đánh giá và điểm dịch vụ; nhận ưu đãi. | `rmit-student-cards`, Recursive-400 chunks 3–4. |
| 5 | **[Ngoại lệ]** Nếu hủy đăng ký sau Census Date nhưng không tham gia lớp học, sinh viên có còn phải trả học phí và các khoản phí khác không? | Có. Sinh viên vẫn phải chịu học phí và các khoản phí khác dù không tham gia lớp học. | `rmit-change-cancel-enrolment`, Recursive-400 chunk 9. |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Hạn mức/thời gian mượn | Recursive-400 + local embedding (kết quả hiện có) | Có — 2/2 | Với `audience=all`: top-3 là `library:3` (0.6089), `library:6` (0.5027), `library:4` (0.4708); đủ hai evidence marker. |
| 2 | Điều kiện gia hạn thanh toán | Recursive-400 + local embedding (kết quả hiện có) | Không — 0/2 | Top-3 là `defer-payment:16` (0.6334), `defer-payment:4` (0.6045), `fees-payments:4` (0.5924); đúng chủ đề nhưng thiếu hai điều kiện định lượng. |
| 3 | Quy trình hủy chương trình | Recursive-400 + local embedding (kết quả hiện có) | Có — 2/2 | `change-cancel-enrolment:10` chứa Program Cancellation form đứng top-1 (0.5974). |
| 4 | Công dụng thẻ sinh viên | Recursive-400 + local embedding (kết quả hiện có) | Không — 0/2 | Top-3 là `student-support:6`, `student-support:0`, `defer-payment:4`; không có hai evidence marker về công dụng thẻ. |
| 5 | Nghĩa vụ phí sau Census Date | Recursive-400 + local embedding (kết quả hiện có) | Có — 2/2 | `change-cancel-enrolment:9` chứa “still liable for tuition and other fees” đứng top-1 (0.5777). |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, thể hiện rõ ở Q1. Với filter `audience=all`, top-3 là `[library:3, library:6, library:4]`, đều thuộc tài liệu thư viện và chứa đủ evidence nên đạt 2/2. Không filter, kết quả là `[library:3, defer-payment:8, fees-payments:4]`; hai slot bị tài liệu khác chiếm và chỉ còn một phần evidence, tương ứng mức 1/2. Filter phải chạy trước ranking để tài liệu sai đối tượng không chiếm top-k. Tuy nhiên filter quá chặt hoặc metadata gắn sai có thể làm giảm recall.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. Local multilingual embedding nâng kết quả Recursive-400 từ 0/10 của baseline mock lên 6/10, cho thấy MockEmbedder chỉ phù hợp kiểm luồng kỹ thuật.
> 2. Đúng `doc_id` chưa chắc đúng retrieval: Q2 có hai chunk đầu từ đúng tài liệu nhưng không chứa evidence và vẫn nhận 0/2.
> 3. Metadata filter có giá trị đo được ở Q1: lọc `audience=all` giữ cả ba slot cho tài liệu thư viện và nâng kết quả từ một phần lên đầy đủ.
> 4. Trên cùng benchmark local, số chunk và điểm lần lượt là Recursive-400: 103 chunks/6 điểm; FixedSize-400-overlap-50: 105 chunks/4 điểm; Sentence-3: 58 chunks/3 điểm. Ít chunk hơn không tự động đồng nghĩa retrieval tốt hơn.

**Bài học rút ra khi so sánh trong nhóm:**
> Fixed-size có overlap giúp Q1 giữ đủ evidence và Q5 có similarity top-1 cao nhất, nhưng cắt giữa câu nên chỉ đạt 4/10. Sentence chunking giữ câu hoàn chỉnh và thắng ở Q1, song các danh sách ít dấu câu làm chunk dài nên tổng chỉ đạt 3/10. Recursive giữ đoạn/dòng tự nhiên tốt hơn trên corpus này và đạt 6/10, dù không overlap. Kết quả cho thấy phải đánh giá theo từng kiểu câu hỏi và evidence marker, không thể chọn strategy chỉ dựa trên số chunk hoặc similarity cao nhất.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ làm sạch navigation, header/footer và nội dung lặp trước khi chunk. Với văn bản quy định có cấu trúc mục, nhóm sẽ tách theo heading trước; section dài mới đưa qua recursive chunker, gắn lại heading vào từng chunk con và thử overlap nhỏ. Nhóm cũng sẽ làm giàu metadata cấp chunk bằng `section_title`/`content_type`, đồng thời dùng hash và vector similarity để phát hiện duplicate nhưng không tự động xóa các đoạn gần nghĩa chứa ngoại lệ khác nhau.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 — đã so sánh ba strategy trên cùng corpus/query/embedder |
| Chất lượng truy xuất (Retrieval Quality) | 6 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **36 / 40** |