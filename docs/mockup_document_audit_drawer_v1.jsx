/**
 * Servanda — Audit Drawer "Lịch sử chỉnh sửa"  (mockup_document_audit_drawer_v1.jsx)
 * KHE_Designer · issue #312 finding F1 (D-07 audit trail, BLOCKING for #281 close)
 * STATIC PROTOTYPE — scope-lock docs/mockup_*.jsx. Not production code.
 * ----------------------------------------------------------------------------
 * WHY THIS FILE: #312 F1 — D-07 requires every field edit to be visible
 *   ("edit → Event"), but the document-detail page has no surface to READ
 *   that event history. F2 (sidebar badge) and F3 (H1 self-party) from the
 *   same issue are already baked into mockup_obligation_tab_v3.jsx /
 *   mockup_document_detail_v4.jsx — this file closes the remaining,
 *   blocking finding.
 *
 * TOKENS/COMPONENTS: real import from mockup_design_system_v1.1.jsx, same
 *   discipline as v4/documents_list_v3. `AuditDrawer` itself is a NEW local
 *   component (v1.1 has no Drawer export) built from real tokens only — same
 *   pattern as LifecycleBadge/ConfidenceMeter in prior mockups.
 *
 * FIELD/COMPONENT THẬT — verified via Explore agent (2026-07-06). This is
 *   NOT a speculative-API mockup: a real read endpoint already exists.
 *
 *   - `Event` model (backend/app/models/tenant.py:168-184): generic
 *     `entity_type` + `entity_id` (not separate document_id/term_id/
 *     clause_id columns) + free-form `event_type` string + `actor`
 *     (username or `"system"`) + `payload` (JSON blob, SHAPE VARIES per
 *     call site — old/new or old_value/new_value depending on where it's
 *     logged, no single fixed schema) + `created_at`.
 *   - Read endpoint **EXISTS**: `GET /documents/{doc_id}/events`
 *     (routers/documents.py:1663-1716) → `EventListOut` { document_id,
 *     total, limit, offset, items: EventOut[] }. `EventOut` = { id,
 *     event_type, entity_type, entity_id, actor, created_at, payload }.
 *     Pagination: `limit` (default 50, max 200) + `offset` — no page-number
 *     UI anywhere in this app (confirmed in #481 research too), so this
 *     mockup uses a "Tải thêm" (load more) pattern, not page numbers.
 *   - **CRITICAL GAP (flagged, not silently worked around):** the endpoint
 *     (documents.py:1693-1699) only includes rows where
 *     `entity_type == "document"` OR (`entity_type == "obligation"` AND the
 *     obligation belongs to this doc). It does **NOT** include
 *     `entity_type == "term"` or `entity_type == "party"` — even though
 *     BOTH are real, confirmed Event writes today (`documents.py:1117` term
 *     value edit, `documents.py:1229` party field edit). Term-value edits
 *     and party-field edits are D-07-compliant at the WRITE layer but
 *     currently INVISIBLE to this READ endpoint. See Q-Audit-Scope below.
 *   - `event_type` strings are inconsistently generic — `"updated"` is
 *     reused across `entity_type="term"`, `entity_type="obligation"`, and
 *     relationship edits. Disambiguation requires a lookup keyed on
 *     `(entity_type, event_type)`, never `event_type` alone — see
 *     `EVENT_LABELS` below. Obligation `"updated"` additionally needs
 *     payload inspection (`old_status`/`new_status`/`fulfilled_at`) to tell
 *     "hoàn thành" from "hoàn tác" from a plain status change (D-14/D-15).
 *   - **Zero existing frontend pattern to mirror** — grepped the whole app;
 *     the only "event" reference in the frontend is a static label on the
 *     Obligations page ("ghi Event", `Obligations.tsx:266`), not an actual
 *     rendered list. This drawer is the first Event-list UI in Servanda.
 *   - No TS type for `Event`/`EventOut` exists in the frontend yet — that's
 *     new work for whoever implements this (`for:frontend`, per #312).
 *
 * OPEN DECISION (chờ Kevin/PM ratify, không tự quyết ngầm):
 *   Q-Audit-Scope: Term/party edits bị loại khỏi endpoint hiện tại. Mockup
 *     mặc định (toggle TẮT) chỉ hiện đúng những gì API thật trả về hôm nay
 *     (document + obligation events). Toggle "Hiện cả sửa trường/bên
 *     (đề xuất)" demo nếu Backend mở filter — nhưng đây là thay đổi Backend
 *     thật (documents.py:1693-1699), không phải chỉ UI.
 */
import React, { useState } from "react";
import {
  tokens as t, Button, Badge, EmptyState,
} from "./mockup_design_system_v1.1.jsx";

/* ===========================================================================
 * EVENT LABEL LOOKUP — keyed (entity_type:event_type), NOT event_type alone
 * (event_type "updated" is reused across term/obligation/relationship —
 * confirmed via research; a flat lookup on event_type would collide).
 * ========================================================================= */
const EVENT_LABELS = {
  "document:document_uploaded": "Tải lên tài liệu",
  "document:document_field_edited": "Sửa trường tài liệu",
  "document:definition_edited": "Sửa định nghĩa",
  "document:definition_deleted": "Xóa định nghĩa",
  "document:clause_edited": "Sửa điều khoản",
  "document:self_party_confirmed": "Xác nhận bên mình",
  "document:document_confirmed_by_user": "Xác nhận tài liệu",
  "document:doc_type_corrected": "Sửa loại hợp đồng",
  "document:clause_re_derived": "Đọc lại điều khoản",
  "document:extraction_retriggered": "Trích xuất lại",
  "document:re_read_triggered": "Kích hoạt đọc lại",
  "document:extraction_performed": "Trích xuất hoàn tất",
  "document:extraction_failed": "Trích xuất lỗi",
  "document:extraction_two_pass_completed": "Trích xuất 2 lượt hoàn tất",
  "term:updated": "Sửa giá trị trường",
  "party:party_field_edited": "Sửa thông tin bên",
  "obligation:updated": "Cập nhật nghĩa vụ", // special-cased, see describeObligationUpdate()
  "obligation:evidence_attached": "Đính kèm minh chứng",
  "obligation:reminder_snoozed": "Hoãn nhắc",
};

function eventLabel(ev) {
  return EVENT_LABELS[`${ev.entity_type}:${ev.event_type}`] || `${ev.entity_type}: ${ev.event_type}`;
}

/* obligation:updated needs payload inspection — D-14/D-15 (fulfilled_at is
 * the cascade anchor, revert is a distinct real flow, plain status change
 * is a 3rd case). Same generic event_type, 3 different real meanings. */
function describeObligationUpdate(payload) {
  if (!payload) return "Cập nhật nghĩa vụ";
  if (payload.new_status === "done" && payload.fulfilled_at) return "Hoàn thành nghĩa vụ";
  if (payload.old_status === "done" && payload.new_status !== "done") return "Hoàn tác hoàn thành";
  if (payload.new_status) return `Đổi trạng thái → ${payload.new_status}`;
  return "Cập nhật nghĩa vụ";
}

/* ===========================================================================
 * SAMPLE DATA — same document as v4 (ALPHATECH ↔ Minh Phát), real Event
 * shape (entity_type/entity_id/event_type/actor/payload/created_at). Payload
 * KEY NAMES are illustrative (research confirmed shape "varies per call
 * site," not one fixed schema) — not verified byte-for-byte per event_type.
 * ========================================================================= */
const DOCUMENT_ID = 8;

// Events the REAL API returns today (entity_type document|obligation only)
const VISIBLE_EVENTS = [
  { id: 1, entity_type: "document", entity_id: DOCUMENT_ID, event_type: "document_uploaded", actor: "system", created_at: "2026-06-20T09:12:00", payload: { file_name: "license_phanmem_IP.pdf" } },
  { id: 2, entity_type: "document", entity_id: DOCUMENT_ID, event_type: "extraction_performed", actor: "system", created_at: "2026-06-20T09:13:40", payload: { model: "gemini-2.5-flash", fields_extracted: 7 } },
  { id: 3, entity_type: "document", entity_id: DOCUMENT_ID, event_type: "doc_type_corrected", actor: "huong.minhphat", created_at: "2026-06-20T10:02:11", payload: { old_value: "hd_dan_su", new_value: "cong_nghe_ip" } },
  { id: 4, entity_type: "document", entity_id: DOCUMENT_ID, event_type: "self_party_confirmed", actor: "huong.minhphat", created_at: "2026-06-20T10:05:03", payload: { party_name: "Cty TNHH Thương Mại Minh Phát" } },
  { id: 5, entity_type: "document", entity_id: DOCUMENT_ID, event_type: "clause_edited", actor: "huong.minhphat", created_at: "2026-06-21T14:30:22", payload: { clause_num: "Điều 4.1", old_content: "Bên B thanh toán 15.000.000đ/tháng.", new_content: "Bên B thanh toán 18.000.000đ/tháng." } },
  { id: 6, entity_type: "document", entity_id: DOCUMENT_ID, event_type: "re_read_triggered", actor: "huong.minhphat", created_at: "2026-06-21T14:31:05", payload: {} },
  { id: 7, entity_type: "document", entity_id: DOCUMENT_ID, event_type: "clause_re_derived", actor: "system", created_at: "2026-06-21T14:31:40", payload: { obligations_updated: 2 } },
  { id: 8, entity_type: "document", entity_id: DOCUMENT_ID, event_type: "document_confirmed_by_user", actor: "huong.minhphat", created_at: "2026-06-22T08:15:00", payload: {} },
  { id: 9, entity_type: "obligation", entity_id: 101, event_type: "updated", actor: "huong.minhphat", created_at: "2026-06-28T16:20:00", payload: { old_status: "pending", new_status: "done", fulfilled_at: "2026-06-28T16:20:00", fulfilled_by: "huong.minhphat" } },
  { id: 10, entity_type: "obligation", entity_id: 101, event_type: "evidence_attached", actor: "huong.minhphat", created_at: "2026-06-28T16:21:15", payload: { evidence_doc_ids: [42] } },
];

// Events that ARE logged (real, confirmed) but INVISIBLE to the real API
// today — only shown when the Q-Audit-Scope proposal toggle is on.
const HIDDEN_TERM_PARTY_EVENTS = [
  { id: 11, entity_type: "term", entity_id: 5, event_type: "updated", actor: "huong.minhphat", created_at: "2026-06-20T10:10:30", payload: { field_name: "gia_tri_hd", old_value: "15.000.000 đ/tháng", new_value: "18.000.000 đ/tháng" } },
  { id: 12, entity_type: "party", entity_id: 1, event_type: "party_field_edited", actor: "huong.minhphat", created_at: "2026-06-20T10:12:00", payload: { field: "representative", old_value: "Nguyễn Văn Minh", new_value: "Nguyễn Văn Minh — Giám đốc" } },
];

/* ===========================================================================
 * RENDER HELPERS
 * ========================================================================= */
function formatTimestamp(iso) {
  const d = new Date(iso);
  const dm = `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
  const hm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return `${dm} · ${hm}`;
}

function actorLabel(actor) {
  return actor === "system" ? "Hệ thống" : actor;
}

/* Generic payload-diff renderer — handles the two real shapes seen in
 * research (old_value/new_value, old_content/new_content) and falls back to
 * a flat key:value listing for anything else, since payload has no single
 * fixed schema across call sites. */
function PayloadDiff({ payload }) {
  if (!payload || Object.keys(payload).length === 0) return null;
  const oldKey = ["old_value", "old_content"].find((k) => k in payload);
  const newKey = ["new_value", "new_content"].find((k) => k in payload);
  if (oldKey && newKey) {
    return (
      <div style={{ fontSize: t.font.size.xs, marginTop: t.space[1] }}>
        <span style={{ color: t.color.danger, textDecoration: "line-through" }}>{String(payload[oldKey])}</span>
        {" → "}
        <span style={{ color: t.color.done, fontWeight: t.font.weight.medium }}>{String(payload[newKey])}</span>
      </div>
    );
  }
  const entries = Object.entries(payload).filter(([k]) => k !== "field" && k !== "field_name" && k !== "clause_num");
  if (entries.length === 0) return null;
  return (
    <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[1] }}>
      {entries.map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : String(v)}`).join(" · ")}
    </div>
  );
}

function EventRow({ ev, hidden }) {
  const isObligationUpdate = ev.entity_type === "obligation" && ev.event_type === "updated";
  const label = isObligationUpdate ? describeObligationUpdate(ev.payload) : eventLabel(ev);
  const fieldNote = ev.payload?.field_name || ev.payload?.field || ev.payload?.clause_num;
  return (
    <div style={{
      padding: `${t.space[3]}px ${t.space[4]}px`, borderBottom: `1px solid ${t.color.n200}`,
      opacity: hidden ? 0.85 : 1,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: t.space[3] }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: t.space[2], flexWrap: "wrap" }}>
            <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{label}</span>
            {fieldNote && <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>· {fieldNote}</span>}
            {hidden && <Badge kind="unclear">chưa hiện trên API</Badge>}
          </div>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, marginTop: 2 }}>
            {actorLabel(ev.actor)} · {formatTimestamp(ev.created_at)}
          </div>
          <PayloadDiff payload={ev.payload} />
        </div>
      </div>
    </div>
  );
}

/* ===========================================================================
 * AUDIT DRAWER — new local component (v1.1 has no Drawer export), built
 * from real tokens only. Slide-in from the right, own overlay (same
 * treatment as v1.1's Modal overlay color), own scroll region.
 * ========================================================================= */
function AuditDrawer({ open, onClose, events, showHidden, pageSize, onLoadMore }) {
  const visible = showHidden ? [...events, ...HIDDEN_TERM_PARTY_EVENTS].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) : events;
  const shown = visible.slice(0, pageSize);
  const hasMore = visible.length > pageSize;

  return (
    <>
      <div onClick={onClose} style={{
        position: "fixed", inset: 0, background: t.color.overlay, zIndex: t.z.overlay,
        opacity: open ? 1 : 0, pointerEvents: open ? "auto" : "none",
        transition: `opacity ${t.motion.base} ${t.motion.ease}`,
      }} />
      <div style={{
        position: "fixed", top: 0, right: 0, bottom: 0, width: 420, maxWidth: "100vw",
        background: t.color.surface, boxShadow: t.elevation.e3, zIndex: t.z.modal,
        display: "flex", flexDirection: "column", fontFamily: t.font.family,
        transform: open ? "translateX(0)" : "translateX(100%)",
        transition: `transform ${t.motion.base} ${t.motion.ease}`,
      }}>
        <div style={{ padding: t.space[5], borderBottom: `1px solid ${t.color.n200}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.semibold, color: t.color.ink }}>Lịch sử chỉnh sửa</div>
            <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginTop: 2 }}>{visible.length} sự kiện</div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>Đóng</Button>
        </div>

        <div style={{ flex: 1, overflowY: "auto" }}>
          {shown.length === 0 ? (
            <EmptyState title="Chưa có sự kiện nào" description="Mọi lần sửa trường, sửa điều khoản, xác nhận... sẽ hiện ở đây." />
          ) : (
            shown.map((ev) => <EventRow key={`${ev.entity_type}-${ev.id}`} ev={ev} hidden={ev.entity_type === "term" || ev.entity_type === "party"} />)
          )}
        </div>

        {hasMore && (
          <div style={{ padding: t.space[4], borderTop: `1px solid ${t.color.n200}`, textAlign: "center" }}>
            <Button variant="secondary" size="sm" onClick={onLoadMore}>Tải thêm ({visible.length - shown.length} còn lại)</Button>
          </div>
        )}
      </div>
    </>
  );
}

/* ===========================================================================
 * SHOWCASE
 * ========================================================================= */
export default function AuditDrawerShowcase() {
  const [open, setOpen] = useState(true);
  const [showHidden, setShowHidden] = useState(false);
  const [pageSize, setPageSize] = useState(6);

  return (
    <div style={{ minHeight: "100vh", background: t.color.paper, fontFamily: t.font.family }}>
      <div style={{ maxWidth: t.layout.maxWidth, margin: "0 auto", padding: t.space[6] }}>

        <div style={{ marginBottom: t.space[5] }}>
          <div style={{ fontSize: t.font.size.label, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: t.font.tracking.label, fontWeight: t.font.weight.semibold }}>
            Chi tiết hợp đồng · #312 F1 · Audit Drawer
          </div>
          <h1 style={{ fontSize: t.font.size.display, fontWeight: t.font.weight.semibold, color: t.color.ink, margin: `${t.space[1]}px 0 0` }}>Lịch sử chỉnh sửa (D-07)</h1>
          <p style={{ fontSize: t.font.size.base, color: t.color.inkMuted, marginTop: t.space[2], maxWidth: 620, lineHeight: t.font.lineHeight.relaxed }}>
            Trigger thật: nút "Lịch sử chỉnh sửa" ở header/footer trang chi tiết hợp đồng (mockup_document_detail_v4.jsx). Mở drawer để xem — đóng bằng nút Đóng, click ra ngoài, hoặc Esc (áp dụng khi Frontend impl).
          </p>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: t.space[4], marginBottom: t.space[5], padding: t.space[3], background: t.color.surface, border: `1px solid ${t.color.n200}`, borderRadius: t.radius.control, fontSize: t.font.size.xs, color: t.color.inkMuted, alignItems: "center" }}>
          <strong style={{ color: t.color.ink }}>Preview controls:</strong>
          <Button size="sm" onClick={() => setOpen(true)}>Mở Lịch sử chỉnh sửa</Button>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={showHidden} onChange={(e) => setShowHidden(e.target.checked)} /> Hiện cả sửa trường/bên (Q-Audit-Scope, đề xuất)
          </label>
        </div>

        <div style={{ background: t.color.surface, borderRadius: t.radius.card, border: `1px solid ${t.color.n200}`, padding: t.space[6], textAlign: "center", color: t.color.inkFaint }}>
          (Nội dung trang chi tiết hợp đồng — xem mockup_document_detail_v4.jsx. Drawer mở đè lên bên phải.)
        </div>

        <AuditDrawer open={open} onClose={() => setOpen(false)} events={VISIBLE_EVENTS} showHidden={showHidden} pageSize={pageSize} onLoadMore={() => setPageSize(pageSize + 6)} />

        {/* Open decision */}
        <div style={{ marginTop: t.space[7] }}>
          <h2 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[4] }}>Quyết định mở — chờ Kevin/PM ratify</h2>
          <div style={{ border: `2px dashed ${t.color.warning}`, borderRadius: t.radius.card, padding: t.space[4], background: t.color.warning_soft }}>
            <div style={{ fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: t.color.warning, textTransform: "uppercase", letterSpacing: t.font.tracking.label, marginBottom: t.space[2] }}>Q-Audit-Scope — chờ ratify</div>
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>GET /documents/{"{doc_id}"}/events</code> (routers/documents.py:1663-1716) hiện chỉ trả <code>entity_type="document"</code> và <code>entity_type="obligation"</code> thuộc doc. <strong>Sửa giá trị trường (`term`) và sửa thông tin bên ký kết (`party`) ĐÃ được ghi Event đầy đủ</strong> (documents.py:1117, 1229) nhưng <strong>vô hình trên endpoint này</strong> — D-07 đúng ở tầng ghi, sai ở tầng đọc. Toggle "Hiện cả sửa trường/bên" ở trên demo drawer sẽ trông thế nào nếu mở filter — nhưng đây là thay đổi Backend thật (mở rộng <code>entity_type</code> filter tại documents.py:1693-1699), không phải chỉ UI. Cần Kevin/PM quyết: mở filter trước khi #312 đóng, hay ship phase 1 chỉ document+obligation rồi follow-up riêng.
            </div>
          </div>
        </div>

        {/* Designer Notes */}
        <div style={{ marginTop: t.space[7], padding: t.space[5], borderRadius: t.radius.card, border: `2px dashed ${t.color.n300}`, background: t.color.surface }}>
          <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[4] }}>Designer Notes — #312 F1</div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed, display: "flex", flexDirection: "column", gap: t.space[4] }}>
            <div><strong>API thật đã tồn tại:</strong> <code>GET /documents/{"{doc_id}"}/events</code> — không phải mockup speculative. Trigger/limit/offset/response shape đều lấy từ endpoint thật, không bịa.</div>
            <div><strong>Lookup (entity_type, event_type), không phải event_type đơn:</strong> chuỗi <code>"updated"</code> dùng chung cho term/obligation/relationship — <code>EVENT_LABELS</code> key theo cặp để tránh đụng nhãn. <code>obligation:updated</code> cần soi thêm <code>payload</code> (D-14/D-15: hoàn thành vs hoàn tác vs đổi trạng thái thường) qua <code>describeObligationUpdate()</code>.</div>
            <div><strong>Payload không có schema cố định</strong> — research xác nhận "shape varies per call site". <code>PayloadDiff</code> chỉ nhận dạng 2 cặp khóa thấy trong code thật (<code>old_value/new_value</code>, <code>old_content/new_content</code>), còn lại fallback liệt kê key:value thô. Tên khóa payload trong sample data là minh họa hợp lý, KHÔNG verify từng call site 1-1.</div>
            <div><strong>Không pagination số trang</strong> — app không dùng page-number ở đâu cả (xác nhận qua research #481 cũng vậy). Dùng "Tải thêm (N còn lại)" khớp <code>limit</code>/<code>offset</code> thật.</div>
            <div><strong>Drawer là component MỚI, không có trong v1.1</strong> — xây từ token thật (overlay từ Modal's overlay color, elevation e3, motion tokens) chứ không tự chế giá trị. Đúng pattern đã dùng cho LifecycleBadge/ConfidenceMeter ở các mockup trước.</div>
            <div><strong>Không có UI nào để tham khảo</strong> — grep toàn app xác nhận đây là Event-list UI đầu tiên của Servanda. Không copy được pattern có sẵn.</div>
            <div><strong>Không thuộc scope:</strong> filter theo entity_type/actor (API thật chưa hỗ trợ query param này, chỉ limit/offset) · TS type cho Event/EventOut (việc Frontend khi impl) · mở rộng entity_type filter ở Backend (chờ Q-Audit-Scope ratify).</div>
            <div><strong>Dependencies để Frontend áp dụng:</strong> gắn trigger button vào header/footer thật của <code>DocumentDetail.tsx</code> (v4 mockup dùng làm tham chiếu layout). Cần TS type mới cho Event/EventOut. Q-Audit-Scope cần Backend sửa filter trước khi hiện term/party thật (không phải mock toggle).</div>
          </div>
        </div>
      </div>
    </div>
  );
}
