"""Graph retrieval over QuantBase's public company knowledge, with source-bound B citations."""
from __future__ import annotations

import re

from . import knowledge_graph as kg

STOP = {"what", "does", "how", "the", "and", "for", "with", "about", "this", "that", "are", "can", "you",
        "tell", "have", "has", "its", "our", "from", "quantbase", "sniff", "handle", "handles"}
RELATIONS = "SUPPORTS|CONTRADICTS|PART_OF|DECIDED_ON"
CITATION = re.compile(r"\[([BE]\d+)\]")


def terms_for(question: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9]+", question.lower())
    terms = list(dict.fromkeys(w for w in words if len(w) > 2 and w not in STOP))[:8]
    return terms or ["QuantBase"]


def retrieve(question: str) -> dict:
    question = question.strip()
    if not question or len(question) > 500:
        raise ValueError("Ask a question of 1-500 characters.")
    terms = terms_for(question)
    # Entity -> up to two typed relationship hops -> exact mentioning section -> source Doc.
    # No arbitrary Cypher or model-generated query is accepted.
    connected = kg.read("brain", f"""
    MATCH (seed:Entity)
    WHERE any(term IN $terms WHERE toLower(seed.name) CONTAINS toLower(term))
    WITH seed LIMIT 20
    MATCH p = (seed)-[:{RELATIONS}*0..2]-(entity:Entity)
    MATCH (s:Section)-[:MENTIONS]->(entity)
    MATCH (s)-[:PART_OF]->(d:Doc)
    WHERE s.active = true
    RETURN DISTINCT s.sid AS sid, s.title AS title, s.text AS text, s.at AS at,
           d.url AS url, d.title AS doc_title, p AS path
    LIMIT 40
    """, {"terms": terms})
    fulltext = kg.read("brain", """
    CALL db.idx.fulltext.queryNodes('Section', $q) YIELD node, score
    WITH node AS s, score WHERE s.active = true
    MATCH (s)-[:PART_OF]->(d:Doc)
    RETURN s.sid AS sid, s.title AS title, s.text AS text, s.at AS at,
           d.url AS url, d.title AS doc_title, score
    ORDER BY score DESC LIMIT 30
    """, {"q": " | ".join(terms)})  # RediSearch union; literal OR would require every term.
    candidates = {}
    for row in connected + fulltext:
        candidates.setdefault(row["sid"], row)
    # Prefer sections containing all question terms, and specific headings over boilerplate.
    def rank(row):
        body = (row["title"] + " " + row["text"]).lower()
        return (sum(bool(re.search(r"\b" + re.escape(t.lower()) + r"\b", body)) for t in terms),
                sum(t.lower() in row["title"].lower() for t in terms),
                row["url"].startswith("https://quantbase.live/"), float(row.get("score", 0)))
    selected = sorted(candidates.values(), key=rank, reverse=True)[:5]
    # Fetch the actual source's entity neighbourhood to visualise grounding even for a fulltext hit.
    neighbourhood = []
    if selected:
        neighbourhood = kg.read("brain", f"""
        MATCH (s:Section)-[:MENTIONS]->(e:Entity)
        WHERE s.sid IN $sids AND s.active = true
        OPTIONAL MATCH (e)-[r:{RELATIONS}]->(other:Entity)
        RETURN s.sid AS sid, e AS entity, type(r) AS relation, other, r.source_sid AS relation_source
        LIMIT 80
        """, {"sids": [s["sid"] for s in selected]})
    return {"sections": selected, "neighbourhood": neighbourhood, "terms": terms}


def _excerpt(text: str, terms: list[str], limit: int = 650) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.strip().startswith("Source:")]
    best = max(paragraphs or [text], key=lambda p: sum(t.lower() in p.lower() for t in terms))
    best = re.sub(r"\s+", " ", best).strip()
    if len(best) <= limit:
        return best
    # End at a word boundary; preserve an exact contiguous source excerpt.
    return best[:limit].rsplit(" ", 1)[0] + "…"


def check_citations(answer: str, evidence: list[dict]) -> tuple[str, list[str]]:
    """Brain answers consist only of literal excerpts paired with their own source id.

    This stricter contract rejects unsupported prose, unknown ids, E ids and an excerpt
    attributed to the wrong section. It does not claim to verify the source's truth.
    """
    known = {e["id"]: e for e in evidence if e.get("tool") == "brain_ask" and e.get("source", {}).get("url")}
    kept, cited = [], []
    for line in answer.splitlines():
        match = re.fullmatch(r"(.+?)\s*\[(B\d+)\]", line.strip())
        if not match:
            continue
        quote, eid = match.groups()
        if eid not in known:
            continue
        literal = quote.removesuffix("…")
        section = re.sub(r"\s+", " ", known[eid].get("section", "")).strip()
        if literal and re.sub(r"\s+", " ", literal) in section:
            kept.append(f"{quote} [{eid}]")
            cited.append(eid)
    return "\n\n".join(kept), list(dict.fromkeys(cited))


def ask(question: str) -> dict:
    found = retrieve(question)
    nodes, edges, evidence, sources, answers = {}, [], [], [], []
    for i, section in enumerate(found["sections"], 1):
        bid = f"B{i}"
        sid = "section:" + section["sid"]
        did = "doc:" + section["url"]
        source = {"url": section["url"], "title": section["doc_title"], "section_title": section["title"],
                  "section_id": section["sid"], "fetched_at": section["at"]}
        excerpt = _excerpt(section["text"], found["terms"])
        nodes[sid] = {"key": sid, "label": "Section", "name": section["title"], "citation": bid}
        nodes[did] = {"key": did, "label": "Doc", "name": section["doc_title"], "url": section["url"]}
        edge = {"src": sid, "dst": did, "type": "PART_OF"}
        edges.append(edge)
        evidence.append({"id": bid, "tool": "brain_ask", "args": {}, "summary": excerpt,
                         "source": source, "section": section["text"], "nodes": [nodes[sid], nodes[did]], "edges": [edge]})
        sources.append({"id": bid, **source, "excerpt": excerpt, "text": section["text"]})
        if i <= 3:
            answers.append(f"{excerpt} [{bid}]")
    for row in found["neighbourhood"]:
        e, other = row["entity"], row.get("other")
        key = "entity:" + e["eid"]
        nodes[key] = {"key": key, "label": e.get("kind", "Entity"), "name": e["name"]}
        edges.append({"src": "section:" + row["sid"], "dst": key, "type": "MENTIONS"})
        if other and row.get("relation"):
            other_key = "entity:" + other["eid"]
            nodes[other_key] = {"key": other_key, "label": other.get("kind", "Entity"), "name": other["name"]}
            edges.append({"src": key, "dst": other_key, "type": row["relation"], "source_section": row.get("relation_source")})
    answer, cited = check_citations("\n".join(answers), evidence)
    return {"answer": answer or "No public source found for that question. Try a product, policy, paper vs live, or research question.",
            "cited": cited, "evidence": evidence, "sources": sources,
            "graph": {"nodes": list(nodes.values()), "edges": list({(e["src"], e["dst"], e["type"]): e for e in edges}.values())},
            "mode": "source excerpts", "note": "Public source excerpts, retrieved through graph neighbourhoods and full-text indexes. Sources can disagree; dates and contexts matter."}


def status() -> dict:
    counts = kg.read("brain", "MATCH (n) RETURN labels(n) AS labels, count(n) AS count")
    docs = kg.read("brain", "MATCH (d:Doc) RETURN d.title AS title, d.url AS url, d.at AS fetched_at, d.mode AS extraction ORDER BY title")
    return {"counts": counts, "docs": docs, "public_only": True}
