/**
 * Khế — UX Journey Primitives v0.1  (mockup_journey_primitives_v0.1.jsx)
 * KHE_Designer · issue #198 Phase A · builds ON Design System v0.2
 * ----------------------------------------------------------------------------
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.2.
 *
 * WHY (issue #198 root cause): zero-state collapsed 4 distinct meanings into one
 * "Khế sẽ nhắc bạn khi có hạn mới" → FALSE REASSURANCE on a cold/empty tenant,
 * which contradicts Khế's WHY. This file establishes the journey-layer primitives
 * that the 8-stage flow composes — built on v0.2 (foundation), consumed by the
 * Stage screen mockups (Phase B/C).
 *
 * SCOPE (PM scope decision 2026-06-23): SME journey only (Anh Dũng + Bạn Linh).
 *   Firm journey deferred to a separate issue.
 *
 * RATIFIED CONSTRAINTS (PM amendment + Kevin ratify 2026-06-23):
 *   • tenant_journey_stage (per-tenant, MONOTONIC) ≠ document.extraction_status.
 *       NEW → EXTRACTING → NEEDS_REVIEW → CONFIRMED → ACTIVATED → STEADY
 *       Home = f(tenant_journey_stage). A new doc after ACTIVATED is a per-doc
 *       cycle (floating nudge), it NEVER regresses the tenant stage.
 *   • Nav-lock ONLY on is_first_session (cleared at CONFIRMED — DEC-040 #238, was
 *       ACTIVATED). Return visits = full nav always; never punitive.
 *   • Achievement copy = PER-CONTRACT scope + hint loop. NEVER "đã được bảo vệ"
 *       (overpromise on a partial vault).
 *   • ACTIVATED gate = ≥1 reminder channel (Telegram OR email). No hard block —
 *       skip both → CONFIRMED + persistent top-bar "Bật nhắc" nudge.
 *   • Concierge (D-02 Option B, Kevin-ratified): operator pre-fills, tenant lands
 *       at NEEDS_REVIEW; USER self-confirms (D-02 preserved — user is final author).
 *   • Steady-state 6-tab entity nav = Phase 1 OK. // PHASE-2-IA-DEBT below.
 *
 * D-rules: D-01/02 (user is final author of legal writes), D-06 (immutable original),
 *   D-07 (every field editable→Event), D-08 (no guess + an exit, never a dead end).
 */

import React, { useState } from "react";
import {
  tokens as t, Button, Card, Badge, EmptyState as DSEmptyState,
} from "./mockup_design_system_v0.2.jsx";

/* ===========================================================================
 * 1. tenant_journey_stage — state machine (design constraint for routing/home)
 * ========================================================================= */
export const JOURNEY = ["NEW", "EXTRACTING", "NEEDS_REVIEW", "CONFIRMED", "ACTIVATED", "STEADY"];
export const JOURNEY_LABEL = {
  NEW:          "Mới — chưa có tài liệu",
  EXTRACTING:   "Đang bóc tách",
  NEEDS_REVIEW: "Cần bạn kiểm tra",
  CONFIRMED:    "Đã xác nhận",
  ACTIVATED:    "Đã bật nhắc",
  STEADY:       "Ổn định",
};

/* ===========================================================================
 * 2. JourneyEmptyState — the 4-STATE MATRIX (CRITICAL — fixes #198 anti-pattern)
 *   Apply on EVERY surface that renders a list. State 1 must NEVER borrow
 *   state 3's "Khế sẽ nhắc khi có hạn" message.
 *
 *   DRIFT GUARD (QC Gap B): this is a CLOSED contract — `state` MUST be one of
 *   EMPTY_STATES. Free-form empty copy is forbidden; unknown state dev-warns +
 *   renders nothing (so a wrong string can't silently regress to false
 *   reassurance). QC checklist: every list surface uses <JourneyEmptyState>,
 *   never an ad-hoc empty <div>. Recommend a lint rule blocking literal
 *   "Khế sẽ nhắc" outside this file.
 * ========================================================================= */
export const EMPTY_STATES = ["cold_start", "processing", "all_clear", "no_match"];

export function JourneyEmptyState({ state, docCount = 0, onUpload, onRetry }) {
  if (!EMPTY_STATES.includes(state)) {
    // eslint-disable-next-line no-console
    if (typeof console !== "undefined") console.warn(`[JourneyEmptyState] unknown state "${state}" — use one of ${EMPTY_STATES.join("|")}`);
    return null;
  }
  switch (state) {
    case "cold_start": // 0 documents — honest: nothing here yet, drive the 1 CTA
      return (
        <DSEmptyState
          icon="＋"
          title="Chưa có tài liệu"
          description="Tải hợp đồng lên để Khế tự bóc hạn và nhắc bạn."
          action={<Button size="lg" onClick={onUpload}>Tải hợp đồng</Button>}
        />
      );
    case "processing": // docs exist, extraction pending — show motion, no CTA
      return (
        <div style={{ textAlign: "center", padding: `${t.space[9]}px ${t.space[5]}px`, fontFamily: t.font.family }}>
          <div style={{ fontSize: 22, marginBottom: t.space[3] }}>⏳</div>
          <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
            Đang bóc tách {docCount} tài liệu…
          </div>
          <div style={{ width: 200, height: 4, margin: `${t.space[4]}px auto 0`, background: t.color.neutral[200], borderRadius: t.radius.pill, overflow: "hidden" }}>
            <div style={{ width: "55%", height: "100%", background: t.color.primary }} />
          </div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[3] }}>Khoảng ~30 giây mỗi tài liệu.</div>
        </div>
      );
    case "all_clear": // extracted, genuinely 0 dated obligations — legitimate reassurance
      return (
        <DSEmptyState
          icon="✓"
          title="Đã quét — bạn không có hạn nào"
          description="Khế đã đọc tài liệu của bạn và không tìm thấy nghĩa vụ có ngày tháng nào. Sẽ báo ngay khi có."
        />
      );
    case "no_match": // a specific query found nothing — D-08 integrity + an exit
      return (
        <DSEmptyState
          notFound
          action={<div style={{ display: "flex", gap: t.space[2], justifyContent: "center" }}>
            <Button variant="secondary" onClick={onRetry}>Thử cách khác</Button>
            <Button variant="ghost" onClick={onUpload}>Tải thêm tài liệu</Button>
          </div>}
        />
      );
    default:
      return null;
  }
}

/* ===========================================================================
 * 3. SetupProgress — stepper/progress ("0/3 → 3/3 thiết lập")
 * ========================================================================= */
export function SetupProgress({ steps }) {
  const done = steps.filter((s) => s.done).length;
  return (
    <div style={{ fontFamily: t.font.family }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: t.space[2] }}>
        <span style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.ink }}>Thiết lập</span>
        <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontVariantNumeric: "tabular-nums" }}>{done}/{steps.length}</span>
      </div>
      <div style={{ height: 6, background: t.color.neutral[200], borderRadius: t.radius.pill, overflow: "hidden" }}>
        <div style={{ width: `${(done / steps.length) * 100}%`, height: "100%", background: t.color.primary, transition: `width ${t.motion.slow} ${t.motion.ease}` }} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: t.space[2], marginTop: t.space[3] }}>
        {steps.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: t.space[2], fontSize: t.font.size.sm, color: s.done ? t.color.inkMuted : t.color.ink }}>
            <span style={{
              width: 18, height: 18, borderRadius: "50%", flexShrink: 0, fontSize: 11,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: s.done ? t.color.primary : t.color.surfaceSunken,
              color: s.done ? "#fff" : t.color.inkSubtle, border: s.done ? "none" : `1px solid ${t.color.border}`,
            }}>{s.done ? "✓" : i + 1}</span>
            <span style={{ textDecoration: s.done ? "line-through" : "none" }}>{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ===========================================================================
 * 4. LockedNav — nav-lock ONLY on first session (clarification 2)
 * ========================================================================= */
const NAV = [
  { key: "home", label: "Tổng quan" },
  { key: "docs", label: "Tài liệu" },
  { key: "obligations", label: "Nghĩa vụ" },
  { key: "chat", label: "Hỏi-đáp" },
  { key: "settings", label: "Cài đặt" },
];
export function LockedNav({ isFirstSession, active = "home" }) {
  // PHASE-2-IA-DEBT: nav entity-shaped (Tài liệu/Nghĩa vụ/Hỏi-đáp); job-shaped
  //   candidate ("Hôm nay cần lo / Sắp tới / Đã xong / Khám phá") post-pilot.
  return (
    <nav style={{ display: "flex", gap: t.space[1], padding: t.space[2], background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, fontFamily: t.font.family }}>
      {NAV.map((n) => {
        const locked = isFirstSession && n.key !== "home"; // focus the single onboarding CTA (Hick's law)
        const isActive = n.key === active;
        return (
          <span key={n.key} title={locked ? "Mở khoá sau khi bật nhắc" : undefined} style={{
            padding: `${t.space[2]}px ${t.space[3]}px`, borderRadius: t.radius.md, fontSize: t.font.size.sm,
            fontWeight: t.font.weight.medium, whiteSpace: "nowrap",
            background: isActive ? t.color.primarySoft : "transparent",
            color: locked ? t.color.inkSubtle : isActive ? t.color.primary : t.color.inkBody,
            opacity: locked ? 0.5 : 1, cursor: locked ? "not-allowed" : "pointer",
            display: "inline-flex", alignItems: "center", gap: t.space[1],
          }}>
            {locked && <span style={{ fontSize: 10 }}>🔒</span>}{n.label}
          </span>
        );
      })}
    </nav>
  );
}

/* ===========================================================================
 * 5. ScopeCard — per-contract scope + hint loop (clarification 3)
 *    NEVER "đã được bảo vệ" / "toàn kho an toàn".
 * ========================================================================= */
export function ScopeCard({ contractName, onAddMore }) {
  return (
    <Card style={{ borderColor: t.color.primaryBorder, background: t.color.primarySoft }}>
      <div style={{ display: "flex", gap: t.space[3], alignItems: "flex-start" }}>
        <span style={{ fontSize: 20 }}>🔔</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: t.font.size.base, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
            Khế đang nhắc bạn về <strong>{contractName}</strong>.
          </div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>
            Tải thêm hợp đồng để Khế nhắc trọn vẹn hơn.
          </div>
          <div style={{ marginTop: t.space[3] }}>
            <Button size="sm" onClick={onAddMore}>Tải hợp đồng tiếp theo →</Button>
          </div>
        </div>
      </div>
    </Card>
  );
}

/* ===========================================================================
 * 6. ReminderNudge — persistent top bar until ≥1 channel (clarification 4)
 * ========================================================================= */
export function ReminderNudge({ onEnable }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between", gap: t.space[3], flexWrap: "wrap",
      background: t.color.warning_soft, border: `1px solid ${t.color.warningBorder}`, borderRadius: t.radius.md,
      padding: `${t.space[2]}px ${t.space[4]}px`, fontFamily: t.font.family,
    }}>
      <span style={{ fontSize: t.font.size.sm, color: t.color.warning }}>
        ⏰ Bật nhắc qua Telegram hoặc email để không bỏ lỡ hạn nào.
      </span>
      <Button size="sm" onClick={onEnable}>Bật nhắc</Button>
    </div>
  );
}

/* ===========================================================================
 * 6b. ProgressChip — compact inline "N/M bước" pill (DEC-040)
 *   Sibling of SetupProgress (§3): same {label, done} step shape, but a single
 *   inline pill for reuse on dense surfaces (dashboard banner, doc-detail,
 *   doc-list headers) where the full stepper is too heavy. Steps are caller-
 *   supplied — NO hardcoded copy here (drift guard, same spirit as §3).
 * ========================================================================= */
export function ProgressChip({ steps }) {
  const done = steps.filter((s) => s.done).length;
  return (
    <div role="group" aria-label={`Tiến độ thiết lập ${done}/${steps.length} bước`} style={{ display: "inline-flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap", padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, background: t.color.surfaceSunken, border: `1px solid ${t.color.border}` }}>
      <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.bold, color: t.color.ink }}>{done}/{steps.length} bước</span>
      {steps.map((s, i) => (
        <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: t.font.size.xs, color: s.done ? t.color.success : t.color.inkMuted }}>
          <span aria-hidden="true">{s.done ? "✅" : "⬜"}</span>{s.label}
        </span>
      ))}
    </div>
  );
}

/* ===========================================================================
 * 7. ConciergeWelcome — D-02 Option B (pre-filled → user self-confirms)
 * ========================================================================= */
export function ConciergeWelcome({ firmName, docCount, oblCount, nearest, onReview }) {
  return (
    <Card>
      <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, letterSpacing: t.font.tracking.snug }}>
        {firmName} đã chuẩn bị sẵn cho bạn
      </div>
      <p style={{ fontSize: t.font.size.base, color: t.color.inkBody, lineHeight: t.font.lineHeight.relaxed, marginTop: t.space[2] }}>
        {firmName} đã tải và đọc <strong>{docCount} hợp đồng</strong>, tìm ra <strong>{oblCount} nghĩa vụ</strong>.
        Hãy kiểm tra lại lần cuối và xác nhận — Khế chỉ bắt đầu nhắc sau khi bạn đồng ý.
      </p>
      {nearest && (
        <div style={{ marginTop: t.space[3], padding: t.space[3], background: t.color.surfaceSunken, borderRadius: t.radius.md, fontSize: t.font.size.sm }}>
          Gần nhất: <strong>{nearest.label}</strong> — còn {nearest.days} ngày
        </div>
      )}
      <div style={{ marginTop: t.space[4], display: "flex", gap: t.space[2], alignItems: "center" }}>
        <Button onClick={onReview}>Kiểm tra & xác nhận</Button>
        {/* D-02: user is the final author — concierge only pre-filled */}
        <Badge kind="needs_review" dot>Cần bạn xác nhận</Badge>
      </div>
    </Card>
  );
}

/* ===========================================================================
 * 8. FAILURE / REFUSE PATHS (QC missing-scope flag) — honesty over silence
 * ========================================================================= */

/* 8.1 ExtractionFailure (Stage 2) — never a skeleton stuck forever.
 *   D-08 spirit: say it plainly + give a way forward (retry / manual / contact). */
export function ExtractionFailure({ fileName, reason = "Ảnh quá mờ", onRetry, onManual }) {
  return (
    <Card style={{ borderColor: t.color.dangerBorder }}>
      <div style={{ display: "flex", gap: t.space[3], alignItems: "flex-start" }}>
        <span style={{ fontSize: 20 }}>⚠️</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
            Khế chưa đọc được “{fileName}”
          </div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2, lineHeight: t.font.lineHeight.relaxed }}>
            Lý do: {reason}. Bản gốc vẫn được lưu — bạn có thể thử lại hoặc nhập tay.
          </div>
          <div style={{ marginTop: t.space[3], display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
            <Button size="sm" onClick={onRetry}>Thử đọc lại</Button>
            <Button size="sm" variant="secondary" onClick={onManual}>Nhập tay</Button>
          </div>
        </div>
      </div>
    </Card>
  );
}

/* 8.2 PartialUpload (Stage 1) — batch with mixed outcomes; never hide the failures. */
export function PartialUpload({ ok = 0, failed = [], onReviewFailed }) {
  return (
    <Card>
      <div style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
        Đã xử lý {ok + failed.length} tài liệu
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: t.space[2], marginTop: t.space[3] }}>
        <div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
          <Badge kind="done" dot>{ok} đã đọc xong</Badge>
        </div>
        {failed.length > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
            <Badge kind="overdue" dot>{failed.length} chưa đọc được</Badge>
            <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>{failed.join(", ")}</span>
          </div>
        )}
      </div>
      {failed.length > 0 && (
        <div style={{ marginTop: t.space[3] }}>
          {/* batch stays partial — tenant stage NOT blocked by failed docs (per stage-vs-doc rule) */}
          <Button size="sm" variant="secondary" onClick={onReviewFailed}>Xem {failed.length} tài liệu lỗi</Button>
        </div>
      )}
    </Card>
  );
}

/* Note (Stage 4 refuse): handled by ReminderNudge (§6) — skip both channels → CONFIRMED
 * (not ACTIVATED) + persistent top-bar nudge, never a hard block / stuck state. */

/* ===========================================================================
 * 9. SHOWCASE
 * ========================================================================= */
function Block({ title, note, children }) {
  return (
    <section style={{ marginBottom: t.space[9] }}>
      <h2 style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, margin: 0, letterSpacing: t.font.tracking.snug }}>{title}</h2>
      {note && <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1], maxWidth: 640, lineHeight: t.font.lineHeight.relaxed }}>{note}</p>}
      <div style={{ marginTop: t.space[4], display: "flex", flexWrap: "wrap", gap: t.space[5], alignItems: "flex-start" }}>{children}</div>
    </section>
  );
}
function Frame({ label, children }) {
  return (
    <div style={{ width: 360 }}>
      <div style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: t.font.tracking.wide, marginBottom: t.space[2] }}>{label}</div>
      <div style={{ background: t.color.surface, border: `1px solid ${t.color.border}`, borderRadius: t.radius.lg, minHeight: 80 }}>{children}</div>
    </div>
  );
}

export default function JourneyPrimitivesShowcase() {
  const [stage, setStage] = useState("NEW");
  return (
    <div style={{ background: t.color.surfaceAlt, minHeight: "100vh", padding: t.space[8], fontFamily: t.font.family }}>
      <header style={{ marginBottom: t.space[9], maxWidth: 720 }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Phase A</span>
        <div style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, marginTop: t.space[2] }}>UX Journey Primitives</div>
        <p style={{ fontSize: t.font.size.md, color: t.color.inkMuted, marginTop: t.space[2], lineHeight: t.font.lineHeight.relaxed }}>
          Lớp journey trên Design System v0.2 — sửa anti-pattern false-reassurance bằng ma trận 4 empty-state, + các primitive cho 8-stage flow. SME-only scope.
        </p>
      </header>

      {/* journey stage machine */}
      <Block title="tenant_journey_stage" note="Per-tenant, monotonic. Home = f(stage). Doc mới sau ACTIVATED không kéo lùi stage.">
        <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
          {JOURNEY.map((s, i) => (
            <span key={s} onClick={() => setStage(s)} style={{
              display: "inline-flex", alignItems: "center", gap: t.space[1], cursor: "pointer",
              padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold,
              background: stage === s ? t.color.primary : t.color.surface, color: stage === s ? "#fff" : t.color.inkBody,
              border: `1px solid ${stage === s ? "transparent" : t.color.border}`,
            }}>{i + 1}. {s}</span>
          ))}
        </div>
        <div style={{ width: "100%", fontSize: t.font.size.sm, color: t.color.inkMuted }}>→ {JOURNEY_LABEL[stage]}</div>
      </Block>

      {/* THE 4-STATE MATRIX */}
      <Block title="⚠️ Empty-state matrix (áp MỌI surface có list)" note="State 1 (cold-start) TUYỆT ĐỐI không dùng thông điệp state 3 (all-clear) → tránh trấn an sai.">
        <Frame label="1 · Cold-start (0 doc)"><JourneyEmptyState state="cold_start" /></Frame>
        <Frame label="2 · Processing"><JourneyEmptyState state="processing" docCount={3} /></Frame>
        <Frame label="3 · All-clear (đã quét, 0 hạn)"><JourneyEmptyState state="all_clear" /></Frame>
        <Frame label="4 · No-match (D-08)"><JourneyEmptyState state="no_match" /></Frame>
      </Block>

      {/* primitives */}
      <Block title="SetupProgress · ReminderNudge" note="ACTIVATED gate = ≥1 channel; skip cả hai → nudge top-bar bền bỉ, không hard-block.">
        <Frame label="Setup stepper">
          <div style={{ padding: t.space[5] }}>
            <SetupProgress steps={[{ label: "Tải hợp đồng đầu tiên", done: true }, { label: "Xác nhận thông tin bóc tách", done: true }, { label: "Bật nhắc (Telegram/email)", done: false }]} />
          </div>
        </Frame>
        <Frame label="Reminder nudge (top bar)"><div style={{ padding: t.space[3] }}><ReminderNudge /></div></Frame>
        <Frame label="ProgressChip (inline, DEC-040)"><div style={{ padding: t.space[3] }}><ProgressChip steps={[{ label: "Đã duyệt tài liệu", done: true }, { label: "Bật nhắc Telegram", done: false }, { label: "Theo dõi tự động", done: false }]} /></div></Frame>
      </Block>

      <Block title="LockedNav" note="Nav-lock CHỈ is_first_session (clear khi CONFIRMED — DEC-040). Return = full nav, không punitive.">
        <div style={{ width: "100%", maxWidth: 560, display: "flex", flexDirection: "column", gap: t.space[3] }}>
          <div><div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginBottom: t.space[1] }}>First session</div><LockedNav isFirstSession /></div>
          <div><div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginBottom: t.space[1] }}>Return visit</div><LockedNav isFirstSession={false} active="obligations" /></div>
        </div>
      </Block>

      <Block title="ScopeCard · ConciergeWelcome" note="ScopeCard: per-contract + hint loop, KHÔNG 'đã được bảo vệ'. Concierge: D-02 Option B (pre-fill → user self-confirm).">
        <div style={{ width: 360 }}><ScopeCard contractName="HĐ thuê mặt bằng Q7" /></div>
        <div style={{ width: 420 }}>
          <ConciergeWelcome firmName="Đại lý thuế Chị Hằng" docCount={3} oblCount={7} nearest={{ label: "gia hạn mặt bằng Q7", days: 23 }} />
        </div>
      </Block>

      <Block title="Failure / refuse paths" note="QC missing-scope: extraction fail không để skeleton kẹt; batch partial không giấu lỗi; Stage 4 refuse → CONFIRMED + nudge (không stuck).">
        <div style={{ width: 360 }}><ExtractionFailure fileName="HĐ thuê kho.jpg" onRetry={() => {}} onManual={() => {}} /></div>
        <div style={{ width: 360 }}><PartialUpload ok={2} failed={["HĐ thuê kho.jpg"]} onReviewFailed={() => {}} /></div>
      </Block>
    </div>
  );
}
