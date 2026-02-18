# Conversation Starter — Per-Request Cost Estimate

This document estimates the cost of running **one** Conversation Starter program (one LinkedIn URL → one report).

## Cost breakdown per run

### 1. OpenAI (gpt-4o-mini)

The crew uses **CrewAI hierarchical** with 5 agents and 4 tasks. Each run involves:

- **Manager (Orchestrator):** multiple LLM calls for delegation and (optionally) re-delegation after critique
- **Agents:** Research, Context Sync, Critique, and Question Architect each make one or more LLM calls
- **Context:** task outputs are passed as context, so token counts grow over the run

**Typical gpt-4o-mini pricing:** ~$0.15 / 1M input tokens, ~$0.60 / 1M output tokens.

| Component | Estimate per run |
|-----------|------------------|
| Input     | ~40k–70k tokens → ~$0.006–$0.011 |
| Output    | ~10k–20k tokens → ~$0.006–$0.012 |
| **OpenAI**| **~$0.015–$0.025** (1.5–2.5¢) |

If the critique loop triggers re-research, add roughly **$0.005–$0.01**.

---

### 2. Proxycurl (LinkedIn profile)

- **1 request** per run when `PROXYCURL_API_KEY` is set
- Often quoted at **~$0.01 per request** (or 1 credit at similar effective price)

| Component  | Estimate per run |
|------------|------------------|
| **Proxycurl** | **~$0.01** (when used) |

If Proxycurl is not configured, the crew uses only Firecrawl for research (no LinkedIn API cost).

---

### 3. Firecrawl (web search)

- **Search:** 2 credits per 10 results; this project uses `limit=5` → ~1–2 credits per search call
- Web Researcher typically makes **1–3 search calls** per run → **~2–6 credits**
- At Firecrawl Hobby ($16/mo for 3,000 credits): ~$0.0053 per credit → **~$0.01–$0.03 per run**

| Component   | Estimate per run |
|-------------|------------------|
| **Firecrawl** | **~$0.01–$0.03** |

---

## Total per request

| Component   | Low    | High   |
|------------|--------|--------|
| OpenAI     | ~$0.015 | ~$0.03 |
| Proxycurl  | ~$0.01  | ~$0.01 |
| Firecrawl  | ~$0.01  | ~$0.03 |
| **Total**  | **~$0.035** | **~$0.07** |

**Summary:** **~$0.03–$0.07 per run** (about **3–7 cents per request**). A typical single run is around **$0.04–$0.05**.

---

## Notes

- **No Proxycurl:** If `PROXYCURL_API_KEY` is not set, the crew falls back to Firecrawl-only research; you save ~$0.01 per run and may use slightly more Firecrawl credits.
- **Model change:** Using `gpt-4o` instead of `gpt-4o-mini` in `main.py` will increase OpenAI cost (often 5–10×); keep `gpt-4o-mini` for cheaper testing.
- **Pricing sources:** OpenAI and third-party API pricing can change; check [OpenAI pricing](https://platform.openai.com/docs/pricing), [Proxycurl](https://nubela.co/proxycurl/pricing.html), and [Firecrawl](https://firecrawl.dev/pricing) for current rates.
