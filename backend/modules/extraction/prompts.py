"""Vietnamese extraction prompts. Shared across providers so the benchmark is fair.

The system/instruction prompt bakes in D-06 (read-only) and D-08 (say "not found",
don't guess). Field definitions are tuned to the F&B/bán lẻ seed verticals
(HĐ thuê mặt bằng / HĐ nhà cung cấp / HĐ lao động).
"""

from __future__ import annotations

# Hard guardrail prepended to every extraction request.
SYSTEM_GUARDRAIL = (
    "Bạn là công cụ BÓC TÁCH THÔNG TIN chỉ-đọc cho hợp đồng tiếng Việt. "
    "TUYỆT ĐỐI KHÔNG sinh, sửa, diễn giải hay tóm tắt lại nội dung pháp lý. "
    "Chỉ trích đúng những gì XUẤT HIỆN trên tài liệu. "
    "Nếu một trường KHÔNG có trên tài liệu, đặt value = null và needs_review = true — "
    "TUYỆT ĐỐI không phỏng đoán. "
    "Với mỗi trường: confidence ∈ [0,1]; đặt needs_review = true khi confidence < 0.9 "
    "hoặc khi ảnh mờ/chữ viết tay/không chắc chắn."
)

# Field-by-field extraction spec (Vietnamese), referenced in the main instruction.
_FIELD_SPEC = """\
Các trường cần bóc (canonical key → mô tả):
- doi_tac: TÊN các bên ký kết (bên A / bên B, bên cho thuê / bên thuê, NSDLĐ / NLĐ,
  nhà cung cấp / khách hàng). Nếu nhiều bên, nối bằng dấu ";".
- ngay_hieu_luc: ngày hợp đồng có hiệu lực. Định dạng yyyy-mm-dd nếu đọc được rõ.
- ngay_het_han: ngày hết hạn / ngày chấm dứt hợp đồng. Định dạng yyyy-mm-dd nếu rõ.
- gia_tri_hd: giá trị hợp đồng / tiền thuê / lương / giá trị đơn hàng (kèm đơn vị tiền nếu có).
- thoi_han_hd: thời hạn hợp đồng (vd "12 tháng", "2 năm", "không xác định thời hạn").
- dieu_khoan_gia_han: điều khoản gia hạn / tái ký / thông báo trước khi hết hạn.
- dieu_khoan_thanh_toan: điều khoản/lịch thanh toán (vd "trả ngày 5 hàng tháng").

Phân loại doc_type:
- hd_thue_mat_bang: hợp đồng thuê mặt bằng/nhà/kho.
- hd_nha_cung_cap: hợp đồng mua bán / cung cấp hàng hóa, dịch vụ.
- hd_lao_dong: hợp đồng lao động.
- khac: không thuộc 3 loại trên (đặt needs_review cao).
"""

# Clause list spec (DEC-026): extracted in the SAME vision call, as the `clauses`
# array of the response schema — no extra API call.
_CLAUSES_SPEC = """\
Ngoài ra, bóc TẤT CẢ điều/khoản/mục có đánh số thành danh sách "clauses":
- Mỗi phần tử gồm: num (số hiệu, vd "Điều 1", "Khoản 2.3", "Mục IV"), title (tiêu đề
  nếu có), content (TOÀN VĂN nội dung điều khoản, nguyên gốc).
- Bao gồm MỌI Điều / Khoản / Mục xuất hiện trong tài liệu, theo đúng thứ tự.
- Nếu điều khoản không có tiêu đề, đặt title = null.
- GIỮ NGUYÊN tiếng Việt — TUYỆT ĐỐI không dịch, không tóm tắt, không diễn giải (D-06).
- Nếu tài liệu không có điều khoản đánh số, để clauses = [].
"""


def build_instruction(doc_type: str = "auto") -> str:
    """Main user-turn instruction. `doc_type` is a hint; the model still returns its
    own classification + confidence (FR-EX-01)."""
    hint = ""
    if doc_type and doc_type != "auto":
        hint = (
            f"\nGỢI Ý từ người dùng: tài liệu có thể là loại '{doc_type}'. "
            "Vẫn tự phân loại và cho doc_type_confidence của bạn.\n"
        )
    return (
        "Đọc ảnh tài liệu hợp đồng bên dưới và bóc tách thông tin theo schema JSON yêu cầu.\n"
        f"{hint}\n{_FIELD_SPEC}\n{_CLAUSES_SPEC}\n"
        "Trả về CHÍNH XÁC theo cấu trúc đã định, không thêm văn bản ngoài JSON."
    )
