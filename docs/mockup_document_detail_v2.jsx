/**
 * Khế — Admin · Chi tiết hợp đồng  (mockup_document_detail_v2.jsx)
 * KHE_Designer · issue #281 · DEC-043 + QC doc-detail report
 * STATIC PROTOTYPE — scope-lock docs/mockup_*.jsx. Not production code.
 * ----------------------------------------------------------------------------
 * FULL REVAMP of /admin/documents/:id — inverted IA per DEC-043.
 * Old order: Terms → obligations (wrong — extraction positioning).
 * New order: derived title → self-party gate → Nghĩa vụ & Quyền lợi → completeness → Terms (demoted).
 *
 * 3-TAB STRUCTURE (Kevin comment 2026-06-26):
 *   Tab 1: Tổng quan — snapshot, self-party gate, completeness, term-fields
 *   Tab 2: Nghĩa vụ & Quyền lợi — the CORE output (DEC-043)
 *   Tab 3: Nội dung hợp đồng — clauses accordion (from extracted clauses[])
 *
 * DESIGN DIRECTION (same as #278): B&W minimalist, color rationed to CTA/status/badges.
 *
 * STATES EXERCISED:
 *   - Self-party: unset vs set (blocking gate)
 *   - Direction: NV / QL / NULL per obligation
 *   - Due date: date-anchored (resolved) vs event-anchored ("Chờ mốc")
 *   - Standing commitments (NDA/non-compete, due_date=NULL)
 *   - DEC-020 review row (vô thời hạn)
 *   - Completeness banner (green / amber / unchecked)
 *   - Footer split (no "đã xác nhận" pre-self-party)
 *   - Clauses tab: populated vs empty (D-08)
 *
 * PM DECISIONS:
 *   - Reject DRL-09: NO DEC-040 "X/N nghĩa vụ" counter on detail page
 *   - Keep DEC-020 review row, type="Review", excluded from duty tally
 *   - FR-EX-05: ⚠ badge only, NO raw confidence % shown
 *   - D-02 footer: split confirm vs self-party; no "đã xác nhận" while self-party unset
 *   - D-13: honest NULL "?" for direction — never hidden
 *   - Snake_case NEVER renders (DEC-029)
 */
import React, { useState } from "react";

/* ===========================================================================
 * TOKENS — B&W minimalist (shared spec with #278 / DS v0.2 direction)
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
  },
  font: {
    family: "'Inter', 'Be Vietnam Pro', system-ui, -apple-system, sans-serif",
    size: { xs: 12, sm: 13, md: 14, base: 15, lg: 18, xl: 22, "2xl": 26 },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
  },
  space: { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48 },
  radius: { sm: 6, md: 8, lg: 12, pill: 999 },
};

const BETA_CHAT = true;
const TODAY = new Date("2026-06-26");

/* ===========================================================================
 * DEC-029 — doc_type → Vietnamese label map (shared with #278 mockup)
 * ========================================================================= */
const DOC_TYPE_LABELS = {
  hd_nha_cung_cap: "Nhà cung cấp", hd_thue_mat_bang: "Thuê mặt bằng",
  hd_lao_dong: "Lao động", hd_dan_su: "Dân sự", hd_bat_dong_san: "Bất động sản",
  hd_van_tai_logistics: "Vận tải & Logistics", hd_xay_dung: "Xây dựng",
  hd_cong_nghe_ip: "Công nghệ & IP", hd_tai_chinh: "Tài chính", hd_hanh_chinh: "Hành chính",
};
const docTypeLabel = (dt) => DOC_TYPE_LABELS[dt] || "Chưa phân loại";

/* ===========================================================================
 * SAMPLE DATA — Công nghệ & IP contract with ALPHATECH
 * Exercises: multi-direction obligations, event-anchored dates, standing
 * commitments (NDA/IP), review row, completeness=amber.
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
  self_party: null, // unset → blocking gate
  parties: [
    { id: "p1", name: "Cty Phần Mềm ALPHATECH", role: "Bên A (cung cấp)" },
    { id: "p2", name: "Cty TNHH Thương Mại Minh Phát", role: "Bên B (sử dụng)" },
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
  { key: "dieu_khoan_gia_han", label: "Điều khoản gia hạn", value: "Tự động gia hạn 12 tháng nếu không có thông báo trước 60 ngày", needsReview: true },
  { key: "phat_vi_pham", label: "Phạt vi phạm", value: null, needsReview: true, notFound: true },
  { key: "bao_mat", label: "Điều khoản bảo mật", value: "Bảo mật 3 năm kể từ khi hết hạn HĐ", needsReview: false },
  { key: "so_huu_tri_tue", label: "Sở hữu trí tuệ", value: "Bên A giữ toàn bộ quyền SHTT; Bên B được cấp quyền sử dụng không độc quyền", needsReview: false },
];

const OBLIGATIONS_SELF_PARTY_SET = [
  { id: 1, title: "Thanh toán phí license tháng 7/2026", direction: "nv", type: "payment",
    due_type: "date", due_date: "2026-07-05", payer: "Cty TNHH Thương Mại Minh Phát", payee: "ALPHATECH",
    amount: "18.000.000 đ", status: "upcoming", standing: false },
  { id: 2, title: "Thanh toán phí license tháng 8/2026", direction: "nv", type: "payment",
    due_type: "date", due_date: "2026-08-05", payer: "Cty TNHH Thương Mại Minh Phát", payee: "ALPHATECH",
    amount: "18.000.000 đ", status: "upcoming", standing: false },
  { id: 3, title: "Bàn giao tài liệu hướng dẫn sử dụng", direction: "ql", type: "delivery",
    due_type: "event", due_event: "sau khi ký hợp đồng 15 ngày", due_date: null,
    status: "waiting_event", standing: false },
  { id: 4, title: "Cập nhật phần mềm phiên bản mới", direction: "ql", type: "delivery",
    due_type: "event", due_event: "khi có phiên bản mới", due_date: null,
    status: "waiting_event", standing: false },
  { id: 5, title: "Hỗ trợ kỹ thuật trong giờ hành chính", direction: "ql", type: "service",
    due_type: "date", due_date: null, status: "standing", standing: true },
  { id: 6, title: "Không tiết lộ thông tin kỹ thuật và thương mại", direction: "nv", type: "confidentiality",
    due_type: "date", due_date: null, status: "standing", standing: true },
  { id: 7, title: "Không sử dụng phần mềm ngoài phạm vi HĐ", direction: "nv", type: "ip",
    due_type: "date", due_date: null, status: "standing", standing: true },
  { id: 8, title: "Thông báo gia hạn / chấm dứt HĐ", direction: "nv", type: "notice",
    due_type: "date", due_date: "2026-01-31", status: "overdue", standing: false },
];

const OBLIGATIONS_SELF_PARTY_UNSET = OBLIGATIONS_SELF_PARTY_SET.map((o) => ({
  ...o, direction: null,
}));

const REVIEW_ITEM = {
  id: 99, title: "Review hợp đồng vô thời hạn",
  type: "review", due_date: null, standing: false, direction: null, status: "review",
};

const CLAUSES = [
  { num: "Điều 1", title: "Phạm vi cung cấp", page: 1,
    content: "Bên A cấp cho Bên B quyền sử dụng không độc quyền Phần mềm Quản lý Kho ALPHATECH v3.2, bao gồm các module: Quản lý tồn kho, Xuất nhập kho, Báo cáo thống kê. Quyền sử dụng giới hạn trong phạm vi hoạt động kinh doanh của Bên B tại Việt Nam.",
    editedBy: null },
  { num: "Điều 2", title: "Thời hạn và hiệu lực", page: 1,
    content: "Hợp đồng có hiệu lực từ ngày 01/04/2026 đến ngày 31/03/2028. Tự động gia hạn thêm 12 tháng nếu không bên nào thông báo chấm dứt trước 60 ngày.",
    editedBy: null },
  { num: "Điều 3", title: "Phí sử dụng và thanh toán", page: 2,
    content: "Phí sử dụng: 18.000.000 đồng/tháng (đã bao gồm VAT). Thanh toán trước ngày 05 hàng tháng bằng chuyển khoản ngân hàng. Chậm thanh toán quá 15 ngày, Bên A có quyền tạm ngừng cung cấp dịch vụ.",
    editedBy: null },
  { num: "Điều 4", title: "Nghĩa vụ của Bên A", page: 2,
    content: "Bên A có trách nhiệm: (a) Bàn giao tài liệu hướng dẫn sử dụng trong vòng 15 ngày kể từ ngày ký; (b) Cập nhật phiên bản phần mềm mới khi có; (c) Hỗ trợ kỹ thuật trong giờ hành chính (8:00–17:00, T2–T6); (d) Đảm bảo uptime tối thiểu 99.5%.",
    editedBy: null },
  { num: "Điều 5", title: "Nghĩa vụ của Bên B", page: 3,
    content: "Bên B có trách nhiệm: (a) Thanh toán phí đúng hạn; (b) Không sao chép, phân phối, hoặc cho bên thứ ba sử dụng phần mềm; (c) Thông báo kịp thời các lỗi phát sinh; (d) Không can thiệp vào mã nguồn phần mềm.",
    editedBy: null },
  { num: "Điều 6", title: "Bảo mật thông tin", page: 3,
    content: "Hai bên cam kết bảo mật toàn bộ thông tin kỹ thuật và thương mại liên quan đến hợp đồng này trong suốt thời gian thực hiện và 3 năm sau khi chấm dứt hợp đồng.",
    editedBy: null },
  { num: "Điều 7", title: "Sở hữu trí tuệ", page: 4,
    content: "Bên A là chủ sở hữu toàn bộ quyền sở hữu trí tuệ đối với phần mềm. Bên B được cấp quyền sử dụng không độc quyền, không được chuyển nhượng. Mọi dữ liệu do Bên B nhập vào phần mềm thuộc quyền sở hữu của Bên B.",
    editedBy: { user: "Admin", at: "26/06/2026 10:15" },
    originalContent: "Bên A là chủ sở hữu toàn bộ quyền sở hữu trí tuệ đối với phần mềm. Bên B được cấp giấy phép sử dụng." },
  { num: "Điều 8", title: "Chấm dứt hợp đồng", page: 4,
    content: "Hợp đồng chấm dứt khi: (a) Hết thời hạn và không gia hạn; (b) Hai bên thoả thuận chấm dứt; (c) Một bên vi phạm nghiêm trọng nghĩa vụ sau khi được thông báo 30 ngày mà không khắc phục.",
    editedBy: null },
];

/* ===========================================================================
 * DIFF SAMPLE DATA — DEC-048 §G2 (re-read diff-confirm)
 * 2 obligations changed after clause re-read. Exercises date + text diffs.
 * ========================================================================= */
const DIFF_SAMPLE = [
  {
    id: 1, title: "Thanh toán phí license tháng 7/2026",
    field: "due_date", label: "Hạn thanh toán",
    oldValue: "05/07/2026",
    newValue: "10/07/2026",
    source: "ai",
  },
  {
    id: 8, title: "Thông báo gia hạn / chấm dứt HĐ",
    field: "notice_period", label: "Thời hạn thông báo",
    oldValue: "Trước 60 ngày",
    newValue: "Trước 45 ngày",
    source: "ai",
  },
  {
    id: 6, title: "Không tiết lộ thông tin kỹ thuật và thương mại",
    field: "scope", label: "Phạm vi bảo mật",
    oldValue: "Thông tin kỹ thuật và thương mại",
    newValue: "Thông tin kỹ thuật, thương mại và dữ liệu khách hàng",
    source: "manual",
  },
];

/* ===========================================================================
 * SIDEBAR — shared with #278 list-view mockup
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
      <NavItem glyph="○" label="Tổng quan" />
      <NavItem glyph="◇" label="Nghĩa vụ & Quyền lợi" />
      <div style={grp}>Tài liệu</div>
      <NavItem glyph="■" label="Hồ sơ hợp đồng" active />
      <NavItem glyph="↑" label="Tải lên" />
      <div style={grp}>Trợ lý</div>
      <NavItem glyph="✦" label="Hỏi-đáp" beta={BETA_CHAT} />
    </aside>
  );
}

/* ===========================================================================
 * TAB BAR
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
        }}>{tab.label}</button>
      ))}
    </div>
  );
}

/* ===========================================================================
 * SELF-PARTY GATE — promoted, blocking (position 2 in IA)
 * ========================================================================= */
function SelfPartyGate({ parties, selfParty, onSet }) {
  if (selfParty) {
    const p = parties.find((x) => x.id === selfParty);
    return (
      <div style={{ padding: t.space[4], background: t.color.primarySoft, borderRadius: t.radius.md, marginTop: t.space[5], display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.primary, fontWeight: t.font.weight.semibold }}>Bên của bạn</div>
          <div style={{ fontSize: t.font.size.base, color: t.color.ink, fontWeight: t.font.weight.medium, marginTop: 2 }}>{p ? p.name : "—"} <span style={{ color: t.color.inkMuted, fontWeight: t.font.weight.regular }}>({p ? p.role : ""})</span></div>
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
            <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>{p.role}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ===========================================================================
 * COMPLETENESS BANNER — DEC-045 / #276 (3-state)
 * ========================================================================= */
function CompletenessBanner({ value }) {
  if (value === false)
    return (
      <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md, background: t.color.greenSoft, border: `1px solid ${t.color.green}33`, marginTop: t.space[4], display: "flex", alignItems: "center", gap: t.space[2] }}>
        <span style={{ color: t.color.green, fontWeight: t.font.weight.bold }}>✓</span>
        <span style={{ fontSize: t.font.size.md, color: t.color.ink }}>Đã rà soát đủ</span>
      </div>
    );
  if (value === true)
    return (
      <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md, background: t.color.amberSoft, border: `1px solid ${t.color.amber}33`, marginTop: t.space[4], display: "flex", alignItems: "center", gap: t.space[2] }}>
        <span style={{ color: t.color.amber, fontWeight: t.font.weight.bold }}>⚠</span>
        <span style={{ fontSize: t.font.size.md, color: t.color.ink }}>Có thể còn nghĩa vụ chưa bóc — kiểm tra bản gốc</span>
      </div>
    );
  return (
    <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md, background: t.color.graySoft, border: `1px solid ${t.color.border}`, marginTop: t.space[4], display: "flex", alignItems: "center", gap: t.space[2] }}>
      <span style={{ color: t.color.gray, fontWeight: t.font.weight.bold }}>?</span>
      <span style={{ fontSize: t.font.size.md, color: t.color.inkMuted }}>Chưa kiểm tra</span>
    </div>
  );
}

/* ===========================================================================
 * DIRECTION BADGE — per obligation row (NV / QL / NULL)
 * ========================================================================= */
function DirectionBadge({ direction }) {
  if (direction === "nv")
    return <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.ink, background: t.color.graySoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>↑ Phải làm</span>;
  if (direction === "ql")
    return <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, background: t.color.primarySoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>↓ Được hưởng</span>;
  return <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.amber, background: t.color.amberSoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>? Chưa rõ — chọn bên</span>;
}

/* ===========================================================================
 * DUE CELL — date-resolved vs event-anchored vs standing
 * ========================================================================= */
function ObligationDue({ ob }) {
  if (ob.standing)
    return <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontStyle: "italic" }}>Cam kết đang hiệu lực</span>;
  if (ob.due_type === "event" && !ob.due_date)
    return (
      <span style={{ fontSize: t.font.size.sm }}>
        <span style={{ color: t.color.inkMuted }}>Chờ mốc: </span>
        <span style={{ color: t.color.ink }}>{ob.due_event}</span>
      </span>
    );
  if (ob.due_date) {
    const d = new Date(ob.due_date);
    const diff = Math.round((d - TODAY) / 86400000);
    const fmt = `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
    if (diff < 0)
      return <span style={{ fontSize: t.font.size.sm, color: t.color.red, fontWeight: t.font.weight.semibold }}>{fmt} · quá hạn {-diff} ngày</span>;
    if (diff <= 7)
      return <span style={{ fontSize: t.font.size.sm, color: t.color.amber }}>{fmt} · còn {diff} ngày</span>;
    return <span style={{ fontSize: t.font.size.sm, color: t.color.ink }}>{fmt}</span>;
  }
  return <span style={{ color: t.color.inkSubtle }}>—</span>;
}

/* ===========================================================================
 * OBLIGATION ROW — with direction badge, CTA, payment info
 * ========================================================================= */
function ObligationRow({ ob, selfPartySet }) {
  const isOverdue = ob.status === "overdue";
  const isReview = ob.type === "review";
  return (
    <div style={{
      padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: `1px solid ${t.color.border}`,
      background: isOverdue ? t.color.redSoft + "44" : t.color.surface,
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: t.space[3] }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
            <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.medium, color: t.color.ink }}>{ob.title}</span>
            <DirectionBadge direction={selfPartySet ? ob.direction : null} />
            {isReview && <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.gray, background: t.color.graySoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>Review</span>}
          </div>
          {ob.type === "payment" && selfPartySet && ob.direction === "nv" && (
            <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>
              Trả cho {ob.payee} · {ob.amount}
            </div>
          )}
          {ob.type === "payment" && selfPartySet && ob.direction === "ql" && (
            <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>
              Nhận từ {ob.payer} · {ob.amount}
            </div>
          )}
          <div style={{ marginTop: t.space[1] }}>
            <ObligationDue ob={ob} />
          </div>
        </div>
        <div style={{ flexShrink: 0 }}>
          {ob.type === "payment" && ob.status !== "overdue" && (
            <button style={{ border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.ink, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.md, fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family }}>Đánh dấu đã trả</button>
          )}
          {ob.due_type === "event" && ob.status === "waiting_event" && (
            <button style={{ border: `1px solid ${t.color.primary}`, background: t.color.primarySoft, color: t.color.primary, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.md, fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family, fontWeight: t.font.weight.medium }}>Đánh dấu đã bàn giao</button>
          )}
          {ob.status === "overdue" && (
            <button style={{ border: `1px solid ${t.color.red}`, background: t.color.redSoft, color: t.color.red, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.md, fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family, fontWeight: t.font.weight.medium }}>Xem điều khoản gốc</button>
          )}
          {isReview && (
            <button style={{ border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.inkMuted, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.md, fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family }}>Xem điều khoản gốc</button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ===========================================================================
 * TAB 1 — Tổng quan
 * ========================================================================= */
function TabOverview({ doc, selfParty, onSetSelfParty }) {
  const obligations = selfParty ? OBLIGATIONS_SELF_PARTY_SET : OBLIGATIONS_SELF_PARTY_UNSET;
  const nvCount = selfParty ? obligations.filter((o) => o.direction === "nv" && !o.standing).length : 0;
  const qlCount = selfParty ? obligations.filter((o) => o.direction === "ql" && !o.standing).length : 0;
  const standingCount = obligations.filter((o) => o.standing).length;

  return (
    <div style={{ marginTop: t.space[5] }}>
      {/* Summary chips — status-led, NOT extraction-volume */}
      <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
        {selfParty ? (
          <>
            <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.border}`, color: t.color.ink }}>{nvCount} nghĩa vụ</span>
            <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.border}`, color: t.color.ink }}>{qlCount} quyền lợi</span>
          </>
        ) : (
          <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.amber}`, color: t.color.amber }}>{obligations.length} mục cần theo dõi</span>
        )}
        {standingCount > 0 && (
          <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.border}`, color: t.color.inkMuted }}>{standingCount} cam kết hiệu lực</span>
        )}
        {doc.may_have_unextracted && (
          <span style={{ fontSize: t.font.size.sm, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, border: `1px solid ${t.color.amber}`, color: t.color.amber }}>⚠ cần kiểm tra</span>
        )}
      </div>

      {/* Self-party gate */}
      <SelfPartyGate parties={doc.parties} selfParty={selfParty} onSet={onSetSelfParty} />

      {/* Completeness banner */}
      <CompletenessBanner value={doc.may_have_unextracted} />

      {/* Date labels — every date labeled, no bare unlabeled date */}
      <div style={{ display: "flex", gap: t.space[6], marginTop: t.space[5], flexWrap: "wrap" }}>
        <div><div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3 }}>Tải lên</div><div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{doc.upload_date}</div></div>
        <div><div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3 }}>Đã bóc tách</div><div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{doc.extracted_date}</div></div>
        <div><div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3 }}>Ngày ký</div><div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{doc.signing_date}</div></div>
      </div>

      {/* Term fields — editable, ⚠ badge only (no raw %) */}
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
                  <span style={{ color: t.color.amber, fontStyle: "italic" }}>
                    {f.needsReview ? "Có thể bị bỏ sót" : "Không tìm thấy trong HĐ"}
                  </span>
                ) : (
                  <>
                    {f.value}
                    {f.derived && <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginLeft: t.space[2] }}>(suy ra)</span>}
                  </>
                )}
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: t.space[2], flexShrink: 0 }}>
                {f.needsReview && <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.amber, background: t.color.amberSoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>⚠ Cần kiểm tra</span>}
                <button style={{ border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.inkMuted, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.sm, fontSize: t.font.size.xs, cursor: "pointer", fontFamily: t.font.family }}>✎ Sửa</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ===========================================================================
 * TAB 2 — Nghĩa vụ & Quyền lợi (THE CORE)
 * ========================================================================= */
function TabObligations({ selfParty, editedNotReread }) {
  const obligations = selfParty ? OBLIGATIONS_SELF_PARTY_SET : OBLIGATIONS_SELF_PARTY_UNSET;
  const dated = obligations.filter((o) => !o.standing && o.type !== "review");
  const standing = obligations.filter((o) => o.standing);

  return (
    <div style={{ marginTop: t.space[5] }}>
      {/* Stale-edit banner — DEC-048 §G3 */}
      <StaleEditBanner editedCount={editedNotReread} />

      {/* Unresolved direction warning when self-party unset */}
      {!selfParty && (
        <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md, background: t.color.amberSoft + "66", border: `1px solid ${t.color.amber}44`, marginBottom: t.space[4], display: "flex", alignItems: "center", gap: t.space[2] }}>
          <span style={{ color: t.color.amber, fontWeight: t.font.weight.bold }}>?</span>
          <span style={{ fontSize: t.font.size.md, color: t.color.ink }}>Chưa xác định chiều — chọn bên của bạn ở tab Tổng quan để phân loại nghĩa vụ và quyền lợi</span>
        </div>
      )}

      {/* Legend */}
      <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginBottom: t.space[3] }}>
        <strong style={{ color: t.color.ink }}>↑ Phải làm</strong> = nghĩa vụ (mình phải thực hiện) ·
        {" "}<strong style={{ color: t.color.ink }}>↓ Được hưởng</strong> = quyền lợi (mình được nhận) ·
        {" "}<strong style={{ color: t.color.ink }}>?</strong> = chưa xác định chiều
      </div>

      {/* Date-anchored + event-anchored obligations */}
      <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
        {dated.map((ob) => (
          <ObligationRow key={ob.id} ob={ob} selfPartySet={!!selfParty} />
        ))}
      </div>

      {/* Standing commitments — #274 */}
      {standing.length > 0 && (
        <div style={{ marginTop: t.space[6] }}>
          <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3, marginBottom: t.space[3] }}>Cam kết đang hiệu lực</div>
          <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
            {standing.map((ob) => (
              <ObligationRow key={ob.id} ob={ob} selfPartySet={!!selfParty} />
            ))}
          </div>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[2] }}>
            Cam kết không có ngày hết hạn cụ thể — bảo mật, IP, không cạnh tranh. Luôn hiệu lực trong suốt thời gian HĐ.
          </div>
        </div>
      )}

      {/* DEC-020 review row — excluded from duty tally */}
      <div style={{ marginTop: t.space[6] }}>
        <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: 0.3, marginBottom: t.space[3] }}>Review</div>
        <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
          <ObligationRow ob={REVIEW_ITEM} selfPartySet={!!selfParty} />
        </div>
        <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[2] }}>
          Mục review không tính vào số nghĩa vụ — nhắc nhở định kỳ rà soát HĐ vô thời hạn (DEC-020).
        </div>
      </div>
    </div>
  );
}

/* ===========================================================================
 * TAB 3 — Nội dung hợp đồng (clauses accordion + inline edit)
 * Kevin comment 2026-06-26 + Kevin feedback: inline edit per clause with
 * snapshot + attribution (D-07: edit → ghi Event, who edited: system/user).
 * NO "Báo nội dung thiếu/sai" passive button — user edits directly.
 * ========================================================================= */
function ClauseItem({ c, i, expanded, onToggle }) {
  const [editing, setEditing] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);
  const [draft, setDraft] = useState(c.content);
  const hasBeenEdited = !!c.editedBy;

  return (
    <div style={{ borderBottom: `1px solid ${t.color.border}` }}>
      {/* Accordion header */}
      <button onClick={onToggle} style={{
        display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%",
        padding: `${t.space[3]}px ${t.space[4]}px`, border: "none", background: t.color.surface,
        cursor: "pointer", fontFamily: t.font.family, textAlign: "left",
      }}>
        <span style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
          <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
            {c.num} — {c.title}
          </span>
          {hasBeenEdited && (
            <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, color: t.color.primary, background: t.color.primarySoft, padding: `0 ${t.space[2]}px`, borderRadius: t.radius.pill }}>đã sửa</span>
          )}
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: t.space[3] }}>
          {c.page && <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>Tr. {c.page}</span>}
          <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>{expanded ? "▴" : "▾"}</span>
        </span>
      </button>

      {/* Expanded body: view / edit mode */}
      {expanded && (
        <div style={{ padding: `0 ${t.space[4]}px ${t.space[4]}px` }}>
          {/* Attribution line — who last touched this */}
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginBottom: t.space[2], display: "flex", alignItems: "center", gap: t.space[2] }}>
            {hasBeenEdited ? (
              <>
                <span>Sửa bởi <strong style={{ color: t.color.ink }}>{c.editedBy.user}</strong> lúc {c.editedBy.at}</span>
                <span style={{ color: t.color.border }}>·</span>
                <button onClick={() => setShowOriginal(!showOriginal)} style={{ border: "none", background: "none", color: t.color.primary, cursor: "pointer", fontSize: t.font.size.xs, fontFamily: t.font.family, padding: 0, textDecoration: "underline" }}>
                  {showOriginal ? "Ẩn bản gốc" : "Xem bản gốc (AI)"}
                </button>
              </>
            ) : (
              <span>Nội dung gốc (AI bóc tách)</span>
            )}
          </div>

          {/* Original content diff (collapsed by default) */}
          {showOriginal && c.originalContent && (
            <div style={{
              padding: `${t.space[2]}px ${t.space[3]}px`, marginBottom: t.space[3],
              background: t.color.graySoft, borderRadius: t.radius.sm, borderLeft: `3px solid ${t.color.border}`,
              fontSize: t.font.size.sm, color: t.color.inkMuted, lineHeight: 1.6,
            }}>
              <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.inkSubtle, marginBottom: t.space[1] }}>Bản gốc (AI bóc tách):</div>
              {c.originalContent}
            </div>
          )}

          {/* Content: view or edit */}
          {editing ? (
            <div>
              <textarea
                value={draft} onChange={(e) => setDraft(e.target.value)}
                style={{
                  width: "100%", minHeight: 120, padding: t.space[3], fontSize: t.font.size.md,
                  fontFamily: t.font.family, color: t.color.ink, lineHeight: 1.7,
                  border: `1px solid ${t.color.primary}`, borderRadius: t.radius.md,
                  outline: "none", resize: "vertical", boxSizing: "border-box",
                }}
              />
              <div style={{ display: "flex", gap: t.space[2], marginTop: t.space[2], alignItems: "center" }}>
                <button onClick={() => setEditing(false)} style={{
                  background: t.color.primary, color: t.color.surface, border: "none",
                  padding: `${t.space[1]}px ${t.space[4]}px`, borderRadius: t.radius.md,
                  fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family,
                }}>Lưu</button>
                <button onClick={() => { setDraft(c.content); setEditing(false); }} style={{
                  border: `1px solid ${t.color.border}`, background: t.color.surface, color: t.color.ink,
                  padding: `${t.space[1]}px ${t.space[4]}px`, borderRadius: t.radius.md,
                  fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family,
                }}>Hủy</button>
                <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>
                  Thay đổi được ghi lại kèm tên người sửa (D-07)
                </span>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: t.font.size.md, color: t.color.ink, lineHeight: 1.7 }}>{c.content}</div>
              <button onClick={() => setEditing(true)} style={{
                marginTop: t.space[2], border: `1px solid ${t.color.border}`, background: t.color.surface,
                color: t.color.inkMuted, padding: `1px ${t.space[3]}px`, borderRadius: t.radius.sm,
                fontSize: t.font.size.xs, cursor: "pointer", fontFamily: t.font.family,
              }}>✎ Sửa nội dung</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ===========================================================================
 * RE-READ TRIGGER BANNER — DEC-048 §13-D2
 * Shown on Tab 3 after clause edit. "Đọc lại" disabled pre-P1 (#309).
 * (P1 merge required → source_clause_num to map clause→obligation).
 * ========================================================================= */
function ReReadBanner({ editedCount, onReRead, onDismiss, disabled, dismissed }) {
  if (editedCount === 0 || dismissed) return null;
  return (
    <div style={{
      padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md,
      background: t.color.primarySoft, border: `1px solid ${t.color.primary}33`,
      marginBottom: t.space[4], display: "flex", alignItems: "center",
      justifyContent: "space-between", gap: t.space[3], flexWrap: "wrap",
    }}>
      <span style={{ fontSize: t.font.size.md, color: t.color.ink }}>
        Bạn đã sửa <strong>{editedCount}</strong> điều khoản. Khế đọc lại nghĩa vụ?
      </span>
      <div style={{ display: "flex", gap: t.space[2] }}>
        <button
          onClick={disabled ? undefined : onReRead}
          title={disabled ? "Tính năng đọc lại chưa sẵn sàng — chờ P1 (#309) merge (cần source_clause_num để map clause→obligation)" : "Khế đọc lại nghĩa vụ từ điều khoản đã sửa"}
          style={{
            background: disabled ? t.color.graySoft : t.color.primary,
            color: disabled ? t.color.inkMuted : t.color.surface,
            border: disabled ? `1px solid ${t.color.border}` : "none",
            padding: `${t.space[1]}px ${t.space[4]}px`,
            borderRadius: t.radius.md, fontSize: t.font.size.sm,
            fontWeight: t.font.weight.semibold, cursor: disabled ? "not-allowed" : "pointer",
            fontFamily: t.font.family, opacity: disabled ? 0.6 : 1,
          }}
        >Đọc lại</button>
        <button onClick={onDismiss} style={{
          border: `1px solid ${t.color.border}`, background: t.color.surface,
          color: t.color.ink, padding: `${t.space[1]}px ${t.space[4]}px`,
          borderRadius: t.radius.md, fontSize: t.font.size.sm,
          cursor: "pointer", fontFamily: t.font.family,
        }}>Bỏ qua</button>
      </div>
    </div>
  );
}

/* ===========================================================================
 * STALE-EDIT BANNER — DEC-048 §G3, D-08
 * Shown on Tab 2 when clauses edited but not re-read.
 * ========================================================================= */
function StaleEditBanner({ editedCount }) {
  if (editedCount === 0) return null;
  return (
    <div style={{
      padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md,
      background: t.color.amberSoft, border: `1px solid ${t.color.amber}33`,
      marginBottom: t.space[4], display: "flex", alignItems: "center", gap: t.space[2],
    }}>
      <span style={{ color: t.color.amber, fontWeight: t.font.weight.bold }}>⚠️</span>
      <span style={{ fontSize: t.font.size.md, color: t.color.ink }}>
        {editedCount} điều khoản đã sửa chưa đọc lại — nghĩa vụ có thể chưa cập nhật.
      </span>
    </div>
  );
}

/* ===========================================================================
 * DIFF-CONFIRM MODAL — DEC-048 §G2, D-02
 * Per-obligation diff after re-read. Manual-precedence default: user's version
 * is pre-selected. Khế NEVER silently replaces (D-02).
 * ========================================================================= */
function DiffConfirmModal({ diffs, onClose, onApply }) {
  const [choices, setChoices] = useState(() =>
    diffs.reduce((acc, d) => ({ ...acc, [d.id]: "manual" }), {})
  );

  return (
    <div style={{
      position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
      background: "rgba(0,0,0,0.5)", zIndex: 200,
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: t.space[4],
    }}>
      <div style={{
        background: t.color.surface, borderRadius: t.radius.lg,
        maxWidth: 640, width: "100%", maxHeight: "80vh", overflow: "auto",
        padding: t.space[6], boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
      }}>
        <h2 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>
          Khế đề xuất thay đổi nghĩa vụ
        </h2>
        <p style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: 1.6 }}>
          Sau khi đọc lại điều khoản đã sửa, Khế phát hiện {diffs.length} nghĩa vụ có thể cần cập nhật.
          Chọn giữ bản của bạn hoặc dùng đề xuất của Khế cho từng mục.
        </p>

        <div style={{ marginTop: t.space[5] }}>
          {diffs.map((d) => (
            <div key={d.id} style={{
              padding: t.space[4], border: `1px solid ${t.color.border}`,
              borderRadius: t.radius.md, marginBottom: t.space[3],
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
                <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{d.title}</span>
                {d.source === "manual" && (
                  <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.ink, background: t.color.graySoft, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>🔒 Thủ công</span>
                )}
              </div>
              <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>{d.label}</div>

              <div style={{ display: "flex", gap: t.space[3], marginTop: t.space[3] }}>
                <button onClick={() => setChoices((p) => ({ ...p, [d.id]: "manual" }))} style={{
                  flex: 1, padding: t.space[3], borderRadius: t.radius.md, textAlign: "left",
                  border: choices[d.id] === "manual" ? `2px solid ${t.color.primary}` : `1px solid ${t.color.border}`,
                  background: choices[d.id] === "manual" ? t.color.primarySoft : t.color.surface,
                  cursor: "pointer", fontFamily: t.font.family,
                }}>
                  <div style={{ fontSize: t.font.size.xs, color: choices[d.id] === "manual" ? t.color.primary : t.color.inkMuted, fontWeight: t.font.weight.medium }}>
                    Giữ của bạn {choices[d.id] === "manual" ? "✓" : ""}
                  </div>
                  <div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{d.oldValue}</div>
                </button>

                <button onClick={() => setChoices((p) => ({ ...p, [d.id]: "ai" }))} style={{
                  flex: 1, padding: t.space[3], borderRadius: t.radius.md, textAlign: "left",
                  border: choices[d.id] === "ai" ? `2px solid ${t.color.primary}` : `1px solid ${t.color.border}`,
                  background: choices[d.id] === "ai" ? t.color.primarySoft : t.color.surface,
                  cursor: "pointer", fontFamily: t.font.family,
                }}>
                  <div style={{ fontSize: t.font.size.xs, color: choices[d.id] === "ai" ? t.color.primary : t.color.inkMuted, fontWeight: t.font.weight.medium }}>
                    Dùng đề xuất Khế {choices[d.id] === "ai" ? "✓" : ""}
                  </div>
                  <div style={{ fontSize: t.font.size.md, color: t.color.ink, marginTop: 2 }}>{d.newValue}</div>
                </button>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: t.space[3], marginTop: t.space[5] }}>
          <button onClick={onClose} style={{
            border: `1px solid ${t.color.border}`, background: t.color.surface,
            color: t.color.ink, padding: `${t.space[2]}px ${t.space[5]}px`,
            borderRadius: t.radius.md, fontSize: t.font.size.md,
            cursor: "pointer", fontFamily: t.font.family,
          }}>Hủy</button>
          <button onClick={() => onApply(choices)} style={{
            background: t.color.primary, color: t.color.surface, border: "none",
            padding: `${t.space[2]}px ${t.space[5]}px`, borderRadius: t.radius.md,
            fontSize: t.font.size.md, fontWeight: t.font.weight.semibold,
            cursor: "pointer", fontFamily: t.font.family,
          }}>Áp dụng thay đổi</button>
        </div>

        <div style={{ marginTop: t.space[3], fontSize: t.font.size.xs, color: t.color.inkSubtle }}>
          D-02: mọi thay đổi nghĩa vụ phải qua xác nhận người dùng. Khế không tự động thay thế.
        </div>
      </div>
    </div>
  );
}

function TabClauses({ clauses, mayHaveUnextracted, editedNotReread, onReRead, onDismissReRead, rereadDisabled, rereadPromptDismissed }) {
  const [expanded, setExpanded] = useState(() => {
    if (clauses.length <= 8) return new Set(clauses.map((_, i) => i));
    return new Set();
  });

  const toggle = (i) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  const pageNums = clauses.map((c) => c.page).filter(Boolean);
  const minPage = pageNums.length ? Math.min(...pageNums) : null;
  const maxPage = pageNums.length ? Math.max(...pageNums) : null;

  const editedCount = clauses.filter((c) => c.editedBy).length;

  if (clauses.length === 0) {
    return (
      <div style={{ marginTop: t.space[5] }}>
        <div style={{ padding: `${t.space[12]}px ${t.space[6]}px`, textAlign: "center", border: `1px dashed ${t.color.borderStrong}`, borderRadius: t.radius.lg }}>
          <div style={{ fontSize: 40, lineHeight: 1 }} aria-hidden>📄</div>
          <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.bold, color: t.color.ink, marginTop: t.space[4] }}>
            Khế chưa bóc được nội dung chi tiết cho tài liệu này
          </div>
          <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted, maxWidth: 460, margin: `${t.space[3]}px auto 0`, lineHeight: 1.6 }}>
            Vui lòng mở file gốc để tham chiếu.
          </div>
          <button style={{
            marginTop: t.space[5], background: t.color.primary, color: t.color.surface, border: "none",
            padding: `${t.space[2]}px ${t.space[5]}px`, borderRadius: t.radius.md,
            fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family,
          }}>Tải hợp đồng gốc</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ marginTop: t.space[5] }}>
      {/* Header summary */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: t.space[4] }}>
        <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted }}>
          {clauses.length} điều khoản{minPage != null && maxPage != null ? ` · trang ${minPage}–${maxPage}` : ""}
          {editedCount > 0 && <span style={{ color: t.color.primary, marginLeft: t.space[2] }}>· {editedCount} đã sửa</span>}
        </div>
        <button style={{ border: `1px solid ${t.color.borderStrong}`, background: t.color.surface, color: t.color.ink, padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.md, fontSize: t.font.size.sm, cursor: "pointer", fontFamily: t.font.family }}>Tải hợp đồng gốc</button>
      </div>

      {/* Re-read trigger banner — DEC-048 §13-D2 */}
      <ReReadBanner editedCount={editedNotReread} onReRead={onReRead} onDismiss={onDismissReRead} disabled={rereadDisabled} dismissed={rereadPromptDismissed} />

      {/* Clause accordion with inline edit */}
      <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
        {clauses.map((c, i) => (
          <ClauseItem key={i} c={c} i={i} expanded={expanded.has(i)} onToggle={() => toggle(i)} />
        ))}
      </div>

      {/* Completeness footer */}
      <div style={{ marginTop: t.space[4], fontSize: t.font.size.sm, color: t.color.inkMuted }}>
        Khế đọc được {clauses.length} điều khoản từ tài liệu này.
        {mayHaveUnextracted && (
          <span style={{ color: t.color.amber, marginLeft: t.space[2] }}>
            ⚠ Có thể còn nội dung Khế chưa bóc hết — đối chiếu file gốc nếu cần.
          </span>
        )}
      </div>

      {/* Edit audit note */}
      <div style={{ marginTop: t.space[3], fontSize: t.font.size.xs, color: t.color.inkSubtle }}>
        Mọi thay đổi nội dung điều khoản được snapshot và ghi lại người sửa (system / user). Bản gốc AI bóc tách luôn được lưu.
      </div>
    </div>
  );
}

/* ===========================================================================
 * FOOTER — D-02 split: confirm + self-party separate
 * ========================================================================= */
function Footer({ doc, selfParty }) {
  return (
    <div style={{ marginTop: t.space[8], padding: `${t.space[4]}px 0`, borderTop: `1px solid ${t.color.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: t.space[3] }}>
      <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>
        {doc.confirmed && selfParty ? (
          <span>Đã xác nhận trích xuất bởi <strong style={{ color: t.color.ink }}>Admin</strong> lúc 20/06/2026 14:35 · <button style={{ border: "none", background: "none", color: t.color.primary, cursor: "pointer", fontSize: t.font.size.sm, fontFamily: t.font.family, textDecoration: "underline", padding: 0 }}>Hoàn tác</button></span>
        ) : !selfParty ? (
          <span style={{ color: t.color.amber }}>Chưa xác nhận — chọn bên của bạn trước</span>
        ) : (
          <span>Chưa xác nhận trích xuất cho tài liệu này</span>
        )}
      </div>
      <div style={{ display: "flex", gap: t.space[3] }}>
        <button style={{ border: `1px solid ${t.color.borderStrong}`, background: t.color.surface, color: t.color.ink, padding: `${t.space[2]}px ${t.space[4]}px`, borderRadius: t.radius.md, fontSize: t.font.size.md, cursor: "pointer", fontFamily: t.font.family }}>Tải hợp đồng gốc</button>
        {selfParty && !doc.confirmed && (
          <button style={{ background: t.color.primary, color: t.color.surface, border: "none", padding: `${t.space[2]}px ${t.space[5]}px`, borderRadius: t.radius.md, fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family }}>Xác nhận trích xuất</button>
        )}
      </div>
    </div>
  );
}

/* ===========================================================================
 * MAIN — Document Detail V2
 * ========================================================================= */
export default function DocumentDetailV2() {
  const [activeTab, setActiveTab] = useState("overview");
  const [selfParty, setSelfParty] = useState(null);
  const [editedNotReread, setEditedNotReread] = useState(1);
  const [rereadPromptDismissed, setRereadPromptDismissed] = useState(false);
  const [showDiffModal, setShowDiffModal] = useState(false);

  const doc = DOC;
  const typeLabel = docTypeLabel(doc.doc_type);
  const derivedTitle = `Hợp đồng ${typeLabel} với ${doc.primary_party}`;

  const TABS = [
    { key: "overview", label: "Tổng quan" },
    { key: "obligations", label: "Nghĩa vụ & Quyền lợi" },
    { key: "clauses", label: "Nội dung hợp đồng" },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: t.color.surface, fontFamily: t.font.family, color: t.color.ink }}>
      <Sidebar />
      <main style={{ flex: 1, padding: t.space[8], minWidth: 0, maxWidth: 960 }}>
        {/* Breadcrumb */}
        <a href="#" style={{ fontSize: t.font.size.sm, color: t.color.primary, textDecoration: "none" }}>← Hồ sơ hợp đồng</a>

        {/* Header — derived H1 (shared primitive with #278), NOT raw filename */}
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
            {/* Status pill */}
            <span style={{
              display: "inline-flex", alignItems: "center",
              background: doc.confirmed ? t.color.primarySoft : t.color.amberSoft,
              color: doc.confirmed ? t.color.primary : t.color.amber,
              padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill,
              fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold,
            }}>{doc.confirmed ? "Đã xác nhận" : "Cần xác nhận"}</span>
          </div>
          {/* Filename — small "Tệp gốc" line (NOT in H1) */}
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle, marginTop: t.space[2] }}>
            Tệp gốc: {doc.filename}
          </div>
        </div>

        {/* Tab bar */}
        <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} />

        {/* Tab content */}
        {activeTab === "overview" && <TabOverview doc={doc} selfParty={selfParty} onSetSelfParty={setSelfParty} />}
        {activeTab === "obligations" && <TabObligations selfParty={selfParty} editedNotReread={editedNotReread} />}
        {activeTab === "clauses" && (
          <TabClauses
            clauses={CLAUSES}
            mayHaveUnextracted={doc.may_have_unextracted}
            editedNotReread={editedNotReread}
            onReRead={() => setShowDiffModal(true)}
            onDismissReRead={() => setRereadPromptDismissed(true)}
            rereadDisabled={true}
            rereadPromptDismissed={rereadPromptDismissed}
          />
        )}

        {/* Diff-confirm modal — DEC-048 §G2 (rendered above page when open) */}
        {showDiffModal && (
          <DiffConfirmModal
            diffs={DIFF_SAMPLE}
            onClose={() => setShowDiffModal(false)}
            onApply={(choices) => { setShowDiffModal(false); setEditedNotReread(0); setRereadPromptDismissed(false); }}
          />
        )}

        {/* Footer — D-02 split */}
        <Footer doc={doc} selfParty={selfParty} />

        {/* Designer annotations */}
        <div style={{ marginTop: t.space[6], padding: t.space[4], background: t.color.graySoft, borderRadius: t.radius.md, fontSize: t.font.size.xs, color: t.color.inkMuted, lineHeight: 1.7 }}>
          <div style={{ fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[1] }}>📐 Ghi chú thiết kế (không render trong production)</div>
          <div><strong>IA inverted (DEC-043):</strong> derived title → self-party gate (BLOCKING) → Nghĩa vụ & Quyền lợi → Terms (demoted). Obligation graph IS the product.</div>
          <div><strong>3 tabs (Kevin 2026-06-26):</strong> Tổng quan (snapshot + gate + terms) · Nghĩa vụ & Quyền lợi (CORE) · Nội dung hợp đồng (clauses accordion).</div>
          <div><strong>Self-party:</strong> until set → header says "N mục cần theo dõi" NOT "N nghĩa vụ" (D-13/DEC-030). Tab 2 shows "Chưa xác định chiều" warning. Footer blocks "Xác nhận".</div>
          <div><strong>Direction per-row:</strong> "↑ Phải làm" (NV) / "↓ Được hưởng" (QL) / "? Chưa rõ — chọn bên" (NULL). Payment rows add payer/payee after direction resolves.</div>
          <div><strong>Due dates 2-tier:</strong> date-anchored → calendar date + countdown · event-anchored → "Chờ mốc: [event]" + capture CTA. Standing → "Cam kết đang hiệu lực".</div>
          <div><strong>DEC-020:</strong> review row kept, type chip = "Review", excluded from duty tally. DRL-09 counter rejected (detail page gets checklist, not X/N counter).</div>
          <div><strong>FR-EX-05:</strong> ⚠ badge ONLY — raw confidence % hidden. DEC-045 completeness banner 3-state (green/amber/unchecked).</div>
          <div><strong>Footer (D-02):</strong> split confirm vs self-party. "Đã xác nhận" ONLY when self-party set + confirmed. No English. No snake_case anywhere.</div>
          <div><strong>Tab 3 (clauses):</strong> accordion; ≤8 = all expanded, &gt;8 = collapsed. Empty state honest (D-08). <strong>Inline edit per clause (D-07)</strong>: edit button on each clause body; save snapshots original + records who edited (system/user + timestamp) → Event. "đã sửa" badge on edited clause headers. "Xem bản gốc (AI)" toggle shows original extraction. Backend #283.</div>
          <div><strong>DEC-048 §13-D2 (re-read banner):</strong> after clause edit save → "Bạn đã sửa N điều khoản. Khế đọc lại nghĩa vụ?" [Đọc lại] [Bỏ qua]. "Đọc lại" disabled pre-P1 (#309) — tooltip cites P1 gate. "Bỏ qua" hides prompt ONLY; stale banner (Tab 2) persists until actual re-read (apply diff). Shown on Tab 3.</div>
          <div><strong>DEC-048 §G2 (diff-confirm modal):</strong> re-read returns obligation changes → per-item diff. Manual-precedence default: [Giữ của bạn ✓] pre-selected. NOT silent replace (D-02). 3 sample diffs: 2 AI-source (date + text) + 1 manual-source with "🔒 Thủ công" badge (§G2 manual-source protection).</div>
          <div><strong>DEC-048 §G3 (stale-edit banner):</strong> "⚠️ N điều khoản đã sửa chưa đọc lại — nghĩa vụ có thể chưa cập nhật." Shown on Tab 2 (obligations). Honest (D-08).</div>
          <div><strong>Out of scope:</strong> clause↔obligation cross-nav (no source_clause_num today) · AI summary/highlight (bias risk) · DEC-040 X/N counter (DRL-09 rejected).</div>
        </div>
      </main>
    </div>
  );
}
