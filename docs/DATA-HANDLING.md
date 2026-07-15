# Data Handling & Residency

> Short version: **your COBOL never leaves your network.** The open-source toolkit runs entirely
> locally, and the commercial **Cartograph** tier is deployed *inside* your environment, not a
> service you upload source code to.

This document states how these tools handle your source and metadata. It is written for the people
who have to answer security review questionnaires at banks, insurers, and government agencies.

## Principles

1. **Local-first and air-gappable by default.** The `cobol-migrate` CLI reads your source from local
   disk, does all analysis in-process, and writes output to a local path you choose. It works with no
   network access at all.
2. **No telemetry.** The OSS toolkit does not phone home. Any future usage reporting will be **opt-in**
   and **metadata-only** (never source), and clearly documented.
3. **Deployed, not uploaded-to.** The commercial Cartograph dashboard ships as a container / Helm
   deployable that you run inside your own network. There is no multi-tenant service that ingests your
   source code.
4. **Metadata boundary.** If you opt into a managed control plane, only **aggregate metadata** may
   leave — program/copybook counts, dependency graphs, risk and effort scores — and only under an
   explicit data-processing agreement. Raw source and identifiers never leave without your action.
5. **Bring-your-own-model for AI features.** Cartograph's LLM-assisted documentation defaults to
   **customer-hosted models** — e.g. Ollama or vLLM on your infrastructure, or Amazon Bedrock / Azure
   OpenAI **in your own cloud tenant**. No third-party model API is called by default. Redaction and
   path/scope controls are on by default.

## What the OSS toolkit reads and writes

| | Detail |
|---|---|
| **Reads** | COBOL/copybook files under the path you pass to `scan`. |
| **Writes** | `inventory.json`, `report.md`, `dependencies.dot` (+ `report.html` in future) to `--output`. |
| **Network** | None. |
| **Persistence** | None beyond the output files you request. |

## Deployment models for Cartograph (commercial)

- **Air-gapped / on-prem:** fully offline install; license validation supports offline/entitlement
  files. Nothing egresses.
- **Customer cloud (self-hosted):** you deploy into your own VPC/tenant; data stays in your account.
- **Managed control plane (optional):** metadata-only, opt-in, DPA-governed — for teams that want
  Make Directory to host dashboards/benchmarks across their own estate.

## Reporting concerns

Security questions or data-handling clarifications: **andrew@mk-dir.com**. Vulnerabilities: see
[`../SECURITY.md`](../SECURITY.md).
