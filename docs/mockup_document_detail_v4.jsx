/**
 * Servanda — Chi tiết hợp đồng v4  (mockup_document_detail_v4.jsx)
 * KHE_Designer · issue #478 · reorg 3 tab theo Servanda DS v1.1
 * STATIC PROTOTYPE — scope-lock docs/mockup_*.jsx. Not production code.
 * ----------------------------------------------------------------------------
 * SCOPE: chỉ 3 tab — Tổng quan / Nội dung hợp đồng / Bên ký kết.
 *   Tab "Nghĩa vụ & Quyền lợi" KHÔNG redesign — đã có #466/#467/#468, đang
 *   implement ở #472. Tab đó render placeholder trỏ sang #472 để giữ đúng
 *   4-tab structure thật (không âm thầm xoá 1 tab khỏi IA thật).
 *
 * TOKENS/COMPONENTS: import THẬT từ mockup_design_system_v1.1.jsx (PR #473,
 *   đã merge staging), KHÔNG tự viết CSS variable riêng — bài học từ bản
 *   prototype PM lần đầu (dùng hệ token khác hẳn v1.1) + từ #468 (đã có 1 lần
 *   phải patch vì badge "Phạt" tự chế nền đặc thay vì dùng đúng biến thể
 *   outline sẵn có). Khác với mockup_document_detail_v3.jsx (mirror token
 *   inline) — v4 import thật để loại hẳn rủi ro trôi giá trị token.
 *
 * FIELD/COMPONENT THẬT — verify qua Explore agent (2026-07-03), trích dẫn
 *   file:line cụ thể trong Designer Notes cuối file. Điểm khác biệt so với
 *   task brief gốc (đã research, không phải tự suy diễn):
 *   - Term.source có 3 giá trị thật: "extracted" | "remap" | "manual" (KHÔNG
 *     phải chỉ 2 giá trị như brief). Field này CHƯA có trong API (`TermOut`
 *     schema, backend/app/schemas/documents.py:73-84) — badge nguồn field là
 *     tính năng MỚI, không phải mirror hành vi có sẵn.
 *   - Field tên thật là `contract_term` (backend/app/models/tenant.py:57),
 *     KHÔNG phải `contract_duration` (kể cả CLAUDE.md cũng ghi nhầm).
 *   - `content_status` (backend/app/models/tenant.py:227-232, migration
 *     tenant_029) có 4 giá trị thật: NULL / "skeleton" / "filled" /
 *     "truncated" — KHÔNG phải "skeleton"/"complete". 0% expose ở API
 *     (`ClauseOut` không có field này) + 0% frontend.
 *   - `DocumentRelationship.relationship_type` — xác nhận đúng 3 giá trị:
 *     "amends" / "references_framework" / "annex" (backend/app/schemas/
 *     relationships.py:13, backend/app/services/relationships.py:19). Model
 *     comment cũ (tenant.py:280) ghi "MVP 2-value" là STALE — đừng tin. 0%
 *     frontend UI.
 *   - `clause_count` KHÔNG phải cột lưu trong DB — tính động qua COUNT query
 *     (backend/app/routers/documents.py:430-434, 623-625). Mockup tính
 *     `clauses.length`, không hardcode field riêng.
 *   - ConfidenceMeter (frontend/src/components/ConfidenceMeter.tsx:6-23) +
 *     SignatureBadge (DocumentDetail.tsx:109-124) XÁC NHẬN đang dùng
 *     success/xanh lá thật hôm nay — không phải giả định, có thật.
 *   - "Loại hợp đồng" disabled khi clause_count===0 + "Thời hạn hợp đồng" tint
 *     xám — XÁC NHẬN đúng hành vi/copy thật (DocumentDetail.tsx:970-1027),
 *     copy gốc dùng nguyên văn trong mockup này.
 *
 * 4 QUYẾT ĐỊNH MỞ (3 từ PM #478 + 1 tự phát hiện khi research) — đóng khung
 *   callout riêng bên dưới, KHÔNG tự quyết ngầm, chờ Kevin ratify:
 *   Q1: ConfidenceMeter/SignatureBadge màu success → đổi done/warning?
 *   Q2: UI cho content_status (two-pass extraction progress) — vào scope?
 *   Q3: UI cho DocumentRelationship (amends/annex/references_framework)?
 *   Q4 (mới, Designer phát hiện): Term.source="remap" chưa được brief nhắc
 *       tới — cần quyết định hiển thị thế nào (khác "extracted" hay gộp
 *       chung?).
 */
import React, { useState } from "react";
import {
  tokens as t, Button, Card, Modal, Badge,
} from "./mockup_design_system_v1.1.jsx";

/* ===========================================================================
 * REAL FIELD MAPS — mirrored verbatim from source of truth
 * frontend/src/lib/labels.ts:22-34 (DOC_TYPE_GROUP_LABELS)
 * backend/modules/extraction/schemas.py:74-86 (DOC_TYPE_GROUPS enum, same order)
 * ========================================================================= */
const DOC_TYPE_GROUP_LABELS = {
  dan_su: "Dân sự",
  thuong_mai: "Thương mại",
  lao_dong: "Lao động",
  bat_dong_san: "Bất động sản",
  van_tai_logistics: "Vận tải & Logistics",
  xay_dung: "Xây dựng",
  cong_nghe_ip: "Công nghệ & IP",
  tai_chinh: "Tài chính",
  bao_dam: "Bảo đảm",
  hanh_chinh: "Hành chính",
  other: "Khác",
};

/* Lifecycle enum — backend/app/models/tenant.py:58, services/lifecycle.py.
 * Derived: active/expiring/expired. Manual-override-only: settled/suspended
 * (routers/documents.py:713-721 PATCH restricts writes to these 2 + null). */
const LIFECYCLE_VALUES = ["active", "expiring", "expired", "settled", "suspended"];

/* ===========================================================================
 * SAMPLE DATA — same underlying contract as v3 (ALPHATECH ↔ Minh Phát) for
 * easy side-by-side diff, but field SHAPES now match real models exactly.
 * ========================================================================= */
const DOC = {
  id: 8,
  filename: "license_phanmem_IP.pdf",
  doc_type_group: "cong_nghe_ip",
  contract_term: "24 tháng (01/04/2026 – 31/03/2028)",
  lifecycle_status: "active",
  has_signature: true,
  signature_pages: [8, 9],
  upload_date: "2026-06-20",
  signing_date: "2026-03-15",

  terms: [
    { id: 1, field_name: "doi_tac", label: "Đối tác", field_value: "Cty Phần Mềm ALPHATECH", confidence: 0.97, needs_review: false, source: "extracted" },
    { id: 2, field_name: "ngay_ky", label: "Ngày ký", field_value: "15/03/2026", confidence: 0.95, needs_review: false, source: "extracted" },
    { id: 3, field_name: "ngay_hieu_luc", label: "Ngày hiệu lực", field_value: "01/04/2026", confidence: 0.93, needs_review: false, source: "extracted" },
    { id: 4, field_name: "thoi_han_hd", label: "Thời hạn", field_value: "24 tháng", confidence: 0.90, needs_review: false, source: "remap", remapped_note: "Map lại sau khi đổi loại hợp đồng → Công nghệ & IP" },
    { id: 5, field_name: "gia_tri_hd", label: "Giá trị HĐ", field_value: "18.000.000 đ/tháng", confidence: 0.71, needs_review: true, source: "extracted" },
    { id: 6, field_name: "bao_mat", label: "Điều khoản bảo mật", field_value: "5 năm kể từ ngày chấm dứt HĐ", confidence: null, needs_review: false, source: "manual" },
    { id: 7, field_name: "phat_vi_pham", label: "Phạt vi phạm", field_value: "8%/năm trên số tiền chậm", confidence: null, needs_review: false, source: "manual" },
  ],

  parties: [
    {
      id: "p1", name: "Cty Phần Mềm ALPHATECH", role_label: "Bên A (cung cấp)", is_self: false,
      address: "Tầng 12, Tòa nhà Innovation, 123 Nguyễn Huệ, Q.1, TP.HCM",
      representative: "Nguyễn Văn Minh — Giám đốc", contact: "contact@alphatech.vn · 028-3823-4567",
      tax_code: "0316789012", aliases: ["ALPHATECH", "Bên A"],
    },
    {
      id: "p2", name: "Cty TNHH Thương Mại Minh Phát", role_label: "Bên B (sử dụng)", is_self: true,
      address: "456 Lê Lợi, Q. Thanh Khê, TP. Đà Nẵng",
      representative: "Trần Thị Hương — Giám đốc", contact: "huong@minhphat.vn · 0236-382-1234",
      tax_code: "0401234567", aliases: ["Minh Phát", "Bên B", "MP"],
    },
  ],

  /* clause_count is NOT a stored column (routers/documents.py:430-434) —
   * computed here the same way: clauses.length. Do not hardcode a duplicate field. */
  clauses: [
    {
      id: 1, parent_id: null, level: 0, clause_path: "1", num: "Điều 1", title: "Định nghĩa",
      content_status: null, // legacy single-call path — content present at insert
      content: "Các thuật ngữ dùng trong Hợp đồng này được định nghĩa tại {{Phần mềm}} và {{Năm Tài chính}} theo Phụ lục A.",
      page: 1, cross_refs: [{ ref_text: "Phụ lục A", ref_type: "appendix", is_orphan: false, target_clause_path: null }],
    },
    {
      id: 2, parent_id: null, level: 0, clause_path: "4", num: "Điều 4", title: "Thanh toán",
      content_status: null,
      content: "(tổng hợp từ mục con)",
      page: 3,
      children: [
        { id: 21, parent_id: 2, level: 1, clause_path: "4.1", num: "4.1", title: null, content_status: "filled",
          content: "Bên B thanh toán cho Bên A 18.000.000đ/tháng, chậm nhất ngày 15 hàng tháng, theo lịch tại {{Phụ lục B}}.",
          page: 3, cross_refs: [{ ref_text: "Phụ lục B", ref_type: "appendix", is_orphan: true, target_clause_path: null }] },
        { id: 22, parent_id: 2, level: 1, clause_path: "4.2", num: "4.2", title: null, content_status: "filled",
          content: "Chậm thanh toán quá 15 ngày, áp dụng phạt theo [[Điều 9.1]].",
          page: 3, cross_refs: [{ ref_text: "Điều 9.1", ref_type: "clause", is_orphan: false, target_clause_path: "9.1" }] },
        { id: 23, parent_id: 2, level: 1, clause_path: "4.3", num: "4.3", title: null, content_status: "truncated",
          content: "",
          page: 4, note: "Pass 2 hit MAX_TOKENS — chờ Pass 3 paragraph-split retry." },
      ],
    },
    {
      id: 3, parent_id: null, level: 0, clause_path: "7", num: "Điều 7", title: "Sở hữu trí tuệ",
      content_status: "skeleton",
      content: "",
      page: 6,
      children: [
        { id: 31, parent_id: 3, level: 1, clause_path: "7.1", num: "7.1", title: null, content_status: "skeleton", content: "", page: 6 },
        { id: 32, parent_id: 3, level: 1, clause_path: "7.2", num: "7.2", title: null, content_status: "skeleton", content: "", page: 6 },
      ],
    },
    {
      id: 4, parent_id: null, level: 0, clause_path: "9", num: "Điều 9", title: "Phạt vi phạm",
      content_status: "filled",
      content: "Chậm thanh toán chịu phạt lãi 8%/năm trên số tiền chậm, tính theo [[Điều 4.1]]. Tham chiếu thêm quy định tại [[Điều 12.5]] (không tồn tại) và {{HĐ khung dịch vụ CNTT 2025}}.",
      page: 8,
      cross_refs: [
        { ref_text: "Điều 4.1", ref_type: "clause", is_orphan: false, target_clause_path: "4.1" },
        { ref_text: "Điều 12.5", ref_type: "clause", is_orphan: true, target_clause_path: null },
        { ref_text: "HĐ khung dịch vụ CNTT 2025", ref_type: "document", is_orphan: false, target_doc_id: 5, target_doc_title: "HĐ khung dịch vụ CNTT 2025" },
      ],
    },
    // Extra standalone orphan refs to exercise the capped panel realistically
    // (real case on doc #14: 14 orphan refs — panel must not grow unbounded).
    {
      id: 5, parent_id: null, level: 0, clause_path: "11", num: "Điều 11", title: "Bất khả kháng",
      content_status: "filled",
      content: "Áp dụng theo [[Điều 15.2]], [[Điều 15.3]], [[Điều 16.1]] và {{Phụ lục C}}.",
      page: 10,
      cross_refs: [
        { ref_text: "Điều 15.2", ref_type: "clause", is_orphan: true, target_clause_path: null },
        { ref_text: "Điều 15.3", ref_type: "clause", is_orphan: true, target_clause_path: null },
        { ref_text: "Điều 16.1", ref_type: "clause", is_orphan: true, target_clause_path: null },
        { ref_text: "Phụ lục C", ref_type: "appendix", is_orphan: true, target_clause_path: null },
      ],
    },
  ],

  definitions: [
    { id: "g1", term: "Phần mềm", definition: "Phần mềm Quản lý Kho ALPHATECH phiên bản 3.2 và các bản cập nhật được cung cấp trong thời hạn hợp đồng.", source_clause: "Điều 1" },
    { id: "g2", term: "Năm Tài chính", definition: "Kỳ 12 tháng bắt đầu từ ngày 01/04 đến ngày 31/03 năm sau.", source_clause: "Điều 1" },
  ],

  /* DocumentRelationship — 0% frontend today (research confirmed). Sample
   * only rendered if the Q3 proposal toggle is on (see Showcase). */
  relationships: [
    { id: 1, relationship_type: "amends", target_doc_id: 5, target_doc_title: "HĐ license phần mềm gốc (v1)", status: "confirmed" },
    { id: 2, relationship_type: "annex", target_doc_id: 21, target_doc_title: "Phụ lục A — Định nghĩa & Bảng giá", status: "confirmed" },
    { id: 3, relationship_type: "references_framework", target_doc_id: null, unresolved_ref: "HĐ khung dịch vụ CNTT 2025", status: "pending" },
  ],
};

/* ===========================================================================
 * LOCAL COMPONENTS — built from v1.1 tokens directly. v1.1 doesn't export a
 * ConfidenceMeter/LifecycleBadge (no widget for every domain vocabulary is
 * expected) — these reuse t.color/t.font/t.radius/t.space, zero new hex.
 * ========================================================================= */

/* LifecycleBadge — 5-state vocabulary doesn't map onto Badge's 13 canonical
 * kinds except "settled"→kind="done" (literally already in the vocabulary:
 * "Đã hoàn thành / Đã thanh lý"). For active/expiring/expired/suspended,
 * apply the SAME color-scarcity philosophy as the 13-badge system: a
 * healthy/ongoing contract (active) doesn't need color — reserve tone for
 * genuinely exceptional states (color rule #2: max ONE red zone/screen). */
function LifecycleBadge({ status }) {
  if (status === "settled") return <Badge kind="done">Đã thanh lý</Badge>;
  const MAP = {
    active: { label: "Đang hiệu lực", tone: t.color.inkMuted, variant: "outline" },
    expiring: { label: "Sắp hết hạn", tone: t.color.warning, variant: "solid" },
    expired: { label: "Hết hạn", tone: t.color.danger, variant: "solid" },
    suspended: { label: "Tạm dừng", tone: t.color.inkMuted, variant: "outline" },
  };
  const s = MAP[status] || MAP.active;
  const solid = s.variant === "solid";
  const TONE_TINT = { [t.color.warning]: t.color.warning_soft, [t.color.danger]: t.color.danger_soft };
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", fontFamily: t.font.family,
      fontSize: t.font.size.xs, fontWeight: t.font.weight.medium,
      padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill,
      background: solid ? TONE_TINT[s.tone] : "transparent",
      color: s.tone, border: solid ? "none" : `1px solid ${s.tone}`,
    }}>{s.label}</span>
  );
}

/* ConfidenceMeter — TWO variants for Q1 (open decision). Legacy = today's real
 * production colors (frontend/src/components/ConfidenceMeter.tsx:6-23,
 * success/warning). V11 = PM-suggested v1.1-native fix (done/warning, no
 * green — v1.1 has no success token at all). Toggle picks which renders. */
function ConfidenceMeter({ value, variant }) {
  const pct = Math.round(value * 100);
  const low = value < 0.8;
  const legacyGreen = "#15803D"; // NOT a v1.1 token — shown only to label what's being replaced
  const fg = variant === "legacy" ? (low ? t.color.warning : legacyGreen) : (low ? t.color.warning : t.color.done);
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: t.space[2], fontFamily: t.font.family }}>
      <div style={{ width: 56, height: 4, borderRadius: t.radius.pill, background: t.color.n200, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: fg }} />
      </div>
      <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: fg, fontVariantNumeric: "tabular-nums" }}>{pct}%</span>
    </div>
  );
}

function SignatureBadge({ hasSig, variant }) {
  if (hasSig == null) return null;
  const legacyGreen = "#15803D";
  const legacyGreenSoft = "#E9F6EE";
  const signedTone = variant === "legacy" ? legacyGreen : t.color.done;
  const signedBg = variant === "legacy" ? legacyGreenSoft : t.color.done_soft;
  return hasSig
    ? <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, background: signedBg, color: signedTone, fontFamily: t.font.family }}>Đã ký</span>
    : <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, padding: `2px ${t.space[2]}px`, borderRadius: t.radius.pill, background: t.color.warning_soft, color: t.color.warning, fontFamily: t.font.family }}>Chưa ký</span>;
}

/* content_status indicator — Q2 proposal, opt-in only (see Showcase toggle).
 * 4 real values: null / skeleton / filled / truncated. */
function ContentStatusIndicator({ status }) {
  if (!status) return null; // legacy single-call clauses show nothing — no regression
  const MAP = {
    skeleton: { label: "Đang tải nội dung…", tone: t.color.info, pct: 33 },
    filled: { label: "Đã tải xong", tone: t.color.done, pct: 100 },
    truncated: { label: "Cần tải lại (quá dài)", tone: t.color.warning, pct: 66 },
  };
  const s = MAP[status];
  if (!s) return null;
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: t.space[2], fontFamily: t.font.family }}>
      <div style={{ width: 48, height: 4, borderRadius: t.radius.pill, background: t.color.n200, overflow: "hidden" }}>
        <div style={{ width: `${s.pct}%`, height: "100%", background: s.tone }} />
      </div>
      <span style={{ fontSize: t.font.size.xs, color: s.tone, fontWeight: t.font.weight.medium }}>{s.label}</span>
    </div>
  );
}

/* DocumentRelationship chip — Q3 proposal, opt-in only. */
function RelationshipChip({ rel }) {
  const LABELS = { amends: "Sửa đổi", annex: "Phụ lục của", references_framework: "Tham chiếu khung" };
  const label = LABELS[rel.relationship_type] || rel.relationship_type;
  const target = rel.target_doc_title || rel.unresolved_ref;
  const pending = rel.status === "pending";
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: t.space[2], padding: `${t.space[2]}px ${t.space[3]}px`,
      borderRadius: t.radius.control, border: `1px solid ${pending ? t.color.n300 : t.color.borderStrong}`,
      background: pending ? t.color.paper : t.color.surface, fontFamily: t.font.family,
    }}>
      <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, textTransform: "uppercase", letterSpacing: t.font.tracking.label }}>{label}</span>
      <span style={{ fontSize: t.font.size.sm, color: t.color.ink }}>{target}</span>
      {pending && <span style={{ fontSize: t.font.size.xs, color: t.color.inkFaint }}>(chưa xác định tài liệu đích)</span>}
    </div>
  );
}

/* OpenDecisionCallout — unmistakable "NOT decided" framing, per acceptance
 * criteria: "3 quyết định mở đóng khung callout rõ ràng, không tự quyết ngầm." */
function OpenDecisionCallout({ qid, title, children }) {
  return (
    <div style={{
      border: `2px dashed ${t.color.warning}`, borderRadius: t.radius.card,
      padding: t.space[4], background: t.color.warning_soft, marginBottom: t.space[5],
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: t.space[2], marginBottom: t.space[2] }}>
        <span style={{ fontSize: t.font.size.label, fontWeight: t.font.weight.semibold, color: t.color.warning, textTransform: "uppercase", letterSpacing: t.font.tracking.label }}>
          Quyết định mở — {qid} — chờ Kevin ratify
        </span>
      </div>
      <div style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[2] }}>{title}</div>
      {children}
    </div>
  );
}

/* ===========================================================================
 * TERM ROW — label màu ink đậm (fix theo feedback), rẽ nhánh theo source
 * ========================================================================= */
function TermRow({ term, meterVariant }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: `${t.space[2]}px 0`, borderBottom: `1px solid ${t.color.n200}`, gap: t.space[3] }}>
      <div style={{ display: "flex", alignItems: "center", gap: t.space[2], minWidth: 0 }}>
        <span style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{term.label}</span>
        {term.needs_review && <Badge kind="unclear">Cần kiểm tra</Badge>}
        {term.source === "remap" && (
          <span title={term.remapped_note} style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, fontStyle: "italic" }}>
            (đã map lại)
          </span>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: t.space[3], flexShrink: 0 }}>
        <span style={{ fontSize: t.font.size.base, color: t.color.ink, fontVariantNumeric: "tabular-nums" }}>{term.field_value || "—"}</span>
        {term.source === "manual" ? (
          <Badge kind="manual">Nhập tay</Badge>
        ) : term.confidence != null ? (
          <ConfidenceMeter value={term.confidence} variant={meterVariant} />
        ) : null}
      </div>
    </div>
  );
}

/* ===========================================================================
 * TAB 1 — TỔNG QUAN
 * ========================================================================= */
function TabOverview({ doc, meterVariant, sigVariant, showContentStatus, showRelationships }) {
  const clauseCount = doc.clauses.length;
  const disabled = clauseCount === 0;

  return (
    <div>
      {/* "Loại hợp đồng" — real disabled logic + real copy (DocumentDetail.tsx:970-1012) */}
      <Card title="Loại hợp đồng" style={{ marginBottom: t.space[5] }}>
        <select
          disabled={disabled}
          title={disabled ? "Chưa có clause text — không thể map lại loại tài liệu này" : undefined}
          value={doc.doc_type_group}
          style={{
            width: "100%", height: 44, padding: `0 ${t.space[3]}px`, borderRadius: t.radius.control,
            border: `1px solid ${t.color.borderStrong}`, fontFamily: t.font.family, fontSize: t.font.size.base,
            color: t.color.ink, background: disabled ? t.color.paper : t.color.surface,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
        >
          {Object.entries(DOC_TYPE_GROUP_LABELS).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
        </select>
        <div style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, marginTop: t.space[2] }}>
          {disabled
            ? "Tài liệu chưa có nội dung điều khoản (clause) nên không thể map lại loại."
            : "Đổi loại sẽ map lại các trường trích xuất theo mẫu mới."}
        </div>
      </Card>

      {/* "Thời hạn hợp đồng" — bỏ tint xám (fix theo feedback), Card mặc định */}
      <Card title="Thời hạn hợp đồng" style={{ marginBottom: t.space[5] }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: t.font.size.base, color: t.color.ink, fontVariantNumeric: "tabular-nums" }}>{doc.contract_term}</span>
          <LifecycleBadge status={doc.lifecycle_status} />
        </div>
      </Card>

      {doc.has_signature != null && (
        <div style={{ display: "flex", alignItems: "center", gap: t.space[3], marginBottom: t.space[5] }}>
          <SignatureBadge hasSig={doc.has_signature} variant={sigVariant} />
          {doc.signature_pages && <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted }}>Trang {doc.signature_pages.join(", ")}</span>}
        </div>
      )}

      {/* Terms */}
      <Card title="Trường đã trích xuất" style={{ marginBottom: t.space[5] }}>
        {doc.terms.map((term) => <TermRow key={term.id} term={term} meterVariant={meterVariant} />)}
      </Card>

      {showRelationships && doc.relationships.length > 0 && (
        <Card title="Quan hệ tài liệu (đề xuất — Q3)" style={{ marginBottom: t.space[5] }}>
          <div style={{ display: "flex", flexDirection: "column", gap: t.space[2] }}>
            {doc.relationships.map((rel) => <RelationshipChip key={rel.id} rel={rel} />)}
          </div>
        </Card>
      )}
    </div>
  );
}

/* ===========================================================================
 * TAB 2 — NỘI DUNG HỢP ĐỒNG
 * ========================================================================= */

function collectOrphans(clauses) {
  const out = [];
  function walk(list, ancestorNum) {
    list.forEach((c) => {
      (c.cross_refs || []).forEach((r) => { if (r.is_orphan) out.push({ ...r, from: c.num || ancestorNum }); });
      if (c.children) walk(c.children, c.num);
    });
  }
  walk(clauses);
  return out;
}

function renderClauseContent(content, onOpenOrphanModal) {
  if (!content) return null;
  const parts = content.split(/(\{\{[^}]+\}\}|\[\[[^\]]+\]\])/g);
  return parts.map((part, i) => {
    const termMatch = part.match(/^\{\{([^}]+)\}\}$/);
    const refMatch = part.match(/^\[\[([^\]]+)\]\]$/);
    if (termMatch) {
      return (
        <span key={i} title="Định nghĩa — xem Glossary" style={{ borderBottom: `1px dashed ${t.color.primary}`, color: t.color.primary, cursor: "help" }}>
          {termMatch[1]}
        </span>
      );
    }
    if (refMatch) {
      return (
        <button key={i} onClick={onOpenOrphanModal} style={{
          border: "none", background: "transparent", padding: 0, cursor: "pointer",
          color: t.color.danger, borderBottom: `1px dashed ${t.color.danger}`, fontFamily: t.font.family, fontSize: "inherit",
        }} title="Không tìm thấy điều khoản đích">
          {refMatch[1]}
        </button>
      );
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

function ClauseCrossRefChips({ crossRefs }) {
  if (!crossRefs || crossRefs.length === 0) return null;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: t.space[2], marginTop: t.space[2] }}>
      {crossRefs.filter((r) => !r.is_orphan).map((r, i) => {
        const isDoc = r.ref_type === "document";
        return (
          <span key={i} style={{
            fontSize: t.font.size.xs, color: isDoc ? t.color.info : t.color.primary,
            border: `1px solid ${isDoc ? t.color.info : t.color.primary}`, borderRadius: t.radius.pill,
            padding: `1px ${t.space[2]}px`,
          }}>
            {isDoc ? `→ ${r.target_doc_title}` : r.ref_text}
          </span>
        );
      })}
    </div>
  );
}

function ClauseTreeItem({ clause, depth, onOpenOrphanModal, showContentStatus }) {
  const [expanded, setExpanded] = useState(depth === 0);
  const hasChildren = clause.children && clause.children.length > 0;
  const isStub = clause.content === "(tổng hợp từ mục con)"; // real marker, DocumentDetail.tsx:1194
  const isLoading = clause.content_status === "skeleton";

  return (
    <div>
      <button onClick={() => setExpanded(!expanded)} style={{
        display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%",
        padding: `${t.space[3]}px ${t.space[4]}px`, paddingLeft: t.space[4] + depth * 24,
        border: "none", borderBottom: `1px solid ${t.color.n200}`, background: t.color.surface,
        cursor: "pointer", fontFamily: t.font.family, textAlign: "left",
      }}>
        <span style={{ display: "flex", alignItems: "center", gap: t.space[2] }}>
          {depth > 0 && <span style={{ color: t.color.n300, fontSize: t.font.size.xs }}>└</span>}
          <span style={{ fontSize: depth === 0 ? t.font.size.base : t.font.size.sm, fontWeight: depth === 0 ? t.font.weight.semibold : t.font.weight.medium, color: t.color.ink }}>
            {clause.num}{clause.title ? ` — ${clause.title}` : ""}
          </span>
          {hasChildren && <span style={{ fontSize: t.font.size.xs, color: t.color.inkMuted, background: t.color.done_soft, borderRadius: t.radius.control, padding: `0 ${t.space[1]}px` }}>{clause.children.length}</span>}
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: t.space[3] }}>
          {showContentStatus && <ContentStatusIndicator status={clause.content_status} />}
          <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>{expanded ? "▴" : "▾"}</span>
        </span>
      </button>

      {expanded && !hasChildren && (
        <div style={{ padding: `${t.space[3]}px ${t.space[4]}px`, paddingLeft: t.space[4] + depth * 24 + 16 }}>
          {isLoading ? (
            <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontStyle: "italic" }}>Đang tải nội dung điều khoản…</div>
          ) : isStub ? (
            <div style={{ fontSize: t.font.size.sm, color: t.color.inkFaint, fontStyle: "italic" }}>(tổng hợp từ mục con)</div>
          ) : (
            <>
              <div style={{ fontSize: t.font.size.base, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
                {renderClauseContent(clause.content, onOpenOrphanModal)}
              </div>
              <ClauseCrossRefChips crossRefs={clause.cross_refs} />
              {clause.note && <div style={{ fontSize: t.font.size.xs, color: t.color.warning, marginTop: t.space[2] }}>{clause.note}</div>}
            </>
          )}
        </div>
      )}

      {expanded && hasChildren && clause.children.map((child) => (
        <ClauseTreeItem key={child.id} clause={child} depth={depth + 1} onOpenOrphanModal={onOpenOrphanModal} showContentStatus={showContentStatus} />
      ))}
    </div>
  );
}

function OrphanRefPanel({ orphans, onOpenModal }) {
  if (orphans.length === 0) return null;
  const teaser = orphans.slice(0, 2);
  return (
    <div style={{ background: t.color.danger_soft, border: `1px solid ${t.color.danger}33`, borderRadius: t.radius.control, padding: t.space[4], marginBottom: t.space[5], maxHeight: 160, overflow: "hidden" }}>
      <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.danger, marginBottom: t.space[2] }}>
        {orphans.length} tham chiếu không tìm thấy
      </div>
      {teaser.map((o, i) => (
        <div key={i} style={{ fontSize: t.font.size.xs, color: t.color.ink, marginBottom: 2 }}>
          {o.from} → "{o.ref_text}"
        </div>
      ))}
      {orphans.length > teaser.length && (
        <button onClick={onOpenModal} style={{ border: "none", background: "transparent", color: t.color.danger, fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, cursor: "pointer", padding: 0, marginTop: t.space[2] }}>
          Xem tất cả ({orphans.length}) →
        </button>
      )}
    </div>
  );
}

function GlossarySection({ definitions }) {
  const [open, setOpen] = useState(false);
  if (definitions.length === 0) return null;
  return (
    <div style={{ border: `1px solid ${t.color.n200}`, borderRadius: t.radius.card, marginBottom: t.space[5], overflow: "hidden" }}>
      <button onClick={() => setOpen(!open)} style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", padding: t.space[3], background: t.color.paper, border: "none", cursor: "pointer", fontFamily: t.font.family }}>
        <span style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink }}>Định nghĩa ({definitions.length})</span>
        <span style={{ color: t.color.inkMuted }}>{open ? "▴" : "▾"}</span>
      </button>
      {open && definitions.map((d) => (
        <div key={d.id} style={{ padding: t.space[3], borderTop: `1px solid ${t.color.n200}` }}>
          <div style={{ fontSize: t.font.size.sm, fontWeight: t.font.weight.semibold, color: t.color.primary }}>{d.term}</div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.ink, marginTop: 2 }}>{d.definition}</div>
          <div style={{ fontSize: t.font.size.xs, color: t.color.inkFaint, marginTop: 2 }}>{d.source_clause}</div>
        </div>
      ))}
    </div>
  );
}

function TabClauses({ doc, showContentStatus }) {
  const [modalOpen, setModalOpen] = useState(false);
  const orphans = collectOrphans(doc.clauses);

  return (
    <div>
      <OrphanRefPanel orphans={orphans} onOpenModal={() => setModalOpen(true)} />
      <GlossarySection definitions={doc.definitions} />
      <div style={{ border: `1px solid ${t.color.n200}`, borderRadius: t.radius.card, overflow: "hidden" }}>
        {doc.clauses.map((c) => <ClauseTreeItem key={c.id} clause={c} depth={0} onOpenOrphanModal={() => setModalOpen(true)} showContentStatus={showContentStatus} />)}
      </div>

      <Modal open={modalOpen} title={`Tham chiếu không tìm thấy (${orphans.length})`} onClose={() => setModalOpen(false)}
        footer={<Button onClick={() => setModalOpen(false)}>Đóng</Button>}>
        <div style={{ maxHeight: 320, overflowY: "auto", display: "flex", flexDirection: "column", gap: t.space[3] }}>
          {orphans.map((o, i) => (
            <div key={i} style={{ paddingBottom: t.space[2], borderBottom: i < orphans.length - 1 ? `1px solid ${t.color.n200}` : "none" }}>
              <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted }}>{o.from}</div>
              <div style={{ fontSize: t.font.size.base, color: t.color.ink }}>"{o.ref_text}" <span style={{ color: t.color.inkFaint, fontSize: t.font.size.xs }}>({o.ref_type})</span></div>
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
}

/* ===========================================================================
 * TAB 3 — BÊN KÝ KẾT
 * ========================================================================= */
function PartyCard({ party }) {
  const isSelf = party.is_self;
  return (
    <div style={{
      padding: t.space[5], borderRadius: t.radius.card, marginBottom: t.space[4],
      border: isSelf ? `2px solid ${t.color.primary}` : `1px solid ${t.color.n200}`,
      background: isSelf ? t.color.primarySoft : t.color.surface,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: t.space[2], marginBottom: t.space[1] }}>
        <span style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink }}>{party.name}</span>
        {isSelf && <span style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.semibold, color: t.color.primary, background: t.color.surface, padding: `1px ${t.space[2]}px`, borderRadius: t.radius.pill }}>Bên mình</span>}
      </div>
      <div style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, marginBottom: t.space[3] }}>{party.role_label}</div>
      <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: `${t.space[2]}px ${t.space[3]}px` }}>
        {[
          ["Người đại diện", party.representative],
          ["Địa chỉ", party.address],
          ["Mã số thuế", party.tax_code],
          ["Liên hệ", party.contact],
        ].map(([label, value]) => (
          <React.Fragment key={label}>
            <span style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, fontWeight: t.font.weight.medium }}>{label}</span>
            <span style={{ fontSize: t.font.size.base, color: t.color.ink }}>{value || "—"}</span>
          </React.Fragment>
        ))}
      </div>
      {party.aliases && party.aliases.length > 0 && (
        <div style={{ display: "flex", gap: t.space[1], marginTop: t.space[3], flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: t.font.size.xs, color: t.color.inkFaint }}>gọi chung là</span>
          {party.aliases.map((a) => (
            <span key={a} style={{ fontSize: t.font.size.xs, fontWeight: t.font.weight.medium, color: t.color.inkMuted, background: t.color.done_soft, padding: `0 ${t.space[2]}px`, borderRadius: t.radius.pill }}>{a}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function TabParties({ parties }) {
  const self = parties.find((p) => p.is_self);
  const others = parties.filter((p) => !p.is_self);
  return (
    <div>
      {self && <PartyCard party={self} />}
      {others.map((p) => <PartyCard key={p.id} party={p} />)}
    </div>
  );
}

/* ===========================================================================
 * TAB BAR — 4 tab THẬT (DocumentDetail.tsx:2014-2031), obligations = placeholder
 * ========================================================================= */
const TABS = [
  { key: "overview", label: "Tổng quan" },
  { key: "obligations", label: "Nghĩa vụ & Quyền lợi" },
  { key: "clauses", label: "Nội dung hợp đồng" },
  { key: "parties", label: "Bên ký kết" },
];

function TabBar({ active, onChange, counts }) {
  return (
    <div style={{ display: "flex", gap: t.space[2], borderBottom: `1px solid ${t.color.n200}`, marginBottom: t.space[5] }}>
      {TABS.map((tb) => {
        const isActive = tb.key === active;
        return (
          <button key={tb.key} onClick={() => onChange(tb.key)} style={{
            padding: `${t.space[2]}px ${t.space[3]}px`, background: "transparent", border: "none",
            borderBottom: `2px solid ${isActive ? t.color.primary : "transparent"}`, cursor: "pointer",
            fontFamily: t.font.family, fontSize: t.font.size.base,
            fontWeight: isActive ? t.font.weight.semibold : t.font.weight.medium,
            color: isActive ? t.color.primary : t.color.inkMuted,
            display: "flex", alignItems: "center", gap: t.space[2],
          }}>
            {tb.label}
            {counts[tb.key] != null && (
              <span style={{ fontSize: t.font.size.xs, fontVariantNumeric: "tabular-nums", background: isActive ? t.color.primarySoft : t.color.done_soft, color: isActive ? t.color.primary : t.color.inkMuted, borderRadius: t.radius.pill, padding: `0 ${t.space[2]}px` }}>
                {counts[tb.key]}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/* ===========================================================================
 * SHOWCASE
 * ========================================================================= */
export default function DocumentDetailV4() {
  const [tab, setTab] = useState("overview");
  const [meterVariant, setMeterVariant] = useState("legacy");
  const [sigVariant, setSigVariant] = useState("legacy");
  const [showContentStatus, setShowContentStatus] = useState(false);
  const [showRelationships, setShowRelationships] = useState(false);

  const counts = { obligations: 5, clauses: DOC.clauses.length, parties: DOC.parties.length };

  return (
    <div style={{ minHeight: "100vh", background: t.color.paper, fontFamily: t.font.family }}>
      <div style={{ maxWidth: t.layout.maxWidth, margin: "0 auto", padding: t.space[6] }}>

        <div style={{ marginBottom: t.space[5] }}>
          <div style={{ fontSize: t.font.size.label, color: t.color.inkMuted, textTransform: "uppercase", letterSpacing: t.font.tracking.label, fontWeight: t.font.weight.semibold }}>
            Chi tiết hợp đồng · #478 · v4
          </div>
          <h1 style={{ fontSize: t.font.size.display, fontWeight: t.font.weight.semibold, color: t.color.ink, margin: `${t.space[1]}px 0 0` }}>
            HĐ license phần mềm — {DOC.parties.find((p) => !p.is_self)?.name}
          </h1>
        </div>

        {/* Preview controls for the 4 open decisions */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: t.space[4], marginBottom: t.space[5], padding: t.space[3], background: t.color.surface, border: `1px solid ${t.color.n200}`, borderRadius: t.radius.control, fontSize: t.font.size.xs, color: t.color.inkMuted, alignItems: "center" }}>
          <strong style={{ color: t.color.ink }}>Preview controls:</strong>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={meterVariant === "v1.1"} onChange={(e) => setMeterVariant(e.target.checked ? "v1.1" : "legacy")} /> ConfidenceMeter dùng v1.1 (Q1)
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={sigVariant === "v1.1"} onChange={(e) => setSigVariant(e.target.checked ? "v1.1" : "legacy")} /> SignatureBadge dùng v1.1 (Q1)
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={showContentStatus} onChange={(e) => setShowContentStatus(e.target.checked)} /> Hiện content_status (Q2, đề xuất)
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <input type="checkbox" checked={showRelationships} onChange={(e) => setShowRelationships(e.target.checked)} /> Hiện DocumentRelationship (Q3, đề xuất)
          </label>
        </div>

        <TabBar active={tab} onChange={setTab} counts={counts} />

        <div style={{ background: t.color.surface, borderRadius: t.radius.card, padding: t.space[5], boxShadow: t.elevation.e1 }}>
          {tab === "overview" && (
            <TabOverview doc={DOC} meterVariant={meterVariant} sigVariant={sigVariant} showContentStatus={showContentStatus} showRelationships={showRelationships} />
          )}
          {tab === "obligations" && (
            <div style={{ textAlign: "center", padding: t.space[8], color: t.color.inkMuted }}>
              <div style={{ fontSize: t.font.size.base, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[2] }}>
                Ngoài scope #478
              </div>
              <div style={{ fontSize: t.font.size.sm, maxWidth: 420, margin: "0 auto" }}>
                Tab này đã có design + implementation riêng — xem #466 (BA gốc), #467/#468 (mockup), #472 (Frontend đang làm). Không redesign lại ở đây để tránh 2 nguồn sự thật song song.
              </div>
            </div>
          )}
          {tab === "clauses" && <TabClauses doc={DOC} showContentStatus={showContentStatus} />}
          {tab === "parties" && <TabParties parties={DOC.parties} />}
        </div>

        {/* 4 open decisions */}
        <div style={{ marginTop: t.space[7] }}>
          <h2 style={{ fontSize: t.font.size.xl, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[4] }}>
            Quyết định mở — chờ Kevin ratify
          </h2>

          <OpenDecisionCallout qid="Q1">
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>ConfidenceMeter</code> (frontend/src/components/ConfidenceMeter.tsx:6-23) và <code>SignatureBadge</code> (DocumentDetail.tsx:109-124)
              đang dùng <strong>success/xanh lá thật</strong> trên production hôm nay — xác nhận, không phải giả định. v1.1 <strong>không có token success</strong> nào
              cả (triết lý "hoàn thành = xám lặng, không ăn mừng"). Toggle "ConfidenceMeter/SignatureBadge dùng v1.1" ở trên để so sánh: hiện tại (xanh lá,
              không phải token v1.1) vs đề xuất (<code>done</code> cho trạng thái tốt, <code>warning</code> cho trạng thái cần chú ý — giữ nguyên ngưỡng 0.8
              hiện có). Đây là đổi hành vi production thật — cần Kevin quyết trước khi Frontend áp dụng.
            </div>
          </OpenDecisionCallout>

          <OpenDecisionCallout qid="Q2">
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>content_status</code> (backend/app/models/tenant.py:227-232, migration <code>tenant_029</code>, #449/#443 two-pass map-reduce extraction)
              có 4 giá trị thật: <code>NULL</code> / <code>"skeleton"</code> / <code>"filled"</code> / <code>"truncated"</code> — <strong>hoàn toàn khác</strong> cơ chế
              stub hiện tại (<code>content === '(tổng hợp từ mục con)'</code>, dùng cho node cha tổng hợp, không liên quan two-pass). Field này{" "}
              <strong>chưa có trong API</strong> (<code>ClauseOut</code> không expose) và <strong>0% frontend</strong>. Toggle "Hiện content_status" ở trên
              để xem đề xuất (progress bar nhẹ: skeleton=đang tải, filled=xong, truncated=cần tải lại). Cần Kevin quyết có vào scope sprint này không — nếu có,
              cần thêm field vào <code>ClauseOut</code> trước.
            </div>
          </OpenDecisionCallout>

          <OpenDecisionCallout qid="Q3">
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>DocumentRelationship.relationship_type</code> — xác nhận đúng 3 giá trị <code>amends</code> / <code>references_framework</code> / <code>annex</code>{" "}
              (backend/app/schemas/relationships.py:13, services/relationships.py:19 — model comment ở tenant.py:280 nói "MVP 2-value" là <strong>stale</strong>,
              đừng theo). <strong>0% frontend UI</strong> tồn tại hôm nay. Toggle "Hiện DocumentRelationship" ở trên để xem đề xuất chip trong tab Tổng quan
              (mẫu: 1 amends, 1 annex đã xác nhận, 1 references_framework còn <code>pending</code>/chưa xác định tài liệu đích). Phát hiện phụ khi research — cờ lên,
              không tự thêm vào scope.
            </div>
          </OpenDecisionCallout>

          <OpenDecisionCallout qid="Q4 — Designer tự phát hiện, không có trong brief #478">
            <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed }}>
              <code>Term.source</code> thật có <strong>3 giá trị</strong>, không phải 2 như brief: <code>"extracted"</code> / <code>"remap"</code> / <code>"manual"</code>{" "}
              (backend/app/models/tenant.py:87). <code>"remap"</code> xảy ra khi user đổi "Loại hợp đồng" ở card phía trên và field được trích lại theo mẫu mới
              (routers/documents.py:1392). Mockup này hiện field đó với nhãn phụ "(đã map lại)" — nhưng đây là <strong>quyết định UI tạm thời của Designer</strong>,
              chưa được PM/Kevin ratify. Ngoài ra: field <code>source</code> hiện <strong>chưa hề có trong API</strong> (<code>TermOut</code> schema không expose) —
              nghĩa là toàn bộ badge "Nhập tay"/"đã map lại" trong mockup này là <strong>tính năng mới cần backend thêm field</strong>, không phải mirror UI có sẵn.
            </div>
          </OpenDecisionCallout>
        </div>

        {/* Designer notes */}
        <div style={{ marginTop: t.space[7], padding: t.space[5], borderRadius: t.radius.card, border: `2px dashed ${t.color.n300}`, background: t.color.surface }}>
          <div style={{ fontSize: t.font.size.lg, fontWeight: t.font.weight.semibold, color: t.color.ink, marginBottom: t.space[4] }}>
            Designer Notes — #478
          </div>
          <div style={{ fontSize: t.font.size.sm, color: t.color.ink, lineHeight: t.font.lineHeight.relaxed, display: "flex", flexDirection: "column", gap: t.space[4] }}>
            <div><strong>Import thật, không mirror:</strong> khác với <code>mockup_document_detail_v3.jsx</code> (mirror token DS v0.2 inline), file này <code>import</code> trực tiếp <code>tokens</code>/<code>Button</code>/<code>Card</code>/<code>Modal</code>/<code>Badge</code> từ <code>mockup_design_system_v1.1.jsx</code> — loại hẳn rủi ro trôi giá trị token mà 2 bản prototype trước (PM's HTML, và badge Phạt ở #468) đều gặp phải.</div>
            <div><strong>4 tab thật, 1 placeholder:</strong> giữ đúng cấu trúc TabKey thật (overview/obligations/clauses/parties, DocumentDetail.tsx:2014-2031) — tab Nghĩa vụ &amp; Quyền lợi render placeholder trỏ #472, không âm thầm bỏ tab khỏi IA thật.</div>
            <div><strong>Card "Loại hợp đồng" + "Thời hạn hợp đồng":</strong> disabled logic + copy/tooltip lấy nguyên văn từ DocumentDetail.tsx:970-1027 (không diễn giải lại). Card "Thời hạn" bỏ hẳn <code>bg-surface-alt</code> tint theo feedback Kevin — dùng <code>Card</code> mặc định từ v1.1.</div>
            <div><strong>Term label:</strong> đổi <code>ink-muted</code> → <code>ink</code> đậm hơn theo feedback (dễ quét nhanh khi list dài).</div>
            <div><strong>Badge "Nhập tay":</strong> dùng đúng <code>&lt;Badge kind="manual"&gt;</code> có sẵn trong v1.1 (verify: <code>BADGE_KINDS.manual = {"{"} tone: inkMuted, variant: outline {"}"}</code>) — không tự chế class, đúng bài học từ #468.</div>
            <div><strong>Cross-ref 3 loại thật:</strong> <code>ref_type: "clause"|"appendix"|"document"</code> (ClauseCrossRef model, tenant.py:255-269) — mockup render cả 3, không chỉ 2 loại như v3 (v3 chưa có case cross-document). Orphan panel cap <code>maxHeight: 160px</code> + "Xem tất cả (N) →" mở <code>Modal</code> thật từ v1.1, cuộn riêng bên trong — fix case thật 14 orphan refs trên doc #14.</div>
            <div><strong>PartyCard:</strong> self trước (tint <code>primarySoft</code> + badge "Bên mình"), field grid theo đúng field <code>Party</code> model (address/contact/representative/tax_code/aliases, tenant.py:142-161).</div>
            <div><strong>4 quyết định mở:</strong> đóng khung <code>OpenDecisionCallout</code> riêng biệt (viền đứt vàng, nhãn "chờ Kevin ratify") — 3 từ PM #478 + 1 tự phát hiện (Term.source="remap"). Mỗi callout trích dẫn file:line thật, không suy diễn.</div>
            <div><strong>Không thuộc scope:</strong> tab Nghĩa vụ &amp; Quyền lợi (đã có #466/#467/#468/#472). Đổi hành vi backend/API (kể cả khi mockup đề xuất field mới như <code>content_status</code> expose ở <code>ClauseOut</code> — đó là việc Backend, không tự làm ở đây).</div>
            <div><strong>Dependencies để Frontend áp dụng được:</strong> Q1 cần Kevin chốt màu → Frontend đổi CSS class trong <code>ConfidenceMeter.tsx</code>/<code>SignatureBadge</code>. Q2 cần Backend thêm <code>content_status</code> vào <code>ClauseOut</code> trước khi FE dùng được. Q3 cần Backend thêm endpoint expose <code>DocumentRelationship</code> cho FE (hiện chưa có route nào trả về, theo research). Q4 cần Backend thêm <code>source</code> vào <code>TermOut</code>.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
