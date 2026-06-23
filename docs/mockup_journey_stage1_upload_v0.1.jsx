/**
 * Khế — Journey · Stage 1 Upload  (mockup_journey_stage1_upload_v0.1.jsx)
 * KHE_Designer · issue #198 Phase C · Design System v0.2 + journey primitives v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Stage 1 = first upload. Big drop zone + "📷 Chụp ảnh" (ảnh giấy thật — concierge
 * reality). Instant ack + honest expectation ("~30 giây/tài liệu"). Batch OK.
 * States shown: idle · dragging · uploaded-ack · partial-success (failure path).
 */
import React, { useState } from "react";
import { tokens as t, Button, Card } from "./mockup_design_system_v0.2.jsx";
import { PartialUpload } from "./mockup_journey_primitives_v0.1.jsx";

function Dropzone({ dragging }) {
  return (
    <div style={{
      border: `2px dashed ${dragging ? t.color.primary : t.color.borderStrong}`,
      background: dragging ? t.color.primarySoft : t.color.surfaceSunken,
      borderRadius: t.radius.lg, padding: t.space[9], textAlign: "center",
      transition: `all ${t.motion.base} ${t.motion.ease}`, fontFamily: t.font.family,
    }}>
      <div style={{ fontSize: 40, marginBottom: t.space[2] }}>{dragging ? "📥" : "📄"}</div>
      <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink }}>
        {dragging ? "Thả vào đây" : "Kéo-thả hoặc chụp ảnh hợp đồng"}
      </div>
      <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: t.space[1] }}>
        PDF · Word · ảnh (JPG/PNG) — tải nhiều cùng lúc cũng được
      </div>
      <div style={{ marginTop: t.space[4], display: "flex", gap: t.space[2], justifyContent: "center", flexWrap: "wrap" }}>
        <Button>Chọn tệp</Button>
        <Button variant="secondary">📷 Chụp ảnh</Button>
      </div>
      <div style={{ marginTop: t.space[3], fontSize: t.font.size.xs, color: t.color.inkSubtle }}>
        Khế đọc xong khoảng <strong>~30 giây</strong> mỗi tài liệu.
      </div>
    </div>
  );
}

export default function Stage1Upload() {
  const [view, setView] = useState("idle");
  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.wide }}>Issue #198 · Stage 1</span>
        <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: `${t.space[1]}px 0 0` }}>Tải hợp đồng đầu tiên</h1>
        <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[1] }}>
          Bản gốc được lưu bất biến; Khế chỉ đọc để bóc hạn (D-06).
        </p>

        <div style={{ display: "flex", gap: t.space[2], margin: `${t.space[5]}px 0` }}>
          {[["idle", "Idle"], ["dragging", "Dragging"], ["ack", "Uploaded ack"], ["partial", "Partial success"]].map(([k, l]) => (
            <button key={k} onClick={() => setView(k)} style={{ padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer", fontFamily: t.font.family, fontSize: t.font.size.sm, fontWeight: t.font.weight.medium, border: `1px solid ${view === k ? t.color.primary : t.color.border}`, background: view === k ? t.color.primarySoft : t.color.surface, color: view === k ? t.color.primary : t.color.inkMuted }}>{l}</button>
          ))}
        </div>

        {view === "idle" && <Dropzone dragging={false} />}
        {view === "dragging" && <Dropzone dragging />}
        {view === "ack" && (
          <Card>
            <div style={{ display: "flex", alignItems: "center", gap: t.space[3] }}>
              <span style={{ fontSize: 28 }}>✅</span>
              <div>
                <div style={{ fontSize: t.font.size.md, fontWeight: t.font.weight.semibold, color: t.color.ink }}>Đã nhận 3 tài liệu</div>
                <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>Khế đang đọc — bạn không cần đợi ở đây, sẽ báo khi xong (~30s/tài liệu).</div>
              </div>
            </div>
            <div style={{ marginTop: t.space[4] }}><Button variant="secondary">Xem tiến trình</Button></div>
          </Card>
        )}
        {view === "partial" && <PartialUpload ok={2} failed={["HĐ thuê kho.jpg"]} onReviewFailed={() => {}} />}
      </div>
    </div>
  );
}
