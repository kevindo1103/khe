/**
 * Khế — Admin · Obligations v0.2  (mockup_admin_obligation_v0.2.jsx)
 * KHE_Designer · DEC-030 revamp · gates FE #157 (#146b) · supersedes v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * WHY v0.2: v0.1 was a flat list bucketed only by due_date. BA 2026-06-20
 * (DEC-019..022 + DEC-030) introduces two nested axes + milestone series +
 * trigger-based ("vô thời hạn") obligations. This mockup is the design
 * reference for #157 (Obligations.tsx rewrite) + the "Cần xác nhận" tab CTA
 * that links to self-party confirm (#158, see mockup_admin_self_party_confirm).
 *
 * AXIS 1 — direction tabs (DEC-030):
 *   Nghĩa vụ (direction='nghĩa_vụ', bạn phải làm)
 *   Quyền lợi (direction='quyền_lợi', đối tác phải làm cho bạn)
 *   Cần xác nhận (direction=null → user chưa khai self-party; D-02)
 *
 * AXIS 2 — due-date bucket, with the #157 ordering FIX:
 *   1. status==='waiting_trigger' → bucket 'waiting'  (NO date shown)
 *   2. !due_date                  → bucket 'open_ended' (T4 "vô thời hạn", DEC-020)
 *   3. else classifyDueDate()     → overdue / due_soon / upcoming
 *   (v0.1 bug: null due_date fell into 'upcoming'. Now null ≠ soon.)
 *
 * SERIES (DEC-021): obligations sharing milestone_series_id render under one
 *   collapsible header with progress; standalone (series_id=null) render flat.
 *
 * D-rules: D-02 (direction is user-confirmed, never auto → "Cần xác nhận" tab),
 *          FR-OB-04 (status change → Event), D-08 (no fabricated dates for triggers).
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge, Toast, EmptyState } from "./mockup_design_system_v0.2.jsx";

/* ---- category label map (obligation_type) ---- */
const CATEGORY = {
  payment:    { label: "Thanh toán", icon: "💵" },
  delivery:   { label: "Giao hàng",  icon: "📦" },
  renewal:    { label: "Gia hạn",    icon: "🔁" },
  compliance: { label: "Tuân thủ",   icon: "📋" },
  other:      { label: "Khác",       icon: "•" },
};

/* ---- seed obligations (covers every branch) ---- */
const SEED = [
  // direction = nghĩa_vụ — a payment SERIES of 3 milestones
  { id: 1, doc: "HĐ thuê mặt bằng Q7", direction: "nghĩa_vụ", category: "payment", status: "done",            due: "01/06/2026", amount: "30% · 13.500.000đ", obligor: "Bạn", series: "S1", idx: 1, total: 3, desc: "Đặt cọc thuê" },
  { id: 2, doc: "HĐ thuê mặt bằng Q7", direction: "nghĩa_vụ", category: "payment", status: "in_progress",     due: "15/08/2026", amount: "40% · 18.000.000đ", obligor: "Bạn", series: "S1", idx: 2, total: 3, desc: "Thanh toán đợt 2" },
  { id: 3, doc: "HĐ thuê mặt bằng Q7", direction: "nghĩa_vụ", category: "payment", status: "pending",         due: "15/09/2026", amount: "30% · 13.500.000đ", obligor: "Bạn", series: "S1", idx: 3, total: 3, desc: "Thanh toán đợt cuối" },
  // direction = nghĩa_vụ — standalone, OVERDUE
  { id: 4, doc: "HĐ cung cấp bao bì", direction: "nghĩa_vụ", category: "renewal", status: "pending",          due: "01/07/2026", amount: null, obligor: "Bạn", series: null, desc: "Gia hạn/chấm dứt (báo trước 30 ngày)" },
  // direction = nghĩa_vụ — OPEN-ENDED (T4 vô thời hạn, DEC-020) recurring compliance
  { id: 5, doc: "HĐ lao động — N.V.An", direction: "nghĩa_vụ", category: "compliance", status: "pending",     due: null, amount: null, obligor: "Bạn", series: null, recurring: "hàng tháng", desc: "Đóng BHXH nhân viên" },

  // direction = quyền_lợi — partner must deliver to you, WAITING on a trigger
  { id: 6, doc: "HĐ cung cấp bao bì", direction: "quyền_lợi", category: "delivery", status: "waiting_trigger", trigger: "kể từ khi bên bán ký biên bản nghiệm thu", amount: null, obligor: "Cty CP Bao Bì Việt", series: null, desc: "Giao lô hàng đợt 1" },
  // direction = quyền_lợi — partner payment due soon
  { id: 7, doc: "HĐ dịch vụ marketing", direction: "quyền_lợi", category: "delivery", status: "pending",      due: "10/07/2026", amount: null, obligor: "Agency XYZ", series: null, desc: "Bàn giao báo cáo chiến dịch" },

  // direction = null — NEEDS self-party confirm (D-02)
  { id: 8, doc: "HĐ hợp tác ABC-XYZ", direction: null, category: "payment", status: "pending",                due: "20/08/2026", amount: "50.000.000đ", obligor: "Bên A", series: null, desc: "Thanh toán phí hợp tác" },
  { id: 9, doc: "HĐ hợp tác ABC-XYZ", direction: null, category: "delivery", status: "pending",               due: "30/08/2026", amount: null, obligor: "Bên B", series: null, desc: "Bàn giao hạng mục 1" },
];

const TABS = [
  { key: "nghĩa_vụ", label: "Nghĩa vụ", hint: "Bạn phải làm" },
  { key: "quyền_lợi", label: "Quyền lợi", hint: "Đối tác phải làm cho bạn" },
  { key: "null", label: "Cần xác nhận", hint: "Chưa biết bên nào là bạn" },
];

const BUCKETS = [
  { key: "overdue",    label: "Quá hạn",            tone: t.color.danger },
  { key: "due_soon",   label: "Sắp tới hạn (≤30 ngày)", tone: t.color.warning },
  { key: "upcoming",   label: "Sắp tới",            tone: t.color.info },
  { key: "waiting",    label: "Chờ sự kiện",        tone: t.color.inkMuted },
  { key: "open_ended", label: "Vô thời hạn",        tone: t.color.inkMuted },
];

/* #157 classifier — waiting_trigger FIRST, then null=open_ended, then date. */
function classify(ob) {
  if (ob.status === "waiting_trigger") return "waiting";
  if (!ob.due) return "open_ended";
  // toy date logic for the prototype (today ~ 20/06/2026)
  const [d, m, y] = ob.due.split("/").map(Number);
  const due = new Date(y, m - 1, d), now = new Date(2026, 5, 20);
  const days = Math.round((due - now) / 86400000);
  if (days < 0) return "overdue";
  if (days <= 30) return "due_soon";
  return "upcoming";
}

/* ---------- small UI atoms ---------- */
function Chip({ children, tone = "neutral" }) {
  return <Badge kind={tone}>{children}</Badge>;
}
function PlainChip({ children, bg = t.color.surfaceAlt, fg = t.color.inkMuted }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4, background: bg, color: fg,
      fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, padding: `2px ${t.space[2]}px`,
      borderRadius: t.radius.pill, fontFamily: t.font.family,
    }}>{children}</span>
  );
}

function StatusActions({ ob, onAction }) {
  if (ob.status === "done") return <Badge kind="done">✓ hoàn thành</Badge>;
  if (ob.status === "cancelled") return <Badge kind="neutral">đã hủy</Badge>;
  if (ob.status === "waiting_trigger") {
    return <Button size="sm" onClick={() => onAction("trigger", ob)}>Đánh dấu sự kiện đã xảy ra</Button>;
  }
  // pending | in_progress
  return (
    <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
      <Button size="sm" onClick={() => onAction("done", ob)}>Hoàn thành</Button>
      {ob.status !== "in_progress" && <Button size="sm" variant="secondary" onClick={() => onAction("in_progress", ob)}>Đang làm</Button>}
      <Button size="sm" variant="ghost" onClick={() => onAction("cancel", ob)}>Hủy</Button>
    </div>
  );
}

function ObligationRow({ ob, onAction }) {
  const cat = CATEGORY[ob.category] || CATEGORY.other;
  const dim = ob.status === "done" || ob.status === "cancelled";
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: t.space[3], alignItems: "flex-start", padding: `${t.space[3]}px 0`, borderBottom: `1px solid ${t.color.border}`, opacity: dim ? 0.6 : 1 }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.medium, color: t.color.ink, textDecoration: ob.status === "done" ? "line-through" : "none" }}>
          {ob.desc}
        </div>
        {/* chip row */}
        <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginTop: t.space[2] }}>
          <PlainChip>{cat.icon} {cat.label}</PlainChip>
          {ob.total > 1 && <PlainChip bg={t.color.primarySoft} fg={t.color.primary}>Đợt {ob.idx}/{ob.total}</PlainChip>}
          {ob.obligor && <PlainChip>{ob.obligor} phải làm</PlainChip>}
          {ob.amount && <PlainChip bg={t.color.success_soft} fg={t.color.success}>{ob.amount}</PlainChip>}
          {ob.status === "waiting_trigger"
            ? <PlainChip bg={t.color.warning_soft} fg={t.color.warning}>⏳ Chờ: {ob.trigger}</PlainChip>
            : ob.due
              ? <PlainChip>📅 {ob.due}</PlainChip>
              : <PlainChip bg={t.color.surfaceAlt} fg={t.color.inkMuted}>Vô thời hạn — không có ngày hết hạn</PlainChip>}
          {ob.recurring && <PlainChip>🔁 {ob.recurring}</PlainChip>}
          <PlainChip>📄 {ob.doc}</PlainChip>
        </div>
      </div>
      <div style={{ flexShrink: 0 }}><StatusActions ob={ob} onAction={onAction} /></div>
    </div>
  );
}

/* Series group — collapsible header + progress + milestone chips (DEC-021) */
function SeriesGroup({ items, onAction }) {
  const [open, setOpen] = useState(true);
  const total = items[0].total;
  const doneN = items.filter((o) => o.status === "done").length;
  const cat = CATEGORY[items[0].category] || CATEGORY.other;
  const milestoneIcon = (s) => (s === "done" ? "✅" : s === "in_progress" ? "🔄" : "⬜");
  return (
    <div style={{ border: `1px solid ${t.color.border}`, borderRadius: t.radius.md, marginBottom: t.space[3], overflow: "hidden" }}>
      <button onClick={() => setOpen(!open)} style={{
        width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: t.space[3], background: t.color.surfaceAlt, border: "none", cursor: "pointer", fontFamily: t.font.family,
      }}>
        <span style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
          {cat.icon} {cat.label} ({items[0].doc}) — {doneN}/{total} hoàn thành
        </span>
        <span style={{ display: "flex", gap: t.space[1] }}>
          {items.map((m) => <span key={m.id} title={`Đợt ${m.idx}`}>{milestoneIcon(m.status)}</span>)}
          <span style={{ color: t.color.inkMuted, marginLeft: t.space[2] }}>{open ? "▾" : "▸"}</span>
        </span>
      </button>
      {open && (
        <div style={{ padding: `0 ${t.space[3]}px` }}>
          {items.map((ob) => <ObligationRow key={ob.id} ob={ob} onAction={onAction} />)}
        </div>
      )}
    </div>
  );
}

/* ---------- screen ---------- */
export default function AdminObligationsV2() {
  const [tab, setTab] = useState("nghĩa_vụ");
  const [toast, setToast] = useState(null);

  const act = (kind) => {
    if (kind === "trigger") setToast("Hoàn thành ✅ — 1 nghĩa vụ tiếp theo đã được kích hoạt"); // chain (DEC-021)
    else if (kind === "done") setToast("Đã đánh dấu hoàn thành — ghi Event ✓"); // FR-OB-04
    else if (kind === "in_progress") setToast("Đã chuyển 'đang làm' — ghi Event ✓");
    else setToast("Đã hủy nghĩa vụ — ghi Event ✓");
    setTimeout(() => setToast(null), 2800);
  };

  const inTab = SEED.filter((o) => (tab === "null" ? o.direction === null : o.direction === tab));
  const counts = {
    "nghĩa_vụ": SEED.filter((o) => o.direction === "nghĩa_vụ").length,
    "quyền_lợi": SEED.filter((o) => o.direction === "quyền_lợi").length,
    "null": SEED.filter((o) => o.direction === null).length,
  };

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 860, margin: "0 auto" }}>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>Nghĩa vụ & hạn</h1>
        <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
          Danh sách tất định từ kho (FR-OB-03). Hướng (nghĩa vụ / quyền lợi) do bạn xác nhận, không tự suy (D-02).
        </p>

        {/* AXIS 1 — direction tabs */}
        <div style={{ display: "flex", gap: t.space[2], borderBottom: `1px solid ${t.color.border}`, margin: `${t.space[5]}px 0` }}>
          {TABS.map((tb) => {
            const active = tab === tb.key;
            return (
              <button key={tb.key} onClick={() => setTab(tb.key)} title={tb.hint} style={{
                padding: `${t.space[2]}px ${t.space[4]}px`, background: "transparent", border: "none", cursor: "pointer",
                fontFamily: t.font.family, fontSize: t.font.size.md, fontWeight: t.font.weight.semibold,
                color: active ? t.color.primary : t.color.inkMuted,
                borderBottom: `2px solid ${active ? t.color.primary : "transparent"}`,
                display: "flex", alignItems: "center", gap: t.space[2],
              }}>
                {tb.label}
                <span style={{
                  fontSize: t.font.size.xs, background: tb.key === "null" && counts.null > 0 ? t.color.warning_soft : t.color.surfaceAlt,
                  color: tb.key === "null" && counts.null > 0 ? t.color.warning : t.color.inkMuted,
                  borderRadius: t.radius.pill, padding: `0 ${t.space[2]}px`,
                }}>{counts[tb.key]}</span>
              </button>
            );
          })}
        </div>

        {/* "Cần xác nhận" tab — CTA to self-party confirm (#158) */}
        {tab === "null" && counts.null > 0 && (
          <div style={{ background: t.color.warning_soft, borderRadius: t.radius.md, padding: t.space[4], marginBottom: t.space[5], display: "flex", justifyContent: "space-between", alignItems: "center", gap: t.space[3], flexWrap: "wrap" }}>
            <div style={{ fontSize: t.font.size.sm, color: t.color.warning }}>
              <strong>Chưa biết bên nào là bạn trong các hợp đồng này.</strong> Xác nhận để Khế tách đúng nghĩa vụ vs quyền lợi. (D-02)
            </div>
            <Button onClick={() => act("noop")}>Xác nhận “bên nào là bạn?”</Button>
          </div>
        )}

        {/* AXIS 2 — buckets, with series grouping inside each */}
        {inTab.length === 0 ? (
          <EmptyState icon="✅" title={tab === "null" ? "Không có gì cần xác nhận" : "Không có mục nào ở đây"} description="Khế sẽ cập nhật khi có tài liệu/hạn mới." />
        ) : (
          BUCKETS.map((b) => {
            const bucketItems = inTab.filter((o) => classify(o) === b.key);
            if (bucketItems.length === 0) return null;
            // split series vs standalone
            const seriesIds = [...new Set(bucketItems.filter((o) => o.series).map((o) => o.series))];
            const standalone = bucketItems.filter((o) => !o.series);
            return (
              <Card key={b.key} style={{ marginBottom: t.space[5] }}>
                <div style={{ display: "flex", alignItems: "center", gap: t.space[2], marginBottom: t.space[3] }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: b.tone }} />
                  <span style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{b.label}</span>
                </div>
                {seriesIds.map((sid) => (
                  <SeriesGroup key={sid} items={bucketItems.filter((o) => o.series === sid).sort((a, c) => a.idx - c.idx)} onAction={act} />
                ))}
                {standalone.map((ob) => <ObligationRow key={ob.id} ob={ob} onAction={act} />)}
              </Card>
            );
          })
        )}
      </div>

      {toast && (
        <div style={{ position: "fixed", bottom: t.space[6], left: "50%", transform: "translateX(-50%)", zIndex: t.z.toast }}>
          <Toast kind="success">{toast}</Toast>
        </div>
      )}
    </div>
  );
}
