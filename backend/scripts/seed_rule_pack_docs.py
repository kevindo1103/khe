#!/usr/bin/env python3
"""Seed virtual rule-pack documents for a tenant (#494).

These metadata-only documents represent common regulations (rule packs) that
obligations can be linked to. The script is idempotent: rule packs with the
same title are skipped on subsequent runs.

Usage (from backend/ directory):
    python scripts/seed_rule_pack_docs.py --tenant <tenant_id>
"""
import argparse
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.db.database import get_tenant_session
from app.models.tenant import Document, Obligation


RULE_PACKS = [
    {
        "title": "Nghị định 70/2025/NĐ-CP — Hợp đồng điện tử",
        "source_rule_id": "nd70/2025",
        "obligations": [
            {
                "description": "Lưu trữ hợp đồng điện tử theo quy định",
                "obligation_type": "reporting",
                "direction": "nghĩa_vụ",
            },
            {
                "description": "Cung cấp bản sao hợp đồng theo yêu cầu của đối tác",
                "obligation_type": "review",
                "direction": "quyền_lợi",
                "milestone_trigger": "event",
                "trigger_condition": "Bên đối tác yêu cầu bản sao",
                "trigger_delay_days": 5,
            },
        ],
    },
    {
        "title": "Luật Bảo hiểm xã hội 2024",
        "source_rule_id": "luat-bhxh-2024",
        "obligations": [
            {
                "description": "Đóng BHXH đầy đủ cho người lao động",
                "obligation_type": "payment",
                "direction": "nghĩa_vụ",
                "due_date": "2026-01-15",
            },
            {
                "description": "Khai báo biến động lao động hàng tháng",
                "obligation_type": "reporting",
                "direction": "nghĩa_vụ",
            },
        ],
    },
    {
        "title": "Nghị định 13/2025/NĐ-CP — Bảo vệ dữ liệu cá nhân",
        "source_rule_id": "nd13/2025",
        "obligations": [
            {
                "description": "Thông báo xử lý dữ liệu cá nhân với cơ quan nhà nước",
                "obligation_type": "reporting",
                "direction": "nghĩa_vụ",
            },
            {
                "description": "Cập nhật chính sách bảo mật khi có quy định mới",
                "obligation_type": "review",
                "direction": "nghĩa_vụ",
                "milestone_trigger": "event",
                "trigger_condition": "Ban hành văn bản pháp luật mới về bảo vệ dữ liệu",
            },
        ],
    },
    {
        "title": "Thông tư 78/2024/TT-BTC — Thuế TNDN",
        "source_rule_id": "tt78/2024",
        "obligations": [
            {
                "description": "Quyết toán thuế TNDN theo năm tài chính",
                "obligation_type": "reporting",
                "direction": "nghĩa_vụ",
            },
        ],
    },
    {
        "title": "Luật Lao động 2019 (sửa đổi, bổ sung 2024)",
        "source_rule_id": "luat-lao-dong-2024",
        "obligations": [
            {
                "description": "Ký kết hợp đồng lao động bằng văn bản",
                "obligation_type": "standing",
                "direction": "nghĩa_vụ",
            },
            {
                "description": "Thông báo tuyển dụng và đăng ký lao động",
                "obligation_type": "reporting",
                "direction": "nghĩa_vụ",
            },
        ],
    },
]


def _initial_status(ob: dict) -> str:
    if ob.get("milestone_trigger") == "event" and not ob.get("due_date"):
        return "waiting_trigger"
    return "pending"


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed virtual rule-pack documents for a tenant")
    parser.add_argument("--tenant", required=True, help="Tenant ID to seed rule packs into")
    args = parser.parse_args()

    db = get_tenant_session(args.tenant)
    try:
        seeded = 0
        skipped = 0
        for pack in RULE_PACKS:
            existing = (
                db.query(Document)
                .filter(
                    Document.tenant_id == args.tenant,
                    Document.title == pack["title"],
                    Document.doc_type == "rule_pack",
                )
                .first()
            )
            if existing is not None:
                skipped += 1
                continue

            doc = Document(
                tenant_id=args.tenant,
                file_name=pack["title"],
                file_path="",  # virtual doc, no PDF
                title=pack["title"],
                doc_type="rule_pack",
                status="needs_review",
            )
            db.add(doc)
            db.flush()

            for ob in pack["obligations"]:
                db.add(
                    Obligation(
                        tenant_id=args.tenant,
                        document_id=doc.id,
                        description=ob["description"],
                        obligation_type=ob.get("obligation_type", "other"),
                        direction=ob.get("direction"),
                        source="rule_pack",
                        source_rule_id=pack["source_rule_id"],
                        milestone_trigger=ob.get("milestone_trigger", "date"),
                        trigger_condition=ob.get("trigger_condition"),
                        trigger_delay_days=ob.get("trigger_delay_days"),
                        due_date=ob.get("due_date"),
                        status=_initial_status(ob),
                    )
                )

            seeded += 1

        db.commit()
        print(f"[OK] Seeded {seeded} rule-pack document(s); {skipped} already present.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
