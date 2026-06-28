/**
 * Khế — Admin · Chi tiết hợp đồng v3  (mockup_document_detail_v3.jsx)
 * KHE_Designer · issue #378 · EPIC #362 (DEC-050)
 * STATIC PROTOTYPE — scope-lock docs/mockup_*.jsx. Not production code.
 * ----------------------------------------------------------------------------
 * EXTENDS v2 (#281) with 6 DEC-050 surfaces:
 *   R2  (#364) — "Bên ký kết" parties tab
 *   R3  (#365) — Clause hierarchy (nested accordion)
 *   R5  (#368) — Table/diagram/signature display in clauses
 *   R8  (#371) — Contract lifecycle status badge
 *   R9  (#372) — Defined-terms glossary + inline tooltip
 *   R10 (#373) — Cross-reference links + orphan-ref indicator
 *
 * TAB STRUCTURE (4 tabs):
 *   1. Tổng quan — snapshot, self-party gate, lifecycle badge, terms
 *   2. Nghĩa vụ & Quyền lợi — the CORE (unchanged from v2)
 *   3. Bên ký kết (NEW R2) — self-party + counterparty details
 *   4. Nội dung hợp đồng — clause hierarchy + tables + glossary + cross-refs
 *
 * DESIGN DIRECTION: B&W minimalist (DS v0.2), color rationed to CTA/status.
 */
import React, { useState } from "react";

/* ===========================================================================
 * TOKENS — B&W minimalist (DS v0.2 direction)
 * ========================================================================= */
const t = {
  color: {
    ink: "#1A1A1A", inkMuted: "#6B7280", inkSubtle: "#9CA3AF",
    surface: "#FFFFFF", rowHover: "#F9FAFB",
    border: "#E5E7EB", borderStrong: "#D1D5DB",
    primary: "#0F7A56", primarySoft: "#E7F3EE",
    amber: "#D97706", amberSoft: "#FEF3E2",
    red: "#DC2626", redSoft: "#FDECEC",
    gray: "#6B7280", graySoft: "#F3F4F6",
    green: "#059669", greenSoft: "#ECFDF5",
    blue: "#2563EB", blueSoft: "#EFF6FF",
  },
  font: {
    family: "'Inter', 'Be Vietnam Pro', system-ui, -apple-system, sans-serif",
    size: { xs: 12, sm: 13, md: 14, base: 15, lg: 18, xl: 22, "2xl": 26 },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
  },
  space: { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48 },
  radius: { sm: 6, md: 8, lg: 12, pill: 999 },
};

const TODAY = new Date("2026-06-28");

/* ===========================================================================
 * DEC-029 — doc_type label map
 * ========================================================================= */
const DOC_TYPE_LABELS = {
  hd_nha_cung_cap: "Nhà cung cấp", hd_thue_mat_bang: "Thuê mặt bằng",
  hd_lao_dong: "Lao động", hd_dan_su: "Dân sự", hd_bat_dong_san: "Bất động sản",
  hd_van_tai_logistics: "Vận tải & Logistics", hd_xay_dung: "Xây dựng",
  hd_cong_nghe_ip: "Công nghệ & IP", hd_tai_chinh: "Tài chính", hd_hanh_chinh: "Hành chính",
};
const docTypeLabel = (dt) => DOC_TYPE_LABELS[dt] || "Chưa phân loại";

/* ===========================================================================
 * R8 — LIFECYCLE STATUS
 * ========================================================================= */
const LIFECYCLE = {
  active:    { label: "Đang hiệu lực",  color: t.color.green,  bg: t.color.greenSoft },
  expiring:  { label: "Sắp hết hạn",    color: t.color.amber,  bg: t.color.amberSoft },
  expired:   { label: "Hết hạn",        color: t.color.red,    bg: t.color.redSoft },
  settled:   { label: "Đã thanh lý",    color: t.color.gray,   bg: t.color.graySoft },
  suspended: { label: "Tạm dừng",       color: t.color.gray,   bg: t.color.graySoft },
};

/* ===========================================================================
 * SAMPLE DATA — Công nghệ & IP contract with ALPHATECH (extended for DEC-050)
 * ========================================================================= */
const DOC = {
  id: 8,
  doc_type: "hd_cong_nghe_ip",
  filename: "license_phanmem_IP.pdf",
  primary_party: "Cty Phần Mềm ALPHATECH",
  upload_date: "2026-06-20",
  extracted_date: "2026-06-20",
  signing_date: "2026-03-15",
  status: "extracted",
  confirmed: false,
  may_have_unextracted: true,
  self_party: null,
  lifecycle_status: "active",
  contract_term: "24 tháng (01/04/2026 – 31/03/2028)",
  parties: [
    {
      id: "p1", name: "Cty Phần Mềm ALPHATECH", role_label: "Bên A (cung cấp)",
      aliases: ["ALPHATECH", "Bên A"],
      is_self: false,
      address: "Tầng 12, Tòa nhà Innovation, 123 Nguyễn Huệ, Q.1, TP.HCM",
      representative: "Nguyễn Văn Minh", representative_title: "Giám đốc",
      tax_code: "0316789012",
      contact: "contact@alphatech.vn · 028-3823-4567",
    },
    {
      id: "p2", name: "Cty TNHH Thương Mại Minh Phát", role_label: "Bên B (sử dụng)",
      aliases: ["Minh Phát", "Bên B", "MP"],
      is_self: true,
      address: "456 Lê Lợi, Q. Thanh Khê, TP. Đà Nẵng",
      representative: "Trần Thị Hương", representative_title: "Giám đốc",
      tax_code: "0401234567",
      contact: "huong@minhphat.vn · 0236-382-1234",
    },
  ],
};

const TERMS = [
  { key: "loai_hd", label: "Loại hợp đồng", value: "Công nghệ & IP", needsReview: false },
  { key: "doi_tac", label: "Đối tác", value: "Cty Phần Mềm ALPHATECH", needsReview: false },
  { key: "ngay_ky", label: "Ngày ký", value: "15/03/2026", needsReview: false },
  { key: "ngay_hieu_luc", label: "Ngày hiệu lực", value: "01/04/2026", needsReview: false },
  { key: "thoi_han_hd", label: "Thời hạn", value: "24 tháng", needsReview: false },
  { key: "ngay_het_han", label: "Ngày hết hạn", value: "31/03/2028", needsReview: false, derived: true },
  { key: "gia_tri_hd", label: "Giá trị HĐ", value: "18.000.000 đ/tháng", needsReview: false },
  { key: "phat_vi_pham", label: "Phạt vi phạm", value: null, needsReview: true, notFound: true },
];

/* R9 — Glossary definitions (from Phụ lục A) */
const GLOSSARY = [
  { id: "g1", term: "Phần mềm", definition: "Phần mềm Quản lý Kho ALPHATECH phiên bản 3.2 và các bản cập nhật được cung cấp trong thời hạn hợp đồng.", source_clause: "Phụ lục A" },
  { id: "g2", term: "Năm Tài chính", definition: "Kỳ 12 tháng bắt đầu từ ngày 01/04 đến ngày 31/03 năm sau.", source_clause: "Phụ lục A" },
  { id: "g3", term: "Thương hiệu", definition: "Tên thương mại, logo, nhãn hiệu đã đăng ký của Bên A liên quan đến Phần mềm.", source_clause: "Phụ lục A" },
  { id: "g4", term: "Dữ liệu Khách hàng", definition: "Toàn bộ dữ liệu do Bên B nhập vào, lưu trữ hoặc xử lý thông qua Phần mềm.", source_clause: "Phụ lục A" },
  { id: "g5", term: "Sự cố", definition: "Lỗi kỹ thuật khiến Phần mềm không hoạt động đúng theo tài liệu hướng dẫn.", source_clause: "Phụ lục A" },
];

/* R3 — Hierarchical clauses with parent/child + R5 table/image/signature + R10 cross-refs */
const CLAUSES_HIERARCHY = [
  {
    id: "c1", num: "Điều 1", title: "Phạm vi cung cấp", page: 1,
    level: 0, clause_path: "1", parent_id: null,
    content: 'Bên A cấp cho Bên B quyền sử dụng không độc quyền {{Phần mềm}}, bao gồm các module quy định tại [[Phụ lục B]].',
    children: [
      {
        id: "c1.1", num: "1.1", title: "Module được cấp phép", page: 1,
        level: 1, clause_path: "1.1", parent_id: "c1",
        content: "Quyền sử dụng bao gồm: Quản lý tồn kho, Xuất nhập kho, Báo cáo thống kê. Chi tiết tại [[Phụ lục B]].",
        children: [],
      },
      {
        id: "c1.2", num: "1.2", title: "Giới hạn phạm vi", page: 1,
        level: 1, clause_path: "1.2", parent_id: "c1",
        content: "Quyền sử dụng giới hạn trong phạm vi hoạt động kinh doanh của Bên B tại Việt Nam, theo định nghĩa {{Dữ liệu Khách hàng}}.",
        children: [],
      },
    ],
  },
  {
    id: "c2", num: "Điều 2", title: "Thời hạn và hiệu lực", page: 1,
    level: 0, clause_path: "2", parent_id: null,
    content: "Hợp đồng có hiệu lực từ ngày 01/04/2026 đến ngày 31/03/2028 theo {{Năm Tài chính}}. Tự động gia hạn thêm 12 tháng nếu không bên nào thông báo chấm dứt theo [[Điều 8]].",
    children: [],
  },
  {
    id: "c3", num: "Điều 3", title: "Phí sử dụng và thanh toán", page: 2,
    level: 0, clause_path: "3", parent_id: null,
    content: "Phí sử dụng: 18.000.000 đồng/tháng (đã bao gồm VAT). Thanh toán trước ngày 05 hàng tháng. Chậm thanh toán quá 15 ngày, Bên A có quyền tạm ngừng cung cấp dịch vụ theo [[Điều 8]].",
    children: [
      {
        id: "c3.1", num: "3.1", title: "Lịch thanh toán", page: 2,
        level: 1, clause_path: "3.1", parent_id: "c3",
        content: "Bên B thanh toán theo lịch quy định tại bảng dưới đây:",
        table: {
          headers: ["Kỳ", "Thời hạn", "Số tiền (VNĐ)"],
          rows: [
            ["Tháng 4–6/2026", "Ngày 05 hàng tháng", "18.000.000"],
            ["Tháng 7–9/2026", "Ngày 05 hàng tháng", "18.000.000"],
            ["Tháng 10–12/2026", "Ngày 05 hàng tháng", "18.000.000"],
            ["Tháng 1–3/2027", "Ngày 05 hàng tháng", "19.800.000 *"],
          ],
        },
        children: [],
      },
      {
        id: "c3.2", num: "3.2", title: "Điều chỉnh phí", page: 2,
        level: 1, clause_path: "3.2", parent_id: "c3",
        content: "(*) Phí sử dụng được điều chỉnh tăng 10% sau mỗi {{Năm Tài chính}}, có hiệu lực từ kỳ thanh toán đầu tiên của năm mới.",
        children: [],
      },
    ],
  },
  {
    id: "c4", num: "Điều 4", title: "Nghĩa vụ của Bên A", page: 2,
    level: 0, clause_path: "4", parent_id: null,
    content: "Bên A có trách nhiệm theo quy định tại [[Điều 4]] khoản 4.1 đến 4.4:",
    children: [
      {
        id: "c4.1", num: "4.1", title: "Bàn giao tài liệu", page: 2,
        level: 1, clause_path: "4.1", parent_id: "c4",
        content: "Bàn giao tài liệu hướng dẫn sử dụng trong vòng 15 ngày kể từ ngày ký.",
        children: [],
      },
      {
        id: "c4.2", num: "4.2", title: "Cập nhật phần mềm", page: 3,
        level: 1, clause_path: "4.2", parent_id: "c4",
        content: "Cập nhật phiên bản {{Phần mềm}} mới khi có, bao gồm bản vá lỗi và cải tiến.",
        children: [],
      },
      {
        id: "c4.3", num: "4.3", title: "Hỗ trợ kỹ thuật", page: 3,
        level: 1, clause_path: "4.3", parent_id: "c4",
        content: "Hỗ trợ kỹ thuật trong giờ hành chính (8:00–17:00, T2–T6). Xử lý {{Sự cố}} trong vòng 4 giờ làm việc.",
        children: [],
      },
      {
        id: "c4.4", num: "4.4", title: "Cam kết uptime", page: 3,
        level: 1, clause_path: "4.4", parent_id: "c4",
        content: "Đảm bảo uptime tối thiểu 99.5% trong mỗi tháng lịch.",
        children: [],
      },
    ],
  },
  {
    id: "c5", num: "Điều 5", title: "Nghĩa vụ của Bên B", page: 3,
    level: 0, clause_path: "5", parent_id: null,
    content: "Bên B có trách nhiệm tuân thủ các quy định tại [[Điều 6]] về bảo mật và [[Điều 7]] về sở hữu trí tuệ.",
    children: [],
  },
  {
    id: "c6", num: "Điều 6", title: "Bảo mật thông tin", page: 3,
    level: 0, clause_path: "6", parent_id: null,
    content: "Hai bên cam kết bảo mật toàn bộ thông tin kỹ thuật và thương mại, bao gồm {{Dữ liệu Khách hàng}}, trong suốt thời gian thực hiện và 3 năm sau khi chấm dứt hợp đồng.",
    children: [],
  },
  {
    id: "c7", num: "Điều 7", title: "Sở hữu trí tuệ", page: 4,
    level: 0, clause_path: "7", parent_id: null,
    content: "Bên A là chủ sở hữu toàn bộ quyền sở hữu trí tuệ đối với {{Phần mềm}} và {{Thương hiệu}}. Bên B được cấp quyền sử dụng không độc quyền. Danh sách tài sản trí tuệ tại [[Phụ lục B]].",
    image_ref: { page: 4, description: "Bảng đăng ký nhãn hiệu — 2 nhãn hiệu + số văn bằng" },
    children: [],
  },
  {
    id: "c8", num: "Điều 8", title: "Chấm dứt hợp đồng", page: 4,
    level: 0, clause_path: "8", parent_id: null,
    content: "Hợp đồng chấm dứt khi: (a) Hết thời hạn và không gia hạn; (b) Hai bên thoả thuận chấm dứt; (c) Một bên vi phạm nghiêm trọng nghĩa vụ theo [[Điều 4]] hoặc [[Điều 5]] sau khi được thông báo 30 ngày mà không khắc phục.",
    children: [],
  },
];

const SIGNATURE_REFS = [
  { page: 5, type: "signature", description: "Chữ ký Bên A — Nguyễn Văn Minh, Giám đốc" },
  { page: 5, type: "signature", description: "Chữ ký Bên B — Trần Thị Hương, Giám đốc" },
  { page: 5, type: "stamp", description: "Con dấu Cty Phần Mềm ALPHATECH" },
  { page: 5, type: "stamp", description: "Con dấu Cty TNHH Thương Mại Minh Phát" },
];

const ORPHAN_REFS = [
  { text: "Phụ lục E", found_in: "Điều 7, dòng 3", resolved: false },
];

const OBLIGATIONS_SAMPLE = [
  { id: 1, title: "Thanh toán phí license tháng 7/2026", direction: "nv", type: "payment",
    due_date: "2026-07-05", amount: "18.000.000 đ", status: "upcoming", standing: false },
  { id: 2, title: "Bàn giao tài liệu hướng dẫn sử dụng", direction: "ql", type: "delivery",
    due_date: null, due_event: "sau khi ký hợp đồng 15 ngày", status: "waiting_event", standing: false },
  { id: 3, title: "Không tiết lộ thông tin kỹ thuật và thương mại", direction: "nv", type: "confidentiality",
    due_date: null, status: "standing", standing: true },
];

/* ===========================================================================
 * SIDEBAR
 * ========================================================================= */
function NavItem({ glyph, label, active, badge, beta }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: t.space[2],
      padding: `${t.space[2]}px ${t.space[3]}px`, borderRadius: t.radius.md, cursor: "pointer",
      background: active ? t.color.primarySoft : "transparent",
      color: active ? t.color.primary : t.color.ink,
      fontWeight: active ? t.font.weight.semibold : t.font.weight.regular, fontSize: t.font.size.md,
    }}>
      <span style={{ width: 16, textAlign: "center", color: active ? t.color.primary : t.color.inkMuted }}>{glyph}</span>
      <span style={{ flex: 1 }}>{label}</span>
      {beta && <span style={{ fontSize: 10, fontWeight: t.font.weight.semibold, color: t.color.amber, background: t.color.amberSoft, padding: "1px 6px", borderRadius: t.radius.pill }}>Beta</span>}
      {badge != null && <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.surface, background: t.color.amber, minWidth: 18, textAlign: "center", padding: "0 5px", borderRadius: t.radius.pill }}>{badge}</span>}
    </div>
  );
}

function Sidebar() {
  const grp = { fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.inkSubtle,
    letterSpacing: 0.5, textTransform: "uppercase", padding: `${t.space[2]}px ${t.space[3]}px ${t.space[1]}px` };
  return (
    <aside style={{ width: 232, borderRight: `1px solid ${t.color.border}`, padding: t.space[4], boxSizing: "border-box", background: t.color.surface }}>
      <div style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.primary, padding: `${t.space[2]}px ${t.space[3]}px ${t.space[5]}px` }}>Khế</div>
      <div style={grp}>Theo dõi</div>
      <NavItem glyph="○" label="Tổng quan" badge={3} />
      <NavItem glyph="◇" label="Nghĩa vụ & Quyền lợi" />
      <div style={grp}>Tài liệu</div>
      <NavItem glyph="■" label="Hồ sơ hợp đồng" active />
      <NavItem glyph="↑" label="Tải lên" />
      <div style={grp}>Trợ lý</div>
      <NavItem glyph="✦" label="Hỏi-đáp" beta />
    </aside>
  );
}

/* ===========================================================================
 * TAB BAR (4 tabs)
 * ========================================================================= */
function TabBar({ tabs, active, onChange }) {
  return (
    <div style={{ display: "flex", gap: 0, borderBottom: `1px solid ${t.color.border}`, marginTop: t.space[6] }}>
      {tabs.map((tab) => (
        <button key={tab.key} onClick={() => onChange(tab.key)} style={{
          padding: `${t.space[3]}px ${t.space[5]}px`, cursor: "pointer",
          fontFamily: t.font.family, fontSize: t.font.size.md, border: "none", background: "transparent",
          fontWeight: active === tab.key ? t.font.weight.semibold : t.font.weight.regular,
          color: active === tab.key ? t.color.primary : t.color.inkMuted,
          borderBottom: active === tab.key ? `2px solid ${t.color.primary}` : "2px solid transparent",
          marginBottom: -1,
        }}>{tab.label}{tab.badge != null && <span style={{ marginLeft: t.space[1], fontSize: t.font.size.xs, color: t.color.amber }}>({tab.badge})</span>}</button>
      ))}
    </div>
  );
}

/* ===========================================================================
 * R8 — LIFECYCLE STATUS BADGE
 * Shown in header next to confirm status. Auto-derived from dates, manual
 * override for thanh lý / tạm dừng → Event.
 * ========================================================================= */
function LifecycleBadge({ status }) {
  const s = LIFECYCLE[status];
  if (!s) return null;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: t.space[1],
      padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill,
      fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold,
      color: s.color, background: s.bg,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: s.color }} />
      {s.label}
    </span>
  );
}

function LifecycleShowcase() {
  return (
    <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[3] }}>
      {Object.keys(LIFECYCLE).map((k) => <LifecycleBadge key={k} status={k} />)}
    </div>
  );
}

/* ===========================================================================
 * DIRECTION BADGE
 * ========================================================================= */
function DirectionBadge({ direction }) {
  if (direction === "nv")
    return <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.ink, background: t.color.graySoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>↑ Phải làm</span>;
  if (direction === "ql")
    return <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, background: t.color.primarySoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>↓ Được hưởng</span>;
  return <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.amber, background: t.color.amberSoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>? Chưa rõ</span>;
}

/* ===========================================================================
 * SELF-PARTY GATE
 * ========================================================================= */
function SelfPartyGate({ parties, selfParty, onSet }) {
  if (selfParty) {
    const p = parties.find((x) => x.id === selfParty);
    return (
      <div style={{ padding: t.space[4], background: t.color.primarySoft, borderRadius: t.radius.md, marginTop: t.space[5], display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.primary, fontWeight: t.font.weight.semibold }}>Bên của bạn</div>
          <div style={{ fontSize: t.font.size.base, color: t.color.ink, fontWeight: t.font.weight.medium, marginTop: 2 }}>{p ? p.name : "—"} <span style={{ color: t.color.inkMuted, fontWeight: t.font.weight.regular }}>({p ? p.role_label : ""})</span></div>
        </div>
        <button onClick={() => onSet(null)} style={{ border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.ink, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.md, fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family }}>Đổi</button>
      </div>
    );
  }
  return (
    <div style={{ padding: t.space[5], border: `2px solid ${t.color.amber}`, borderRadius: t.radius.lg, marginTop: t.space[5], background: t.color.amberSoft + "44" }}>
      <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.bold, color: t.color.ink }}>Bên nào trong hợp đồng này là bạn?</div>
      <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: 1.6 }}>
        Chọn bên bạn đại diện để Khế biết đâu là việc bạn phải làm, đâu là quyền lợi bạn được hưởng.
      </div>
      <div style={{ display: "flex", gap: t.space[3], marginTop: t.space[4], flexWrap: "wrap" }}>
        {parties.map((p) => (
          <button key={p.id} onClick={() => onSet(p.id)} style={{
            flex: 1, minWidth: 200, padding: t.space[4], border: `1px solid ${t.color.borderStrong}`,
            borderRadius: t.radius.md, background: t.color.surface, cursor: "pointer", textAlign: "left", fontFamily: t.font.family,
          }}>
            <div style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{p.name}</div>
            <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>{p.role_label}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ===========================================================================
 * R9 — DEFINED-TERM TOOLTIP + CROSS-REFERENCE LINK (R10)
 * Renders clause content with {{term}} → tooltip and [[ref]] → link.
 * ========================================================================= */
function renderClauseContent(text, glossary, onRefClick) {
  if (!text) return null;
  const parts = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    const termMatch = remaining.match(/\{\{(.+?)\}\}/);
    const refMatch = remaining.match(/\[\[(.+?)\]\]/);

    let nextMatch = null;
    let matchType = null;

    if (termMatch && refMatch) {
      if (termMatch.index < refMatch.index) { nextMatch = termMatch; matchType = "term"; }
      else { nextMatch = refMatch; matchType = "ref"; }
    } else if (termMatch) { nextMatch = termMatch; matchType = "term"; }
    else if (refMatch) { nextMatch = refMatch; matchType = "ref"; }

    if (!nextMatch) {
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    }

    if (nextMatch.index > 0) {
      parts.push(<span key={key++}>{remaining.slice(0, nextMatch.index)}</span>);
    }

    if (matchType === "term") {
      const termName = nextMatch[1];
      const def = glossary.find((g) => g.term === termName);
      parts.push(
        <span key={key++} style={{
          borderBottom: `1px dashed ${t.color.primary}`, color: t.color.primary,
          cursor: "help", position: "relative",
        }} title={def ? `${def.term}: ${def.definition}` : `Thuật ngữ: ${termName}`}>
          {termName}
        </span>
      );
    } else {
      const refText = nextMatch[1];
      const isOrphan = ORPHAN_REFS.some((o) => o.text === refText && !o.resolved);
      parts.push(
        <span key={key++} onClick={() => onRefClick && onRefClick(refText)} style={{
          color: isOrphan ? t.color.red : t.color.blue,
          textDecoration: isOrphan ? "underline wavy" : "underline",
          cursor: "pointer", fontWeight: t.font.weight.medium,
        }} title={isOrphan ? `⚠ Tham chiếu không tìm thấy: ${refText}` : `Chuyển tới ${refText}`}>
          {refText}{isOrphan && <span style={{ fontSize: t.font.size.xs, color: t.color.red, marginLeft: 2 }}>⚠</span>}
        </span>
      );
    }

    remaining = remaining.slice(nextMatch.index + nextMatch[0].length);
  }

  return <>{parts}</>;
}

/* ===========================================================================
 * R5 — TABLE RENDER in clause
 * ========================================================================= */
function ClauseTable({ table }) {
  if (!table) return null;
  return (
    <div style={{ marginTop: t.space[3], overflowX: "auto" }}>
      <table style={{
        width: "100%", borderCollapse: "collapse", fontSize: t.font.size.sm,
        border: `1px solid ${t.color.border}`, borderRadius: t.radius.sm,
      }}>
        <thead>
          <tr>
            {table.headers.map((h, i) => (
              <th key={i} style={{
                padding: `${t.space[2]}px ${t.space[3]}px`, textAlign: "left",
                background: t.color.graySoft, borderBottom: `1px solid ${t.color.border}`,
                fontWeight: t.font.weight.semibold, color: t.color.ink, fontSize: t.font.size.sm,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td key={ci} style={{
                  padding: `${t.space[2]}px ${t.space[3]}px`,
                  borderBottom: ri < table.rows.length - 1 ? `1px solid ${t.color.border}` : "none",
                  color: t.color.ink, fontSize: t.font.size.sm,
                }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ===========================================================================
 * R5 — IMAGE/DIAGRAM CROP REFERENCE
 * ========================================================================= */
function ImageCropRef({ ref_data }) {
  if (!ref_data) return null;
  return (
    <div style={{
      marginTop: t.space[3], padding: t.space[3],
      background: t.color.graySoft, borderRadius: t.radius.md, border: `1px dashed ${t.color.borderStrong}`,
      display: "flex", alignItems: "center", gap: t.space[3],
    }}>
      <div style={{
        width: 48, height: 48, background: t.color.surface, border: `1px solid ${t.color.border}`,
        borderRadius: t.radius.sm, display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 20, color: t.color.inkMuted,
      }}>🖼</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: t.font.size.sm, color: t.color.ink }}>{ref_data.description}</div>
        <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: 2 }}>Trang {ref_data.page}</div>
      </div>
      <button style={{
        border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.ink,
        padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.md,
        fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family,
      }}>Xem ảnh gốc</button>
    </div>
  );
}

/* ===========================================================================
 * R5 — SIGNATURE / STAMP BADGES
 * ========================================================================= */
function SignatureStampSection({ refs }) {
  if (!refs || refs.length === 0) return null;
  return (
    <div style={{ marginTop: t.space[5] }}>
      <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3, marginBottom: t.space[3] }}>Chữ ký & Con dấu</div>
      <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
        {refs.map((r, i) => (
          <div key={i} style={{
            display: "flex", alignItems: "center", gap: t.space[3],
            padding: `${t.space[2]}px ${t.space[4]}px`,
            borderBottom: i < refs.length - 1 ? `1px solid ${t.color.border}` : "none",
          }}>
            <span style={{ fontSize: 16 }}>{r.type === "signature" ? "✍️" : "🔴"}</span>
            <span style={{ flex: 1, fontSize: t.font.size.sm, color: t.color.ink }}>{r.description}</span>
            <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>Tr. {r.page}</span>
            <button style={{
              border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.inkMuted,
              padding: `1px ${t.space[2]}px`, borderRadius: t.radius.sm,
              fontSize: t.font.size.xs, cursor: "pointer", fontFamily: t.font.family,
            }}>Xem trang</button>
          </div>
        ))}
      </div>
      <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[2] }}>
        Khế nhận diện vị trí chữ ký và con dấu — không OCR nội dung (D-01).
      </div>
    </div>
  );
}

/* ===========================================================================
 * R3 — CLAUSE HIERARCHY ITEM (nested accordion)
 * ========================================================================= */
function ClauseHierarchyItem({ clause, expanded, onToggle, glossary, onRefClick, depth }) {
  const indent = depth * 24;
  const hasChildren = clause.children && clause.children.length > 0;

  return (
    <>
      <div style={{ borderBottom: `1px solid ${t.color.border}` }}>
        <button onClick={onToggle} style={{
          display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%",
          padding: `${t.space[3]}px ${t.space[4]}px`, paddingLeft: t.space[4] + indent,
          border: "none", background: t.color.surface,
          cursor: "pointer", fontFamily: t.font.family, textAlign: "left",
        }}>
          <span style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
            {depth > 0 && <span style={{ color: t.color.border, fontSize: t.font.size.xs }}>└</span>}
            <span style={{
              fontSize: depth === 0 ? t.font.size.base : t.font.size.md,
              fontWeight: depth === 0 ? t.font.weight.semibold : t.font.weight.medium,
              color: t.color.ink,
            }}>
              {clause.num}{clause.title ? ` — ${clause.title}` : ""}
            </span>
            {hasChildren && (
              <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, background: t.color.graySoft, padding: `0 ${t.space[1]}px`, borderRadius: t.radius.sm }}>
                {clause.children.length}
              </span>
            )}
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: t.space[3] }}>
            {clause.page && <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>Tr. {clause.page}</span>}
            <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>{expanded ? "▴" : "▾"}</span>
          </span>
        </button>

        {expanded && (
          <div style={{ padding: `0 ${t.space[4]}px ${t.space[4]}px`, paddingLeft: t.space[4] + indent }}>
            <div style={{ fontSize: t.font.size.md, color: t.color.ink, lineHeight: 1.7 }}>
              {renderClauseContent(clause.content, glossary, onRefClick)}
            </div>
            {clause.table && <ClauseTable table={clause.table} />}
            {clause.image_ref && <ImageCropRef ref_data={clause.image_ref} />}
          </div>
        )}
      </div>

      {/* FE NOTE: children hardcoded expanded={true} + no-op toggle for prototype.
         Production must make each child independently collapsible (real nested accordion state). */}
      {expanded && hasChildren && clause.children.map((child) => (
        <ClauseHierarchyItem
          key={child.id}
          clause={child}
          expanded={true}
          onToggle={() => {}}
          glossary={glossary}
          onRefClick={onRefClick}
          depth={depth + 1}
        />
      ))}
    </>
  );
}

/* ===========================================================================
 * R10 — ORPHAN REFERENCE PANEL
 * ========================================================================= */
function OrphanRefPanel({ orphans }) {
  if (!orphans || orphans.length === 0) return null;
  return (
    <div style={{
      padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md,
      background: t.color.redSoft + "44", border: `1px solid ${t.color.red}33`,
      marginBottom: t.space[4], display: "flex", alignItems: "flex-start", gap: t.space[2],
    }}>
      <span style={{ color: t.color.red, fontWeight: t.font.weight.bold, marginTop: 1 }}>⚠</span>
      <div>
        <div style={{ fontSize: t.font.size.md, color: t.color.ink, fontWeight: t.font.weight.medium }}>
          {orphans.length} tham chiếu không tìm thấy
        </div>
        {orphans.map((o, i) => (
          <div key={i} style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
            <span style={{ color: t.color.red, fontWeight: t.font.weight.medium }}>"{o.text}"</span>
            {" "}(trong {o.found_in}) — có thể phụ lục chưa được tải lên hoặc không tồn tại
          </div>
        ))}
      </div>
    </div>
  );
}

/* ===========================================================================
 * R9 — GLOSSARY SECTION
 * ========================================================================= */
function GlossarySection({ definitions }) {
  const [expanded, setExpanded] = useState(false);
  if (!definitions || definitions.length === 0) return null;

  return (
    <div style={{ marginBottom: t.space[5] }}>
      <button onClick={() => setExpanded(!expanded)} style={{
        display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%",
        padding: `${t.space[3]}px ${t.space[4]}px`, border: `1px solid ${t.color.border}`,
        borderRadius: t.radius.md, background: t.color.graySoft, cursor: "pointer", fontFamily: t.font.family,
      }}>
        <span style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
          <span style={{ fontSize: 14 }}>📖</span>
          <span style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
            Định nghĩa ({definitions.length})
          </span>
          <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>
            Thuật ngữ được định nghĩa trong hợp đồng — di chuột vào từ gạch nét đứt trong điều khoản để xem
          </span>
        </span>
        <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>{expanded ? "▴" : "▾"}</span>
      </button>

      {expanded && (
        <div style={{ border: `1px solid ${t.color.border}`, borderTop: "none", borderRadius: `0 0 ${t.radius.md}px ${t.radius.md}px`, overflow: "hidden" }}>
          {definitions.map((d, i) => (
            <div key={d.id} style={{
              display: "flex", gap: t.space[3],
              padding: `${t.space[3]}px ${t.space[4]}px`,
              borderBottom: i < definitions.length - 1 ? `1px solid ${t.color.border}` : "none",
            }}>
              <span style={{ width: 140, flexShrink: 0, fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.primary }}>{d.term}</span>
              <span style={{ flex: 1, fontSize: t.font.size.sm, color: t.color.ink, lineHeight: 1.5 }}>{d.definition}</span>
              <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, flexShrink: 0 }}>{d.source_clause}</span>
              <button style={{ border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.inkMuted, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.sm, fontSize: t.font.size.xs, cursor: "pointer", fontFamily: t.font.family, flexShrink: 0 }}>✎</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ===========================================================================
 * TAB 1 — Tổng quan (with R8 lifecycle)
 * ========================================================================= */
function TabOverview({ doc, selfParty, onSetSelfParty }) {
  return (
    <div style={{ marginTop: t.space[5] }}>
      <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
        {selfParty ? (
          <>
            <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.border}`, color: t.color.ink }}>3 nghĩa vụ</span>
            <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.border}`, color: t.color.ink }}>1 quyền lợi</span>
          </>
        ) : (
          <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.amber}`, color: t.color.amber }}>8 mục cần theo dõi</span>
        )}
        <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.border}`, color: t.color.inkMuted }}>3 cam kết hiệu lực</span>
      </div>

      <SelfPartyGate parties={doc.parties} selfParty={selfParty} onSet={onSetSelfParty} />

      {/* Contract term + lifecycle (R8) */}
      <div style={{
        marginTop: t.space[4], padding: t.space[4], background: t.color.graySoft,
        borderRadius: t.radius.md, display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3 }}>Thời hạn hợp đồng</div>
          <div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{doc.contract_term}</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: t.space[3] }}>
          <LifecycleBadge status={doc.lifecycle_status} />
          <button style={{ border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.inkMuted, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.sm, fontSize: t.font.size.xs, cursor: "pointer", fontFamily: t.font.family }} title="Cập nhật trạng thái thủ công (thanh lý, tạm dừng) → Event">⋮</button>
        </div>
      </div>

      {/* Dates */}
      <div style={{ display: "flex", gap: t.space[6], marginTop: t.space[5], flexWrap: "wrap" }}>
        <div><div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3 }}>Ngày ký</div><div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{doc.signing_date}</div></div>
        <div><div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3 }}>Tải lên</div><div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{doc.upload_date}</div></div>
        <div><div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3 }}>Đã bóc tách</div><div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{doc.extracted_date}</div></div>
      </div>

      {/* Terms */}
      <div style={{ marginTop: t.space[6] }}>
        <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3, marginBottom: t.space[3] }}>Thông tin trích xuất</div>
        <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
          {TERMS.map((f, i) => (
            <div key={f.key} style={{
              display: "flex", alignItems: "center", gap: t.space[3],
              padding: `${t.space[3]}px ${t.space[4]}px`,
              borderBottom: i < TERMS.length - 1 ? `1px solid ${t.color.border}` : "none",
              background: f.needsReview ? t.color.amberSoft + "33" : t.color.surface,
            }}>
              <span style={{ width: 160, flexShrink: 0, fontSize: t.font.size.sm, color: t.color.inkMuted, fontWeight: t.font.weight.medium }}>{f.label}</span>
              <span style={{ flex: 1, fontSize: t.font.size.md, color: t.color.ink }}>
                {f.notFound ? (
                  <span style={{ color: t.color.amber, fontStyle: "italic" }}>Có thể bị bỏ sót</span>
                ) : (
                  <>{f.value}{f.derived && <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginLeft: t.space[2] }}>(suy ra)</span>}</>
                )}
              </span>
              {f.needsReview && <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.amber, background: t.color.amberSoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>⚠ Cần kiểm tra</span>}
              <button style={{ border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.inkMuted, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.sm, fontSize: t.font.size.xs, cursor: "pointer", fontFamily: t.font.family }}>✎</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ===========================================================================
 * TAB 2 — Nghĩa vụ & Quyền lợi (condensed from v2, same structure)
 * ========================================================================= */
function TabObligations({ selfParty }) {
  return (
    <div style={{ marginTop: t.space[5] }}>
      {!selfParty && (
        <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md, background: t.color.amberSoft + "66", border: `1px solid ${t.color.amber}44`, marginBottom: t.space[4], display: "flex", alignItems: "center", gap: t.space[2] }}>
          <span style={{ color: t.color.amber, fontWeight: t.font.weight.bold }}>?</span>
          <span style={{ fontSize: t.font.size.md, color: t.color.ink }}>Chưa xác định chiều — chọn bên ở tab Tổng quan</span>
        </div>
      )}
      <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
        {OBLIGATIONS_SAMPLE.map((ob, i) => (
          <div key={ob.id} style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: i < OBLIGATIONS_SAMPLE.length - 1 ? `1px solid ${t.color.border}` : "none" }}>
            <div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
              <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.medium, color: t.color.ink }}>{ob.title}</span>
              <DirectionBadge direction={selfParty ? ob.direction : null} />
            </div>
            <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>
              {ob.standing ? "Cam kết đang hiệu lực" : ob.due_date ? ob.due_date : `Chờ mốc: ${ob.due_event}`}
              {ob.amount && ` · ${ob.amount}`}
            </div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[3] }}>
        Tab Nghĩa vụ đầy đủ xem v2 (#281). Ở đây trình bày condensed để focus DEC-050 surfaces.
      </div>
    </div>
  );
}

/* ===========================================================================
 * TAB 3 — R2: BÊN KÝ KẾT (Parties)
 * Self-party highlighted + counterparties with full details.
 * D-07: every field editable → Event.
 * ========================================================================= */
function PartyCard({ party, isSelf }) {
  return (
    <div style={{
      padding: t.space[5], borderRadius: t.radius.lg,
      border: isSelf ? `2px solid ${t.color.primary}` : `1px solid ${t.color.border}`,
      background: isSelf ? t.color.primarySoft + "33" : t.color.surface,
      marginBottom: t.space[4],
    }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: t.space[4] }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
            <span style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.bold, color: t.color.ink }}>{party.name}</span>
            {isSelf && <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, background: t.color.primarySoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>Bên của bạn</span>}
          </div>
          <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: 2 }}>{party.role_label}</div>
          {party.aliases && party.aliases.length > 0 && (
            <div style={{ display: "flex", gap: t.space[1], marginTop: t.space[1], flexWrap: "wrap" }}>
              <span style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle }}>gọi chung là</span>
              {party.aliases.map((a) => (
                <span key={a} style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, color: t.color.inkMuted, background: t.color.graySoft, padding: `0 ${t.space[2]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.border}` }}>{a}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Details grid */}
      <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: `${t.space[3]}px ${t.space[4]}px` }}>
        {[
          { label: "Người đại diện", value: `${party.representative} — ${party.representative_title}` },
          { label: "Địa chỉ", value: party.address },
          { label: "Mã số thuế", value: party.tax_code },
          { label: "Liên hệ", value: party.contact },
        ].map((field) => (
          <React.Fragment key={field.label}>
            <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontWeight: t.font.weight.medium }}>{field.label}</span>
            <div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
              <span style={{ fontSize: t.font.size.md, color: t.color.ink }}>{field.value || "—"}</span>
              <button style={{ border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.inkMuted, padding: `0 ${t.space[1]}px`, borderRadius: t.radius.sm, fontSize: t.font.size.xs, cursor: "pointer", fontFamily: t.font.family }}>✎</button>
            </div>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

function TabParties({ parties, selfParty }) {
  const selfP = parties.find((p) => p.id === selfParty);
  const counterparties = parties.filter((p) => p.id !== selfParty);

  return (
    <div style={{ marginTop: t.space[5] }}>
      {!selfParty && (
        <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md, background: t.color.amberSoft + "66", border: `1px solid ${t.color.amber}44`, marginBottom: t.space[4], display: "flex", alignItems: "center", gap: t.space[2] }}>
          <span style={{ color: t.color.amber, fontWeight: t.font.weight.bold }}>?</span>
          <span style={{ fontSize: t.font.size.md, color: t.color.ink }}>Chọn bên của bạn ở tab Tổng quan để phân biệt bên mình / đối tác</span>
        </div>
      )}

      {/* Self-party (highlighted) */}
      {selfP && <PartyCard party={selfP} isSelf={true} />}

      {/* Counterparties */}
      <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3, marginBottom: t.space[3], marginTop: selfP ? t.space[2] : 0 }}>
        {selfP ? "Đối tác" : "Các bên ký kết"}
      </div>
      {(selfP ? counterparties : parties).map((p) => (
        <PartyCard key={p.id} party={p} isSelf={false} />
      ))}

      <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[2] }}>
        Thông tin bên ký kết được bóc tách từ hợp đồng. Mỗi trường có thể sửa — thay đổi được ghi nhận (D-07).
      </div>
    </div>
  );
}

/* ===========================================================================
 * TAB 4 — NỘI DUNG HỢP ĐỒNG (R3 hierarchy + R5 tables + R9 glossary + R10 refs)
 * ========================================================================= */
function TabClauses({ clauses, glossary, signatureRefs, orphanRefs }) {
  const [expandedSet, setExpandedSet] = useState(() => new Set(clauses.map((c) => c.id)));

  const toggle = (id) => {
    setExpandedSet((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const totalClauses = clauses.reduce((sum, c) => sum + 1 + (c.children ? c.children.length : 0), 0);

  return (
    <div style={{ marginTop: t.space[5] }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: t.space[4] }}>
        <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted }}>
          {totalClauses} điều khoản · {clauses.length} cấp chính
        </div>
        <button style={{ border: `1px solid ${t.color.borderStrong}`, background: t.color.surface, color: t.color.ink, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.md, fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family }}>Tải hợp đồng gốc</button>
      </div>

      {/* R10: Orphan reference warning */}
      <OrphanRefPanel orphans={orphanRefs} />

      {/* R9: Glossary (collapsible) */}
      <GlossarySection definitions={glossary} />

      {/* R3: Clause hierarchy accordion */}
      <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
        {clauses.map((clause) => (
          <ClauseHierarchyItem
            key={clause.id}
            clause={clause}
            expanded={expandedSet.has(clause.id)}
            onToggle={() => toggle(clause.id)}
            glossary={glossary}
            onRefClick={(ref) => { /* scroll to target clause */ }}
            depth={0}
          />
        ))}
      </div>

      {/* R5: Signatures & stamps */}
      <SignatureStampSection refs={signatureRefs} />
    </div>
  );
}

/* ===========================================================================
 * FOOTER
 * ========================================================================= */
function Footer({ doc, selfParty }) {
  return (
    <div style={{ marginTop: t.space[8], padding: `${t.space[4]}px 0`, borderTop: `1px solid ${t.color.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: t.space[3] }}>
      <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>
        {!selfParty ? <span style={{ color: t.color.amber }}>Chưa xác nhận — chọn bên của bạn trước</span>
          : <span>Chưa xác nhận trích xuất cho tài liệu này</span>}
      </div>
      <div style={{ display: "flex", gap: t.space[3] }}>
        <button style={{ border: `1px solid ${t.color.borderStrong}`, background: t.color.surface, color: t.color.ink, padding: `${t.space[2]}px ${t.space[4]}px`, borderRadius: t.radius.md, fontSize: t.font.size.md, cursor: "pointer", fontFamily: t.font.family }}>Tải hợp đồng gốc</button>
        {selfParty && (
          <button style={{ background: t.color.primary, color: t.color.surface, border: "none", padding: `${t.space[2]}px ${t.space[5]}px`, borderRadius: t.radius.md, fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family }}>Xác nhận trích xuất</button>
        )}
      </div>
    </div>
  );
}

/* ===========================================================================
 * MAIN — Document Detail V3 (DEC-050)
 * ========================================================================= */
export default function DocumentDetailV3() {
  const [activeTab, setActiveTab] = useState("overview");
  const [selfParty, setSelfParty] = useState("p2");

  const doc = DOC;
  const typeLabel = docTypeLabel(doc.doc_type);
  const selfP = doc.parties.find((p) => p.id === selfParty);
  const counterP = doc.parties.find((p) => p.id !== selfParty);
  const derivedTitle = selfParty && counterP
    ? `Hợp đồng ${typeLabel} với ${counterP.name}`
    : `Hợp đồng ${typeLabel} với ${doc.primary_party}`;

  const TABS = [
    { key: "overview", label: "Tổng quan" },
    { key: "obligations", label: "Nghĩa vụ & Quyền lợi" },
    { key: "parties", label: "Bên ký kết", badge: doc.parties.length },
    { key: "clauses", label: "Nội dung hợp đồng" },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: t.color.surface, fontFamily: t.font.family, color: t.color.ink }}>
      <Sidebar />
      <main style={{ flex: 1, padding: t.space[8], minWidth: 0, maxWidth: 960 }}>
        <a href="#" style={{ fontSize: t.font.size.sm, color: t.color.primary, textDecoration: "none" }}>← Hồ sơ hợp đồng</a>

        {/* Header — derived H1 + lifecycle badge (R8) */}
        <div style={{ marginTop: t.space[3] }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: t.space[4], flexWrap: "wrap" }}>
            <div>
              <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>
                {derivedTitle}
              </h1>
              <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
                Ngày ký: {doc.signing_date}
              </div>
            </div>
            <div style={{ display: "flex", gap: t.space[2], alignItems: "center" }}>
              <LifecycleBadge status={doc.lifecycle_status} />
              <span style={{
                display: "inline-flex", alignItems: "center",
                background: doc.confirmed ? t.color.primarySoft : t.color.amberSoft,
                color: doc.confirmed ? t.color.primary : t.color.amber,
                padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill,
                fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold,
              }}>{doc.confirmed ? "Đã xác nhận" : "Cần xác nhận"}</span>
            </div>
          </div>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[2] }}>
            Tệp gốc: {doc.filename}
          </div>
        </div>

        <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} />

        {activeTab === "overview" && <TabOverview doc={doc} selfParty={selfParty} onSetSelfParty={setSelfParty} />}
        {activeTab === "obligations" && <TabObligations selfParty={selfParty} />}
        {activeTab === "parties" && <TabParties parties={doc.parties} selfParty={selfParty} />}
        {activeTab === "clauses" && (
          <TabClauses
            clauses={CLAUSES_HIERARCHY}
            glossary={GLOSSARY}
            signatureRefs={SIGNATURE_REFS}
            orphanRefs={ORPHAN_REFS}
          />
        )}

        <Footer doc={doc} selfParty={selfParty} />

        {/* Designer annotations */}
        <div style={{ marginTop: t.space[6], padding: t.space[4], background: t.color.graySoft, borderRadius: t.radius.md, fontSize: t.font.size.xs, color: t.color.inkMuted, lineHeight: 1.7 }}>
          <div style={{ fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[1] }}>📐 Ghi chú thiết kế — DEC-050 surfaces (không render production)</div>

          <div><strong>R2 (#364) — Bên ký kết tab:</strong> self-party card highlighted (primary border + soft bg) with "Bên của bạn" badge + role label + <strong>alias chips</strong> ("gọi chung là ALPHATECH / Bên A" — feeds obligation direction resolution). Counterparties = full section each (name, representative+title, address, MST, contact, aliases). All fields editable → Event (D-07). When self-party unset → warning + all parties shown equal. Tab shows (2) badge = party count.</div>

          <div><strong>R3 (#365) — Clause hierarchy:</strong> nested accordion indent 24px/level. Parent nodes show child count badge. "└" connector at child level. Child expansion cascades with parent. Header summary shows "N điều khoản · M cấp chính". Font: parent=semibold base, child=medium md.</div>

          <div><strong>R5 (#368) — Table/diagram/signature:</strong> Tables rendered as HTML &lt;table&gt; in clause body (gray header, bordered cells). Image/diagram refs = dashed-border card with 🖼 icon + description + page + "Xem ảnh gốc" CTA (D-01: no AI extraction of image content). Signatures/stamps = dedicated section at bottom — type icon (✍️/🔴) + description + page + "Xem trang" link. Note "Khế nhận diện vị trí — không OCR nội dung."</div>

          <div><strong>R8 (#371) — Lifecycle status:</strong> 5 states with dot+label badge: đang hiệu lực (green), sắp hết hạn (amber), hết hạn (red), đã thanh lý (gray), tạm dừng (gray). Auto-derived from contract dates, manual override via ⋮ menu → Event. Shown in (a) page header next to confirm badge, (b) Tổng quan tab contract-term row. Showcase renders all 5 variants.</div>

          <div><strong>R9 (#372) — Glossary:</strong> collapsible "Định nghĩa (N)" section in Tab 4 before clauses. Each row = term (primary color) + definition + source clause + edit btn (D-07). In clause content: defined terms rendered as dashed-underline primary-colored spans with title tooltip showing definition. Pattern: {"{{term}}"} in content → rendered inline.</div>

          <div><strong>R10 (#373) — Cross-references:</strong> In clause content: {"[[ref]]"} → blue underline clickable link (jumps to target clause/appendix). Orphan refs (target not found): red wavy underline + ⚠ icon. OrphanRefPanel at top of Tab 4: "N tham chiếu không tìm thấy" warning with details (which ref, found where). Helps completeness — obligations often scattered via cross-refs.</div>

          <div><strong>Self-party reactive H1 (F3 fix):</strong> derivedTitle now uses counterparty name (excludes self) when self-party is set. If user selects ALPHATECH → H1 shows "Hợp đồng Công nghệ & IP với Cty TNHH Thương Mại Minh Phát". Default selfParty="p2" (Minh Phát) to showcase both states.</div>

          <div><strong>F2 fix (sidebar badge):</strong> Sidebar Tổng quan now has badge [3] (consistent with list mockup #278).</div>

          <div><strong>Tab order rationale:</strong> Tổng quan → Nghĩa vụ (CORE, DEC-043) → Bên ký kết (reference context) → Nội dung (source material). Parties after obligations because obligations = product, parties = supporting context.</div>

          <div><strong>Dependencies:</strong> R3 needs #282 (party separation) + backend hierarchy post-process. R5 table needs DocAI table structure output. R8 needs new schema fields (contract_term, lifecycle_status). R9 needs definitions table + AI extraction. R10 needs R3 clause_path for intra-doc resolution + R4 for appendix refs.</div>
        </div>

        {/* R8 lifecycle showcase (designer reference) */}
        <div style={{ marginTop: t.space[4], padding: t.space[4], background: t.color.graySoft, borderRadius: t.radius.md }}>
          <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[1] }}>R8 — Lifecycle badge variants (all 5 states)</div>
          <LifecycleShowcase />
        </div>
      </main>
    </div>
  );
}
