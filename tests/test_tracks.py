"""Privacy, grounded extraction, budget and source citation contracts (no network)."""
from __future__ import annotations

import asyncio
import copy
import json
from types import SimpleNamespace

import httpx
import pytest

from app import brain, tools
from app.privacy import PrivacyError, require_public, scan
from build import brain as builder


@pytest.mark.parametrize("value,kind", [
    ("reader@example.org", "email"),
    ("sk-ant-" + "a" * 40, "api_key"),
    ("AKIA" + "A" * 16, "aws_id"),
    ("arn:aws:iam::123456789012:role/demo", "aws_id"),
    ("192.0.2.12", "ip_address"),
    ("2001:db8::1", "ip_address"),
    ("-----BEGIN PRIVATE KEY-----", "private_key"),
    ("5" * 88, "private_key"),
    ("0x" + "ab" * 32, "private_key"),
    (json.dumps(list(range(64))), "wallet_key_array"),
    ("password=demonstration-value", "credential_assignment"),
    ("seed phrase: " + "alpha " * 11 + "beta", "seed_phrase"),
])
def test_privacy_refuses_secret_and_pii_classes_without_echoing_values(value, kind):
    assert kind in scan(value)
    with pytest.raises(PrivacyError) as error:
        require_public({"content": value})
    assert value not in str(error.value)


def test_privacy_accepts_public_addresses_metrics_and_random_session_tokens():
    require_public("Coin DLTiLKB7wuNcXQKkY5SUJkUDME7bsV1Ax8574xZ7pump; 3.7%; FalkorDB 6.0.2; ±0.01")
    require_public({"sid": "abc123" * 5 + "ab", "at": 1792330224})


def test_html_ingests_selected_public_scope_and_refuses_hidden_secrets():
    parser = builder.PublicHTML()
    parser.feed('<main><aside>Navigation</aside><article><h1>Policy</h1><p>Public facts.</p></article></main><footer>support@example.org</footer>')
    assert parser.result() == "## Policy\n\nPublic facts."
    parser = builder.PublicHTML("pricing")
    parser.feed('<section id="pricing"><p><span>$19</span><small>a month</small></p><p>Paper results.</p></section>')
    assert "$19 a month" in parser.result() and "\n\nPaper results." in parser.result()
    for hidden in ['<p>support@example.org</p>', '<script>const key="sk-ant-' + 'a' * 40 + '"</script>']:
        parser = builder.PublicHTML()
        parser.feed('<article><h1>Policy</h1>' + hidden + '</article>')
        with pytest.raises(PrivacyError):
            parser.result()


def test_public_collection_allowlist_and_whole_source_refusal(tmp_path, monkeypatch):
    for path in builder.LOCAL:
        p = tmp_path / path
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_text("# Public source\nQuantBase paper mode uses play money.")
    requests = []
    def respond(request):
        requests.append(str(request.url))
        if request.url.path == "/":
            body = ''.join(f'<section id="{fragment}"><h2>{fragment}</h2><p>Public QuantBase facts.</p></section>'
                           for fragment in ("paper", "pricing", "faq", "safety"))
        elif "privacy" in request.url.path or "terms" in request.url.path:
            body = '<article><p>Contact person@example.org</p></article>'
        else:
            body = '<article><h1>Public docs</h1><p>QuantBase uses paper money.</p></article>'
        return httpx.Response(200, text=body)
    original = httpx.AsyncClient
    monkeypatch.setattr(builder.httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    docs, audit = asyncio.run(builder.collect(tmp_path))
    assert all(builder.source_allowed(d["url"]) for d in docs)
    assert not any("person@" in json.dumps(d) for d in docs)
    assert sum(a["status"] == "refused" for a in audit) == 2
    assert all(url.startswith("https://quantbase.live/") for url in requests)
    assert requests.count("https://quantbase.live/") == 1  # fragment sources use one fetched page
    assert not builder.source_allowed("https://quantbase.live/internal/HANDOVER.md")
    assert not builder.source_allowed("https://attacker.invalid/docs/")


def sample_corpus():
    url = builder.REPO_URL + "README.md"
    text = "QuantBase uses paper mode. Paper results are not real fills."
    section = {"sid": builder.ident(url, text), "title": "Paper", "text": text, "at": 10,
               "method": "source-only", "entities": builder.source_entities({"text": text}), "relations": []}
    return {"schema": 1, "public_only": True, "documents": [{"did": builder.ident(url), "url": url,
            "title": "README.md", "at": 10, "mode": "source-only", "sections": [section]}]}


def test_extraction_requires_literal_names_quotes_and_relation_grounding():
    section = {"text": "QuantBase paper mode cannot touch a wallet. Paper results are not real fills."}
    data = {"entities": [
        {"kind": "Product", "name": "QuantBase", "quote": "QuantBase paper mode cannot touch a wallet."},
        {"kind": "Feature", "name": "paper mode", "quote": "QuantBase paper mode cannot touch a wallet."},
        {"kind": "Finding", "name": "Guaranteed profits", "quote": "Guaranteed profits"},
        {"kind": "Policy) DELETE n", "name": "wallet", "quote": "QuantBase paper mode cannot touch a wallet."},
    ], "relations": [
        {"from": "paper mode", "to": "QuantBase", "type": "PART_OF", "quote": "QuantBase paper mode cannot touch a wallet."},
        {"from": "paper mode", "to": "QuantBase", "type": "SUPPORTS", "quote": "Made up profits"},
    ]}
    entities, edges = builder.validate_extraction(section, data)
    assert {e["name"] for e in entities} == {"QuantBase", "paper mode"}
    assert [e["type"] for e in edges] == ["PART_OF"]
    with pytest.raises(PrivacyError):
        builder.validate_extraction(section, {"entities": [], "leak": "person@example.org"})


def test_load_preflights_entire_corpus_before_any_graph_mutation(monkeypatch):
    writes = []
    monkeypatch.setattr(builder.kg, "write", lambda *a: writes.append(a))
    monkeypatch.setattr(builder.kg, "ensure_indexes", lambda *a: writes.append(a))
    corpus = sample_corpus()
    corpus["documents"].append(copy.deepcopy(corpus["documents"][0]))
    corpus["documents"][-1]["sections"][0]["text"] += " person@example.org"
    with pytest.raises(PrivacyError):
        builder.load(corpus)
    assert writes == []
    corpus = sample_corpus()
    corpus["documents"][0]["url"] = "file:///private/HANDOVER.md"
    with pytest.raises(PrivacyError):
        builder.load(corpus)
    assert writes == []


def test_budget_caps_requests_tokens_and_reserved_cost():
    budget = builder.Budget(max_requests=1)
    assert budget.reserve("Public", 1000)
    assert not budget.reserve("Public", 1000)
    assert budget.requests == 1 and budget.output_tokens == 1000
    assert not builder.Budget(max_cost_usd=0).reserve("Public", 1)
    assert not builder.Budget(max_input_tokens=10).reserve("Public", 1)
    assert not builder.Budget(max_output_tokens=10).reserve("Public", 11)


def test_existing_ai_client_extracts_with_cheap_model_and_hard_call_cap(monkeypatch):
    calls = []
    class FakeClient:
        def __init__(self):
            self.messages = self
        def with_options(self, **kw):
            assert kw["max_retries"] == 0
            return self
        async def create(self, **kw):
            calls.append(kw)
            payload = {"entities": [{"kind": "Product", "name": "QuantBase", "quote": "QuantBase uses paper mode."}], "relations": []}
            return SimpleNamespace(content=[SimpleNamespace(text=json.dumps(payload))])
    monkeypatch.setattr(builder.ai, "load_owner", lambda: None)
    monkeypatch.setattr(builder.ai, "client_for", lambda key: (FakeClient(), "expensive-model", "owner"))
    corpus = sample_corpus()
    corpus["documents"][0]["sections"] *= 3
    report = asyncio.run(builder.extract(corpus["documents"], builder.Budget(max_requests=1)))
    assert len(calls) == report["requests"] == 1
    assert calls[0]["model"] == builder.ai.CHEAP[0] and "haiku" in calls[0]["model"]
    assert calls[0]["max_tokens"] == 1000
    assert corpus["documents"][0]["mode"] == "AI + source anchors"


def test_source_only_is_explicit_and_does_not_claim_ai_extraction(monkeypatch):
    monkeypatch.setattr(builder.ai, "load_owner", lambda: None)
    monkeypatch.setattr(builder.ai, "client_for", lambda _: (None, None, "none"))
    with pytest.raises(ValueError, match="owner key"):
        asyncio.run(builder.extract(sample_corpus()["documents"], builder.Budget()))
    report = asyncio.run(builder.extract(sample_corpus()["documents"], builder.Budget(), source_only=True))
    assert report["source_only"] and report["model"] is None and report["requests"] == 0


def test_brain_citation_contract_rejects_fabrications_unknown_and_wrong_source_ids():
    evidence = [{"id": "B1", "tool": "brain_ask", "section": "Paper mode cannot touch a wallet.", "source": {"url": "https://quantbase.live/#paper"}},
                {"id": "B2", "tool": "brain_ask", "section": "No claim of profit.", "source": {"url": "https://quantbase.live/#faq"}}]
    text, cited = brain.check_citations(
        "Paper mode cannot touch a wallet. [B1]\n"
        "Guaranteed profits. [B1]\nNo claim of profit. [B1]\n"
        "No claim of profit. [B99]\nNo claim of profit. [E1]\nNo claim of profit. [B2]", evidence)
    assert cited == ["B1", "B2"] and "Guaranteed" not in text and "B99" not in text and "E1" not in text
    assert text.count("No claim of profit") == 1


def test_excerpt_keeps_negation_and_wrapped_paragraph_context():
    text = "Paper mode uses play money. Do not claim\nthat a paper result is a real fill or live execution is available.\n\nSource: public"
    excerpt = brain._excerpt(text, ["paper", "live"])
    assert "Do not claim that a paper result" in excerpt
    evidence = [{"id": "B1", "tool": "brain_ask", "section": text, "source": {"url": "https://quantbase.live/#paper"}}]
    assert brain.check_citations(excerpt + " [B1]", evidence)[1] == ["B1"]


def test_compact_mcp_result_always_remains_valid_json():
    result = {"rows": [{"text": "x" * 10000}], "graph": {"nodes": [{"name": "y" * 1000} for _ in range(50)]}}
    compact = tools.cap(result, 3000)
    assert len(compact) <= 3000 and isinstance(json.loads(compact), dict)
