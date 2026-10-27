"""In-tree Queensland and Australian Legal MCP server.

Exposes official Australian and Queensland legal connectors, deterministic
claim verification, and document analysis tools over stdio MCP.

Run via:
    python -m legal_helper.mcp.servers.babs_au_legal
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from ....connectors import (
    cth_legislation,
    hca_judgments,
    qld_caselaw,
    qld_legislation,
)
from ....citations.claim_verifier import (
    AtomicClaim,
    EvidenceSource,
    verify_claims,
)
from ....documents.upload_parser import parse_upload
from ....au_analysis import (
    GroundedSourceItem,
    StructuredClaim,
    render_grounded_answer,
    run_critic_loop,
)


def dispatch(name: str, arguments: dict[str, Any]) -> str:
    """Route one MCP tools/call to its backing connector or verifier.

    Kept free of mcp-package imports so it is unit-testable offline.
    """
    if name == "qld_legislation_search":
        res = qld_legislation.qld_legislation_search(
            query=arguments.get("query", ""),
            as_at_date=arguments.get("as_at_date"),
            per_page=arguments.get("per_page", 10),
        )
        return json.dumps(res, ensure_ascii=False)

    if name == "qld_legislation_fetch":
        res = qld_legislation.qld_legislation_fetch(
            title_or_slug=arguments.get("title_or_slug", ""),
            pinpoint=arguments.get("pinpoint"),
            as_at_date=arguments.get("as_at_date"),
        )
        return json.dumps(res, ensure_ascii=False)

    if name == "qld_caselaw_fetch":
        res = qld_caselaw.qld_caselaw_fetch(
            citation=arguments.get("citation", ""),
            url=arguments.get("url"),
        )
        return json.dumps(res, ensure_ascii=False)

    if name == "cth_legislation_fetch":
        res = cth_legislation.cth_legislation_fetch(
            title_or_id=arguments.get("title_or_id", ""),
            pinpoint=arguments.get("pinpoint"),
            as_at_date=arguments.get("as_at_date"),
        )
        return json.dumps(res, ensure_ascii=False)

    if name == "hca_judgment_fetch":
        res = hca_judgments.hca_judgment_fetch(
            citation=arguments.get("citation", ""),
            url=arguments.get("url"),
        )
        return json.dumps(res, ensure_ascii=False)

    if name == "verify_claims":
        claims_raw = arguments.get("claims", [])
        evidence_raw = arguments.get("evidence_sources", [])
        as_at_date = arguments.get("as_at_date")

        claims = [
            AtomicClaim(
                claim_id=c.get("claim_id", f"c_{i}"),
                text=c.get("text", ""),
                evidence_ids=c.get("evidence_ids", []),
                pinpoint=c.get("pinpoint"),
                relevant_date=c.get("relevant_date") or as_at_date,
            )
            for i, c in enumerate(claims_raw)
        ]
        evidence_sources = [
            EvidenceSource(
                id=e.get("source_id", e.get("id", f"e_{j}")),
                title=e.get("title", ""),
                citation=e.get("citation", ""),
                source_type=e.get("source_type", "statute"),
                text=e.get("text", ""),
                status=e.get("status", "in_force"),
                in_force_start=e.get("in_force_start"),
                in_force_end=e.get("in_force_end"),
                trust_level=e.get("trust_level", "high"),
                pages=e.get("pages") or e.get("known_pages"),
                clauses=e.get("clauses") or e.get("known_clauses"),
            )
            for j, e in enumerate(evidence_raw)
        ]

        verified = verify_claims(claims, evidence_sources)
        return json.dumps(asdict(verified), ensure_ascii=False)

    if name == "analyze_document":
        file_path_str = arguments.get("file_path", "")
        file_path = Path(file_path_str)
        if not file_path.exists():
            return json.dumps({"error": f"File not found: {file_path_str}"}, ensure_ascii=False)

        parsed_doc = parse_upload(file_path)
        ev_source = parsed_doc.to_evidence_source()
        as_at_date = arguments.get("as_at_date")
        matter_type = arguments.get("matter_type", "standard")

        claims = []
        for cl in parsed_doc.clauses:
            quote_sub = f'"{cl.text[:100]}"' if cl.text else ""
            claims.append(
                StructuredClaim(
                    claim_id=f"doc_{cl.page_number}_{cl.clause_number}",
                    section="application",
                    text=f"Clause {cl.clause_number} on page {cl.page_number} states {quote_sub}.",
                    evidence_ids=[ev_source.id],
                    pinpoint=f"p. {cl.page_number}, cl {cl.clause_number}",
                )
            )

        if not claims:
            for p in parsed_doc.pages:
                claims.append(
                    StructuredClaim(
                        claim_id=f"doc_p_{p.page_number}",
                        section="application",
                        text=f"Page {p.page_number} content: {p.text[:200]}",
                        evidence_ids=[ev_source.id],
                        pinpoint=f"p. {p.page_number}",
                    )
                )

        evidence_dict = {ev_source.id: ev_source}
        audited_claims, rounds_log = run_critic_loop(
            claims=claims,
            evidence_store=evidence_dict,
            relevant_date=as_at_date,
            max_rounds=3,
        )

        sources = [
            GroundedSourceItem(
                index=1,
                citation_text=f"Uploaded Document: {file_path.name}",
                status="verified in uploaded document",
            )
        ]
        unverified_notes = []
        for c in audited_claims:
            if c.status == "UNVERIFIED":
                unverified_notes.extend(c.reasons + c.critic_flags)

        rendered = render_grounded_answer(
            matter_type=matter_type,
            claims=audited_claims,
            sources=sources,
            what_could_not_be_verified=unverified_notes or None,
        )

        return json.dumps(
            {
                "rendered_analysis": rendered,
                "pages": len(parsed_doc.pages),
                "trust_level": parsed_doc.trust_level,
                "parser_used": parsed_doc.parser_used,
            },
            ensure_ascii=False,
        )

    return json.dumps({"error": f"unknown tool: {name}"})


async def _amain() -> None:
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool
    except ImportError as e:
        raise SystemExit(f"mcp package not installed: {e!s}")

    server = Server("babs_au_legal")

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return [
            Tool(
                name="qld_legislation_search",
                description="Search Queensland legislation via legislation.qld.gov.au.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "as_at_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "per_page": {"type": "integer", "default": 10},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="qld_legislation_fetch",
                description="Fetch Queensland statute or regulation text with optional pinpoint and point-in-time date.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title_or_slug": {"type": "string"},
                        "pinpoint": {"type": "string"},
                        "as_at_date": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["title_or_slug"],
                },
            ),
            Tool(
                name="qld_caselaw_fetch",
                description="Fetch Queensland court judgments (QCA, QSC, QDC, QCAT) by citation or URL.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "citation": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["citation"],
                },
            ),
            Tool(
                name="cth_legislation_fetch",
                description="Fetch Commonwealth legislation text by Act title or ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title_or_id": {"type": "string"},
                        "pinpoint": {"type": "string"},
                        "as_at_date": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["title_or_id"],
                },
            ),
            Tool(
                name="hca_judgment_fetch",
                description="Fetch High Court of Australia judgments by citation (e.g. [2024] HCA 1).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "citation": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["citation"],
                },
            ),
            Tool(
                name="verify_claims",
                description="Deterministically verify atomic claims against evidence text with quote roundtripping and pinpoint checks.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "claims": {"type": "array", "items": {"type": "object"}},
                        "evidence_sources": {"type": "array", "items": {"type": "object"}},
                        "as_at_date": {"type": "string"},
                    },
                    "required": ["claims", "evidence_sources"],
                },
            ),
            Tool(
                name="analyze_document",
                description="Parse an uploaded PDF or DOCX document and produce a grounded, verified IRAC analysis.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "matter_type": {"type": "string", "enum": ["standard", "fact_heavy"]},
                        "as_at_date": {"type": "string"},
                    },
                    "required": ["file_path"],
                },
            ),
        ]

    @server.call_tool()
    async def _call(name: str, arguments: dict) -> list[TextContent]:
        return [TextContent(type="text", text=dispatch(name, arguments))]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
