"""Vietnamese extraction prompts. Shared across providers so the benchmark is fair.

The system/instruction prompt bakes in D-06 (read-only) and D-08 (say "not found",
don't guess). Field definitions are tuned to the F&B/bán lẻ seed verticals
(HĐ thuê mặt bằng / HĐ nhà cung cấp / HĐ lao động).
"""

from __future__ import annotations

from .schemas import DOC_TYPE_GROUPS

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

# Step 1 (DEC-029) — classify doc_type_group BEFORE field extraction. Drives which
# type-specific fields to look for. List built from the enum so prompt ↔ schema stay
# in sync.
_DOC_TYPE_GROUP_SPEC = (
    "BƯỚC 1 — PHÂN LOẠI: Xác định doc_type_group của văn bản. Chọn ĐÚNG 1 trong:\n  "
    + " | ".join(DOC_TYPE_GROUPS)
    + "\nNếu không đủ dấu hiệu để chắc chắn → \"other\". KHÔNG đoán mò (D-08).\n"
    "Ghi giá trị vào trường doc_type_group (value = đúng một mã ở trên).\n"
)

# Universal fields — always extracted (12 canonical). doc_type giữ enum cũ (4 loại)
# cho tương thích ngược; doc_type_group là phân nhóm rộng mới (DEC-029).
_FIELD_SPEC = """\
BƯỚC 2 — TRÍCH XUẤT. Luôn bóc các trường phổ quát (canonical key → mô tả):
- doi_tac: TÊN các bên ký kết (bên A / bên B, bên cho thuê / bên thuê, NSDLĐ / NLĐ,
  nhà cung cấp / khách hàng). Nếu nhiều bên, nối bằng dấu ";".
- ngay_hieu_luc: ngày hợp đồng có hiệu lực. Định dạng yyyy-mm-dd nếu đọc được rõ.
- ngay_het_han: ngày hết hạn / ngày chấm dứt hợp đồng. Định dạng yyyy-mm-dd nếu rõ.
- gia_tri_hd: giá trị hợp đồng / tiền thuê / lương / giá trị đơn hàng (kèm đơn vị tiền nếu có).
- thoi_han_hd: thời hạn hợp đồng (vd "12 tháng", "2 năm", "không xác định thời hạn").
- dieu_khoan_gia_han: điều khoản gia hạn / tái ký / thông báo trước khi hết hạn.
- dieu_khoan_thanh_toan: điều khoản/lịch thanh toán (vd "trả ngày 5 hàng tháng").
- ngay_ky: ngày ký kết (có thể KHÁC ngày hiệu lực). yyyy-mm-dd nếu rõ.
- tien_dat_coc: tiền đặt cọc / ký quỹ / bảo đảm (kèm đơn vị tiền).
- thoi_han_bao_hanh: thời hạn bảo hành (vd "12 tháng kể từ bàn giao").
- thoi_han_thong_bao: thời hạn báo trước khi chấm dứt (vd "30 ngày").

Phân loại doc_type (enum cũ, song song với doc_type_group):
- hd_thue_mat_bang: hợp đồng thuê mặt bằng/nhà/kho.
- hd_nha_cung_cap: hợp đồng mua bán / cung cấp hàng hóa, dịch vụ.
- hd_lao_dong: hợp đồng lao động.
- khac: không thuộc 3 loại trên (đặt needs_review cao).
"""

# Type-specific field descriptions (DEC-029). Only the set whose group matches
# doc_type_group needs filling; the rest stay null. Generated → schema-synced.
_TYPE_SPECIFIC_DESC: dict[str, str] = {
    "lao_dong": (
        "luong_co_ban (lương cơ bản/tháng), thoi_gian_thu_viec (thời gian thử việc), "
        "chu_ky_dong_bao_hiem (chu kỳ đóng BHXH)"
    ),
    "bat_dong_san": (
        "dia_chi_tai_san (địa chỉ tài sản), dien_tich (diện tích m²), "
        "lich_nop_tien_theo_tien_do (lịch nộp tiền theo tiến độ)"
    ),
    "xay_dung": (
        "tien_bao_lanh_thuc_hien (bảo lãnh thực hiện), tien_giu_lai_bao_hanh (tiền giữ lại bảo hành), "
        "lich_tien_do_thi_cong (lịch tiến độ thi công)"
    ),
    "bao_dam": (
        "tai_san_the_chap (tài sản thế chấp), gia_tri_bao_dam (giá trị bảo đảm), "
        "thoi_han_dang_ky_bien_phap (hạn đăng ký biện pháp bảo đảm)"
    ),
    "cong_nghe_ip": (
        "so_luong_nguoi_dung (số người dùng/license), uptime_cam_ket (SLA uptime %), "
        "chu_ky_gia_han_ban_quyen (chu kỳ gia hạn bản quyền)"
    ),
    "thuong_mai": (
        "pham_vi_dia_ly (phạm vi địa lý đại lý/nhượng quyền), chi_tieu_doanh_so (chỉ tiêu doanh số), "
        "thoi_han_doc_quyen (thời hạn độc quyền), thoi_han_bao_mat (thời hạn bảo mật NDA)"
    ),
    "van_tai_logistics": (
        "tuyen_duong (tuyến đường), trong_tai_hang_hoa (trọng tải/khối lượng hàng), "
        "phuong_thuc_van_chuyen (đường bộ/biển/hàng không)"
    ),
    "tai_chinh": (
        "lai_suat (lãi suất, trần 20%/năm theo BLDS), lich_tra_goc_lai (lịch trả gốc+lãi), "
        "tai_san_dam_bao (tài sản đảm bảo khoản vay)"
    ),
    "hanh_chinh": (
        "pham_vi_uy_quyen (phạm vi ủy quyền), thoi_han_uy_quyen (thời hạn ủy quyền)"
    ),
}

_TYPE_SPECIFIC_SPEC = (
    "BƯỚC 3 — TRƯỜNG THEO NHÓM. Chỉ với nhóm KHỚP doc_type_group ở Bước 1, thêm các\n"
    "trường tương ứng vào danh sách \"type_specific\" (mỗi phần tử: key, value, confidence,\n"
    "needs_review). KEY phải đúng tên dưới đây. Trường không thấy trong tài liệu → bỏ qua\n"
    "(KHÔNG thêm vào list, KHÔNG bịa). Nhóm khác doc_type_group thì KHÔNG thêm:\n"
    + "\n".join(f"- nếu doc_type_group == \"{g}\": {desc}" for g, desc in _TYPE_SPECIFIC_DESC.items())
    + "\n"
)

# Parties + roles spec (DEC-030): captures role↔name so the obligation engine can
# split nghĩa vụ (self) vs quyền lợi (đối tác). Does NOT decide who is the SME.
_PARTIES_SPEC = """\
Ngoài ra, liệt kê các bên ký kết thành danh sách "parties":
- Mỗi phần tử: name (tên bên, đúng như trên tài liệu), role_label (vai trò dùng TRONG
  hợp đồng, vd "Owner", "Operator", "Bên A", "Bên cho thuê", "NSDLĐ"; null nếu không có).
- Bao gồm MỌI bên ký kết. KHÔNG suy đoán bên nào là người dùng (hệ thống tự xác định sau).
- Giữ nguyên tên + vai trò như văn bản, KHÔNG dịch/diễn giải (D-06).
"""

# Obligation schedule spec (DEC-030 Phase 2 / #154): generalized from payments to
# EVERY scheduled obligation, with series + event-trigger support, in the SAME call.
_OBLIGATION_SCHEDULE_SPEC = """\
Ngoài ra, bóc MỌI nghĩa vụ có lịch/đợt thành danh sách "obligation_schedule"
(KHÔNG chỉ thanh toán — gồm cả giao hàng, bàn giao, nghiệm thu, gia hạn, bảo hành...):
- Mỗi phần tử: obligation_type (payment|delivery|handover|expiration|renewal|review|warranty|other),
  description (diễn giải đợt, nguyên văn, vd "Đợt 2 — giao 40% hàng"),
  amount_raw (số tiền/giá trị NGUYÊN VĂN "40%" / "150.000.000 VND" — KHÔNG parse),
  due_date (yyyy-mm-dd nếu có ngày rõ), recurrence ("monthly"/"quarterly"/"yearly"/null),
  obligor (BÊN THỰC HIỆN đợt này — tên hoặc vai trò như văn bản, vd "Owner", "Bên B"; null nếu không rõ).
- CHUỖI NHIỀU ĐỢT (thanh toán/giao hàng theo đợt): gán CÙNG series_id cho mọi đợt cùng chuỗi,
  đặt milestone_index (1, 2, 3...) và milestone_total (tổng số đợt).
- NEO THEO SỰ KIỆN: nếu đợt đến hạn theo sự kiện ("khi giao hàng", "sau nghiệm thu") thay vì ngày:
  đặt trigger = "event", due_date = null, trigger_condition = NGUYÊN VĂN điều kiện,
  trigger_delay_days = số ngày nếu nêu rõ ("30 ngày sau nghiệm thu" → 30). TUYỆT ĐỐI không bịa ngày (D-08).
- Đến hạn theo ngày cụ thể: trigger = "date".
- Chỉ thêm phần tử khi nghĩa vụ RÕ RÀNG. Phi cấu trúc ("theo từng đợt theo thông báo") → bỏ qua,
  giữ dieu_khoan_thanh_toan ở dạng văn bản. KHÔNG bịa lịch (D-06).
"""

# Source-anchor spec (#230 / FR-EX-05): for each extracted field, record WHERE on the
# document it was read so the review UI can link straight to it (Stage 3 trust gate).
# Claude's lean schema has no anchor slots → it simply ignores this (same as it ignores
# clauses/parties/obligation_schedule); Gemini's Full schema fills page_num/ref.
#
# Live smoke (#232, doc 16) showed Gemini fills `value` but leaves page_num/ref null
# when the anchor ask is generic — the per-field descriptions only mention `value`, so
# the model treats the anchor slots as ignorable optionals. This spec is therefore
# explicit + example-driven + mandatory-when-found, and gives the trivial single-page
# default so a 1-page contract has no excuse to return page_num=null.
_ANCHOR_SPEC = """\
NGUỒN TRÍCH DẪN (BẮT BUỘC) — Mỗi trường bóc ra là một object
{value, confidence, needs_review, page_num, ref}. KHI value ≠ null, PHẢI điền THÊM:
- page_num: số trang (số nguyên, BẮT ĐẦU TỪ 1) nơi đọc được value. Tài liệu CHỈ 1 trang → page_num = 1.
- ref: nhãn điều/khoản/mục NGUYÊN VĂN chứa value — vd "Điều 3", "Khoản 2.1", "Mục IV".
  Nếu value ở phần mở đầu/không thuộc điều khoản đánh số → ref = null (nhưng page_num vẫn điền).
Áp dụng cho MỌI trường: cả 12 trường phổ quát LẪN mọi phần tử trong "type_specific".
Ví dụ một trường đã điền ĐỦ neo:
  "ngay_het_han": {"value": "2026-12-31", "confidence": 0.95, "needs_review": false, "page_num": 1, "ref": "Điều 2"}
KHÔNG bịa trang/điều khoản (D-06/D-08): thật sự không chắc trang nào → page_num = null;
không có nhãn điều khoản → ref = null. Nhưng KHÔNG để null chỉ vì bỏ qua bước này.
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
        f"{hint}\n"
        f"{_DOC_TYPE_GROUP_SPEC}\n{_FIELD_SPEC}\n{_TYPE_SPECIFIC_SPEC}\n"
        f"{_ANCHOR_SPEC}\n{_PARTIES_SPEC}\n{_OBLIGATION_SCHEDULE_SPEC}\n{_CLAUSES_SPEC}\n"
        "Trả về CHÍNH XÁC theo cấu trúc đã định, không thêm văn bản ngoài JSON."
    )
