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
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** __ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

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
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
