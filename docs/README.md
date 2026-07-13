# GAMMA Documentation

This directory is the canonical documentation index for GAMMA.

## Architecture Map

| Topic | Canonical doc |
|---|---|
| System architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Engine internals | [ENGINE_ARCHITECTURE.md](ENGINE_ARCHITECTURE.md) |
| Model format compatibility | [MODEL_FORMATS.md](MODEL_FORMATS.md) |
| Benchmarking workflows | [BENCHMARKING.md](BENCHMARKING.md) |
| Evidence-Gated Capability Transfer: controlled lanes, teacher qualification, external selection, and promotion receipts | [EVIDENCE_GATED_CAPABILITY_TRANSFER.md](EVIDENCE_GATED_CAPABILITY_TRANSFER.md) |
| Hybrid distillation legacy-name compatibility pointer | [HYBRID_DISTILLATION.md](HYBRID_DISTILLATION.md) |
| Verifier-guided learning, RLVR, prompt optimization, and experiment states | [VERIFIER_GUIDED_LEARNING.md](VERIFIER_GUIDED_LEARNING.md) |
| Cross-repository experiment register | [../projects/distillation/shared/experiments/README.md](../projects/distillation/shared/experiments/README.md) |
| Translation distillation ops + leaderboards | [../projects/distillation/translation/README.md](../projects/distillation/translation/README.md) |
| Integrations/API usage | [integration-guide.md](integration-guide.md) |
| Mind Meld usage + status | [../src/mind_meld/README.md](../src/mind_meld/README.md) |
| Runtime optimization tips | [optimization-guide.md](optimization-guide.md) |
| Natural-language command patterns | [NATURAL_LANGUAGE_COMMANDS.md](NATURAL_LANGUAGE_COMMANDS.md) |

## Fast Entry Points

- Project overview: [../README.md](../README.md)
- Engine setup and support matrix: [../src/engines/README.md](../src/engines/README.md)
- Tooling commands: [../tools/README.md](../tools/README.md)
- Flux docs: [../flux/README.md](../flux/README.md)
- Translation distillation results bundle: [../projects/distillation/translation/README.md](../projects/distillation/translation/README.md)

## Documentation Conventions

1. Keep exactly one canonical page per topic.
2. Put runnable command examples in the canonical page only.
3. Use repo-relative paths, not machine-specific absolute paths.
4. If behavior changes, update docs in the same change.
