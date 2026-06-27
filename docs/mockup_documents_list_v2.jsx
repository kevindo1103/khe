/**
 * Khế — Admin · Hồ sơ hợp đồng  (mockup_documents_list_v2.jsx)
 * KHE_Designer · issue #278 · DEC-043 repositioning
 * STATIC PROTOTYPE — scope-lock docs/mockup_*.jsx. Not production code.
 * ----------------------------------------------------------------------------
 * WHY v2 (full revamp of /admin/documents):
 *   QC report 2026-06-25 found 7 critical violations on uat-demo — the page was a
 *   file-warehouse ("Kho tài liệu") instead of the obligation & rights portfolio
 *   that DEC-043 says IS the product. This mockup is the primary surface that must
 *   prove the obligation graph.
 *
 * DESIGN DIRECTION (Kevin 2026-06-25 — Design System v0.2 / #197 B&W minimalist):
 *   - Black & white base. Body text = #1A1A1A. Backgrounds = white. Borders = #E5E7EB.
 *   - NO decorative color on regular text / row content. Links = black, hover-underline.
 *   - Color ONLY for: CTA, active filter chip, status badges, completeness icons.
 *     primary khế-emerald #0F7A56 · amber #D97706 (urgent) · red #DC2626 (overdue) · gray #6B7280 (muted).
 *   - Hierarchy via weight + size, NOT color.
 *   NOTE: Design System v0.2 (#197) is not yet merged into this branch, so v2 carries
 *   its own token block matching the #278 spec exactly. Fold into DS v0.2 when it lands.
 *
 * PM DECISIONS folded (issue #278 QC review G1–G10, comments 2026-06-26):
 *   G1  classifier mis-label (8/9 rows = hd_nha_cung_cap) is for:ai, OUT of design scope —
 *       mockup uses ground-truth-correct labels per DEC-029 map. Designer ≠ responsible for classifier.
 *   G2  default sort: action-required first → nearest deadline asc → confirmed+quiet last. (see SORT below)
 *   G3  standing-only row: obligation_count>0 AND next_due_date=NULL → "Cam kết đang hiệu lực", NOT em dash.
 *   G4  direction NULL shown honestly (D-13): "5↑ NV · 2↓ QL · 3?", all-NULL "3?", zero "—". Never hidden.
 *   G5  CTA always "Tải hợp đồng" (fixed primary). NO conditional "Xác nhận N" CTA — the counter
 *       chip "4/17 cần xác nhận" already carries the action-nudge. Less state, less surprise.
 *   G6  Status PILL carries all color. NO amber row border (would be a 2nd color channel vs B&W).
 *       Unconfirmed signal = "Cần xác nhận" pill winning Col 5 priority.
 *   G7  glyph ↑NV / ↓QL kept but NEVER glyph-only — always paired with "NV"/"QL" text + header legend.
 *   G8  snake_case lint (CI fail on /hd_[a-z_]+/ in rendered JSX) = AC for the FE-impl issue; here we
 *       prove the label map. Snake_case NEVER renders (table, filters, detail, chat citations).
 *   G10 "Hỏi-đáp [Beta]" chip is REMOVABLE post-#277 (chat reliability) — gated on BETA_CHAT flag, not hardcoded.
 *
 * Backend API delta (designed against TARGET state — mockup unblocked, FE blocks on #279):
 *   primary_party · next_due_date · nghia_vu_count · quyen_loi_count · direction_null_count ·
 *   may_have_unextracted_obligations. None exist in GET /documents/ today.
 *
 * D-rules: D-08 (honest "không tìm thấy" — empty file) · D-13 (honest NULL, never hide ?).
 */
import React, { useState } from "react";

/* ===========================================================================
 * TOKENS — B&W minimalist (#278 / DS v0.2 direction). Color is rationed.
 * ========================================================================= */
export const tokens = {
  color: {
    ink:        "#1A1A1A",  // body text — black
    inkMuted:   "#6B7280",  // secondary line, "Loại", muted counts
    inkSubtle:  "#9CA3AF",  // hints
    surface:    "#FFFFFF",  // page + card bg
    rowHover:   "#F9FAFB",  // whole-row hover
    border:     "#E5E7EB",  // dividers / borders
    borderStrong:"#D1D5DB",

    // Rationed accents — CTA / status / completeness ONLY
    primary:    "#0F7A56",  primarySoft: "#E7F3EE",  // khế-emerald
    amber:      "#D97706",  amberSoft:   "#FEF3E2",   // urgent / needs-confirm / completeness ⚠
    red:        "#DC2626",  redSoft:     "#FDECEC",   // overdue
    gray:       "#6B7280",  graySoft:    "#F3F4F6",   // muted / pipeline pills
  },
  font: {
    family: "'Inter', 'Be Vietnam Pro', system-ui, -apple-system, sans-serif",
    size: { xs: 12, sm: 13, md: 14, base: 15, lg: 18, xl: 22, "2xl": 26 },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
  },
  space: { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48 },
  radius: { sm: 6, md: 8, lg: 12, pill: 999 },
};
const t = tokens;

/* Feature flag — Beta chip on "Hỏi-đáp" is temporary, removed post-#277 (G10). */
const BETA_CHAT = true;

/* "today" for relative-deadline math — static mockup pins to QC report date. */
const TODAY = new Date("2026-06-26");

/* ===========================================================================
 * DEC-029 — doc_type → Vietnamese display label (all 10 enums + fallback).
 * Snake_case NEVER reaches a rendered surface; this map is the single gate.
 * ========================================================================= */
export const DOC_TYPE_LABELS = {
  hd_nha_cung_cap:      "Nhà cung cấp",
  hd_thue_mat_bang:     "Thuê mặt bằng",
  hd_lao_dong:          "Lao động",
  hd_dan_su:            "Dân sự",
  hd_bat_dong_san:      "Bất động sản",
  hd_van_tai_logistics: "Vận tải & Logistics",
  hd_xay_dung:          "Xây dựng",
  hd_cong_nghe_ip:      "Công nghệ & IP",
  hd_tai_chinh:         "Tài chính",
  hd_hanh_chinh:        "Hành chính",
};
const docTypeLabel = (dt) => DOC_TYPE_LABELS[dt] || "Chưa phân loại";

/* ===========================================================================
 * Sample portfolio — 17-contract concierge tenant. Shaped EXACTLY like the
 * target GET /documents/ payload (see Backend API delta). The visible subset
 * below is curated to exercise all 7 row states + 3 direction display cases.
 * ========================================================================= */
const DOCS = [
  // 1 · unconfirmed + near deadline → top of sort (action-required). Mixed direction (G4).
  { id: 1, doc_type: "hd_thue_mat_bang", primary_party: "Cty TNHH Hải Đăng",
    filename: "223692#FCV_thue_matbang_Q7_signed.pdf",
    nghia_vu_count: 5, quyen_loi_count: 2, direction_null_count: 3,
    obligation_count: 10, next_due_date: "2026-07-08",
    confirmed: false, pipeline: "extracted", may_have_unextracted: false, duplicate: false },

  // 2 · confirmed but OVERDUE obligation (red). All-classified direction.
  { id: 2, doc_type: "hd_nha_cung_cap", primary_party: "Cty CP Bao Bì Việt",
    filename: "hopdong_baobi_2026.pdf",
    nghia_vu_count: 4, quyen_loi_count: 0, direction_null_count: 0,
    obligation_count: 4, next_due_date: "2026-06-23",
    confirmed: true, pipeline: "extracted", may_have_unextracted: false, duplicate: false },

  // 3 · STANDING-ONLY (G3): has obligations, none with a date (NDA / non-compete).
  { id: 3, doc_type: "hd_lao_dong", primary_party: "Nguyễn Văn An",
    filename: "HDLD_NguyenVanAn_2026.pdf",
    nghia_vu_count: 2, quyen_loi_count: 1, direction_null_count: 0,
    obligation_count: 3, next_due_date: null,   // standing → "Cam kết đang hiệu lực"
    confirmed: true, pipeline: "extracted", may_have_unextracted: false, duplicate: false },

  // 4 · unconfirmed + completeness ⚠ (may_have_unextracted=True). Quyền-lợi heavy (cần thu).
  { id: 4, doc_type: "hd_xay_dung", primary_party: "Cty Xây Dựng Trường Sơn",
    filename: "thau_xaydung_kho_BinhTan.pdf",
    nghia_vu_count: 3, quyen_loi_count: 6, direction_null_count: 0,
    obligation_count: 9, next_due_date: "2026-07-15",
    confirmed: false, pipeline: "extracted", may_have_unextracted: true, duplicate: false },

  // 5 · legacy doc, completeness NULL "?" + direction ALL-NULL "3?" (G4 case 3).
  { id: 5, doc_type: "hd_dan_su", primary_party: "Ông Trần Văn B",
    filename: "phuluc_dansu_cu.pdf",
    nghia_vu_count: 0, quyen_loi_count: 0, direction_null_count: 3,
    obligation_count: 3, next_due_date: "2026-08-01",
    confirmed: true, pipeline: "extracted", may_have_unextracted: null, duplicate: false },

  // 6 · DUPLICATE suspected ("!" icon). Zero obligations → em dash (G4 case 4).
  { id: 6, doc_type: "hd_nha_cung_cap", primary_party: "Cty CP Bao Bì Việt",
    filename: "hopdong_baobi_2026 (1).pdf",
    nghia_vu_count: 0, quyen_loi_count: 0, direction_null_count: 0,
    obligation_count: 0, next_due_date: null,
    confirmed: false, pipeline: "extracted", may_have_unextracted: false, duplicate: true },

  // 7 · still processing (pipeline state). No obligations yet.
  { id: 7, doc_type: "hd_van_tai_logistics", primary_party: "Cty Vận Tải Phương Nam",
    filename: "vantai_logistics_Q3.pdf",
    nghia_vu_count: 0, quyen_loi_count: 0, direction_null_count: 0,
    obligation_count: 0, next_due_date: null,
    confirmed: false, pipeline: "processing", may_have_unextracted: null, duplicate: false },

  // 8 · normal confirmed + quiet (far deadline) → bottom of sort.
  { id: 8, doc_type: "hd_cong_nghe_ip", primary_party: "Cty Phần Mềm FSoft",
    filename: "license_phanmem_IP.pdf",
    nghia_vu_count: 2, quyen_loi_count: 1, direction_null_count: 0,
    obligation_count: 3, next_due_date: "2026-11-30",
    confirmed: true, pipeline: "extracted", may_have_unextracted: false, duplicate: false },
];

/* ===========================================================================
 * G2 — default sort. action-required first → nearest deadline → confirmed/quiet.
 * ========================================================================= */
function sortKey(d) {
  const overdue = d.next_due_date && new Date(d.next_due_date) < TODAY;
  const actionRequired = (!d.confirmed && d.pipeline !== "processing") || overdue;
  const due = d.next_due_date ? new Date(d.next_due_date).getTime() : Infinity;
  return [actionRequired ? 0 : 1, due];
}
const sortDocs = (arr) =>
  [...arr].sort((a, b) => {
    const [ka, da] = sortKey(a), [kb, db] = sortKey(b);
    return ka - kb || da - db;
  });

/* ===========================================================================
 * Small cell helpers
 * ========================================================================= */
function fmtDue(iso) {
  const d = new Date(iso);
  const dm = `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
  const diff = Math.round((d - TODAY) / 86400000);
  if (diff < 0) return { dm, label: `quá hạn ${-diff} ngày`, overdue: true };
  if (diff === 0) return { dm, label: "hôm nay", overdue: false, soon: true };
  return { dm, label: `còn ${diff} ngày`, overdue: false, soon: diff <= 7 };
}

/* Col 3 — Nghĩa vụ · Quyền lợi. Glyph + text label, never glyph-only (G7). NULL honest (G4). */
function DirectionCell({ d }) {
  if (d.obligation_count === 0)
    return <span style={{ color: t.color.inkSubtle }}>—</span>;
  const parts = [];
  if (d.nghia_vu_count > 0)
    parts.push(<span key="nv" style={{ color: t.color.ink }}>{d.nghia_vu_count}<span style={{ color: t.color.inkMuted }}>↑</span> NV</span>);
  if (d.quyen_loi_count > 0)
    parts.push(<span key="ql" style={{ color: t.color.ink }}>{d.quyen_loi_count}<span style={{ color: t.color.inkMuted }}>↓</span> QL</span>);
  if (d.direction_null_count > 0)
    parts.push(<span key="nu" style={{ color: t.color.inkMuted }} title="Chưa xác định nghĩa vụ hay quyền lợi">{d.direction_null_count}?</span>);
  return (
    <span style={{ fontSize: t.font.size.sm }}>
      {parts.map((p, i) => (
        <React.Fragment key={i}>{i > 0 && <span style={{ color: t.color.border }}> · </span>}{p}</React.Fragment>
      ))}
    </span>
  );
}

/* Col 4 — Hạn gần nhất. deadline / overdue / standing-only / none (G3). */
function DueCell({ d }) {
  if (d.next_due_date) {
    const f = fmtDue(d.next_due_date);
    const color = f.overdue ? t.color.red : f.soon ? t.color.amber : t.color.ink;
    return (
      <span style={{ fontSize: t.font.size.sm, color: t.color.ink }}>
        {f.dm} <span style={{ color: t.color.border }}>·</span>{" "}
        <span style={{ color, fontWeight: f.overdue ? t.font.weight.semibold : t.font.weight.regular }}>{f.label}</span>
      </span>
    );
  }
  if (d.obligation_count > 0)  // standing-only (G3)
    return <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontStyle: "italic" }}>Cam kết đang hiệu lực</span>;
  return <span style={{ color: t.color.inkSubtle }}>—</span>;
}

/* Col 5 — single composite status pill (UIX-02, no stacking) + completeness icon. */
function CompletenessIcon({ value }) {
  // DEC-045 / #276. False → render nothing.
  if (value === false) return null;
  const amber = value === true;
  return (
    <span
      title={amber ? "Có thể còn nghĩa vụ chưa bóc — xem chi tiết điều khoản" : "Chưa kiểm tra toàn bộ điều khoản"}
      style={{
        marginLeft: t.space[2], fontSize: t.font.size.sm, fontWeight: t.font.weight.bold,
        color: amber ? t.color.amber : t.color.gray, cursor: "help",
      }}
    >{amber ? "⚠" : "?"}</span>
  );
}

function StatusPill({ d }) {
  let label, fg, bg;
  if (d.pipeline === "processing") { label = "Đang xử lý"; fg = t.color.gray; bg = t.color.graySoft; }
  else if (!d.confirmed)           { label = "Cần xác nhận"; fg = t.color.amber; bg = t.color.amberSoft; }   // wins priority
  else                             { label = "Đã xác nhận"; fg = t.color.primary; bg = t.color.primarySoft; }
  return (
    <span style={{ display: "inline-flex", alignItems: "center" }}>
      <span style={{
        display: "inline-flex", alignItems: "center", background: bg, color: fg,
        padding: `${t.space[1]}px ${t.space[2]}px`, borderRadius: t.radius.pill,
        fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, whiteSpace: "nowrap",
      }}>{label}</span>
      <CompletenessIcon value={d.may_have_unextracted} />
    </span>
  );
}

/* ===========================================================================
 * Sidebar IA (REP-07 revised) — fixes "Tài lên" typo, renames Nghĩa vụ nav.
 * ========================================================================= */
function NavItem({ glyph, label, active, badge, beta }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: t.space[2],
      padding: `${t.space[2]}px ${t.space[3]}px`, borderRadius: t.radius.md, cursor: "pointer",
      background: active ? t.color.primarySoft : "transparent",
      color: active ? t.color.primary : t.color.ink,
      fontWeight: active ? t.font.weight.semibold : t.font.weight.regular,
      fontSize: t.font.size.md,
    }}>
      <span style={{ width: 16, textAlign: "center", color: active ? t.color.primary : t.color.inkMuted }}>{glyph}</span>
      <span style={{ flex: 1 }}>{label}</span>
      {beta && (
        <span style={{
          fontSize: 10, fontWeight: t.font.weight.semibold, color: t.color.amber,
          background: t.color.amberSoft, padding: "1px 6px", borderRadius: t.radius.pill,
        }}>Beta</span>
      )}
      {badge != null && (
        <span style={{
          fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.surface,
          background: t.color.amber, minWidth: 18, textAlign: "center",
          padding: "0 5px", borderRadius: t.radius.pill,
        }}>{badge}</span>
      )}
    </div>
  );
}

function Sidebar({ pendingCount }) {
  const grp = { fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.inkSubtle,
    letterSpacing: 0.5, textTransform: "uppercase", padding: `${t.space[2]}px ${t.space[3]}px ${t.space[1]}px` };
  return (
    <aside style={{ width: 232, borderRight: `1px solid ${t.color.border}`, padding: t.space[4], boxSizing: "border-box", background: t.color.surface }}>
      <div style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.bold, color: t.color.primary, padding: `${t.space[2]}px ${t.space[3]}px ${t.space[5]}px` }}>Khế</div>
      <div style={grp}>Theo dõi</div>
      <NavItem glyph="○" label="Tổng quan" />
      <NavItem glyph="◇" label="Nghĩa vụ & Quyền lợi" />
      <div style={grp}>Tài liệu</div>
      <NavItem glyph="■" label="Hồ sơ hợp đồng" active badge={pendingCount} />
      <NavItem glyph="↑" label="Tải lên" />
      <div style={grp}>Trợ lý</div>
      <NavItem glyph="✦" label="Hỏi-đáp" beta={BETA_CHAT} />
    </aside>
  );
}

/* ===========================================================================
 * Header — counter chips + fixed CTA (G5) + filter rows.
 * ========================================================================= */
function CounterChip({ children, tone, onClick }) {
  const map = {
    amber: { fg: t.color.amber, bd: t.color.amber, bg: t.color.amberSoft },
    red:   { fg: t.color.red,   bd: t.color.red,   bg: t.color.redSoft },
    muted: { fg: t.color.inkMuted, bd: t.color.border, bg: "transparent" },
  };
  const s = map[tone];
  return (
    <button onClick={onClick} style={{
      border: `1px solid ${s.bd}`, background: s.bg, color: s.fg,
      padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill,
      fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, fontFamily: t.font.family,
      cursor: onClick ? "pointer" : "default",
    }}>{children}</button>
  );
}

function FilterChip({ label, count, active, muted, onClick }) {
  return (
    <button onClick={onClick} style={{
      display: "inline-flex", alignItems: "center", gap: t.space[1],
      padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill,
      fontFamily: t.font.family, fontSize: t.font.size.sm,
      fontWeight: active ? t.font.weight.semibold : t.font.weight.medium, cursor: "pointer",
      border: `1px solid ${active ? t.color.primary : t.color.border}`,
      background: active ? t.color.primary : t.color.surface,
      color: active ? t.color.surface : muted ? t.color.inkMuted : t.color.ink,
    }}>
      {label}
      {count != null && (
        <span style={{
          fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold,
          color: active ? t.color.surface : t.color.inkMuted,
        }}>{count}</span>
      )}
    </button>
  );
}

/* ===========================================================================
 * MAIN
 * ========================================================================= */
export default function DocumentsListV2() {
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const [showPipeline, setShowPipeline] = useState(false);
  const [hoverId, setHoverId] = useState(null);

  const total = DOCS.length;                                  // 17 in a real tenant; 8 curated rows here
  const pending = DOCS.filter((d) => !d.confirmed && d.pipeline !== "processing").length;
  const dueSoon = DOCS.filter((d) => d.next_due_date && (() => { const x = Math.round((new Date(d.next_due_date) - TODAY) / 86400000); return x >= 0 && x <= 7; })()).length;
  const overdue = DOCS.filter((d) => d.next_due_date && new Date(d.next_due_date) < TODAY).length;

  const COMMITMENT_FILTERS = [
    { key: "all", label: "Tất cả", count: total },
    { key: "due7", label: "Tới hạn 7 ngày", count: dueSoon },
    { key: "overdue", label: "Quá hạn", count: overdue },
    { key: "pending", label: "Cần xác nhận", count: pending },
    { key: "rights", label: "Quyền lợi cần thu", count: DOCS.filter((d) => d.quyen_loi_count > 0).length },
  ];
  const PIPELINE_FILTERS = [
    { key: "processing", label: "Đang xử lý" },
    { key: "extracted", label: "Đã bóc tách" },
    { key: "needs_review", label: "Cần kiểm tra" },
  ];

  const match = (d) => {
    if (q && !(`${docTypeLabel(d.doc_type)} ${d.primary_party} ${d.filename}`.toLowerCase().includes(q.toLowerCase()))) return false;
    switch (filter) {
      case "all": return true;
      case "due7": return d.next_due_date && (() => { const x = Math.round((new Date(d.next_due_date) - TODAY) / 86400000); return x >= 0 && x <= 7; })();
      case "overdue": return d.next_due_date && new Date(d.next_due_date) < TODAY;
      case "pending": return !d.confirmed && d.pipeline !== "processing";
      case "rights": return d.quyen_loi_count > 0;
      case "processing": return d.pipeline === "processing";
      case "extracted": return d.pipeline === "extracted";
      case "needs_review": return d.pipeline === "needs_review";
      default: return true;
    }
  };
  const rows = sortDocs(DOCS.filter(match));

  const cols = [
    { key: "contract", label: "Hợp đồng", w: "34%" },
    { key: "type", label: "Loại", w: "12%" },
    { key: "direction", label: "Nghĩa vụ · Quyền lợi", w: "18%" },
    { key: "due", label: "Hạn gần nhất", w: "18%" },
    { key: "status", label: "Trạng thái", w: "18%" },
  ];

  const th = { textAlign: "left", padding: `${t.space[2]}px ${t.space[3]}px`, color: t.color.inkMuted,
    fontWeight: t.font.weight.semibold, fontSize: t.font.size.xs, textTransform: "uppercase",
    letterSpacing: 0.3, borderBottom: `1px solid ${t.color.borderStrong}`, whiteSpace: "nowrap" };
  const td = { padding: `${t.space[3]}px`, borderBottom: `1px solid ${t.color.border}`, verticalAlign: "middle" };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: t.color.surface, fontFamily: t.font.family, color: t.color.ink }}>
      <Sidebar pendingCount={pending} />

      <main style={{ flex: 1, padding: t.space[8], minWidth: 0 }}>
        {/* Header row: title + fixed CTA (G5) */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: t.space[4], flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>Hồ sơ hợp đồng</h1>
            <div style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: t.space[2] }}>
              {pending} cần xác nhận · {dueSoon} nghĩa vụ tới hạn · {total} hợp đồng
            </div>
          </div>
          <button style={{
            background: t.color.primary, color: t.color.surface, border: "none",
            padding: `${t.space[2]}px ${t.space[5]}px`, borderRadius: t.radius.md,
            fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family,
          }}>+ Tải hợp đồng</button>
        </div>

        {/* Counter chips — clickable, drive filters */}
        <div style={{ display: "flex", gap: t.space[2], alignItems: "center", flexWrap: "wrap", marginTop: t.space[4] }}>
          <CounterChip tone="amber" onClick={() => setFilter("pending")}>{pending}/{total} cần xác nhận</CounterChip>
          <CounterChip tone={overdue > 0 ? "red" : "muted"} onClick={() => setFilter(overdue > 0 ? "overdue" : "due7")}>{dueSoon} NV tới hạn 7 ngày{overdue > 0 ? ` · ${overdue} quá hạn` : ""}</CounterChip>
          <CounterChip tone="muted">{total} hợp đồng</CounterChip>
        </div>

        {/* Search + filter chips */}
        <div style={{ marginTop: t.space[5] }}>
          <input
            value={q} onChange={(e) => setQ(e.target.value)} placeholder="🔍  Tìm theo tên hoặc đối tác..."
            style={{
              width: "100%", maxWidth: 360, boxSizing: "border-box", height: 40,
              padding: `0 ${t.space[3]}px`, fontSize: t.font.size.md, fontFamily: t.font.family,
              border: `1px solid ${t.color.border}`, borderRadius: t.radius.md, outline: "none", color: t.color.ink,
            }}
          />
          {/* Row 1 — commitment-state (primary, always visible) */}
          <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[3] }}>
            {COMMITMENT_FILTERS.map((f) => (
              <FilterChip key={f.key} label={f.label} count={f.count} active={filter === f.key} onClick={() => setFilter(f.key)} />
            ))}
            <button onClick={() => setShowPipeline((s) => !s)} style={{
              border: "none", background: "transparent", color: t.color.inkMuted, cursor: "pointer",
              fontSize: t.font.size.sm, fontFamily: t.font.family, padding: `${t.space[1]}px ${t.space[2]}px`,
            }}>{showPipeline ? "Ẩn trạng thái xử lý ▴" : "Trạng thái xử lý ▾"}</button>
          </div>
          {/* Row 2 — pipeline-state (secondary, muted, collapsible) */}
          {showPipeline && (
            <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[2] }}>
              {PIPELINE_FILTERS.map((f) => (
                <FilterChip key={f.key} label={f.label} muted active={filter === f.key} onClick={() => setFilter(f.key)} />
              ))}
            </div>
          )}
        </div>

        {/* Column-3 glyph legend (G7) — never leave ↑↓ unexplained */}
        <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[4] }}>
          <strong style={{ color: t.color.ink }}>↑ NV</strong> = nghĩa vụ (mình phải làm) ·
          {" "}<strong style={{ color: t.color.ink }}>↓ QL</strong> = quyền lợi (mình được nhận) ·
          {" "}<strong style={{ color: t.color.ink }}>?</strong> = chưa xác định
        </div>

        {/* TABLE */}
        <div style={{ marginTop: t.space[3], border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <colgroup>{cols.map((c) => <col key={c.key} style={{ width: c.w }} />)}</colgroup>
            <thead><tr>{cols.map((c) => <th key={c.key} style={th}>{c.label}</th>)}</tr></thead>
            <tbody>
              {rows.length === 0 ? (
                <tr><td colSpan={5} style={{ ...td, textAlign: "center", color: t.color.inkMuted, padding: t.space[10] }}>
                  Không có hợp đồng phù hợp bộ lọc.
                </td></tr>
              ) : rows.map((d) => (
                <tr key={d.id}
                  onMouseEnter={() => setHoverId(d.id)} onMouseLeave={() => setHoverId(null)}
                  style={{ background: hoverId === d.id ? t.color.rowHover : t.color.surface, cursor: "pointer" }}
                >
                  {/* Col 1 — Hợp đồng: human title + filename secondary. NO raw snake_case. */}
                  <td style={td}>
                    <div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
                      <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.medium, color: t.color.ink, textDecoration: hoverId === d.id ? "underline" : "none" }}>
                        HĐ {docTypeLabel(d.doc_type)} với {d.primary_party}
                      </span>
                      {d.duplicate && (
                        <span title="Tệp trùng — kiểm tra" style={{ color: t.color.amber, fontWeight: t.font.weight.bold, cursor: "help" }}>!</span>
                      )}
                    </div>
                    <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 320 }}>
                      {d.filename}
                    </div>
                  </td>
                  {/* Col 2 — Loại: VN label, muted */}
                  <td style={{ ...td, color: t.color.inkMuted, fontSize: t.font.size.sm }}>{docTypeLabel(d.doc_type)}</td>
                  {/* Col 3 — Nghĩa vụ · Quyền lợi */}
                  <td style={td}><DirectionCell d={d} /></td>
                  {/* Col 4 — Hạn gần nhất */}
                  <td style={td}><DueCell d={d} /></td>
                  {/* Col 5 — Trạng thái (composite pill + completeness icon) */}
                  <td style={td}><StatusPill d={d} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* On-page designer annotations (not part of production UI) */}
        <div style={{ marginTop: t.space[6], padding: t.space[4], background: t.color.graySoft, borderRadius: t.radius.md, fontSize: t.font.size.xs, color: t.color.inkMuted, lineHeight: 1.7 }}>
          <div style={{ fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[1] }}>📐 Ghi chú thiết kế (không render trong production)</div>
          <div><strong>Sort (G2):</strong> cần xác nhận / quá hạn lên đầu → hạn gần nhất tăng dần → đã xác nhận + xa hạn xuống cuối.</div>
          <div><strong>7 trạng thái hàng:</strong> (1) đã xác nhận thường · (2) quá hạn = đỏ ở Cột 4 · (3) cần xác nhận = pill amber Cột 5 (KHÔNG viền hàng — G6) · (4) standing-only = "Cam kết đang hiệu lực" Cột 4 (G3) · (5) completeness ⚠/? Cột 5 (DEC-045) · (6) hover = nền #F9FAFB + gạch chân tiêu đề, cả hàng click → chi tiết · (7) nghi trùng = "!" Cột 1.</div>
          <div><strong>Direction (G4):</strong> hàng #1 mixed "5↑NV · 2↓QL · 3?" · #5 all-NULL "3?" · #6 zero "—". Dấu "?" không bao giờ bị ẩn (D-13).</div>
          <div><strong>CTA (G5):</strong> luôn là "Tải hợp đồng" — chip đếm "{pending}/{total} cần xác nhận" gánh vai nudge. Không có CTA điều kiện.</div>
          <div><strong>Out of scope:</strong> phân loại sai (classifier, for:ai — G1) · standing obligation detail section (BA #272) · firm portal cross-tenant (DEC-046) · mobile card-collapse &lt;1024px (post-pilot).</div>
          <div><strong>Backend (FE blocks on #279):</strong> primary_party · next_due_date · nghia_vu_count · quyen_loi_count · direction_null_count · may_have_unextracted_obligations.</div>
        </div>
      </main>
    </div>
  );
}
