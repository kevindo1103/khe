/**
 * Servanda — Danh sách tài liệu v3  (mockup_documents_list_v3.jsx)
 * KHE_Designer · issue #481 (QC relay, gap 3/3: document list page) · DS v1.1
 * STATIC PROTOTYPE — scope-lock docs/mockup_*.jsx. Not production code.
 * ----------------------------------------------------------------------------
 * WHY THIS FILE: #481 flagged 3 gaps causing visual inconsistency after PR
 *   #476 shipped DS v1.1 only for the obligation tab: (1) Tổng quan tab —
 *   closed by mockup_document_detail_v4.jsx / PR #480 (awaiting ratify);
 *   (2) Nội dung hợp đồng tab — same PR; (3) THIS FILE — document list page
 *   (`/admin/documents`, `frontend/src/pages/admin/DocumentList.tsx`).
 *
 * TOKENS/COMPONENTS: real import from mockup_design_system_v1.1.jsx, same
 *   discipline as v4 — no mirrored/reinvented CSS values.
 *
 * FIELD/COMPONENT THẬT — verified via Explore agent (2026-07-03) against
 *   frontend/src/pages/admin/DocumentList.tsx (634 lines) + backend
 *   routers/documents.py + schemas/documents.py + AdminShell.tsx. Key
 *   findings that changed what this mockup does vs. a naive re-skin:
 *
 *   - `StatusPill` (DocumentList.tsx:137-158) hand-rolls 3 states with inline
 *     Tailwind (`bg-surface-alt`/`bg-warning-soft`/`bg-primary-soft`) — does
 *     NOT import the app's own `Badge.tsx` atom despite one existing with a
 *     matching `kind` union. Confirms #481's "ad-hoc, not atoms" claim, for
 *     this component specifically (LifecycleBadge, below, is NOT ad-hoc).
 *   - **StatusPill has a real logic gap, found during research, not in scope
 *     of #481's brief:** it branches on `status === 'processing'` then falls
 *     through to `!confirmed_by_user_at` for everything else — INCLUDING
 *     `status === 'failed'`. A doc whose extraction failed has
 *     `confirmed_by_user_at = null` too, so it renders "Cần xác nhận" (amber,
 *     "needs confirmation") instead of surfacing the failure. This mockup
 *     does NOT silently fix this (it's a behavior change, not a re-skin) —
 *     flagged as an explicit open decision below (Q-Status-Failed).
 *   - `may_have_unextracted_obligations` (drives `CompletenessIcon`'s ⚠/?)
 *     is **hardcoded `None`** in the router today
 *     (routers/documents.py, `# TODO(#276): map doc.may_have_unextracted...`)
 *     — `CompletenessIcon` never renders anything in production right now.
 *     Mockup treats it as an opt-in preview (off by default), not live UI.
 *   - `LifecycleBadge.tsx` (real shared atom, unlike StatusPill) uses
 *     `active: bg-success-soft text-success` — confirms the SAME v1.1
 *     conflict already flagged for ConfidenceMeter/SignatureBadge in v4's
 *     Q1 (v1.1 has no success/green token) — this extends Q1 to a 3rd
 *     component. Reuses v4's exact LifecycleBadge treatment for consistency
 *     across both mockups (same component, same open question).
 *   - `duplicate` field (drove a "!" icon in the current list AND in the old
 *     `mockup_documents_list_v2.jsx`) is **not in the backend schema at
 *     all** — `frontend/src/types/documents.ts` marks it optional/never
 *     populated. Dead code today. OMITTED from this mockup rather than
 *     reproducing a UI element that never renders in production.
 *   - List API (`DocumentListItem`, schemas/documents.py:104-141) does NOT
 *     return `doc_type_group` — only legacy `doc_type` (10-value enum, no
 *     "other"). So unlike `mockup_document_detail_v4.jsx` (which correctly
 *     uses the newer `doc_type_group`), THIS mockup uses legacy
 *     `DOC_TYPE_LABELS` — that's the real, current API shape, not a
 *     regression. Flagged as an informational note, not an open decision
 *     (changing the list API is out of scope for a visual redesign).
 *   - No pagination anywhere in the app: list fetches `page_size=100` once,
 *     filters/sorts client-side, shows a static "Hiển thị 100/N — thu hẹp bộ
 *     lọc" banner past 100 results. Mirrored as-is — adding real pagination
 *     is a different, larger feature, out of scope here.
 *   - `AdminShell.tsx:21` confirmed exact:
 *     `<main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">` — no
 *     per-page override mechanism exists. #481's "quick tactical fix"
 *     width question is demonstrated as a toggle below (open decision).
 *
 * OPEN DECISIONS (chờ Kevin ratify, không tự quyết ngầm):
 *   Q1-ext: LifecycleBadge cũng dùng success/xanh lá — cùng câu hỏi Q1 đã
 *     nêu ở #478/PR #480 (ConfidenceMeter/SignatureBadge), giờ áp dụng thêm
 *     cho component thứ 3.
 *   Q-Status-Failed: StatusPill không phân biệt "failed" vs "cần xác nhận" —
 *     bug thật, phát hiện khi research, không có trong brief #481.
 *   Q-Width: max-w-5xl (1024px) áp dụng đều mọi trang — có nên nới riêng cho
 *     trang bảng/list không? Demo so sánh bên dưới.
 *   Q-CompletenessIcon: ⚠/? hiện chết (luôn null) — có nên build UI sống
 *     trước khi backend #276 xong không, hay chờ?
 */
import React, { useState } from "react";
import {
  tokens as t, Button, Card, Table, EmptyState,
} from "./mockup_design_system_v1.1.jsx";

/* ===========================================================================
 * REAL FIELD MAP — legacy DOC_TYPE_LABELS (10 values, no "other"), the map
 * the LIST API actually uses (frontend/src/lib/labels.ts:8-18, verified
 * verbatim — different from doc_type_group used in mockup_document_detail_v4)
 * ========================================================================= */
const DOC_TYPE_LABELS = {
  hd_nha_cung_cap: "Nhà cung cấp",
  hd_thue_mat_bang: "Thuê mặt bằng",
  hd_lao_dong: "Lao động",
  hd_dan_su: "Dân sự",
  hd_bat_dong_san: "Bất động sản",
  hd_van_tai_logistics: "Vận tải & Logistics",
  hd_xay_dung: "Xây dựng",
  hd_cong_nghe_ip: "Công nghệ & IP",
  hd_tai_chinh: "Tài chính",
  hd_hanh_chinh: "Hành chính",
};
const docTypeLabel = (dt) => (dt ? DOC_TYPE_LABELS[dt] || dt : "Chưa phân loại");

const TODAY = new Date(2026, 6, 3);

/* ===========================================================================
 * SAMPLE DATA — real DocumentListItem field shape (schemas/documents.py:104-141)
 * ========================================================================= */
const DOCS = [
  { id: 1, file_name: "hd_thue_qz_2026.pdf", title: "HĐ ký quỹ thuê mặt bằng Q7", doc_type: "hd_thue_mat_bang", status: "processing", confirmed_by_user_at: null, primary_party: "Cty TNHH Hải Đăng", next_due_date: null, obligation_count: 0, nghia_vu_count: undefined, quyen_loi_count: undefined, direction_null_count: undefined, lifecycle_status: null, has_signature: null, may_have_unextracted_obligations: null, created_at: "2026-07-03" },
  { id: 2, file_name: "hd_ky_quy_sunrise.pdf", title: "HĐ mua bán căn hộ Sunrise Tower", doc_type: "hd_bat_dong_san", status: "extracted", confirmed_by_user_at: null, primary_party: "Cty CP BĐS Sunrise", next_due_date: "2026-06-28", obligation_count: 8, nghia_vu_count: 6, quyen_loi_count: 2, direction_null_count: 0, lifecycle_status: "active", has_signature: true, may_have_unextracted_obligations: true, created_at: "2026-06-20" },
  { id: 3, file_name: "hd_bao_bi_viet.pdf", title: "HĐ cung cấp bao bì", doc_type: "hd_nha_cung_cap", status: "extracted", confirmed_by_user_at: "2026-06-21", primary_party: "Cty CP Bao Bì Việt", next_due_date: "2026-07-03", obligation_count: 3, nghia_vu_count: 2, quyen_loi_count: 1, direction_null_count: 0, lifecycle_status: "active", has_signature: true, may_have_unextracted_obligations: false, created_at: "2026-06-18" },
  { id: 4, file_name: "hd_marketing_xyz.pdf", title: "HĐ dịch vụ marketing", doc_type: "hd_dan_su", status: "extracted", confirmed_by_user_at: "2026-06-15", primary_party: "Agency XYZ", next_due_date: "2026-07-10", obligation_count: 2, nghia_vu_count: 1, quyen_loi_count: 1, direction_null_count: 0, lifecycle_status: "expiring", has_signature: true, may_have_unextracted_obligations: false, created_at: "2026-06-10" },
  { id: 5, file_name: "hd_ld_nvan.pdf", title: "HĐ lao động — N.V.An", doc_type: "hd_lao_dong", status: "extracted", confirmed_by_user_at: "2026-05-01", primary_party: "Nguyễn Văn An", next_due_date: null, obligation_count: 4, nghia_vu_count: 4, quyen_loi_count: 0, direction_null_count: 0, lifecycle_status: "active", has_signature: true, may_have_unextracted_obligations: false, created_at: "2026-05-01" },
  { id: 6, file_name: "hd_ip_alphatech.pdf", title: "HĐ license phần mềm — ALPHATECH", doc_type: "hd_cong_nghe_ip", status: "extracted", confirmed_by_user_at: "2026-06-20", primary_party: "Cty Phần Mềm ALPHATECH", next_due_date: null, obligation_count: 0, nghia_vu_count: 0, quyen_loi_count: 0, direction_null_count: 0, lifecycle_status: "settled", has_signature: true, may_have_unextracted_obligations: false, created_at: "2026-03-15" },
  { id: 7, file_name: "hd_hop_tac_abcxyz.pdf", title: "HĐ hợp tác ABC-XYZ", doc_type: "hd_dan_su", status: "extracted", confirmed_by_user_at: null, primary_party: "Bên A / Bên B", next_due_date: "2026-06-25", obligation_count: 2, nghia_vu_count: undefined, quyen_loi_count: undefined, direction_null_count: 2, lifecycle_status: "active", has_signature: false, may_have_unextracted_obligations: false, created_at: "2026-06-22" },
  { id: 8, file_name: "hd_van_tai_logistics.pdf", title: "HĐ vận tải logistics", doc_type: "hd_van_tai_logistics", status: "failed", confirmed_by_user_at: null, primary_party: null, next_due_date: null, obligation_count: 0, nghia_vu_count: undefined, quyen_loi_count: undefined, direction_null_count: undefined, lifecycle_status: null, has_signature: null, may_have_unextracted_obligations: null, created_at: "2026-07-01" },
  { id: 9, file_name: "hd_xay_dung_q9.pdf", title: "HĐ xây dựng nhà xưởng Q9", doc_type: "hd_xay_dung", status: "extracted", confirmed_by_user_at: "2026-06-01", primary_party: "Cty CP Xây Dựng Miền Nam", next_due_date: "2026-06-15", obligation_count: 5, nghia_vu_count: 4, quyen_loi_count: 1, direction_null_count: 0, lifecycle_status: "expired", has_signature: true, may_have_unextracted_obligations: false, created_at: "2026-04-01" },
];

/* ===========================================================================
 * LOCAL COMPONENTS — v1.1 tokens directly (Badge's 13-kind vocabulary
 * doesn't cover these domain states — confirmed via research; same pattern
 * as v4's LifecycleBadge/ConfidenceMeter: new component shape, real tokens)
 * ========================================================================= */

/* LifecycleBadge — reused verbatim from mockup_document_detail_v4.jsx for
 * cross-mockup consistency (same open question, same component, one answer
 * needed, not two divergent ones). */
function LifecycleBadge({ status }) {
  if (!status) return null;
  if (status === "settled") return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: t.font.family, fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, background: t.color.done_soft, color: t.color.done }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: "currentColor", opacity: 0.7 }} />Đã thanh lý
    </span>
  );
  const MAP = {
    active: { label: "Đang hiệu lực", tone: t.color.inkMuted, variant: "outline" },
    expiring: { label: "Sắp hết hạn", tone: t.color.warning, variant: "solid" },
    expired: { label: "Hết hạn", tone: t.color.danger, variant: "solid" },
    suspended: { label: "Tạm dừng", tone: t.color.inkMuted, variant: "outline" },
  };
  const s = MAP[status];
  if (!s) return null;
  const solid = s.variant === "solid";
  const TONE_TINT = { [t.color.warning]: t.color.warning_soft, [t.color.danger]: t.color.danger_soft };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: t.font.family, fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, background: solid ? TONE_TINT[s.tone] : "transparent", color: s.tone, border: solid ? "none" : `1px solid ${s.tone}` }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: "currentColor", opacity: 0.7 }} />{s.label}
    </span>
  );
}

function SignatureBadge({ hasSig, variant }) {
  if (hasSig == null) return null;
  const legacyGreen = "#15803D", legacyGreenSoft = "#E9F6EE";
  const signedTone = variant === "legacy" ? legacyGreen : t.color.done;
  const signedBg = variant === "legacy" ? legacyGreenSoft : t.color.done_soft;
  return hasSig
    ? <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, background: signedBg, color: signedTone, fontFamily: t.font.family }}>Đã ký</span>
    : <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, background: t.color.warning_soft, color: t.color.warning, fontFamily: t.font.family }}>Chưa ký</span>;
}

/* isPendingDoc — single source of truth for "Cần xác nhận" membership, used
 * by BOTH the filter-chip count and the actual filter logic below. Kept as
 * one function (not duplicated inline in two places) specifically so the
 * fixFailedState toggle can't drift between what StatusPill *shows* and
 * what the "Cần xác nhận" filter actually *includes* — that drift was a
 * real QC finding on an earlier version of this file. */
function isPendingDoc(doc, fixFailedState) {
  if (doc.status === "processing") return false;
  if (fixFailedState && doc.status === "failed") return false; // now its own state, not "pending"
  return !doc.confirmed_by_user_at;
}

/* StatusPill — 3 real states + optional 4th "failed" state (Q-Status-Failed
 * proposal, opt-in toggle — NOT default, since fixing this is a behavior
 * change beyond a visual re-skin). Default (toggle off) mirrors today's
 * REAL (buggy) behavior: failed docs show "Cần xác nhận", same as prod. */
function StatusPill({ doc, fixFailedState }) {
  let label, tone, variant;
  if (doc.status === "processing") {
    label = "Đang xử lý"; tone = t.color.inkMuted; variant = "outline";
  } else if (fixFailedState && doc.status === "failed") {
    label = "Lỗi trích xuất"; tone = t.color.danger; variant = "solid";
  } else if (!doc.confirmed_by_user_at) {
    label = "Cần xác nhận"; tone = t.color.warning; variant = "solid";
  } else {
    label = "Đã xác nhận"; tone = t.color.primary; variant = "solid";
  }
  const solid = variant === "solid";
  const TONE_TINT = { [t.color.warning]: t.color.warning_soft, [t.color.danger]: t.color.danger_soft, [t.color.primary]: t.color.primarySoft };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", fontFamily: t.font.family, fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, background: solid ? TONE_TINT[tone] : "transparent", color: tone, border: solid ? "none" : `1px solid ${tone}`, whiteSpace: "nowrap" }}>
      {label}
    </span>
  );
}

/* CompletenessIcon — dead in production today (may_have_unextracted_obligations
 * hardcoded None, router TODO #276). Opt-in preview only, off by default. */
function CompletenessIcon({ value, showPreview }) {
  if (!showPreview || value === false || value == null) return null;
  return (
    <span title="Có thể còn nghĩa vụ chưa bóc — xem chi tiết điều khoản" style={{ marginLeft: 4, fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.warning }}>
      cần xem
    </span>
  );
}

function DirectionCell({ doc }) {
  if (doc.obligation_count === 0) return <span style={{ color: t.color.inkFaint, fontSize: t.font.size.xs }}>—</span>;
  if (doc.nghia_vu_count === undefined) {
    return <span title="Chưa xác định nghĩa vụ hay quyền lợi" style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>{doc.obligation_count}?</span>;
  }
  const nv = doc.nghia_vu_count || 0, ql = doc.quyen_loi_count || 0, nu = doc.direction_null_count || 0;
  const parts = [];
  if (nv > 0) parts.push(<span key="nv" style={{ color: t.color.ink }}>{nv}<span style={{ color: t.color.inkFaint }}>↑</span> NV</span>);
  if (ql > 0) parts.push(<span key="ql" style={{ color: t.color.ink }}>{ql}<span style={{ color: t.color.inkFaint }}>↓</span> QL</span>);
  if (nu > 0) parts.push(<span key="nu" title="Chưa xác định nghĩa vụ hay quyền lợi" style={{ color: t.color.inkMuted }}>{nu}?</span>);
  return (
    <span style={{ fontSize: t.font.size.xs, display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap" }}>
      {parts.map((p, i) => <span key={i} style={{ display: "flex", alignItems: "center", gap: 4 }}>{i > 0 && <span style={{ color: t.color.inkFaint }}>·</span>}{p}</span>)}
    </span>
  );
}

function DueCell({ doc }) {
  if (doc.next_due_date) {
    const d = new Date(doc.next_due_date);
    const diff = Math.round((d - TODAY) / 86400000);
    const dm = `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
    let label, color;
    if (diff < 0) { label = `quá hạn ${-diff} ngày`; color = t.color.danger; }
    else if (diff === 0) { label = "hôm nay"; color = t.color.warning; }
    else if (diff <= 7) { label = `còn ${diff} ngày`; color = t.color.warning; }
    else { label = `còn ${diff} ngày`; color = t.color.inkMuted; }
    return (
      <span style={{ fontSize: t.font.size.xs, color: t.color.ink, fontVariantNumeric: "tabular-nums" }}>
        {dm} <span style={{ color: t.color.inkFaint }}>·</span> <span style={{ color, fontWeight: t.font.weight.semibold }}>{label}</span>
      </span>
    );
  }
  if (doc.obligation_count > 0) {
    return (
      <span style={{ fontSize: t.font.size.xs, display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        <span style={{ color: t.color.ink, fontWeight: t.font.weight.medium }}>Cam kết đang hiệu lực</span>
        <span style={{ display: "inline-flex", alignItems: "center", padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill, background: t.color.paper, color: t.color.inkMuted, fontSize: 10, fontWeight: t.font.weight.medium, border: `1px solid ${t.color.n200}` }}>Liên tục</span>
      </span>
    );
  }
  return <span style={{ color: t.color.inkFaint, fontSize: t.font.size.xs }}>—</span>;
}

function FilterChip({ label, count, active, onClick }) {
  return (
    <button onClick={onClick} aria-pressed={active} style={{
      display: "inline-flex", alignItems: "center", gap: 4, padding: `${t.space[1]}px ${t.space[3]}px`,
      borderRadius: t.radius.pill, fontSize: t.font.size.xs, fontWeight: t.font.weight.medium,
      border: `1px solid ${active ? t.color.primary : t.color.n300}`,
      background: active ? t.color.primary : t.color.surface, color: active ? "#fff" : t.color.ink,
      cursor: "pointer", fontFamily: t.font.family, whiteSpace: "nowrap",
    }}>
      {label}
      {count !== undefined && <span style={{ fontWeight: t.font.weight.semibold, color: active ? "rgba(255,255,255,.7)" : t.color.inkFaint }}>{count}</span>}
    </button>
  );
}

/* ===========================================================================
 * SEARCH + FILTER BAR
 * ========================================================================= */
const COMMITMENT_FILTERS = [
  { key: "all", label: "Tất cả" },
  { key: "due7", label: "Sắp đến hạn" },
  { key: "overdue", label: "Quá hạn" },
  { key: "pending", label: "Cần xác nhận" },
  { key: "rights", label: "Quyền lợi" },
];
const PIPELINE_FILTERS = [
  { key: "processing", label: "Đang xử lý" },
  { key: "extracted", label: "Đã bóc tách" },
  { key: "needs_review", label: "Cần kiểm tra" },
];

function FilterBar({ filter, onFilter, query, onQuery, showPipeline, onTogglePipeline, fixFailedState }) {
  const counts = {
    all: DOCS.length,
    due7: DOCS.filter((d) => d.next_due_date && Math.round((new Date(d.next_due_date) - TODAY) / 86400000) <= 7 && Math.round((new Date(d.next_due_date) - TODAY) / 86400000) >= 0).length,
    overdue: DOCS.filter((d) => d.next_due_date && new Date(d.next_due_date) < TODAY).length,
    pending: DOCS.filter((d) => isPendingDoc(d, fixFailedState)).length,
    rights: DOCS.filter((d) => (d.quyen_loi_count || 0) > 0).length,
  };
  return (
    <div style={{ marginBottom: t.space[5] }}>
      <div style={{ marginBottom: t.space[3] }}>
        <input
          type="text" placeholder="Tìm theo tên, đối tác…" value={query} onChange={(e) => onQuery(e.target.value)}
          style={{ width: "100%", maxWidth: 360, height: 40, padding: `0 ${t.space[3]}px`, borderRadius: t.radius.control, border: `1px solid ${t.color.borderStrong}`, fontFamily: t.font.family, fontSize: t.font.size.base, color: t.color.ink }}
        />
      </div>
      <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginBottom: t.space[2] }}>
        {COMMITMENT_FILTERS.map((f) => <FilterChip key={f.key} label={f.label} count={counts[f.key]} active={filter === f.key} onClick={() => onFilter(f.key)} />)}
      </div>
      <button onClick={onTogglePipeline} style={{ border: "none", background: "transparent", color: t.color.primary, fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, cursor: "pointer", padding: 0, fontFamily: t.font.family }}>
        {showPipeline ? "Ẩn bộ lọc theo tiến trình ▴" : "Lọc theo tiến trình xử lý ▾"}
      </button>
      {showPipeline && (
        <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[2] }}>
          {PIPELINE_FILTERS.map((f) => <FilterChip key={f.key} label={f.label} active={filter === f.key} onClick={() => onFilter(f.key)} />)}
        </div>
      )}
    </div>
  );
}

/* ===========================================================================
 * SHOWCASE
 * ========================================================================= */
export default function DocumentsListV3() {
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [showPipeline, setShowPipeline] = useState(false);
  const [sigVariant, setSigVariant] = useState("legacy");
  const [fixFailedState, setFixFailedState] = useState(false);
  const [showCompletenessPreview, setShowCompletenessPreview] = useState(false);
  const [wideLayout, setWideLayout] = useState(false);

  let filtered = DOCS;
  if (query) {
    const q = query.toLowerCase();
    filtered = filtered.filter((d) => d.title.toLowerCase().includes(q) || (d.primary_party || "").toLowerCase().includes(q));
  }
  if (filter === "due7") filtered = filtered.filter((d) => d.next_due_date && (new Date(d.next_due_date) - TODAY) / 86400000 <= 7 && (new Date(d.next_due_date) - TODAY) / 86400000 >= 0);
  else if (filter === "overdue") filtered = filtered.filter((d) => d.next_due_date && new Date(d.next_due_date) < TODAY);
  else if (filter === "pending") filtered = filtered.filter((d) => isPendingDoc(d, fixFailedState));
  else if (filter === "rights") filtered = filtered.filter((d) => (d.quyen_loi_count || 0) > 0);
  else if (filter === "processing") filtered = filtered.filter((d) => d.status === "processing");
  else if (filter === "extracted") filtered = filtered.filter((d) => d.status === "extracted");

  const cols = [
    { key: "doc", label: "Hợp đồng" },
    { key: "type", label: "Loại" },
    { key: "direction", label: "Nghĩa vụ · Quyền lợi" },
    { key: "due", label: "Hạn gần nhất" },
    { key: "status", label: "Trạng thái" },
  ];

  const rows = filtered;

  const renderCell = (key, doc) => {
    if (key === "doc") return (
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
          <span style={{ fontWeight: t.font.weight.semibold, color: t.color.ink }}>{doc.title}</span>
          <LifecycleBadge status={doc.lifecycle_status} />
          <SignatureBadge hasSig={doc.has_signature} variant={sigVariant} />
        </div>
        <div style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, marginTop: 2 }}>{doc.file_name}</div>
      </div>
    );
    if (key === "type") return docTypeLabel(doc.doc_type);
    if (key === "direction") return <DirectionCell doc={doc} />;
    if (key === "due") return <DueCell doc={doc} />;
    if (key === "status") return (
      <span style={{ display: "inline-flex", alignItems: "center" }}>
        <StatusPill doc={doc} fixFailedState={fixFailedState} />
        <CompletenessIcon value={doc.may_have_unextracted_obligations} showPreview={showCompletenessPreview} />
      </span>
    );
    return doc[key];
  };

  return (
    <div style={{ minHeight: "100vh", background: t.color.paper, fontFamily: t.font.family }}>
      <div style={{ maxWidth: wideLayout ? 1400 : t.layout.maxWidth, margin: "0 auto", padding: t.space[6], transition: "max-width 180ms" }}>

        <div style={{ marginBottom: t.space[5] }}>
          <div style={{ fontSize: t.font.size.label, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: t.font.tracking.label, fontWeight: t.font.weight.semibold }}>
            Danh sách tài liệu · #481 · v3
          </div>
          <h1 style={{ fontSize: t.font.size.display, fontWeight: t.font.weight.semibold, color: t.color.ink, margin: `${t.space[1]}px 0 0` }}>Tài liệu</h1>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: t.space[4], marginBottom: t.space[5], padding: t.space[3], background: t.color.surface, border: `1px solid ${t.color.n200}`, borderRadius: t.radius.control, fontSize: t.font.size.xs, color: t.color.inkMuted, alignItems: "center" }}>
          <strong style={{ color: t.color.ink }}>Preview controls:</strong>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={sigVariant === "v1.1"} onChange={(e) => setSigVariant(e.target.checked ? "v1.1" : "legacy")} /> SignatureBadge dùng v1.1 (Q1-ext)
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={fixFailedState} onChange={(e) => setFixFailedState(e.target.checked)} /> Sửa StatusPill "failed" (Q-Status-Failed, đề xuất)
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={showCompletenessPreview} onChange={(e) => setShowCompletenessPreview(e.target.checked)} /> Preview CompletenessIcon (chết trên prod hôm nay)
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={wideLayout} onChange={(e) => setWideLayout(e.target.checked)} /> Width rộng hơn 1024px (Q-Width, so sánh)
          </label>
        </div>

        <FilterBar filter={filter} onFilter={setFilter} query={query} onQuery={setQuery} showPipeline={showPipeline} onTogglePipeline={() => setShowPipeline(!showPipeline)} fixFailedState={fixFailedState} />

        <div style={{ background: t.color.surface, borderRadius: t.radius.card, border: `1px solid ${t.color.n200}`, boxShadow: t.elevation.e1, padding: t.space[2] }}>
          {rows.length === 0 ? (
            <EmptyState title="Không có tài liệu phù hợp bộ lọc" description="Thử bỏ bớt bộ lọc hoặc từ khoá tìm kiếm." />
          ) : (
            <Table columns={cols} rows={rows} renderCell={renderCell} />
          )}
        </div>

        {rows.length > 0 && rows.length < DOCS.length && (
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, marginTop: t.space[2] }}>
            Hiển thị {rows.length}/{DOCS.length} tài liệu.
          </div>
        )}

        {/* Open decisions */}
        <div style={{ marginTop: t.space[7] }}>
          <h2 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[4] }}>Quyết định mở — chờ Kevin ratify</h2>

          <div style={{ border: `2px dashed ${t.color.warning}`, borderRadius: t.radius.card, padding: t.space[4], background: t.color.warning_soft, marginBottom: t.space[4] }}>
            <div style={{ fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: t.color.warning, textTransform: "uppercase", letterSpacing: t.font.tracking.label, marginBottom: t.space[2] }}>Q1-ext — chờ Kevin ratify</div>
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>LifecycleBadge.tsx</code> (production, đã xác nhận) dùng <code>active: bg-success-soft text-success</code> — cùng vấn đề đã nêu ở Q1 (#478/PR #480) cho ConfidenceMeter/SignatureBadge, giờ áp dụng thêm cho component thứ 3. Nếu Kevin chốt hướng v1.1-native cho Q1, nên áp cùng lúc cho cả 3 component để nhất quán, không sửa riêng lẻ.
            </div>
          </div>

          <div style={{ border: `2px dashed ${t.color.warning}`, borderRadius: t.radius.card, padding: t.space[4], background: t.color.warning_soft, marginBottom: t.space[4] }}>
            <div style={{ fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: t.color.warning, textTransform: "uppercase", letterSpacing: t.font.tracking.label, marginBottom: t.space[2] }}>Q-Status-Failed — chờ Kevin ratify</div>
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>StatusPill</code> (DocumentList.tsx:137-158) không phân biệt <code>status==="failed"</code> — tài liệu lỗi trích xuất hiện nhầm thành "Cần xác nhận" (vì <code>confirmed_by_user_at</code> cũng null). Đây là bug thật, phát hiện khi research, không nằm trong scope #481 gốc (thuần visual re-skin). Toggle "Sửa StatusPill failed" ở trên demo phương án: badge đỏ riêng "Lỗi trích xuất" — và (QC fix) toggle này giờ propagate đúng vào cả chip đếm "Cần xác nhận" lẫn kết quả lọc thật (dùng chung 1 hàm <code>isPendingDoc()</code>, không tách logic 2 nơi). Mặc định TẮT — mockup mặc định phản ánh đúng hành vi thật hôm nay (kể cả khi sai), không tự sửa logic production trong 1 PR visual.
            </div>
          </div>

          <div style={{ border: `2px dashed ${t.color.warning}`, borderRadius: t.radius.card, padding: t.space[4], background: t.color.warning_soft, marginBottom: t.space[4] }}>
            <div style={{ fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: t.color.warning, textTransform: "uppercase", letterSpacing: t.font.tracking.label, marginBottom: t.space[2] }}>Q-CompletenessIcon — chờ Kevin ratify</div>
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>may_have_unextracted_obligations</code> hardcode <code>None</code> ở router hôm nay (<code>TODO(#276)</code>) — <code>CompletenessIcon</code> chưa từng render gì trên production. Toggle "Preview CompletenessIcon" demo UI nếu backend #276 xong. Cần Kevin quyết: build UI trước (nằm chờ) hay đợi #276 xong mới làm.
            </div>
          </div>

          <div style={{ border: `2px dashed ${t.color.warning}`, borderRadius: t.radius.card, padding: t.space[4], background: t.color.warning_soft, marginBottom: t.space[4] }}>
            <div style={{ fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: t.color.warning, textTransform: "uppercase", letterSpacing: t.font.tracking.label, marginBottom: t.space[2] }}>Q-Width — chờ Kevin ratify</div>
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>AdminShell.tsx:21</code> áp <code>max-w-5xl</code> (1024px) đều cho MỌI trang admin, không có cơ chế override theo trang. #481 đề xuất "quick tactical fix": nới riêng cho trang bảng/list. Toggle "Width rộng hơn 1024px" ở trên so sánh trực quan (1024px hiện tại vs. 1400px). Đây là thay đổi <code>AdminShell.tsx</code> — việc của Frontend, Designer chỉ demo trade-off để Kevin quyết giá trị cụ thể.
            </div>
          </div>
        </div>

        {/* Designer Notes */}
        <div style={{ marginTop: t.space[7], padding: t.space[5], borderRadius: t.radius.card, border: `2px dashed ${t.color.n300}`, background: t.color.surface }}>
          <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[4] }}>Designer Notes — #481 (gap 3/3)</div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed, display: "flex", flexDirection: "column", gap: t.space[4] }}>
            <div><strong>Cột thật, không bịa:</strong> 5 cột giữ nguyên cấu trúc thật (Hợp đồng/Loại/Nghĩa vụ·Quyền lợi/Hạn gần nhất/Trạng thái, DocumentList.tsx render structure) — chỉ retheme màu/spacing sang v1.1 token, không đổi field/logic (trừ 2 case có callout riêng: StatusPill failed, CompletenessIcon).</div>
            <div><strong>`duplicate` field — OMITTED:</strong> field này không tồn tại trong backend schema (`DocumentListItem`), luôn <code>undefined</code> trên FE (`types/documents.ts`) — dead code từ cả production lẫn `mockup_documents_list_v2.jsx` cũ. Không tái tạo UI cho field không bao giờ có giá trị.</div>
            <div><strong>DirectionCell/DueCell:</strong> mirror chính xác logic thật (nv/ql/direction_null count format, overdue/due-soon/standing-obligation 3 nhánh) — chỉ đổi màu class Tailwind → token v1.1 tương ứng (danger/warning/inkMuted/inkFaint).</div>
            <div><strong>Filter/search:</strong> 5 chip "commitment" luôn hiện + 3 chip "pipeline" ẩn sau toggle — mirror đúng UX thật, không thêm dropdown/select mới.</div>
            <div><strong>Không pagination:</strong> app hiện fetch <code>page_size=100</code> 1 lần, lọc/sort phía client, hiện banner tĩnh khi &gt;100 kết quả — giữ nguyên, không đề xuất pagination mới (nằm ngoài scope redesign thị giác).</div>
            <div><strong>`doc_type_group` KHÔNG có trong list API</strong> — chỉ có legacy <code>doc_type</code> (10 giá trị) — khác doc-detail (v4 dùng <code>doc_type_group</code> 11 giá trị). Đây là gap thật giữa 2 API, không phải Designer chọn sai — flag để biết, không phải quyết định cần Kevin ratify (đổi API ngoài scope 1 PR visual).</div>
            <div><strong>LifecycleBadge dùng lại đúng logic từ v4:</strong> cùng component, cùng câu hỏi Q1-ext — tránh 2 mockup trả lời khác nhau cho cùng 1 vấn đề màu success.</div>
            <div><strong>Không thuộc scope:</strong> mobile card view (`DocCard`, đã có pattern riêng, không đổi ở đây) · pagination mới · đổi API list trả `doc_type_group`.</div>
            <div><strong>Dependencies để Frontend áp dụng:</strong> Q1-ext cần Kevin chốt cùng lúc với Q1 gốc (3 component, 1 quyết định). Q-Status-Failed cần PM/Kevin xác nhận đây là bug cần fix trước khi Frontend đổi logic (không phải chỉ đổi màu). Q-CompletenessIcon chờ Backend #276. Q-Width cần Frontend sửa <code>AdminShell.tsx:21</code> sau khi có giá trị cụ thể.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
