/**
 * Khế — Admin · Document List  (mockup_admin_document_list_v0.1.jsx)
 * KHE_Designer · Phase 2 · issue #24
 * STATIC PROTOTYPE — scope docs/mockup_*.jsx. Imports Design System v0.1.
 *
 * FR-DR / FR-SR: list all documents with status filter
 * (processing / extracted / needs_review) + search by đối tác / loại.
 * `documents` table per Sprint 0 #23.
 */
import React, { useState } from "react";
import { tokens as t, Button, Card, Table, Badge, Input, EmptyState } from "./mockup_design_system_v0.1.jsx";

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

const cols = [
  { key: "ten", label: "Tài liệu" },
  { key: "loai", label: "Loại" },
  { key: "doi_tac", label: "Đối tác" },
  { key: "han", label: "Ngày hết hạn" },
  { key: "status", label: "Trạng thái" },
];

function FilterChip({ active, label, onClick }) {
  return (
    <button onClick={onClick} style={{
      padding: `${t.space[1]}px ${t.space[3]}px`, borderRadius: t.radius.pill,
      fontFamily: t.font.family, fontSize: t.font.size.sm, fontWeight: t.font.weight.medium,
      cursor: "pointer", border: `1px solid ${active ? t.color.primary : t.color.border}`,
      background: active ? t.color.primarySoft : t.color.surface,
      color: active ? t.color.primary : t.color.inkMuted,
    }}>{label}</button>
  );
}

export default function AdminDocumentList() {
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const rows = ALL
    .filter((r) => filter === "all" || r.status === filter)
    .filter((r) => !q || (r.ten + r.doi_tac).toLowerCase().includes(q.toLowerCase()));

  return (
    <div style={{ minHeight: "100vh", background: t.color.surfaceAlt, fontFamily: t.font.family, padding: t.space[6] }}>
      <div style={{ maxWidth: 920, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: t.space[3] }}>
          <h1 style={{ fontSize: t.font.size["2xl"], fontWeight: t.font.weight.bold, color: t.color.ink, margin: 0 }}>Tài liệu</h1>
          <Button>+ Tải tài liệu</Button>
        </div>

        <div style={{ display: "flex", gap: t.space[3], alignItems: "center", flexWrap: "wrap", margin: `${t.space[5]}px 0` }}>
          <div style={{ width: 260 }}>
            <Input value={q} onChange={setQ} placeholder="Tìm theo tên / đối tác…" />
          </div>
          <div style={{ display: "flex", gap: t.space[2], flexWrap: "wrap" }}>
            {FILTERS.map((f) => <FilterChip key={f.key} active={filter === f.key} label={f.label} onClick={() => setFilter(f.key)} />)}
          </div>
        </div>

        <Card style={{ padding: 0 }}>
          <div style={{ padding: t.space[2] }}>
            {rows.length === 0 ? (
              <EmptyState icon="🗂️" title="Không có tài liệu phù hợp" description="Thử bỏ bộ lọc hoặc tải tài liệu mới." />
            ) : (
              <Table
                columns={cols} rows={rows}
                renderCell={(key, row) => {
                  if (key === "status") {
                    const lbl = { processing: "đang xử lý", extracted: "đã bóc tách", needs_review: "⚠ cần kiểm tra" }[row.status];
                    return <Badge kind={row.status}>{lbl}</Badge>;
                  }
                  if (key === "ten") return <a href="#" style={{ color: t.color.primary, fontWeight: t.font.weight.medium, textDecoration: "none" }}>{row.ten}</a>;
                  return row[key];
                }}
              />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
