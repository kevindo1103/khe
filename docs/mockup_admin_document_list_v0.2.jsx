/**
 * Khế — Admin · Document List v0.2  (mockup_admin_document_list_v0.2.jsx)
 * KHE_Designer · steady-state re-layout on Design System v0.2 · supersedes v0.1
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx.
 *
 * Re-layout: doc count + status filter chips (a11y aria-pressed), search, Table.
 * Distinguishes the TWO empty states honestly (4-state matrix spirit):
 *   • filter/search no-match → "không có tài liệu phù hợp" (notFound)
 *   • truly zero docs (cold tenant) → onboarding CTA, NOT a no-match message.
 * FR-DR / FR-SR · doc_type_group (DEC-029) shown as the "Loại" column.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Table, Badge, Input, EmptyState } from "./mockup_design_system_v0.2.jsx";

const ALL = [
  { id: 1, ten: "HĐ thuê mặt bằng Q7", loai: "Thuê mặt bằng", doi_tac: "Cty TNHH Hải Đăng", han: "30/09/2026", status: "extracted" },
  { id: 2, ten: "HĐ cung cấp bao bì", loai: "Nhà cung cấp", doi_tac: "Cty CP Bao Bì Việt", han: "15/07/2026", status: "needs_review" },
  { id: 3, ten: "HĐ lao động — N.V.An", loai: "Lao động", doi_tac: "—", han: "Vô thời hạn", status: "processing" },
  { id: 4, ten: "HĐ thuê kho Bình Tân", loai: "Thuê mặt bằng", doi_tac: "Ông Trần Văn B", han: "01/12/2026", status: "extracted" },
];

const FILTERS = [
  { key: "all", label: "Tất cả" },
  { key: "processing", label: "Đang xử lý" },
  { key: "extracted", label: "Đã bóc tách" },
  { key: "needs_review", label: "Cần kiểm tra" },
];
const STATUS = { processing: { kind: "processing", lbl: "đang xử lý" }, extracted: { kind: "extracted", lbl: "đã bóc tách" }, needs_review: { kind: "needs_review", lbl: "cần kiểm tra" } };

const cols = [
  { key: "ten", label: "Tài liệu" }, { key: "loai", label: "Loại" },
  { key: "doi_tac", label: "Đối tác" }, { key: "han", label: "Ngày hết hạn" }, { key: "status", label: "Trạng thái" },
];

function FilterChip({ active, label, count, onClick }) {
  return (
    <button onClick={onClick} type="button" aria-pressed={active} style={{
      display: "inline-flex", alignItems: "center", gap: t.space[1],
      padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill, cursor: "pointer",
      fontFamily: t.font.family, fontSize: t.font.size.sm, fontWeight: t.font.weight.medium,
      border: `1px solid ${active ? t.color.primary : t.color.border}`,
      background: active ? t.color.primarySoft : t.color.surface, color: active ? t.color.primary : t.color.inkMuted,
    }}>{label}{count != null && <span style={{ fontSize: t.font.size.xs, opacity: .8 }}>· {count}</span>}</button>
  );
}

export default function AdminDocumentListV2() {
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const isEmptyTenant = ALL.length === 0; // cold-start vs filter no-match
  const rows = ALL
    .filter((r) => filter === "all" || r.status === filter)
    .filter((r) => !q || (r.ten + r.doi_tac).toLowerCase().includes(q.toLowerCase()));
  const count = (k) => k === "all" ? ALL.length : ALL.filter((r) => r.status === k).length;

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family }}>
      <div style={{ maxWidth: 920, margin: "0 auto", padding: t.space[7] }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: t.space[3] }}>
          <div>
            <h1 style={{ fontSize: t.font.size["3xl"], fontWeight: t.font.weight.bold, color: t.color.ink, letterSpacing: t.font.tracking.tight, margin: 0 }}>Kho tài liệu</h1>
            <p style={{ fontSize: t.font.size.sm, color: t.color.inkMuted, margin: `${t.space[1]}px 0 0` }}>{ALL.length} tài liệu đang theo dõi</p>
          </div>
          <Button>+ Tải tài liệu</Button>
        </div>

        {!isEmptyTenant && (
          <div style={{ display: "flex", gap: t.space[3], alignItems: "center", flexWrap: "wrap", margin: `${t.space[5]}px 0` }}>
            <div style={{ width: 260 }}><Input value={q} onChange={setQ} placeholder="Tìm theo tên / đối tác…" prefix="🔍" /></div>
            <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
              {FILTERS.map((f) => <FilterChip key={f.key} active={filter === f.key} label={f.label} count={count(f.key)} onClick={() => setFilter(f.key)} />)}
            </div>
          </div>
        )}

        <Card style={{ padding: 0, marginTop: isEmptyTenant ? t.space[5] : 0 }}>
          <div style={{ padding: t.space[2] }}>
            {isEmptyTenant ? (
              <EmptyState icon="＋" title="Chưa có tài liệu nào" description="Tải lên hợp đồng đầu tiên để Khế bắt đầu bóc tách và nhắc hạn." action={<Button>Tải tài liệu</Button>} />
            ) : rows.length === 0 ? (
              <EmptyState notFound title="Không có tài liệu phù hợp" description="Thử bỏ bộ lọc hoặc đổi từ khoá tìm." />
            ) : (
              <Table columns={cols} rows={rows} renderCell={(key, row) => {
                if (key === "status") { const s = STATUS[row.status]; return <Badge kind={s.kind}>{s.lbl}</Badge>; }
                if (key === "ten") return <a href="#" style={{ color: t.color.primary, fontWeight: t.font.weight.medium }}>{row.ten}</a>;
                return row[key];
              }} />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
