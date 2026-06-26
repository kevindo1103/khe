/**
 * Khế — Firm Journey · F3 Portfolio + F4 Lead signals  (mockup_firm_stage_F3_F4_v0.1.jsx)
 * KHE_Designer · issue #236 (DEC-039) · DS v0.2 + firm primitives v0.1 + FirmShell
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Inherits #206 a11y. Desktop-first.
 *
 * F3 — Portfolio overview (J4): grid of consented clients (ClientCard, full business
 *   data DEC-039). Sort (Hạn gần nhất default / Tên / Số HĐ) + filter (30/60/90 ngày).
 *   Pagination: 20/page, sort closest-due first (PM #3). Tap client → detail (implied).
 * F4 — Lead signals (J5 core): grouped Khẩn cấp(≤7)/Sắp tới(8-30)/Theo dõi(31-90),
 *   each LeadSignalCard → external "Liên hệ tư vấn" (firm's channel, not Khế). Count via LiveRegion.
 *   all-clear is legitimate ONLY when there are clients + 0 upcoming.
 * Read-only (D-09). Backend: GET /firm/portfolio · GET /firm/lead-signals (#237).
 */
import React, { useState } from "react";
import { tokens as t, Button, LiveRegion } from "./mockup_design_system_v0.2.jsx";
import { ClientCard, LeadSignalCard, FirmEmptyState, urgencyOf } from "./mockup_firm_journey_primitives_v0.1.jsx";
import { FirmShell } from "./mockup_firm_stage_F0_F1_v0.1.jsx";

const CLIENTS = [
  { name: "Anh Dũng", business: "Nhà hàng Phở Bắc", consent: "granted", restricted: true, obligations: [
    { contractType: "HĐ thuê mặt bằng", obligationType: "gia hạn", days: 5 },
    { contractType: "HĐ nhà cung cấp", obligationType: "thanh toán", days: 7 },
    { contractType: "HĐ lao động (3)", obligationType: "hết hạn", days: 45 },
    { contractType: "HĐ bảo trì", obligationType: "gia hạn", days: 88 },
  ]},
  { name: "Chị Mai", business: "Tạp hoá Mai", consent: "granted", obligations: [
    { contractType: "HĐ nhà cung cấp", obligationType: "thanh toán", days: 18 },
    { contractType: "HĐ thuê kho", obligationType: "gia hạn", days: 62 },
  ]},
  { name: "Cô Lan", business: "Xưởng may Lan", consent: "granted", restricted: true, obligations: [
    { contractType: "HĐ lao động (8)", obligationType: "hết hạn", days: 30 },
    { contractType: "HĐ thuê xưởng", obligationType: "gia hạn", days: 120 },
  ]},
];

const SORTS = [["due", "Hạn gần nhất"], ["name", "Tên client"], ["count", "Số HĐ"]];
const RANGES = [["30", "30 ngày"], ["60", "60 ngày"], ["90", "90 ngày"], ["all", "Tất cả"]];

/* ---- F3 portfolio ---- */
function Portfolio({ empty }) {
  const [sort, setSort] = useState("due");
  const [range, setRange] = useState("30");
  const minDays = (c) => Math.min(...c.obligations.map((o) => o.days));
  let list = empty ? [] : [...CLIENTS];
  if (range !== "all") list = list.filter((c) => minDays(c) <= Number(range));
  list.sort((a, b) => sort === "name" ? a.name.localeCompare(b.name) : sort === "count" ? b.obligations.length - a.obligations.length : minDays(a) - minDays(b));

  return (
    <div>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: t.space[3], marginBottom: t.space[4] }}>
        <div>
          <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: 0 }}>Khách hàng</h1>
          <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, margin: `${t.space[1]}px 0 0` }}>{empty ? "Chưa có client nào trong khoảng lọc" : `${CLIENTS.length} client đang chia sẻ`}</p>
        </div>
        <Button size="sm">+ Mời client</Button>
      </div>

      {/* controls */}
      <div style={{ display: "flex", gap: t.space[4], flexWrap: "wrap", marginBottom: t.space[5], fontSize: t.font.size.sm }}>
        <label style={{ display: "flex", alignItems: "center", gap: t.space[2], color: t.color.inkMuted }}>Sắp xếp:
          <select value={sort} onChange={(e) => setSort(e.target.value)} style={selStyle}>{SORTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: t.space[2], color: t.color.inkMuted }}>Hạn trong:
          <select value={range} onChange={(e) => setRange(e.target.value)} style={selStyle}>{RANGES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
        </label>
      </div>

      {list.length === 0 ? (
        <div style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg }}>
          {empty
            ? <FirmEmptyState state="cold_start" onInvite={() => {}} />
            : <FirmEmptyState state="all_clear" />}
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: t.space[4] }}>
          {list.map((c) => <ClientCard key={c.name} client={c} onOpen={() => {}} />)}
        </div>
      )}
    </div>
  );
}
const selStyle = { fontFamily: t.font.family, fontSize: t.font.size.sm, color: t.color.ink, padding: `${t.space[1]}px ${t.space[2]}px`, borderRadius: t.radius.md, border: `1px solid ${t.color.border}`, background: t.color.surface };

/* ---- F4 lead signals ---- */
const SIGNALS = [
  { clientName: "Anh Dũng", business: "Nhà hàng Phở Bắc", contractType: "HĐ thuê mặt bằng", obligationType: "gia hạn", days: 5, email: "dung@phobac.vn" },
  { clientName: "Anh Dũng", business: "Nhà hàng Phở Bắc", contractType: "HĐ nhà cung cấp", obligationType: "thanh toán", days: 7, email: "dung@phobac.vn" },
  { clientName: "Chị Mai", business: "Tạp hoá Mai", contractType: "HĐ nhà cung cấp", obligationType: "thanh toán", days: 18, email: "mai@example.vn" },
  { clientName: "Cô Lan", business: "Xưởng may Lan", contractType: "HĐ lao động (8)", obligationType: "hết hạn", days: 30, email: "lan@maylan.vn", restricted: true },
  { clientName: "Chị Mai", business: "Tạp hoá Mai", contractType: "HĐ thuê kho", obligationType: "gia hạn", days: 62, email: "mai@example.vn" },
];
const GROUPS = [
  { key: "khan_cap", title: "Khẩn cấp", hint: "≤ 7 ngày", test: (d) => d <= 7 },
  { key: "sap_toi", title: "Sắp tới", hint: "8–30 ngày", test: (d) => d > 7 && d <= 30 },
  { key: "theo_doi", title: "Theo dõi", hint: "31–90 ngày", test: (d) => d > 30 && d <= 90 },
];
function LeadSignals({ allClear }) {
  const signals = allClear ? [] : SIGNALS;
  const within30 = signals.filter((s) => s.days <= 30).length;
  return (
    <div>
      <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: 0 }}>Cảnh báo</h1>
      <LiveRegion style={{ fontSize: t.font.size.base, color: t.color.inkBody, margin: `${t.space[2]}px 0 ${t.space[5]}px` }}>
        {within30 > 0 ? <>🔴 <strong>{within30} client</strong> có hạn trong 30 ngày cần chú ý — gọi để tư vấn trước khi trễ.</> : "Không có hạn khẩn cấp trong 30 ngày tới."}
      </LiveRegion>

      {signals.length === 0 ? (
        <div style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg }}>
          <FirmEmptyState state="all_clear" />
        </div>
      ) : GROUPS.map((g) => {
        const items = signals.filter((s) => g.test(s.days)).sort((a, b) => a.days - b.days);
        if (!items.length) return null;
        return (
          <section key={g.key} style={{ marginBottom: t.space[6] }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: t.space[2], marginBottom: t.space[3] }}>
              <h2 style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink, margin: 0 }}>{g.title}</h2>
              <span style={{ fontSize: t.font.size.xs, color: t.color.inkSubtle }}>{g.hint} · {items.length}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: t.space[3] }}>
              {items.map((s, i) => <LeadSignalCard key={i} signal={s} />)}
            </div>
          </section>
        );
      })}
    </div>
  );
}

/* ============================================================================
 * SHOWCASE
 * ========================================================================== */
const SCREENS = [
  { key: "portfolio", label: "F3 · Portfolio", nav: "clients" },
  { key: "signals", label: "F4 · Lead signals", nav: "signals" },
  { key: "signals_clear", label: "F4 · All-clear", nav: "signals" },
];
export default function FirmF3F4Showcase() {
  const [screen, setScreen] = useState("portfolio");
  const cur = SCREENS.find((s) => s.key === screen);
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[7], fontFamily: t.font.family }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Firm journey · F3–F4</div>
        <div style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 ${t.space[4]}px` }}>Portfolio + lead signals</div>
        <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap", marginBottom: t.space[5] }}>
          {SCREENS.map((s) => (
            <button key={s.key} type="button" onClick={() => setScreen(s.key)} style={{
              padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family,
              fontSize: t.font.size.sm, border: `1px solid ${screen === s.key ? t.color.primary : t.color.border}`,
              background: screen === s.key ? t.color.primarySoft : t.color.surface, color: screen === s.key ? t.color.primary : t.color.inkMuted,
            }}>{s.label}</button>
          ))}
        </div>

        <FirmShell active={cur.nav}>
          {screen === "portfolio" && <Portfolio />}
          {screen === "signals" && <LeadSignals />}
          {screen === "signals_clear" && <LeadSignals allClear />}
        </FirmShell>
      </div>
    </div>
  );
}
