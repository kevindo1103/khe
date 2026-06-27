# Hướng dẫn sử dụng Khế — Phiên bản Pilot

> **Dành cho:** SME pilot · **Phiên bản:** 0a (pre-pilot) · **Ngày:** 2026-06-27
> Rendered từ issue #339 per PM relay 2026-06-27 — canonical store cho pilot onboarding.

---

## Khế là gì?

**Khế** là nền tảng quản lý nghĩa vụ & quyền lợi pháp lý cho doanh nghiệp vừa và nhỏ. Bạn tải hợp đồng lên — Khế tự động phân tích, bóc tách mọi nghĩa vụ (thanh toán, giao hàng, hết hạn...) và quyền lợi, rồi nhắc bạn đúng lúc.

> **Nguyên tắc:** Khế đọc và phân tích — bạn xem xét và xác nhận. AI không bao giờ thay thế phán quyết của bạn.

---

## 1. Đăng nhập

1. Truy cập địa chỉ được cung cấp bởi đại lý/cố vấn của bạn
2. Nhập **Tên đăng nhập** và **Mật khẩu** được cấp
3. Nhấn **Đăng nhập**

> Lần đầu đăng nhập? Hệ thống sẽ hướng dẫn bạn qua các bước thiết lập ban đầu.

---

## 2. Tải hợp đồng lên

### Tự tải lên
1. Từ màn hình chính, nhấn **"+ Tải hợp đồng"**
2. Chọn file PDF hoặc ảnh chụp hợp đồng
3. Nhấn **Tải lên** — Khế bắt đầu phân tích (thường dưới 1 phút)

### Concierge (đại lý tải hộ)
Nếu đại lý/cố vấn của bạn đã tải hợp đồng lên thay bạn, bạn sẽ thấy chúng ở trạng thái **"Chờ xác nhận"** khi đăng nhập lần đầu.

> **Lưu ý định dạng:** PDF rõ nét cho kết quả tốt nhất. Ảnh chụp chấp nhận được nhưng có thể kém chính xác hơn.

---

## 3. Xem danh sách hợp đồng

Màn hình **Tài liệu** hiển thị toàn bộ hợp đồng với các trạng thái:

| Trạng thái | Ý nghĩa |
|---|---|
| 🔄 Đang xử lý | Khế đang phân tích |
| ⚠️ Cần kiểm tra | Khế cần bạn xem lại một số thông tin |
| ✅ Đã xác nhận | Hợp đồng đã được bạn xác nhận, Khế đang quản lý |
| 📋 Chờ xác nhận | Chưa xác nhận — nghĩa vụ chưa được nhắc |

**Chip lọc nhanh:** "Cần kiểm tra" · "Sắp hết hạn" · "Đang hiệu lực"

---

## 4. Xem chi tiết hợp đồng

Nhấn vào một hợp đồng để xem màn hình chi tiết với **3 tab:**

### Tab 1 — Tổng quan
- Tên hợp đồng, loại, các bên ký kết
- Ngày ký, ngày hiệu lực, ngày hết hạn
- Trạng thái tổng thể

### Tab 2 — Nghĩa vụ & Quyền lợi
- **Nghĩa vụ của bạn:** các cam kết bạn phải thực hiện (thanh toán, giao hàng, báo cáo...)
- **Quyền lợi của bạn:** các khoản đối tác phải thực hiện cho bạn
- Trạng thái mỗi mục: Đang chờ · Đến hạn · Đã hoàn thành · Quá hạn
- Nhấn vào từng mục để xem chi tiết và thực hiện hành động

### Tab 3 — Nội dung hợp đồng
- Toàn bộ điều khoản hợp đồng được trích xuất và đánh số
- Tìm kiếm nội dung bằng từ khóa
- Nhấn vào điều khoản để xem và chỉnh sửa (nếu cần)

---

## 5. Xác nhận hợp đồng *(bắt buộc)*

Sau khi Khế phân tích xong, bạn **phải xác nhận** để Khế bắt đầu nhắc nhở nghĩa vụ.

1. Vào Tab **Tổng quan** → kiểm tra thông tin Khế bóc tách
2. Nếu có thông tin sai → nhấn **Chỉnh sửa** để sửa trực tiếp
3. Nhấn **"Xác nhận hợp đồng này"**
4. Khế bắt đầu theo dõi và nhắc nhở từ thời điểm này

> ⚠️ **Quan trọng:** Hợp đồng chưa xác nhận sẽ KHÔNG được nhắc nhở. Đây là cam kết của bạn với dữ liệu — Khế không tự quyết thay bạn.

---

## 6. Ghi nhận thực hiện nghĩa vụ

Khi bạn đã hoàn thành một nghĩa vụ (đã thanh toán, đã giao hàng...):

1. Vào Tab **Nghĩa vụ & Quyền lợi** → tìm nghĩa vụ cần ghi nhận
2. Nhấn **"Đánh dấu đã hoàn thành"**
3. Điền:
   - **Ngày thực hiện** (ngày bạn thực sự hoàn thành, không nhất thiết hôm nay)
   - **Tài liệu bằng chứng** *(tùy chọn)*: biên bản bàn giao, hóa đơn, xác nhận thanh toán
   - **Ghi chú** *(tùy chọn)*
4. Nhấn **Xác nhận**

> Khế lưu lại lịch sử đầy đủ — ai ghi, khi nào, với bằng chứng gì. Hữu ích cho audit và tranh chấp.

### Nghĩa vụ dây chuyền
Một số nghĩa vụ chỉ bắt đầu tính ngày khi nghĩa vụ khác hoàn thành (vd: "thanh toán đợt 2 = 30 ngày sau nghiệm thu"). Khi bạn ghi nhận nghiệm thu hoàn thành, Khế tự động tính ngày đến hạn cho thanh toán đợt 2.

### Nghĩa vụ quá khứ cần xác nhận
Nếu bạn vừa tải lên hợp đồng cũ và có nghĩa vụ đã qua trong quá khứ, Khế sẽ hiển thị chúng với nhãn **"Cần xác nhận đã hoàn thành?"** — không phải "quá hạn". Xem lại và ghi nhận từng mục.

---

## 7. Sửa điều khoản hợp đồng

Nếu bạn phát hiện Khế đọc sai một điều khoản (ví dụ: số tiền, ngày tháng):

1. Vào Tab **Nội dung hợp đồng** → tìm điều khoản cần sửa
2. Nhấn biểu tượng ✏️ bên cạnh điều khoản
3. Chỉnh sửa nội dung → nhấn **Lưu**
4. Khế hiển thị nhãn **"đã sửa"** và cho phép xem lại bản gốc AI bất cứ lúc nào

### Yêu cầu Khế đọc lại
Sau khi sửa điều khoản quan trọng (ví dụ: điều khoản thanh toán), bạn có thể yêu cầu Khế cập nhật lại nghĩa vụ:

1. Nhấn banner **"Khế đọc lại"** *(xuất hiện sau khi sửa)*
2. Khế đề xuất các thay đổi về nghĩa vụ
3. Bạn xem xét từng đề xuất → **Chấp nhận** hoặc **Giữ nguyên**

> Khế không tự áp dụng thay đổi — bạn phải xác nhận từng mục.

---

## 8. Chat với Khế

Nhấn biểu tượng 💬 để hỏi Khế về hợp đồng của bạn.

**Khế có thể trả lời:**
- "Hợp đồng Penfield hết hạn khi nào?"
- "Tôi còn bao nhiêu nghĩa vụ chưa hoàn thành tháng này?"
- "Điều khoản bảo mật trong hợp đồng ABC nói gì?"
- "Tổng giá trị hợp đồng đang hiệu lực là bao nhiêu?"

**Khế sẽ nói thẳng khi không tìm thấy** thay vì đoán mò. Nếu câu hỏi mơ hồ, Khế sẽ hỏi lại để làm rõ.

> Khế đang xem hợp đồng nào? Góc trên chat luôn hiển thị **"Đang trong context: [tên HĐ]"** — bạn có thể nhấn để đổi hoặc mở rộng tìm kiếm.

---

## 9. Thiết lập nhắc nhở qua Telegram

Để nhận thông báo đến hạn qua Telegram:

1. Từ menu → **Cài đặt** → **Kết nối Telegram**
2. Nhấn **"Kết nối"** → làm theo hướng dẫn (nhắn tin `/start` với bot Khế)
3. Sau khi kết nối, bạn sẽ nhận tin nhắn nhắc nhở trước 7 ngày, 3 ngày, và đúng ngày đến hạn

### Snooze nhắc nhở
Nhận nhắc mà chưa xử lý được ngay? Nhấn **"Nhắc lại sau 3 ngày"** — Khế sẽ nhắc lại sau 3 ngày, không spam liên tục.

---

## 10. Những điều Khế KHÔNG làm

| Khế KHÔNG | Lý do |
|---|---|
| Tự ký hoặc sửa hợp đồng gốc | Bạn là người quyết định mọi thay đổi pháp lý |
| Cho luật sư/đại lý xem dữ liệu khi bạn chưa đồng ý | Cần sự đồng ý rõ ràng từ bạn |
| Đưa ra tư vấn pháp lý | Khế phân tích dữ liệu, không thay luật sư |
| Bịa thông tin khi không tìm thấy | Sẽ nói thẳng "không tìm thấy" |

---

## 11. Hỗ trợ

Gặp vấn đề hoặc có câu hỏi? Liên hệ đại lý/cố vấn đã giới thiệu bạn với Khế — họ sẽ hỗ trợ trực tiếp hoặc chuyển phản hồi đến đội kỹ thuật.

---

## Changelog

- **v0.1 (2026-06-27)** — Initial pilot manual rendered from issue #339 (PM Kevin). 11 sections. Aligned với DEC-048 EPIC #300 production state (`ce48bbd`).

---

*Khế v0a — Pilot · 2026-06-27 · Tài liệu này được cập nhật theo phiên bản sản phẩm*
