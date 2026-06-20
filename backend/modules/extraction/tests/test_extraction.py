"""Pure unit tests for the extraction module — no API keys / SDKs required.

Run: `python -m backend.modules.extraction.tests.test_extraction` or `pytest`.
Covers schemas, metric normalization/matching, scoring, and report rendering.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from ..schemas import (
    ALL_TYPE_SPECIFIC_FIELDS,
    BASE_CANONICAL_FIELDS,
    BENCHMARK_TARGET_FIELDS,
    CANONICAL_FIELDS,
    DOC_TYPE_GROUPS,
    TYPE_SPECIFIC_FIELDS,
    ClauseItem,
    ContractExtractionLLM,
    ContractExtractionLLMFull,
    DocType,
    ExtractedField,
    ExtractionResult,
    NamedExtractedField,
    ObligationScheduleItem,
    PartyItem,
    PaymentScheduleItem,
    TokenUsage,
)
from .. import factory
from ..factory import ExtractionUnavailable, get_extraction_provider
from ..benchmark import metrics
from ..benchmark.runner import render_report
from ..benchmark.metrics import field_match, normalize, score


def test_package_imports_without_sdks() -> None:
    # provider Protocol + schemas import with only pydantic present.
    from ..provider import VisionExtractionProvider  # noqa: F401
    from ..prompts import SYSTEM_GUARDRAIL, build_instruction

    assert "KHÔNG" in SYSTEM_GUARDRAIL  # read-only guardrail present (D-06)
    assert "JSON" in build_instruction("hd_thue_mat_bang")
    assert set(BENCHMARK_TARGET_FIELDS).issubset(set(CANONICAL_FIELDS))


def test_cost_vnd_exported_and_correct() -> None:
    from .. import USD_TO_VND, cost_vnd

    assert USD_TO_VND == 25_400.0
    usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000)
    # Gemini 2.5 Flash: $0.30 in + $2.50 out = $2.80 → 2.80 × 25,400 = 71,120đ
    result = cost_vnd(usage, 0.30, 2.50)
    assert result == 71_120.0


def test_extracted_field_defaults_safe() -> None:
    f = ExtractedField()
    assert f.value is None and f.needs_review is True and f.confidence == 0.0


def test_date_normalization_format_agnostic() -> None:
    # 05/01/2026 == 2026-01-05 == 5-1-2026 after digit-signature normalization.
    a = normalize("ngay_het_han", "05/01/2026")
    b = normalize("ngay_het_han", "2026-01-05")
    c = normalize("ngay_het_han", "5-1-2026")
    assert a == b == c
    assert normalize("ngay_het_han", None) == ""


def test_numeric_normalization_strips_separators() -> None:
    assert normalize("gia_tri_hd", "50.000.000 đ") == normalize("gia_tri_hd", "50000000")


def test_doi_tac_subset_match() -> None:
    # Predicted must cover every ground-truth party (order-independent).
    truth = "Cong ty ABC; Ong Nguyen Van X"
    assert field_match("doi_tac", "Ông Nguyễn Văn X; Công ty ABC", truth) is True
    assert field_match("doi_tac", "Cong ty ABC", truth) is False  # missing a party


def test_text_match_accent_insensitive() -> None:
    assert field_match("thoi_han_hd", "12 tháng", "12 thang") is True


def _result(fields: dict[str, str | None], *, latency=1000.0, cost=120.0, warn=False) -> ExtractionResult:
    return ExtractionResult(
        doc_type=DocType.LEASE,
        doc_type_confidence=0.95,
        fields={k: ExtractedField(value=fields.get(k), confidence=0.95, needs_review=False)
                for k in CANONICAL_FIELDS},
        provider="gemini_flash",
        model="gemini-2.5-flash",
        latency_ms=latency,
        cost_vnd=cost,
        warnings=["boom"] if warn else [],
    )


def test_scoring_accuracy_and_aggregates() -> None:
    truth = {
        "doi_tac": "Cong ty ABC; Ong X",
        "ngay_het_han": "2026-12-31",
        "gia_tri_hd": "50000000",
        "thoi_han_hd": "12 thang",
    }
    good = _result(
        {"doi_tac": "Cong ty ABC; Ong X", "ngay_het_han": "31/12/2026",
         "gia_tri_hd": "50.000.000", "thoi_han_hd": "12 tháng"},
        latency=800.0, cost=100.0,
    )
    bad = _result(
        {"doi_tac": "Cong ty ABC", "ngay_het_han": "2026-01-01",
         "gia_tri_hd": "999", "thoi_han_hd": "6 thang"},
        latency=1200.0, cost=140.0,
    )
    ps = score("gemini_flash", "gemini-2.5-flash", [(good, truth), (bad, truth)])

    assert ps.samples == 2
    assert ps.fields["ngay_het_han"].scored == 2 and ps.fields["ngay_het_han"].correct == 1
    assert ps.fields["ngay_het_han"].accuracy == 0.5
    # good matches all 4 targets, bad matches none → mean = 0.5
    assert ps.target_accuracy == 0.5
    assert ps.latency_p50 == 1000.0
    assert ps.cost_mean == 120.0
    assert ps.errors == 0


def test_unscored_when_no_ground_truth() -> None:
    # Empty ground-truth value (e.g. open-ended labor contract expiry) is not scored.
    truth = {"ngay_het_han": ""}
    r = _result({"ngay_het_han": "anything"})
    ps = score("p", "m", [(r, truth)])
    assert "ngay_het_han" not in ps.fields  # never scored → no FieldScore created


def test_percentile_single_and_multi() -> None:
    assert metrics._percentile([5.0], 95) == 5.0
    assert metrics._percentile([0.0, 100.0], 50) == 50.0


def test_render_report_smoke() -> None:
    ps = score(
        "gemini_flash", "gemini-2.5-flash",
        [(_result({"ngay_het_han": "2026-12-31"}), {"ngay_het_han": "2026-12-31"})],
    )
    md = render_report([ps], ["a note"], Path("manifest.json"))
    assert "# Benchmark results" in md and "gemini_flash" in md and "a note" in md


# --- factory (issue #53) ----------------------------------------------------


def _ok_result(provider: str = "fake") -> ExtractionResult:
    r = _result({"ngay_het_han": "2026-12-31"})
    r.provider = provider
    r.usage = TokenUsage(input_tokens=100, output_tokens=20)  # success → tokens used
    return r


def _err_result(provider: str = "fake") -> ExtractionResult:
    # Mirrors providers.base.empty_result: warning + zero tokens.
    return ExtractionResult(
        doc_type=DocType.OTHER, fields={}, provider=provider,
        usage=TokenUsage(), warnings=[f"{provider} boom"],
    )


def test_is_error_distinguishes_failure_from_needs_review() -> None:
    assert _err_result().is_error is True
    # A successful extraction that flags fields for review is NOT an error.
    ok = _ok_result()
    assert ok.is_error is False and ok.any_low_confidence is False
    # warning present but tokens consumed → not a hard failure.
    ok.warnings = ["partial page"]
    assert ok.is_error is False


def test_resolve_chain_prefers_then_defaults() -> None:
    assert factory._resolve_chain("gemini_flash") == ("gemini_flash", "claude_haiku")
    assert factory._resolve_chain("claude_haiku") == ("claude_haiku", "gemini_flash")
    # prefer outside the default chain still leads, defaults follow.
    assert factory._resolve_chain("claude_sonnet")[0] == "claude_sonnet"


def test_get_provider_unknown_prefer_raises() -> None:
    try:
        get_extraction_provider("does_not_exist")
    except ValueError as exc:
        assert "Unknown provider" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_get_provider_unavailable_when_no_keys() -> None:
    saved = {k: os.environ.pop(k, None)
             for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_API_KEY")}
    try:
        get_extraction_provider()
    except ExtractionUnavailable as exc:
        assert "No vision-extraction provider configured" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ExtractionUnavailable")
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


class _FakeProvider:
    """Minimal VisionExtractionProvider for factory wiring tests (no SDK/keys)."""

    def __init__(self, name: str, *, fail: bool) -> None:
        self.name = name
        self._fail = fail
        self.calls = 0

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        self.calls += 1
        return _err_result(self.name) if self._fail else _ok_result(self.name)


def _with_registry(entries: dict, fn):
    saved = factory._REGISTRY.copy()
    factory._REGISTRY.clear()
    factory._REGISTRY.update(entries)
    try:
        return fn()
    finally:
        factory._REGISTRY.clear()
        factory._REGISTRY.update(saved)


def test_get_provider_single_when_one_configured() -> None:
    os.environ["FAKE_PRIMARY"] = "x"
    try:
        prov = _with_registry(
            {"gemini_flash": (lambda: _FakeProvider("primary", fail=False), ("FAKE_PRIMARY",))},
            lambda: get_extraction_provider("gemini_flash"),
        )
        assert isinstance(prov, _FakeProvider) and prov.name == "primary"
    finally:
        os.environ.pop("FAKE_PRIMARY", None)


def test_fallback_advances_only_on_hard_failure() -> None:
    primary = _FakeProvider("primary", fail=True)
    backup = _FakeProvider("backup", fail=False)
    fb = factory._FallbackProvider([primary, backup])
    assert fb.name == "fallback:primary>backup"
    res = asyncio.run(fb.extract(b"img"))
    assert res.provider == "backup" and res.is_error is False
    assert primary.calls == 1 and backup.calls == 1


def test_fallback_charges_once_on_success() -> None:
    primary = _FakeProvider("primary", fail=False)
    backup = _FakeProvider("backup", fail=False)
    fb = factory._FallbackProvider([primary, backup])
    res = asyncio.run(fb.extract(b"img"))
    assert res.provider == "primary"
    assert primary.calls == 1 and backup.calls == 0  # backup never touched


def test_fallback_returns_last_error_when_all_fail() -> None:
    a = _FakeProvider("a", fail=True)
    b = _FakeProvider("b", fail=True)
    res = asyncio.run(factory._FallbackProvider([a, b]).extract(b"img"))
    assert res.is_error is True and res.provider == "b"


# --- clauses (issue #101 / DEC-026) -----------------------------------------


def test_clause_item_schema() -> None:
    c = ClauseItem(num="Điều 8", title="Chấm dứt", content="Bên A có thể...")
    assert c.content == "Bên A có thể..." and c.num == "Điều 8"
    # num + title optional; content required.
    c2 = ClauseItem(content="...")
    assert c2.num is None and c2.title is None
    try:
        ClauseItem()  # type: ignore[call-arg] — content is required
    except Exception:  # pydantic ValidationError
        pass
    else:  # pragma: no cover
        raise AssertionError("ClauseItem.content must be required")


def test_extraction_result_clauses_default_empty() -> None:
    # Backward compatible: callers that never set clauses keep working.
    r = ExtractionResult(fields={}, doc_type="khac")
    assert r.clauses == []


def test_extraction_result_accepts_clauses() -> None:
    r = ExtractionResult(
        fields={}, doc_type=DocType.LEASE,
        clauses=[ClauseItem(num="Điều 1", content="Phạm vi...")],
    )
    assert isinstance(r.clauses, list) and len(r.clauses) == 1
    assert r.clauses[0].num == "Điều 1"


def test_llm_schema_full_has_clauses_and_defaults_empty() -> None:
    # ContractExtractionLLMFull (Gemini schema) carries clauses, defaults to [].
    llm = ContractExtractionLLMFull(doc_type=DocType.OTHER)
    assert llm.clauses == []


def test_llm_schema_base_has_no_clauses() -> None:
    # ContractExtractionLLM (Claude flat schema) must NOT have clauses — grammar
    # compiler timeout on list[ClauseItem] in Claude structured outputs.
    llm = ContractExtractionLLM(doc_type=DocType.OTHER)
    assert not hasattr(llm, "clauses")


def test_to_result_maps_clauses_through_full_schema() -> None:
    from ..providers.base import to_result

    llm = ContractExtractionLLMFull(
        doc_type=DocType.LABOR,
        clauses=[ClauseItem(num="Điều 3", title="Lương", content="...")],
    )
    res = to_result(
        llm, provider="gemini_flash", model="gemini-2.5-flash",
        latency_ms=10.0, usage=TokenUsage(input_tokens=5, output_tokens=2), cost=1.0,
    )
    assert len(res.clauses) == 1 and res.clauses[0].num == "Điều 3"


def test_to_result_clauses_empty_for_flat_schema() -> None:
    # Claude flat schema → ExtractionResult.clauses = [] (backward compat).
    from ..providers.base import to_result

    llm = ContractExtractionLLM(doc_type=DocType.LEASE)
    res = to_result(
        llm, provider="claude_haiku", model="claude-haiku-4-5",
        latency_ms=5.0, usage=TokenUsage(input_tokens=3, output_tokens=1), cost=0.5,
    )
    assert res.clauses == []


def test_prompt_requests_clauses() -> None:
    from ..prompts import build_instruction

    instr = build_instruction("hd_lao_dong")
    assert "clauses" in instr
    assert "Điều" in instr and "Khoản" in instr  # asks for numbered articles/clauses


# --- extraction schema v2: doc_type_group + type-specific + payment (#123/#117) ---


def test_doc_type_groups_enum() -> None:
    assert len(DOC_TYPE_GROUPS) == 11           # 10 groups + "other"
    assert DOC_TYPE_GROUPS[-1] == "other"
    assert "lao_dong" in DOC_TYPE_GROUPS and "xay_dung" in DOC_TYPE_GROUPS
    assert len(set(DOC_TYPE_GROUPS)) == len(DOC_TYPE_GROUPS)  # no dupes


def test_canonical_fields_v2_expanded() -> None:
    # 7 original + 5 universal = 12; benchmark targets still a subset.
    assert len(CANONICAL_FIELDS) == 12
    for new in ("doc_type_group", "ngay_ky", "tien_dat_coc", "thoi_han_bao_hanh", "thoi_han_thong_bao"):
        assert new in CANONICAL_FIELDS
    assert set(BENCHMARK_TARGET_FIELDS).issubset(set(CANONICAL_FIELDS))


def test_type_specific_fields_structure() -> None:
    # Every group key is a real doc_type_group (excluding "other"/"dan_su" which
    # have no type-specific set).
    assert set(TYPE_SPECIFIC_FIELDS).issubset(set(DOC_TYPE_GROUPS))
    # Flattened tuple is de-duplicated and covers every group's fields.
    flat = [f for fields in TYPE_SPECIFIC_FIELDS.values() for f in fields]
    assert len(ALL_TYPE_SPECIFIC_FIELDS) == len(set(flat))
    assert "luong_co_ban" in ALL_TYPE_SPECIFIC_FIELDS  # labor
    assert "lai_suat" in ALL_TYPE_SPECIFIC_FIELDS       # finance


def test_payment_schedule_item_schema() -> None:
    p = PaymentScheduleItem(amount="100000000", due_date="2026-07-15", milestone="Tạm ứng 30%")
    assert p.amount == "100000000" and p.recurrence is None
    # all fields optional — unstructured contract may have none
    assert PaymentScheduleItem().due_date is None


def test_extraction_result_payment_schedule_default_empty() -> None:
    r = ExtractionResult(fields={}, doc_type="khac")
    assert r.payment_schedule == []


def test_full_schema_has_typespecific_payment_clauses() -> None:
    llm = ContractExtractionLLMFull(doc_type=DocType.LABOR)
    # All extras default empty (DEC-026/029/030 Phase 2). payment_schedule is now a
    # generalized obligation_schedule (#154); the flat schema carries neither.
    assert llm.obligation_schedule == [] and llm.clauses == [] and llm.type_specific == []
    assert not hasattr(llm, "payment_schedule")  # LLM schema renamed → obligation_schedule


def test_base_schema_lean_for_claude() -> None:
    # Claude flat schema must stay lean (it rejects wide schemas) — only the 7
    # BASE_CANONICAL_FIELDS, no nested lists, no v2 universal fields.
    llm = ContractExtractionLLM(doc_type=DocType.OTHER)
    assert not hasattr(llm, "obligation_schedule")
    assert not hasattr(llm, "type_specific")
    assert not hasattr(llm, "clauses")
    assert not hasattr(llm, "doc_type_group")   # v2 → Full only
    assert not hasattr(llm, "ngay_ky")
    assert isinstance(llm.doi_tac, ExtractedField)  # core field present
    # the v2 universal fields live on the Full (Gemini) schema instead
    full = ContractExtractionLLMFull(doc_type=DocType.OTHER)
    assert isinstance(full.doc_type_group, ExtractedField)
    assert isinstance(full.ngay_ky, ExtractedField)


def test_named_extracted_field_clamps_confidence() -> None:
    nf = NamedExtractedField(key="luong_co_ban", value="15000000", confidence=1.7)
    assert nf.key == "luong_co_ban" and nf.confidence == 1.0  # clamped
    assert ExtractedField(confidence=-3).confidence == 0.0     # clamp lower bound


def test_full_as_field_map_folds_type_specific_by_key() -> None:
    llm = ContractExtractionLLMFull(
        doc_type=DocType.LABOR,
        type_specific=[
            NamedExtractedField(key="luong_co_ban", value="15000000", confidence=0.9, needs_review=False),
            NamedExtractedField(key="NOT_A_REAL_FIELD", value="x"),  # dropped
        ],
    )
    fm = llm.as_field_map()
    # canonical always present
    for name in CANONICAL_FIELDS:
        assert name in fm
    # known type-specific key folded in; unknown key dropped (no fabricated field)
    assert fm["luong_co_ban"].value == "15000000"
    assert "NOT_A_REAL_FIELD" not in fm
    # type-specific keys not emitted stay absent (not forced to null rows)
    assert "lai_suat" not in fm
    # Full map covers all 12 universal canonical fields
    assert set(CANONICAL_FIELDS).issubset(set(fm))
    # base (Claude) map is the lean 7 only
    assert set(ContractExtractionLLM(doc_type=DocType.LABOR).as_field_map()) == set(BASE_CANONICAL_FIELDS)


def test_to_result_maps_obligation_schedule() -> None:
    from ..providers.base import to_result

    llm = ContractExtractionLLMFull(
        doc_type=DocType.SUPPLIER,
        obligation_schedule=[
            ObligationScheduleItem(
                obligation_type="payment", description="Đợt 1",
                amount_raw="5000000", due_date="2026-08-01",
            )
        ],
    )
    res = to_result(
        llm, provider="gemini_flash", model="gemini-2.5-flash",
        latency_ms=10.0, usage=TokenUsage(input_tokens=5, output_tokens=2), cost=1.0,
    )
    assert len(res.obligation_schedule) == 1 and res.obligation_schedule[0].due_date == "2026-08-01"
    # Claude flat schema → empty obligation_schedule (backward compat)
    flat = ContractExtractionLLM(doc_type=DocType.SUPPLIER)
    res2 = to_result(
        flat, provider="claude_haiku", model="claude-haiku-4-5",
        latency_ms=5.0, usage=TokenUsage(input_tokens=3, output_tokens=1), cost=0.5,
    )
    assert res2.obligation_schedule == []


def test_prompt_has_doctype_group_and_payment() -> None:
    from ..prompts import build_instruction

    instr = build_instruction("hd_lao_dong")
    assert "doc_type_group" in instr
    assert "lao_dong" in instr and "xay_dung" in instr      # group enum listed
    assert "obligation_schedule" in instr                    # schedule section present (#154)
    assert "luong_co_ban" in instr                           # type-specific guidance present


def test_doc_type_confidence_clamped_both_tiers() -> None:
    # #139: LLM schema dropped ge/le on doc_type_confidence (Gemini grammar limit) →
    # must clamp via validator so a >1.0 value doesn't trip ExtractionResult's ge/le.
    base = ContractExtractionLLM(doc_type=DocType.OTHER, doc_type_confidence=1.5)
    assert base.doc_type_confidence == 1.0
    full = ContractExtractionLLMFull(doc_type=DocType.OTHER, doc_type_confidence=-0.2)
    assert full.doc_type_confidence == 0.0  # validator inherited by Full
    # round-trip through to_result must NOT raise (was a 500 in extraction_runner)
    from ..providers.base import to_result

    res = to_result(
        ContractExtractionLLMFull(doc_type=DocType.LEASE, doc_type_confidence=2.0),
        provider="gemini_flash", model="gemini-2.5-flash",
        latency_ms=1.0, usage=TokenUsage(input_tokens=1, output_tokens=1), cost=1.0,
    )
    assert res.doc_type_confidence == 1.0


# --- parties + role labels (DEC-030, #143) ----------------------------------


def test_party_item_schema() -> None:
    p = PartyItem(name="Công ty TNHH ABC", role_label="Operator")
    assert p.name == "Công ty TNHH ABC" and p.role_label == "Operator"
    assert PartyItem(name="Ông X").role_label is None  # role optional
    try:
        PartyItem()  # type: ignore[call-arg] — name required
    except Exception:
        pass
    else:  # pragma: no cover
        raise AssertionError("PartyItem.name must be required")


def test_payment_item_has_payer() -> None:
    p = PaymentScheduleItem(amount="1000", due_date="2026-07-01", payer="Owner")
    assert p.payer == "Owner"
    assert PaymentScheduleItem().payer is None  # optional, default None


def test_full_schema_has_parties_default_empty() -> None:
    full = ContractExtractionLLMFull(doc_type=DocType.OTHER)
    assert full.parties == []
    # base (Claude) schema does NOT carry parties (nested list → Gemini only)
    assert not hasattr(ContractExtractionLLM(doc_type=DocType.OTHER), "parties")


def test_extraction_result_parties_default_and_mapped() -> None:
    assert ExtractionResult(fields={}, doc_type="khac").parties == []
    from ..providers.base import to_result

    full = ContractExtractionLLMFull(
        doc_type=DocType.OTHER,
        parties=[
            PartyItem(name="Cty A", role_label="Owner"),
            PartyItem(name="Cty B", role_label="Operator"),
        ],
        obligation_schedule=[
            ObligationScheduleItem(
                obligation_type="payment", description="Đợt 1",
                amount_raw="5", due_date="2026-07-01", obligor="Owner",
            )
        ],
    )
    res = to_result(
        full, provider="gemini_flash", model="gemini-2.5-flash",
        latency_ms=1.0, usage=TokenUsage(input_tokens=1, output_tokens=1), cost=1.0,
    )
    assert [p.role_label for p in res.parties] == ["Owner", "Operator"]
    assert res.obligation_schedule[0].obligor == "Owner"
    # Claude flat schema → parties stays [] (backward compat)
    flat = ContractExtractionLLM(doc_type=DocType.OTHER)
    res2 = to_result(
        flat, provider="claude_haiku", model="claude-haiku-4-5",
        latency_ms=1.0, usage=TokenUsage(input_tokens=1, output_tokens=1), cost=1.0,
    )
    assert res2.parties == []


def test_prompt_has_parties_and_payer() -> None:
    from ..prompts import build_instruction

    instr = build_instruction("auto")
    assert "parties" in instr and "role_label" in instr
    assert "obligor" in instr  # who performs each scheduled obligation (#154, renamed from payer)


# --- obligation_schedule generalization (DEC-030 Phase 2, #154) -------------


def test_obligation_schedule_item_required_and_defaults() -> None:
    # obligation_type + description required; trigger defaults to "date".
    o = ObligationScheduleItem(obligation_type="delivery", description="Giao 40% hàng")
    assert o.trigger == "date" and o.due_date is None and o.amount_raw is None
    assert o.series_id is None and o.milestone_index is None and o.trigger_delay_days is None
    for kwargs in ({"obligation_type": "payment"}, {"description": "x"}):
        try:
            ObligationScheduleItem(**kwargs)  # type: ignore[arg-type]
        except Exception:  # pydantic ValidationError — both fields required
            pass
        else:  # pragma: no cover
            raise AssertionError("obligation_type + description must be required")


def test_obligation_schedule_series_and_event_trigger() -> None:
    # T3 series: same series_id across installments with index/total.
    s = ObligationScheduleItem(
        obligation_type="payment", description="Đợt 2/3", amount_raw="40%",
        series_id="pay-1", milestone_index=2, milestone_total=3, obligor="Bên B",
    )
    assert s.milestone_index == 2 and s.milestone_total == 3 and s.series_id == "pay-1"
    # Event-anchored milestone: no fabricated date (D-08).
    e = ObligationScheduleItem(
        obligation_type="handover", description="Bàn giao sau nghiệm thu",
        trigger="event", trigger_condition="sau khi nghiệm thu", trigger_delay_days=30,
    )
    assert e.trigger == "event" and e.due_date is None
    assert e.trigger_condition == "sau khi nghiệm thu" and e.trigger_delay_days == 30


def test_extraction_result_obligation_schedule_default_empty() -> None:
    r = ExtractionResult(fields={}, doc_type="khac")
    assert r.obligation_schedule == []


def test_payment_schedule_compat_property_projects_payments_only() -> None:
    # DEPRECATED shim (#154): only payment-type items surface, mapped to old shape.
    r = ExtractionResult(
        fields={}, doc_type=DocType.SUPPLIER,
        obligation_schedule=[
            ObligationScheduleItem(
                obligation_type="payment", description="Tạm ứng 30%",
                amount_raw="30%", due_date="2026-07-05", recurrence="monthly", obligor="Bên B",
            ),
            ObligationScheduleItem(obligation_type="delivery", description="Giao hàng đợt 1"),
        ],
    )
    compat = r.payment_schedule
    assert len(compat) == 1  # delivery item filtered out
    assert isinstance(compat[0], PaymentScheduleItem)
    # field remap: amount_raw→amount, description→milestone, obligor→payer
    assert compat[0].amount == "30%" and compat[0].milestone == "Tạm ứng 30%"
    assert compat[0].payer == "Bên B" and compat[0].due_date == "2026-07-05"
    assert compat[0].recurrence == "monthly"


def test_prompt_has_obligation_schedule_series_and_event() -> None:
    from ..prompts import build_instruction

    instr = build_instruction("auto")
    assert "obligation_schedule" in instr and "obligation_type" in instr
    assert "series_id" in instr and "milestone_index" in instr     # series guidance
    assert "trigger" in instr and "trigger_condition" in instr      # event-anchor guidance
    assert "amount_raw" in instr


def _run_all() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
