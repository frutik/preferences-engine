# preferences-engine
DICE-inspired AI-powered engine for inferring user preferences

![Example](example.png)

## Inspiration

This implementation tries to follow the original [DICE](https://github.com/embabel/dice/tree/90c00d93f8e347ebafa94cf8ba1c855b19eb22b1) design and is heavily inspired by its code and the accompanying article: [Agents That Extract and Use Preferences from Conversations](https://medium.com/embabel/agents-that-extract-and-use-preferences-from-conversations-7b22cca9abb3).

There is also an idea to extend the inference signal beyond chat messages to include implicit user behavior — such as applied filters and item clicks — as additional sources for preference extraction.

Another planned direction is a user-facing API that gives users visibility and control over their inferred preferences — allowing them to inspect what has been inferred and selectively disable individual preferences or turn off inference entirely.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PREFERENCE_ENGINE_OPENAI_API_KEY` | Yes | — | OpenAI API key used for preference extraction |
| `PREFERENCE_ENGINE_OPENAI_MODEL` | No | `gpt-5.5` | OpenAI model used for extraction |

## Maintenance

### `expire_decayed_memories`

Scans all active preferences and marks any whose effective score (`importance × confidence × e^(−decay × age_months)`) has fallen below `DECAY_THRESHOLD = 0.05` as `SUPERSEDED`.

```bash
# Preview without writing
python manage.py expire_decayed_memories --dry-run

# Apply
python manage.py expire_decayed_memories
```

Intended to be run periodically as a cronjob, e.g. nightly:

```cron
0 2 * * * /path/to/venv/bin/python /path/to/manage.py expire_decayed_memories >> /var/log/expire_decayed_memories.log 2>&1
```

## Limitations

- **Domain**: hardcoded for e-commerce in [`preferences_engine/domain_schema.py`](preferences_engine/domain_schema.py); not yet configurable for other domains
- **LLM provider**: OpenAI only; no support for other providers
- **ORM**: Django ORM only; no adapter for other persistence layers
- **No audit module**: there is currently no mechanism to prevent extracting sensitive preferences — use with caution in production
