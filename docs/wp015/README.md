# WP-015 — Research Assistant Workspace (Offline Foundation)

**Status: tested local guided assistant, NOT a deployed LLM or autonomous agent.** User-requested autonomous, guided and conventional modes are selectable. This package intentionally does not execute an AI model, provider network call, or accepted-tree change.

## Implemented

- `POST /api/v1/research/assistant/answer`: 4–1000 character research question, one of three approved research modes, up to six selected observation IDs. All IDs must refer to real source-cited historical appearances. A deterministic local rule engine creates bounded research steps and exact observation/document citations.
- `GET /api/v1/research/assistant/capabilities`: reports the current model and external execution gates truthfully.
- `/workspace` **Guided research assistant**: a structured source-grounded Q&A form, cited summary and researcher-controlled next steps. Historical text is rendered as literal text, not HTML.
- Cited identity and relationship questions prompt alternative hypotheses, direct-evidence checking, source independence and explicit unknown alternatives. No model-sourced numerical probability or unapproved Gramps mutation.

## Acceptance boundaries

This is **not** a semantic LLM chat or automated online researcher. Its summary is templated and limited to the explicitly selected documents. Question text is not sent to the cloud, stored, or billed. 'Autonomous' currently generates only a safe manual plan and does not trigger work.

## Planned later work

Implement separately reviewed local Ollama and opt-in cloud AI adapters, consent/PII minimisation, source quote and citation verification, prompt-injection handling, rate/cost enforcement, graceful local fallback, research task tool contracts, permissions, model benchmarking and full human-approval gates. Do not enable remote model calls as a side effect of installing WP-015.

## Tests

`tests/test_wp015_assistant.py`: authentication and bounds, missing/unknown citations, modes, malicious text as data, false-confidence prevention and disabled model/provider capabilities.
