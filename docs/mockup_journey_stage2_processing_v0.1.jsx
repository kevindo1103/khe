/**
 * Khế — Journey · Stage 2 Processing  (mockup_journey_stage2_processing_v0.1.jsx)
 * KHE_Designer · issue #198 Phase C · Design System v0.2 + journey primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Stage 2 = waiting for extraction. AI is TRANSPARENT (not a 60s blank skeleton):
 * narrate what it recognised + reveal fields progressively. Low-confidence fields
 * pre-announce "sẽ nhờ bạn xác nhận" (sets up Stage 3 trust).
 *
 * ⚠️ This is a PATTERN, not a component (per QC). Skeleton is the atom (v0.2); the
 *    timed reveal below is the composition. SPEC-WATCH: progressive reveal of
 *    confidence/fields → FR-EX → DOCS_INBOX when built (coordinate KHE_AI/Backend).
 * Failure: if extraction errors mid-way → ExtractionFailure primitive (journey v0.1).
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Badge, Skeleton, ConfidenceMeter } from "./mockup_design_system_v0.2.jsx";
import { ExtractionFailure } from "./mockup_journey_primitives_v0.1.jsx";

// 4 timeline phases of the progressive-disclosure pattern
const PHASES = {
  "0-10s": { note: "Đã nhận tài liệu — đang đọc…", fields: [] },
  "10-30s": { note: "Đã nhận ra: Hợp đồng thuê mặt bằng · đang tìm các mốc thời hạn…", fields: ["doi_tac"] },
  "30-60s": { note: "Đang bóc tách điều khoản…", fields: ["doi_tac", "ngay_hieu_luc", "thoi_han"] },
  "done": { note: "Xong! Hãy kiểm tra lại.", fields: ["doi_tac", "ngay_hieu_luc", "thoi_han", "ngay_het_han", "gia_tri"] },
};
const FIELD = {
  doi_tac: { label: "Đối tác", value: "Cty TNHH Hải Đăng", conf: 0.97 },
  ngay_hieu_luc: { label: "Ngày hiệu lực", value: "01/10/2024", conf: 0.95 },
  thoi_han: { label: "Thời hạn", value: "24 tháng", conf: 0.88 },
  ngay_het_han: { label: "Ngày hết hạn", value: "30/09/2026", conf: 0.62 },
  gia_tri: { label: "Giá trị", value: "45.000.000đ/tháng", conf: 0.91 },
};
const ORDER = ["doi_tac", "ngay_hieu_luc", "thoi_han", "ngay_het_han", "gia_tri"];

export default function Stage2Processing() {
  const [phase, setPhase] = useState("10-30s");
  const fail = phase === "fail";
  const cur = PHASES[phase] || PHASES["done"];
  const shown = fail ? [] : cur.fields;

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 640, margin: "0 auto" }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 2 · EXTRACTING</span>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 0` }}>Khế đang đọc tài liệu</h1>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[1] }}>Minh bạch tiến trình — không để bạn nhìn màn hình trống.</p>

        <div style={{ display: "flex", gap: t.space[2], margin: `${t.space[5]}px 0`, flexWrap: "wrap" }}>
          {["0-10s", "10-30s", "30-60s", "done", "fail"].map((k) => (
            <button key={k} onClick={() => setPhase(k)} style={{ padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family, fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, border: `1px solid ${phase === k ? t.color.primary : t.color.border}`, background: phase === k ? t.color.primarySoft : t.color.surface, color: phase === k ? t.color.primary : t.color.inkMuted }}>{k}</button>
          ))}
        </div>

        {fail ? (
          <ExtractionFailure fileName="HĐ thuê Q7.jpg" reason="Ảnh quá mờ ở trang 2" onRetry={() => {}} onManual={() => {}} />
        ) : (
          <Card>
            {/* narration line */}
            <div style={{ display: "flex", alignItems: "center", gap: t.space[2], marginBottom: t.space[4] }}>
              <span style={{ width: 16, height: 16, borderRadius: "50%", border: `2px solid ${t.color.neutral[200]}`, borderTopColor: t.color.primary, display: "inline-block", animation: "khe-spin .6s linear infinite" }} />
              <span style={{ fontSize: t.font.size.base, color: t.color.inkBody }}>{cur.note}</span>
            </div>
            <style>{`@keyframes khe-spin{to{transform:rotate(360deg)}}`}</style>

            {/* progressive reveal: shown fields populate, the rest are skeletons */}
            <div style={{ display: "flex", flexDirection: "column", gap: t.space[3] }}>
              {ORDER.map((k) => {
                const f = FIELD[k];
                const isShown = shown.includes(k);
                return (
                  <div key={k} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: t.space[3], minHeight: 28 }}>
                    <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, width: 130, flexShrink: 0 }}>{f.label}</span>
                    {isShown ? (
                      <span style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "space-between", gap: t.space[2] }}>
                        <span style={{ fontSize: t.font.size.base, color: t.color.ink }}>{f.value}</span>
                        {f.conf < 0.8 ? <Badge kind="needs_review" dot>sẽ nhờ bạn xác nhận</Badge> : <ConfidenceMeter value={f.conf} />}
                      </span>
                    ) : (
                      <span style={{ flex: 1 }}><Skeleton w="70%" /></span>
                    )}
                  </div>
                );
              })}
            </div>

            {phase === "done" && (
              <div style={{ marginTop: t.space[5] }}><Button size="lg">Kiểm tra & xác nhận →</Button></div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
