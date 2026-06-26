/**
 * Khế — Firm Journey · Primitives v0.1  (mockup_firm_journey_primitives_v0.1.jsx)
 * KHE_Designer · issue #236 (DEC-039 full business data model) · Design System v0.2
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Inherits #206 a11y handoff contract.
 *
 * Firm = economic buyer (Chị Hằng, B2B2B DEC-011). Portal = LEAD-GENERATOR for the
 * firm's services, NOT a data dashboard. Every surface points to "call the client" (J5).
 *
 * D-rules (PM-ratified on #236):
 *   • D-09 — firm is READ-ONLY. NO edit affordances anywhere. Only external CTA (mailto/tel).
 *   • D-10 — access gated by explicit SME consent; SME-only revoke; revoke = INSTANT vanish,
 *            NO historical cache (page reload after revoke = gone). Firm has no self-revoke.
 *   • DEC-039 — firm sees FULL business contract data per consented client (supersedes the
 *            #182 "counts-only" spec). B2B commercial data is not NĐ13 personal data.
 *   • Labor exception — `contains_personal_data=true` (hd_lao_dong): show metadata
 *            (doc_type/dates/obligation_type) but HIDE employee name (doi_tac) + salary
 *            (gia_tri_hd) → DataRestrictedLabel. Field map per PM B4 on #236.
 *
 * Backend contract: #237 (POST /firm/consent-requests · POST /firm/tenants/invite ·
 *   GET /firm/portfolio · GET /firm/lead-signals · DELETE /consent/firm-access/{firm_id}).
 *   Built to contract — does NOT require #237 merged first.
 *
 * Desktop-first (Principle 6 — Chị Hằng dùng máy văn phòng).
 * ⚠ DEC-039 chưa fold canonical (PM posts DOCS_INBOX sau Kevin ratify) — header reference only.
 */
import React, { useState } from "react";
import { tokens as t, Badge, Button, EmptyState, LiveRegion, VisuallyHidden } from "./mockup_design_system_v0.2.jsx";

/* ============================================================================
 * Urgency model (shared) — lead-signal buckets per #236 F4.
 *   ≤7 ngày = Khẩn cấp (danger) · 8–30 = Sắp tới (warning) · 31–90 = Theo dõi (info)
 * ========================================================================== */
export function urgencyOf(days) {
  if (days <= 7) return { key: "khan_cap", label: "Khẩn cấp", color: t.color.danger, soft: t.color.danger_soft, bd: t.color.dangerBorder, dot: "🔴" };
  if (days <= 30) return { key: "sap_toi", label: "Sắp tới", color: t.color.warning, soft: t.color.warning_soft, bd: t.color.warningBorder, dot: "🟠" };
  return { key: "theo_doi", label: "Theo dõi", color: t.color.info, soft: t.color.info_soft, bd: t.color.infoBorder, dot: "🟡" };
}

/* ============================================================================
 * 1. ConsentStatus — chip for a consent relationship (D-10 lifecycle).
 * ========================================================================== */
const CONSENT = {
  pending:  { kind: "needs_review", label: "Chờ xác nhận" },
  granted:  { kind: "done",         label: "Đang chia sẻ" }, // success-green = active/ok (PM note: not "extracted")
  revoked:  { kind: "neutral",      label: "Đã thu hồi" },
};
export function ConsentStatus({ status = "pending" }) {
  const c = CONSENT[status] || CONSENT.pending;
  return <Badge kind={c.kind} dot>{c.label}</Badge>;
}

/* ============================================================================
 * 2. DataRestrictedLabel — neutral, non-scary note for labor-contract metadata.
 *    (PM B4: contains_personal_data → hide employee name + salary.)
 * ========================================================================== */
export function DataRestrictedLabel() {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: t.space[1],
      fontSize: t.font.size.xs, color: t.color.inkMuted, fontFamily: t.font.family,
    }}>
      <span aria-hidden="true">🔒</span>
      Một số thông tin bị giới hạn theo quy định bảo vệ dữ liệu cá nhân.
    </span>
  );
}

/* ============================================================================
 * 3. FirmEmptyState — CLOSED 4-state contract (mirror SME JourneyEmptyState).
 *    cold-start ≠ all-clear. Unknown state → dev-warn + render null (no silent
 *    false-reassurance regression). Honest-state principle (#236 P5).
 * ========================================================================== */
export const FIRM_EMPTY_STATES = ["cold_start", "processing", "all_clear", "revoked"];
export function FirmEmptyState({ state, count = 0, clientName, onInvite }) {
  if (!FIRM_EMPTY_STATES.includes(state)) {
    if (typeof console !== "undefined") console.warn(`FirmEmptyState: unknown state "${state}" — render null to avoid false reassurance.`);
    return null;
  }
  if (state === "cold_start")
    return <EmptyState icon="🤝" title="Chưa có client" description="Mời client đầu tiên để bắt đầu theo dõi hạn giúp họ." action={<Button onClick={onInvite}>Mời client</Button>} />;
  if (state === "processing")
    return <EmptyState icon="⏳" title={`Đang xử lý hồ sơ ${count} client…`} description="Khế đang bóc tách hợp đồng. Bạn sẽ thấy hạn ngay khi xong." />;
  if (state === "all_clear")
    // legitimate reassurance ONLY — caller passes this only when there are clients AND zero upcoming
    return <EmptyState icon="✅" title="Tất cả client trong tầm kiểm soát" description="Không có hạn nào trong 30 ngày tới." />;
  // revoked
  return <EmptyState icon="—" title={`${clientName || "Client"} đã thu hồi quyền truy cập`} description="Dữ liệu không còn hiển thị. Liên hệ client nếu cần được cấp quyền lại." />;
}

/* ============================================================================
 * 4. RevokeBanner — D-10 instant-vanish transition (open tab → next fetch 404).
 *    Auto-fade then remove (PM clarification #1). NO historical cache.
 * ========================================================================== */
export function RevokeBanner({ clientName = "Client", onDismiss }) {
  return (
    <div role="status" aria-live="polite" style={{
      display: "flex", alignItems: "center", gap: t.space[3], fontFamily: t.font.family,
      background: t.color.surfaceSunken, border: `1px solid ${t.color.border}`,
      borderRadius: t.radius.md, padding: `${t.space[3]}px ${t.space[4]}px`,
    }}>
      <span aria-hidden="true" style={{ fontSize: 16 }}>🔒</span>
      <span style={{ flex: 1, fontSize: t.font.size.sm, color: t.color.inkBody }}>
        <strong style={{ color: t.color.ink }}>{clientName}</strong> đã thu hồi quyền truy cập. Dữ liệu đã ẩn.
      </span>
      <Button size="sm" variant="ghost" onClick={onDismiss}>Ẩn</Button>
    </div>
  );
}

/* ============================================================================
 * 5. LeadSignalCard — J5 core. WHO + WHEN + WHY + a single external CTA.
 *    CTA = "Liên hệ tư vấn" → mailto (firm's own channel, NOT Khế chat). Read-only (D-09).
 * ========================================================================== */
export function LeadSignalCard({ signal }) {
  const { clientName, business, contractType, obligationType, days, email, restricted } = signal;
  const u = urgencyOf(days);
  const subject = encodeURIComponent(`Về hợp đồng sắp đến hạn của ${clientName}`);
  return (
    <div style={{
      background: t.color.surface, border: `1px solid ${t.color.border}`, borderLeft: `3px solid ${u.color}`,
      borderRadius: t.radius.lg, boxShadow: t.elevation.e1, fontFamily: t.font.family,
      padding: t.space[4], display: "flex", alignItems: "flex-start", gap: t.space[3],
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
          <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{clientName}</span>
          <Badge kind={u.key === "khan_cap" ? "overdue" : u.key === "sap_toi" ? "due_soon" : "processing"}>{u.label}</Badge>
        </div>
        <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>{business}</div>
        <div style={{ fontSize: t.font.size.sm, color: t.color.inkBody, marginTop: t.space[2] }}>
          {contractType} · {obligationType} — <strong style={{ color: u.color }}>còn {days} ngày</strong>
        </div>
        {restricted && <div style={{ marginTop: t.space[2] }}><DataRestrictedLabel /></div>}
      </div>
      {/* external CTA — firm's own channel; read-only re: Khế data (D-09) */}
      <a href={`mailto:${email}?subject=${subject}`} style={{
        flexShrink: 0, display: "inline-flex", alignItems: "center", gap: t.space[1],
        fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, textDecoration: "none",
        color: "#fff", background: t.color.primary, padding: `${t.space[2]}px ${t.space[4]}px`,
        borderRadius: t.radius.md, whiteSpace: "nowrap",
      }}>✉ Liên hệ tư vấn</a>
    </div>
  );
}

/* ============================================================================
 * 6. ClientCard — portfolio entry (F3). Full business data (DEC-039), read-only.
 *    Truncate obligations at 3 + "Xem tất cả N" → drill to client detail.
 * ========================================================================== */
export function ClientCard({ client, onOpen }) {
  const { name, business, obligations = [], consent = "granted", restricted } = client;
  const shown = obligations.slice(0, 3);
  const more = obligations.length - shown.length;
  return (
    <button type="button" onClick={onOpen} aria-label={`Mở hồ sơ ${name} — ${business}`} style={{
      width: "100%", textAlign: "left", display: "block", font: "inherit", fontFamily: t.font.family, cursor: "pointer",
      background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg,
      boxShadow: t.elevation.e1, padding: t.space[4],
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: t.space[2] }}>
        <span style={{ minWidth: 0 }}>
          <span style={{ display: "block", fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{name}</span>
          <span style={{ display: "block", fontSize: t.font.size.sm, color: t.color.inkMuted }}>{business}</span>
        </span>
        <ConsentStatus status={consent} />
      </div>

      <div style={{ marginTop: t.space[3], border: `1px solid ${t.color.border}`, borderRadius: t.radius.md, overflow: "hidden" }}>
        {shown.map((o, i) => {
          const u = urgencyOf(o.days);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: t.space[2], padding: `${t.space[2]}px ${t.space[3]}px`, borderBottom: i < shown.length - 1 ? `1px solid ${t.color.border}` : "none" }}>
              <span style={{ flex: 1, minWidth: 0, fontSize: t.font.size.sm, color: t.color.inkBody, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{o.contractType}</span>
              <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>{o.obligationType}</span>
              <span style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: u.color, whiteSpace: "nowrap" }}>{o.days} ngày <span aria-hidden="true">{u.dot}</span></span>
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: t.space[2] }}>
        {restricted ? <DataRestrictedLabel /> : <span />}
        {more > 0 && <span style={{ fontSize: t.font.size.sm, color: t.color.primary, fontWeight: t.font.weight.medium }}>Xem tất cả {obligations.length} →</span>}
      </div>
    </button>
  );
}

/* ============================================================================
 * SHOWCASE — desktop-first frame demoing every primitive + each state.
 * ========================================================================== */
const SIGNALS = [
  { clientName: "Anh Dũng", business: "Nhà hàng Phở Bắc", contractType: "HĐ thuê mặt bằng", obligationType: "gia hạn", days: 5, email: "dung@phobac.vn" },
  { clientName: "Chị Mai", business: "Tạp hoá Mai", contractType: "HĐ nhà cung cấp", obligationType: "thanh toán", days: 18, email: "mai@example.vn" },
  { clientName: "Cô Lan", business: "Xưởng may Lan", contractType: "HĐ lao động (3)", obligationType: "hết hạn", days: 45, email: "lan@maylan.vn", restricted: true },
];
const CLIENT = {
  name: "Anh Dũng", business: "Nhà hàng Phở Bắc", consent: "granted",
  obligations: [
    { contractType: "HĐ thuê mặt bằng", obligationType: "gia hạn", days: 23 },
    { contractType: "HĐ nhà cung cấp", obligationType: "thanh toán", days: 7 },
    { contractType: "HĐ lao động (3)", obligationType: "hết hạn", days: 45 },
    { contractType: "HĐ bảo trì", obligationType: "gia hạn", days: 88 },
  ],
  restricted: true,
};

function Demo({ label, children }) {
  return (
    <div style={{ marginBottom: t.space[6] }}>
      <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, marginBottom: t.space[2] }}>{label}</div>
      {children}
    </div>
  );
}

export default function FirmPrimitivesShowcase() {
  const [showRevoke, setShowRevoke] = useState(true);
  const urgentCount = SIGNALS.filter((s) => s.days <= 30).length;
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[8], fontFamily: t.font.family }}>
      <header style={{ maxWidth: 760, marginBottom: t.space[7] }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Firm journey · primitives</span>
        <div style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, marginTop: t.space[1] }}>Khối dựng cổng đối tác (firm)</div>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: t.font.lineHeight.relaxed }}>
          Lead-generator cho dịch vụ firm (J5), KHÔNG phải dashboard. Read-only (D-09) · consent-gated (D-10) · full business data (DEC-039). Desktop-first.
        </p>
      </header>

      <div style={{ maxWidth: 760 }}>
        <Demo label="ConsentStatus (3 trạng thái)">
          <div style={{ display: "flex", gap: t.space[2] }}>
            <ConsentStatus status="pending" /><ConsentStatus status="granted" /><ConsentStatus status="revoked" />
          </div>
        </Demo>

        <Demo label="FirmEmptyState — 4-state matrix (cold-start ≠ all-clear)">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: t.space[4] }}>
            {["cold_start", "processing", "all_clear", "revoked"].map((s) => (
              <div key={s} style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg }}>
                <FirmEmptyState state={s} count={3} clientName="ABC Co." onInvite={() => {}} />
              </div>
            ))}
          </div>
        </Demo>

        <Demo label="RevokeBanner (D-10 instant vanish, no cache)">
          {showRevoke ? <RevokeBanner clientName="ABC Company" onDismiss={() => setShowRevoke(false)} /> : <Button size="sm" variant="secondary" onClick={() => setShowRevoke(true)}>Reset banner</Button>}
        </Demo>

        <Demo label={`LeadSignalCard — J5 (${urgentCount} client cần chú ý trong 30 ngày)`}>
          <LiveRegion style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginBottom: t.space[2] }}>
            🔴 {urgentCount} client có hạn trong 30 ngày cần chú ý
          </LiveRegion>
          <div style={{ display: "flex", flexDirection: "column", gap: t.space[3] }}>
            {SIGNALS.map((s, i) => <LeadSignalCard key={i} signal={s} />)}
          </div>
        </Demo>

        <Demo label="ClientCard — portfolio entry (full business data, truncate 3 + xem tất cả)">
          <div style={{ maxWidth: 460 }}><ClientCard client={CLIENT} onOpen={() => {}} /></div>
        </Demo>

        <Demo label="DataRestrictedLabel — labor contract metadata-only">
          <DataRestrictedLabel />
        </Demo>
      </div>
      <VisuallyHidden as="p">Firm portal primitives showcase — read-only, consent-gated.</VisuallyHidden>
    </div>
  );
}
