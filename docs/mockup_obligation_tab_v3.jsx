/**
 * Servanda — Doc-detail · Tab "Nghĩa vụ & Quyền lợi" v3  (mockup_obligation_tab_v3.jsx)
 * KHE_Designer · issue #467 (parent #466) · DEC-055 brand refresh
 * STATIC PROTOTYPE — scope-lock docs/mockup_*.jsx. Not production code.
 * ----------------------------------------------------------------------------
 * REORG of the obligation tab within document detail page.
 * Replaces v2 flat list (#281) + obligation_v0.2 standalone page with 3-axis IA:
 *   AXIS 1 — Direction: Nghĩa vụ (bạn phải làm) / Quyền lợi (được hưởng)
 *   AXIS 2 — Temporal: Quá hạn → Tuần này → Sắp tới
 *   AXIS 3 — Series: collapse by milestone_series_id, progress X/Y
 *
 * Cross-direction sections (pulled OUT of direction groups):
 *   CHỜ KÍCH HOẠT — waiting_trigger + penalties (Q4)
 *   ĐÃ HOÀN THÀNH — collapsed by default
 *
 * KEY CHANGES (Q1–Q7 from #466 ratified):
 *   Q1: SelfPartyGate per-doc REMOVED → "Sửa pháp nhân trong Cài đặt" link
 *   Q2: Checkbox multi-select + action bar "Hoàn thành đã chọn (N)"
 *   Q3: Series collapse card with progress bar + next installment
 *   Q4: "Chờ kích hoạt" separate section (triggers + penalties)
 *   Q5: Amount: parse → currency; unparseable → hide (no raw text beside ₫)
 *   Q6: Tab doc-detail first; tenant dashboard "8am" = later step
 *   Q7: NO ICON/EMOJI — all status via text badge + color token (DEC-055)
 *
 * DESIGN TOKENS: DS v0.2 canonical (mockup_design_system_v0.2.jsx).
 * VOICE: "Servanda" brand (DEC-055 #465). Professional, no emoji.
 */
import React, { useState } from "react";

/* ===========================================================================
 * TOKENS — DS v0.2 canonical (mirrored for self-contained render)
 * Production: import { tokens as t } from "./mockup_design_system_v0.2.jsx"
 * ========================================================================= */
const neutral = {
  0: "#FFFFFF", 25: "#FBFCFD", 50: "#F6F8FA", 100: "#EDF1F5",
  200: "#E2E8F0", 300: "#CBD4E1", 400: "#94A3B8", 500: "#647488",
  600: "#4A5567", 700: "#333E4F", 800: "#1F2733", 900: "#0E141B",
};

const t = {
  color: {
    neutral,
    primary: "#0F7A56", primaryHover: "#0C6648", primarySoft: "#E8F4EF",
    primaryBorder: "#BFE0D1",
    success: "#15803D", success_soft: "#E9F6EE",
    warning: "#8A6300", warning_soft: "#FBF1DD",
    danger: "#B42318", danger_soft: "#FCEBEA",
    info: "#175CD3", info_soft: "#E9F1FD",
    ink: neutral[800], inkBody: neutral[700], inkMuted: neutral[500],
    inkSubtle: neutral[400],
    border: neutral[200], borderStrong: neutral[300],
    surface: neutral[0], surfaceAlt: neutral[25], surfaceSunken: neutral[50],
    ring: "rgba(15,122,86,0.32)",
  },
  font: {
    family: "'Inter', 'Be Vietnam Pro', system-ui, -apple-system, sans-serif",
    size: { xs: 12, sm: 13, base: 14, md: 16, lg: 18, xl: 20, "2xl": 24 },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
    lineHeight: { tight: 1.2, snug: 1.35, normal: 1.5, relaxed: 1.65 },
  },
  space: { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 7: 32, 8: 40 },
  radius: { xs: 4, sm: 6, md: 8, lg: 12, pill: 999 },
  elevation: {
    e1: "0 1px 2px rgba(14,20,27,0.06), 0 1px 1px rgba(14,20,27,0.04)",
    e2: "0 2px 6px -1px rgba(14,20,27,0.08), 0 1px 3px rgba(14,20,27,0.05)",
    e3: "0 16px 32px -12px rgba(14,20,27,0.18), 0 6px 12px -4px rgba(14,20,27,0.08)",
  },
  motion: { fast: "120ms", base: "180ms", ease: "cubic-bezier(0.2, 0, 0, 1)" },
  z: { base: 0, sticky: 100, toast: 1200 },
};

const TODAY = new Date("2026-07-02");

/* ===========================================================================
 * HELPERS
 * ========================================================================= */

function parseDate(s) {
  if (!s) return null;
  const [d, m, y] = s.split("/").map(Number);
  return new Date(y, m - 1, d);
}

function daysDiff(dateStr) {
  const d = parseDate(dateStr);
  if (!d) return null;
  return Math.round((d - TODAY) / 86400000);
}

function formatCurrency(raw) {
  if (!raw) return null;
  const cleaned = raw.replace(/[^\d.,]/g, "").replace(/\./g, "").replace(",", ".");
  const num = parseFloat(cleaned);
  if (isNaN(num) || num <= 0) return null;
  return num.toLocaleString("vi-VN") + " đ";
}

function temporalBucket(ob) {
  if (ob.status === "waiting_trigger") return "waiting";
  if (ob.status === "done") return "done";
  if (ob.status === "cancelled") return "done";
  if (!ob.due_date) return "upcoming";
  const days = daysDiff(ob.due_date);
  if (days < 0) return "overdue";
  if (days <= 7) return "this_week";
  return "upcoming";
}

function overdueLabel(dateStr) {
  const days = Math.abs(daysDiff(dateStr));
  if (days === 0) return "Hôm nay";
  if (days === 1) return "Quá hạn 1 ngày";
  return `Quá hạn ${days} ngày`;
}

function dueLabel(dateStr) {
  const days = daysDiff(dateStr);
  if (days === 0) return "Hôm nay";
  if (days === 1) return "Ngày mai";
  if (days <= 7) return `Còn ${days} ngày`;
  return dateStr;
}

/* ===========================================================================
 * SAMPLE DATA — HĐ mua bán căn hộ Sunrise Tower (exercises all states)
 * 14-installment payment series, overdue, upcoming, waiting trigger, penalties
 * ========================================================================= */
const OBLIGATIONS = [
  // --- NGHĨA VỤ: Payment series 14 installments (S1) ---
  { id: 1,  direction: "nghĩa_vụ", category: "payment",    status: "done",     due_date: "15/01/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 1, series_total: 14, desc: "Thanh toán đợt 1 — ký quỹ",            source_clause: "Điều 4.1" },
  { id: 2,  direction: "nghĩa_vụ", category: "payment",    status: "done",     due_date: "15/02/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 2, series_total: 14, desc: "Thanh toán đợt 2",                     source_clause: "Điều 4.1" },
  { id: 3,  direction: "nghĩa_vụ", category: "payment",    status: "done",     due_date: "15/03/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 3, series_total: 14, desc: "Thanh toán đợt 3",                     source_clause: "Điều 4.1" },
  { id: 4,  direction: "nghĩa_vụ", category: "payment",    status: "done",     due_date: "15/04/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 4, series_total: 14, desc: "Thanh toán đợt 4",                     source_clause: "Điều 4.1" },
  { id: 5,  direction: "nghĩa_vụ", category: "payment",    status: "done",     due_date: "15/05/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 5, series_total: 14, desc: "Thanh toán đợt 5",                     source_clause: "Điều 4.1" },
  { id: 6,  direction: "nghĩa_vụ", category: "payment",    status: "done",     due_date: "15/06/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 6, series_total: 14, desc: "Thanh toán đợt 6",                     source_clause: "Điều 4.1" },
  { id: 7,  direction: "nghĩa_vụ", category: "payment",    status: "pending",  due_date: "28/06/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 7, series_total: 14, desc: "Thanh toán đợt 7",                     source_clause: "Điều 4.1" },
  { id: 8,  direction: "nghĩa_vụ", category: "payment",    status: "pending",  due_date: "05/07/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 8, series_total: 14, desc: "Thanh toán đợt 8",                     source_clause: "Điều 4.1" },
  { id: 9,  direction: "nghĩa_vụ", category: "payment",    status: "pending",  due_date: "15/08/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 9, series_total: 14, desc: "Thanh toán đợt 9",                     source_clause: "Điều 4.1" },
  { id: 10, direction: "nghĩa_vụ", category: "payment",    status: "pending",  due_date: "15/09/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 10, series_total: 14, desc: "Thanh toán đợt 10",                   source_clause: "Điều 4.1" },
  { id: 11, direction: "nghĩa_vụ", category: "payment",    status: "pending",  due_date: "15/10/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 11, series_total: 14, desc: "Thanh toán đợt 11",                   source_clause: "Điều 4.1" },
  { id: 12, direction: "nghĩa_vụ", category: "payment",    status: "pending",  due_date: "15/11/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 12, series_total: 14, desc: "Thanh toán đợt 12",                   source_clause: "Điều 4.1" },
  { id: 13, direction: "nghĩa_vụ", category: "payment",    status: "pending",  due_date: "15/12/2026", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 13, series_total: 14, desc: "Thanh toán đợt 13",                   source_clause: "Điều 4.1" },
  { id: 14, direction: "nghĩa_vụ", category: "payment",    status: "pending",  due_date: "15/01/2027", amount_raw: "130000000",           obligor: "Bạn", series_id: "S1", series_idx: 14, series_total: 14, desc: "Thanh toán đợt cuối — tất toán",      source_clause: "Điều 4.1" },

  // --- NGHĨA VỤ: Standalone overdue ---
  { id: 15, direction: "nghĩa_vụ", category: "renewal",    status: "pending",  due_date: "25/06/2026", amount_raw: null,                  obligor: "Bạn", series_id: null, desc: "Thông báo gia hạn / chấm dứt (trước 30 ngày)",  source_clause: "Điều 12.1" },

  // --- NGHĨA VỤ: Upcoming standalone ---
  { id: 16, direction: "nghĩa_vụ", category: "compliance", status: "pending",  due_date: "31/07/2026", amount_raw: null,                  obligor: "Bạn", series_id: null, desc: "Nộp hồ sơ đăng ký quyền sử dụng",              source_clause: "Điều 7.3" },

  // --- NGHĨA VỤ: Recurring, no due_date ---
  { id: 17, direction: "nghĩa_vụ", category: "compliance", status: "pending",  due_date: null,         amount_raw: "2500000",             obligor: "Bạn", series_id: null, recurring: "hàng tháng", desc: "Phí quản lý tòa nhà",           source_clause: "Điều 8.2" },

  // --- QUYỀN LỢI: Partner delivers ---
  { id: 18, direction: "quyền_lợi", category: "delivery",  status: "pending",  due_date: "15/08/2026", amount_raw: null,                  obligor: "Cty CP BĐS Sunrise", series_id: null, desc: "Bàn giao căn hộ hoàn thiện",     source_clause: "Điều 5.2" },
  { id: 19, direction: "quyền_lợi", category: "warranty",  status: "pending",  due_date: null,         amount_raw: null,                  obligor: "Cty CP BĐS Sunrise", series_id: null, desc: "Bảo hành kết cấu 5 năm kể từ bàn giao",       source_clause: "Điều 6.1" },
  { id: 20, direction: "quyền_lợi", category: "delivery",  status: "done",     due_date: "01/03/2026", amount_raw: null,                  obligor: "Cty CP BĐS Sunrise", series_id: null, desc: "Cung cấp bản vẽ thiết kế căn hộ",              source_clause: "Điều 5.1" },

  // --- CHỜ KÍCH HOẠT: Trigger-based ---
  { id: 21, direction: "nghĩa_vụ", category: "payment",    status: "waiting_trigger", due_date: null, amount_raw: "91000000",             obligor: "Bạn", series_id: null, trigger_condition: "nghiệm thu hoàn thành", trigger_deadline: "trong 30 ngày", desc: "Thanh toán 5% sau nghiệm thu",  source_clause: "Điều 4.3" },

  // --- CHỜ KÍCH HOẠT: Penalty ---
  { id: 22, direction: "nghĩa_vụ", category: "penalty",    status: "waiting_trigger", due_date: null, amount_raw: "theo thực tế phát sinh", obligor: "Bạn", series_id: null, trigger_condition: "chậm thanh toán", is_penalty: true, desc: "Phạt chậm thanh toán — lãi 8%/năm trên số chậm", source_clause: "Điều 9.1" },
  { id: 23, direction: "quyền_lợi", category: "penalty",   status: "waiting_trigger", due_date: null, amount_raw: "theo thực tế phát sinh", obligor: "Cty CP BĐS Sunrise", series_id: null, trigger_condition: "chậm bàn giao", is_penalty: true, desc: "Phạt chậm bàn giao — 0.05%/ngày trên giá trị HĐ", source_clause: "Điều 9.2" },

  // --- DIRECTION NULL: Needs legal_name ---
  { id: 24, direction: null, category: "payment",  status: "pending",  due_date: "20/08/2026", amount_raw: "50000000",            obligor: "Bên A", series_id: null, desc: "Thanh toán phí hợp tác",                        source_clause: "Điều 3.1" },
  { id: 25, direction: null, category: "delivery", status: "pending",  due_date: "30/08/2026", amount_raw: null,                  obligor: "Bên B", series_id: null, desc: "Bàn giao hạng mục 1",                           source_clause: "Điều 5.1" },
];

// Category labels — TEXT ONLY, no icon (Q7/DEC-055)
const CATEGORY_LABELS = {
  payment: "Thanh toán", delivery: "Giao hàng/Bàn giao", renewal: "Gia hạn",
  compliance: "Tuân thủ", warranty: "Bảo hành", penalty: "Phạt", other: "Khác",
};

/* ===========================================================================
 * ATOMS — text+color badges only (Q7: NO ICON/EMOJI)
 * ========================================================================= */

function TextBadge({ children, bg, fg, border }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold,
      color: fg || t.color.inkMuted,
      background: bg || t.color.surfaceSunken,
      border: border ? `1px solid ${border}` : "none",
      padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill,
      fontFamily: t.font.family, lineHeight: t.font.lineHeight.snug,
      whiteSpace: "nowrap",
    }}>{children}</span>
  );
}

function OverdueBadge({ dateStr }) {
  return <TextBadge bg={t.color.danger_soft} fg={t.color.danger}>{overdueLabel(dateStr)}</TextBadge>;
}

function StatusBadge({ status }) {
  const MAP = {
    done:       { label: "Hoàn thành",     bg: t.color.success_soft, fg: t.color.success },
    pending:    { label: "Chưa làm",       bg: t.color.surfaceSunken, fg: t.color.inkMuted },
    in_progress:{ label: "Đang làm",       bg: t.color.info_soft,    fg: t.color.info },
    cancelled:  { label: "Đã hủy",         bg: t.color.surfaceSunken, fg: t.color.inkSubtle },
    waiting_trigger: { label: "Chờ kích hoạt", bg: t.color.warning_soft, fg: t.color.warning },
  };
  const s = MAP[status] || MAP.pending;
  return <TextBadge bg={s.bg} fg={s.fg}>{s.label}</TextBadge>;
}

function CategoryChip({ category }) {
  const label = CATEGORY_LABELS[category] || CATEGORY_LABELS.other;
  return <TextBadge>{label}</TextBadge>;
}

function AmountDisplay({ raw }) {
  const formatted = formatCurrency(raw);
  if (!formatted) return null;
  return <TextBadge bg={t.color.success_soft} fg={t.color.success}>{formatted}</TextBadge>;
}

function SourceClauseLink({ clause }) {
  if (!clause) return null;
  // Q7: no icon glyph — link affordance carried by color + underline-on-hover only.
  return (
    <button style={{
      border: "none", background: "transparent", color: t.color.primary,
      fontSize: t.font.size.xs, fontWeight: t.font.weight.medium,
      cursor: "pointer", fontFamily: t.font.family, padding: 0,
      textDecoration: "underline",
    }}
      title={`Nhảy đến ${clause} trong tab Nội dung hợp đồng`}
    >
      {clause}
    </button>
  );
}

/* ===========================================================================
 * CHECKBOX + ACTION BAR (Q2: multi-select)
 * ========================================================================= */

function ObligationCheckbox({ checked, onChange, disabled }) {
  return (
    <button
      role="checkbox"
      aria-checked={checked}
      disabled={disabled}
      onClick={(e) => { e.stopPropagation(); onChange(!checked); }}
      style={{
        width: 18, height: 18, borderRadius: t.radius.xs, flexShrink: 0,
        border: checked ? `2px solid ${t.color.primary}` : `2px solid ${t.color.borderStrong}`,
        background: checked ? t.color.primary : t.color.surface,
        cursor: disabled ? "not-allowed" : "pointer",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 0, opacity: disabled ? 0.4 : 1,
      }}
    >
      {checked && <span style={{ color: "#fff", fontSize: 11, fontWeight: t.font.weight.bold, lineHeight: 1 }}>&#x2713;</span>}
    </button>
  );
}

function ActionBar({ count, onComplete, onCancel }) {
  if (count === 0) return null;
  return (
    <div style={{
      position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)",
      background: t.color.ink, color: t.color.surface, borderRadius: t.radius.lg,
      padding: `${t.space[3]}px ${t.space[5]}px`,
      display: "flex", alignItems: "center", gap: t.space[4],
      boxShadow: t.elevation.e3, zIndex: t.z.toast, fontFamily: t.font.family,
      minWidth: 320,
    }}>
      <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.medium }}>
        {count} mục đã chọn
      </span>
      <div style={{ flex: 1 }} />
      <button onClick={onComplete} style={{
        border: "none", background: t.color.primary, color: "#fff",
        padding: `${t.space[2]}px ${t.space[4]}px`, borderRadius: t.radius.md,
        fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold,
        cursor: "pointer", fontFamily: t.font.family,
      }}>
        Hoàn thành đã chọn ({count})
      </button>
      <button onClick={onCancel} style={{
        border: `1px solid ${t.color.neutral[600]}`, background: "transparent",
        color: t.color.neutral[300], padding: `${t.space[2]}px ${t.space[3]}px`,
        borderRadius: t.radius.md, fontSize: t.font.size.sm, cursor: "pointer",
        fontFamily: t.font.family,
      }}>
        Bỏ chọn
      </button>
    </div>
  );
}

/* ===========================================================================
 * OBLIGATION ROW — single item with checkbox
 * ========================================================================= */

function ObligationRow({ ob, checked, onCheck, onAction, dim }) {
  const isDone = ob.status === "done" || ob.status === "cancelled";
  const isOverdue = temporalBucket(ob) === "overdue";
  const canCheck = !isDone && ob.status !== "waiting_trigger";
  const amount = formatCurrency(ob.amount_raw);

  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: t.space[3],
      padding: `${t.space[3]}px ${t.space[4]}px`,
      borderBottom: `1px solid ${t.color.border}`,
      opacity: dim || isDone ? 0.55 : 1,
      background: checked ? t.color.primarySoft + "44" : "transparent",
    }}>
      {/* Checkbox */}
      <div style={{ paddingTop: 2 }}>
        <ObligationCheckbox checked={checked} onChange={onCheck} disabled={!canCheck} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
          <span style={{
            fontSize: t.font.size.base, fontWeight: t.font.weight.medium, color: t.color.ink,
            textDecoration: isDone ? "line-through" : "none",
          }}>{ob.desc}</span>
          {isOverdue && <OverdueBadge dateStr={ob.due_date} />}
          {isDone && <StatusBadge status={ob.status} />}
        </div>

        {/* Chip row */}
        <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[1], alignItems: "center" }}>
          <CategoryChip category={ob.category} />
          {ob.due_date && !isOverdue && !isDone && (
            <TextBadge>{dueLabel(ob.due_date)}</TextBadge>
          )}
          {!ob.due_date && ob.recurring && (
            <TextBadge>{ob.recurring}</TextBadge>
          )}
          {!ob.due_date && !ob.recurring && ob.status !== "waiting_trigger" && (
            <TextBadge>Không thời hạn</TextBadge>
          )}
          {amount && <AmountDisplay raw={ob.amount_raw} />}
          <SourceClauseLink clause={ob.source_clause} />
        </div>
      </div>

      {/* Actions */}
      {!isDone && ob.status !== "waiting_trigger" && (
        <div style={{ flexShrink: 0, display: "flex", gap: t.space[1] }}>
          <button onClick={() => onAction("done", ob)} style={{
            border: `1px solid ${t.color.borderStrong}`, background: t.color.surface,
            color: t.color.inkBody, padding: `${t.space[1]}px ${t.space[3]}px`,
            borderRadius: t.radius.md, fontSize: t.font.size.xs,
            fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family,
          }}>
            Hoàn thành
          </button>
        </div>
      )}
    </div>
  );
}

/* ===========================================================================
 * SERIES CARD — collapsible, progress bar, next installment (Q3)
 * ========================================================================= */

function SeriesCard({ items, selected, onCheck, onAction }) {
  const [expanded, setExpanded] = useState(false);
  const total = items[0].series_total;
  const doneCount = items.filter((o) => o.status === "done").length;
  const pct = Math.round((doneCount / total) * 100);

  const sorted = [...items].sort((a, b) => a.series_idx - b.series_idx);
  const nextItem = sorted.find((o) => o.status !== "done" && o.status !== "cancelled");

  const nextOverdue = nextItem && temporalBucket(nextItem) === "overdue";
  const nextAmount = nextItem ? formatCurrency(nextItem.amount_raw) : null;

  return (
    <div style={{
      border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg,
      marginBottom: t.space[3], overflow: "hidden",
    }}>
      {/* Header — always visible */}
      <button onClick={() => setExpanded(!expanded)} style={{
        width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: `${t.space[3]}px ${t.space[4]}px`,
        background: t.color.surfaceAlt, border: "none", cursor: "pointer",
        fontFamily: t.font.family, textAlign: "left", gap: t.space[3],
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
            <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
              {CATEGORY_LABELS[items[0].category] || "Khác"}
            </span>
            <TextBadge bg={t.color.primarySoft} fg={t.color.primary}>
              {doneCount}/{total} hoàn thành
            </TextBadge>
            {nextOverdue && <TextBadge bg={t.color.danger_soft} fg={t.color.danger}>Có đợt quá hạn</TextBadge>}
          </div>

          {/* Progress bar */}
          <div style={{
            marginTop: t.space[2], height: 4, borderRadius: 2,
            background: t.color.neutral[100], overflow: "hidden", maxWidth: 200,
          }}>
            <div style={{
              height: "100%", borderRadius: 2,
              width: `${pct}%`,
              background: nextOverdue ? t.color.danger : t.color.primary,
              transition: `width ${t.motion.base} ${t.motion.ease}`,
            }} />
          </div>

          {/* Next installment preview */}
          {nextItem && (
            <div style={{ marginTop: t.space[2], fontSize: t.font.size.sm, color: t.color.inkMuted }}>
              Kế tiếp: Đợt {nextItem.series_idx} — {nextItem.due_date || "chưa có hạn"}
              {nextAmount && <span style={{ color: t.color.success, fontWeight: t.font.weight.medium }}> · {nextAmount}</span>}
            </div>
          )}
        </div>

        <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, flexShrink: 0 }}>
          {expanded ? "Thu gọn" : "Xem chi tiết"}
        </span>
      </button>

      {/* Expanded: individual rows */}
      {expanded && (
        <div>
          {sorted.map((ob) => (
            <ObligationRow
              key={ob.id} ob={ob}
              checked={selected.has(ob.id)}
              onCheck={(v) => onCheck(ob.id, v)}
              onAction={onAction}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ===========================================================================
 * WAITING TRIGGER SECTION (Q4: separate from today's work)
 * ========================================================================= */

function WaitingTriggerRow({ ob }) {
  const amount = formatCurrency(ob.amount_raw);
  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: t.space[3],
      padding: `${t.space[3]}px ${t.space[4]}px`,
      borderBottom: `1px solid ${t.color.border}`,
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
          <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.medium, color: t.color.ink }}>
            {ob.desc}
          </span>
          {ob.is_penalty && <TextBadge bg={t.color.danger_soft} fg={t.color.danger}>Phạt</TextBadge>}
        </div>
        <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
          Nếu "{ob.trigger_condition}"
          {ob.trigger_deadline && <span> — {ob.trigger_deadline}</span>}
        </div>
        <div style={{ display: "flex", gap: t.space[2], marginTop: t.space[1], alignItems: "center" }}>
          <CategoryChip category={ob.category} />
          {amount && <AmountDisplay raw={ob.amount_raw} />}
          {ob.obligor && <TextBadge>{ob.obligor}</TextBadge>}
          <SourceClauseLink clause={ob.source_clause} />
        </div>
      </div>

      <button style={{
        border: `1px solid ${t.color.borderStrong}`, background: t.color.surface,
        color: t.color.inkBody, padding: `${t.space[1]}px ${t.space[3]}px`,
        borderRadius: t.radius.md, fontSize: t.font.size.xs,
        fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family,
      }}>
        Sự kiện đã xảy ra
      </button>
    </div>
  );
}

/* ===========================================================================
 * SETTINGS NUDGE — replaces SelfPartyGate (Q1)
 * ========================================================================= */

function SettingsNudge() {
  return (
    <div style={{
      padding: `${t.space[3]}px ${t.space[4]}px`, borderRadius: t.radius.md,
      background: t.color.warning_soft, border: `1px solid ${t.color.warning}33`,
      marginBottom: t.space[4], display: "flex", alignItems: "center",
      justifyContent: "space-between", gap: t.space[3], flexWrap: "wrap",
    }}>
      <div>
        <div style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
          Chưa xác định được chiều nghĩa vụ
        </div>
        <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>
          Servanda cần biết tên pháp nhân của bạn để tự phân biệt nghĩa vụ và quyền lợi.
        </div>
      </div>
      <button style={{
        border: `1px solid ${t.color.borderStrong}`, background: t.color.surface,
        color: t.color.primary, padding: `${t.space[2]}px ${t.space[4]}px`,
        borderRadius: t.radius.md, fontSize: t.font.size.sm,
        fontWeight: t.font.weight.semibold, cursor: "pointer", fontFamily: t.font.family,
      }}>
        Sửa pháp nhân trong Cài đặt
      </button>
    </div>
  );
}

/* ===========================================================================
 * SECTION HEADER
 * ========================================================================= */

function SectionHeader({ title, subtitle, count, tone, collapsed, onToggle }) {
  return (
    <button onClick={onToggle} style={{
      width: "100%", display: "flex", alignItems: "center", gap: t.space[2],
      padding: `${t.space[3]}px 0`, border: "none", background: "transparent",
      cursor: onToggle ? "pointer" : "default", fontFamily: t.font.family, textAlign: "left",
    }}>
      {tone && <span style={{ width: 8, height: 8, borderRadius: "50%", background: tone, flexShrink: 0 }} />}
      <span style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
        {title}
      </span>
      {count !== undefined && (
        <TextBadge bg={tone ? tone + "18" : t.color.surfaceSunken} fg={tone || t.color.inkMuted}>
          {count}
        </TextBadge>
      )}
      {subtitle && (
        <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontWeight: t.font.weight.regular }}>
          {subtitle}
        </span>
      )}
      {onToggle && (
        <span style={{ marginLeft: "auto", fontSize: t.font.size.sm, color: t.color.inkMuted }}>
          {collapsed ? "Mở rộng" : "Thu gọn"}
        </span>
      )}
    </button>
  );
}

/* ===========================================================================
 * TEMPORAL BUCKET HEADER
 * ========================================================================= */

function BucketHeader({ bucket, count }) {
  const MAP = {
    overdue:   { label: "Quá hạn",    tone: t.color.danger },
    this_week: { label: "Tuần này",   tone: t.color.warning },
    upcoming:  { label: "Sắp tới",    tone: t.color.info },
  };
  const b = MAP[bucket];
  if (!b || count === 0) return null;
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: t.space[2],
      padding: `${t.space[2]}px ${t.space[4]}px`,
      borderBottom: `1px solid ${t.color.border}`,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: b.tone }} />
      <span style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: b.tone }}>
        {b.label}
      </span>
      <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>{count}</span>
    </div>
  );
}

/* ===========================================================================
 * MAIN TAB COMPONENT
 * ========================================================================= */

function ObligationTabV3({ obligations, hasLegalName }) {
  const [selected, setSelected] = useState(new Set());
  const [showDone, setShowDone] = useState(false);
  const [showWaiting, setShowWaiting] = useState(true);
  const [showNull, setShowNull] = useState(true);
  const [toast, setToast] = useState(null);

  const toggleCheck = (id, val) => {
    setSelected((prev) => {
      const next = new Set(prev);
      val ? next.add(id) : next.delete(id);
      return next;
    });
  };

  const handleAction = (action, ob) => {
    if (action === "done") setToast(`"${ob.desc}" — hoàn thành. Event ghi nhận.`);
    setTimeout(() => setToast(null), 3000);
  };

  const handleBulkComplete = () => {
    setToast(`${selected.size} mục đã đánh dấu hoàn thành. Event ghi nhận.`);
    setSelected(new Set());
    setTimeout(() => setToast(null), 3000);
  };

  // Partition
  const nghiaVu = obligations.filter((o) => o.direction === "nghĩa_vụ" && o.status !== "waiting_trigger" && o.status !== "done" && o.status !== "cancelled");
  const quyenLoi = obligations.filter((o) => o.direction === "quyền_lợi" && o.status !== "waiting_trigger" && o.status !== "done" && o.status !== "cancelled");
  const waiting = obligations.filter((o) => o.status === "waiting_trigger");
  const done = obligations.filter((o) => o.status === "done" || o.status === "cancelled");
  const nullDir = obligations.filter((o) => o.direction === null && o.status !== "waiting_trigger" && o.status !== "done" && o.status !== "cancelled");

  // Within each direction: classify series ONCE by its next actionable item's
  // temporal bucket (not once per bucket its members happen to touch — a
  // 14-installment series has members in 3 different buckets; the card must
  // render exactly once, positioned by urgency of the next unpaid installment).
  function renderDirectionSection(items, title, subtitle) {
    if (items.length === 0) return null;

    const buckets = ["overdue", "this_week", "upcoming"];
    const seriesIds = [...new Set(items.filter((o) => o.series_id).map((o) => o.series_id))];
    const standaloneItems = items.filter((o) => !o.series_id);

    const seriesByBucket = { overdue: [], this_week: [], upcoming: [] };
    seriesIds.forEach((sid) => {
      const allSeriesItems = obligations.filter((o) => o.series_id === sid);
      const sorted = [...allSeriesItems].sort((a, b) => a.series_idx - b.series_idx);
      const next = sorted.find((o) => o.status !== "done" && o.status !== "cancelled");
      const bucket = next ? temporalBucket(next) : "upcoming";
      seriesByBucket[buckets.includes(bucket) ? bucket : "upcoming"].push(sid);
    });

    const standaloneByBucket = {};
    buckets.forEach((b) => { standaloneByBucket[b] = standaloneItems.filter((o) => temporalBucket(o) === b); });

    return (
      <div style={{ marginBottom: t.space[6] }}>
        <SectionHeader title={title} subtitle={subtitle} count={items.length} />
        <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
          {buckets.map((bk) => {
            const seriesInBucket = seriesByBucket[bk];
            const standalone = standaloneByBucket[bk];
            const visibleCount = seriesInBucket.length + standalone.length;
            if (visibleCount === 0) return null;

            return (
              <div key={bk}>
                <BucketHeader bucket={bk} count={visibleCount} />
                {/* Series cards — each series renders exactly once */}
                {seriesInBucket.map((sid) => (
                  <div key={sid} style={{ padding: `${t.space[2]}px ${t.space[3]}px` }}>
                    <SeriesCard
                      items={obligations.filter((o) => o.series_id === sid)}
                      selected={selected}
                      onCheck={toggleCheck}
                      onAction={handleAction}
                    />
                  </div>
                ))}
                {/* Standalone rows */}
                {standalone.map((ob) => (
                  <ObligationRow
                    key={ob.id} ob={ob}
                    checked={selected.has(ob.id)}
                    onCheck={(v) => toggleCheck(ob.id, v)}
                    onAction={handleAction}
                  />
                ))}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: t.font.family }}>

      {/* Q1: Direction NULL — Settings nudge */}
      {nullDir.length > 0 && (
        <div style={{ marginBottom: t.space[5] }}>
          <SettingsNudge />
          <SectionHeader
            title="Cần xác nhận chiều"
            count={nullDir.length}
            tone={t.color.warning}
            collapsed={!showNull}
            onToggle={() => setShowNull(!showNull)}
          />
          {showNull && (
            <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
              {nullDir.map((ob) => (
                <ObligationRow
                  key={ob.id} ob={ob}
                  checked={selected.has(ob.id)}
                  onCheck={(v) => toggleCheck(ob.id, v)}
                  onAction={handleAction}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Direction sections */}
      {renderDirectionSection(nghiaVu, "Nghĩa vụ của bạn", "phải làm")}
      {renderDirectionSection(quyenLoi, "Quyền lợi của bạn", "được hưởng")}

      {/* Q4: Chờ kích hoạt — separate section */}
      {waiting.length > 0 && (
        <div style={{ marginBottom: t.space[6] }}>
          <SectionHeader
            title="Chờ kích hoạt"
            subtitle="khi điều kiện xảy ra"
            count={waiting.length}
            tone={t.color.warning}
            collapsed={!showWaiting}
            onToggle={() => setShowWaiting(!showWaiting)}
          />
          {showWaiting && (
            <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
              {waiting.map((ob) => (
                <WaitingTriggerRow key={ob.id} ob={ob} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Đã hoàn thành — collapsed by default */}
      {done.length > 0 && (
        <div style={{ marginBottom: t.space[6] }}>
          <SectionHeader
            title="Đã hoàn thành"
            count={done.length}
            tone={t.color.success}
            collapsed={!showDone}
            onToggle={() => setShowDone(!showDone)}
          />
          {showDone && (
            <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, overflow: "hidden" }}>
              {done.map((ob) => (
                <ObligationRow
                  key={ob.id} ob={ob}
                  checked={false}
                  onCheck={() => {}}
                  onAction={handleAction}
                  dim
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Q2: Floating action bar */}
      <ActionBar count={selected.size} onComplete={handleBulkComplete} onCancel={() => setSelected(new Set())} />

      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed", bottom: selected.size > 0 ? t.space[8] + 56 : t.space[6],
          left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast + 1,
          background: t.color.success, color: "#fff", padding: `${t.space[3]}px ${t.space[5]}px`,
          borderRadius: t.radius.lg, fontFamily: t.font.family, fontSize: t.font.size.sm,
          fontWeight: t.font.weight.medium, boxShadow: t.elevation.e2,
        }}>
          {toast}
        </div>
      )}
    </div>
  );
}

/* ===========================================================================
 * SHOWCASE — full page wrapper (for preview / Kevin review)
 * ========================================================================= */

export default function Showcase() {
  const [hasLegalName, setHasLegalName] = useState(true);

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family }}>
      <div style={{ maxWidth: 900, margin: "0 auto", padding: t.space[6] }}>

        {/* Page context */}
        <div style={{ marginBottom: t.space[5] }}>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: t.font.size.xs * 0.04, fontWeight: t.font.weight.semibold }}>
            Chi tiết hợp đồng — Tab 2
          </div>
          <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: `${t.space[1]}px 0 0` }}>
            Nghĩa vụ & Quyền lợi
          </h1>
          <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
            HĐ mua bán căn hộ Sunrise Tower — Cty CP BĐS Sunrise
          </p>
        </div>

        {/* Toggle: simulate legal_name set vs unset */}
        <div style={{
          display: "flex", gap: t.space[3], marginBottom: t.space[5],
          padding: `${t.space[2]}px ${t.space[3]}px`,
          background: t.color.surfaceSunken, borderRadius: t.radius.md,
          fontSize: t.font.size.xs, color: t.color.inkMuted, alignItems: "center",
        }}>
          <span style={{ fontWeight: t.font.weight.semibold }}>Preview controls:</span>
          <label style={{ display: "flex", alignItems: "center", gap: t.space[1], cursor: "pointer" }}>
            <input type="checkbox" checked={hasLegalName} onChange={(e) => setHasLegalName(e.target.checked)} />
            legal_name đã set (direction auto-derived)
          </label>
        </div>

        {/* The tab */}
        <div style={{ background: t.color.surface, borderRadius: t.radius.lg, padding: t.space[5], boxShadow: t.elevation.e1 }}>
          <ObligationTabV3
            obligations={hasLegalName ? OBLIGATIONS.filter((o) => o.direction !== null) : OBLIGATIONS}
            hasLegalName={hasLegalName}
          />
        </div>

        {/* Designer annotations */}
        <div style={{
          marginTop: t.space[7], padding: t.space[5], borderRadius: t.radius.lg,
          border: `2px dashed ${t.color.borderStrong}`, background: t.color.surfaceAlt,
        }}>
          <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.bold, color: t.color.ink, marginBottom: t.space[4] }}>
            Designer Notes — #467 (parent #466)
          </div>

          <div style={{ fontSize: t.font.size.sm, color: t.color.inkBody, lineHeight: t.font.lineHeight.relaxed, display: "flex", flexDirection: "column", gap: t.space[4] }}>
            <div><strong>Q1 — Self-party cleanup:</strong> SelfPartyGate per-doc dropdown REMOVED. When direction=NULL (auto-map failed because legal_name not set or alias miss), shows SettingsNudge banner: "Sửa pháp nhân trong Cài đặt" button. Per-tenant, not per-doc (#238 ratified). Backend investigates separately why auto-map failed for specific tenants (alias gap in _self_party_strings).</div>

            <div><strong>Q2 — Multi-select:</strong> Checkbox on every actionable row (not done/cancelled, not waiting_trigger). Selected count shown in floating ActionBar with "Hoàn thành đã chọn (N)" primary CTA + "Bỏ chọn" secondary. Bulk = POST array of obligation IDs (needs new bulk PATCH endpoint — Dev scope, not Designer). Each completion logs Event (FR-OB-04).</div>

            <div><strong>Q3 — Series collapse:</strong> Obligations sharing milestone_series_id render as SeriesCard. Header: category + "X/Y hoàn thành" badge + progress bar. "Kế tiếp: Đợt N — date · amount" preview. Click expands to show all installments as standard ObligationRows (with checkboxes). 14-installment payment series collapses to 1 card instead of 14 rows (solves #466 pain point 3). Progress bar turns red when next installment is overdue.</div>

            <div><strong>Q4 — Chờ kích hoạt:</strong> Separate section pulled OUT of direction groups. Contains waiting_trigger obligations + penalties. Each row shows: trigger condition ("Nếu ..."), deadline if any, penalty badge (danger), "Sự kiện đã xảy ra" CTA. Penalties tagged with red "Phạt" badge. Collapsible section. Solves mixing triggers into "việc cần làm hôm nay".</div>

            <div><strong>Q5 — Amount rule:</strong> formatCurrency() parses raw amount → "130.000.000 đ" locale format. Unparseable amounts ("theo thực tế phát sinh") → hidden from chips, not displayed as raw text beside currency symbol. Only valid numbers get the success-tinted AmountDisplay badge.</div>

            <div><strong>Q7 — No icon/emoji:</strong> ZERO emoji in this mockup. All status conveyed via TextBadge (text + color token). Categories: plain text chip. Overdue: "Quá hạn N ngày" danger badge. Done: "Hoàn thành" success badge. Waiting: "Chờ kích hoạt" warning badge. Penalty: "Phạt" danger badge. Progress: bar + "X/Y hoàn thành" text. Checkbox checkmark is CSS &#x2713; glyph inside styled button, not emoji. Applies to ALL status surfaces — if other screens in brand refresh still use emoji (SelfPartyGate, CompletenessBanner, obligation v0.2 CATEGORY icons), they need the same treatment.</div>

            <div><strong>DEC-055 voice:</strong> "Servanda" brand name used in SettingsNudge copy. Professional tone. No playful emoji. Color rationed to functional status only (danger=overdue/penalty, warning=attention/trigger, success=done/amount, info=upcoming, primary=action/series).</div>

            <div><strong>IA structure:</strong> Cần xác nhận (NULL, top if present) → Nghĩa vụ của bạn → Quyền lợi của bạn → Chờ kích hoạt → Đã hoàn thành (collapsed). Within direction: Quá hạn → Tuần này → Sắp tới. Series cards within temporal buckets. This 3-axis layout (Direction × Temporal × Series) replaces the flat list.</div>

            <div><strong>Screens flagged for icon cleanup (Q7 system-wide):</strong> mockup_admin_obligation_v0.2.jsx (CATEGORY emoji 💵📦🔁📋, milestone icons ✅🔄⬜, chip icons ⏳📅🔁📄), mockup_document_detail_v2.jsx (DirectionBadge if using emoji), any other screen with ad-hoc emoji in JSX. All should migrate to TextBadge pattern from this mockup.</div>

            <div><strong>Out of scope:</strong> Tenant-level dashboard "8am" (Q6 — later step, reuses this tab's UI language). Clause tree / tab "Nội dung hợp đồng" (unchanged). Bulk PATCH endpoint (Dev scope). Backend auto-map alias investigation (separate issue).</div>

            <div><strong>Dependencies:</strong> Bulk PATCH endpoint (new, Backend). Settings page legal_name field (exists in mockup_admin_settings_v0.1.jsx). direction auto-derive (directions.py exists, #238). Series grouping (milestone_series_id exists in schema). source_clause_num → tab 4 jump (data exists from #303).</div>
          </div>
        </div>
      </div>
    </div>
  );
}
