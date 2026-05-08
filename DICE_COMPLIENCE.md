# DICE Compliance

## DICE Compliance Summary Table

| DICE Principle | Status | Notes                                                                                |
|---|---|--------------------------------------------------------------------------------------|
| Typed domain ontology constraining LLM | ✅ Strong | `PreferenceSchema`, `DomainPredicate` with `allowed_object_types`                    |
| Structured bidirectional LLM mapping | ✅ Strong | `ExtractedProposition`, `RevisionResult` as Pydantic output types                    |
| Persistent ORM integration | ✅ Strong | Django/Postgres, full audit log via `UserPreferenceMemoryEvent`                      |
| Code-driven context ranking/filtering | ✅ Good | `inject_for_prompt` with `importance × confidence` ranking                           |
| Context actually injected into agent | ✅ Fixed | `known_preferences` appended to `prompt` in `v1.py` when non-empty                  |
| Memory decay/expiration | ✅ Implemented | `effective_score()` filters at `DECAY_THRESHOLD`; management command for hard expiry |
| Live catalog grounding of domain schema | ⚠️ Partial | Static schema; no link to live `shop_assortment` data                                |
| Privacy / observation audit | ⚠️ Partial | User visibility via `GET /preferences/`; user deletion via `DELETE /preferences/{id}/`; no pre-extraction filter |

---

## DICE Compliance Verdict

The architecture is **fully aligned with DICE in both design and operation**. The schema, structured outputs, ORM integration, two-phase extract/revise pipeline, decay-based filtering, and context injection are all in place. The two remaining gaps are secondary: the domain schema is static rather than grounded in live catalog data, and there is no privacy audit layer to gate what enters the memory store.

### Limitations

- **Domain**: hardcoded for e-commerce in [`preferences_engine/domain_schema.py`](preferences_engine/domain_schema.py); not yet configurable for other domains
- **LLM provider**: OpenAI only; no support for other providers
- **Memory**: Django ORM only; no adapter for other persistence layers
- **No pre-extraction audit**: users can view (`GET /preferences/`) and delete (`DELETE /preferences/{id}/`) stored facts using API, but there is no filter that prevents sensitive inferences from being extracted in the first place — use with caution in production
