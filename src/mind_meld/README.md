# Mind Meld Mode (Experimental)

This directory contains the logic for an experimental feature called **Mind Meld**. The goal of this mode is to dynamically switch between two or more different language models during a single, continuous generation process.

## Concept

The core idea is to leverage the strengths of different models. For example, one could meld a base model (good at creative, unrestricted text) with an instruction-tuned model (good at following commands and being helpful). The `MeldEngine` could use the base model for general text generation but swap to the instruction-tuned model when it detects a question or command.

The current implementation provides the foundational structure for this feature and swaps models whenever a punctuation mark is detected.

## Key Components

- **`core/meld_engine.py`**: The central orchestrator for the melding process. It manages the active model, decides when to swap, and uses the bridge components to translate state between models.

- **`translators/`**: This sub-directory contains modules for bridging the gaps between different model architectures.
    - **`vocabulary_translator.py`**: Handles the challenge of models having different tokenizers and vocabularies. The current `VocabularyIntersectionTranslator` allows the system to function by only predicting tokens that exist in both models' vocabularies.

- **`bridges/`**: This sub-directory is responsible for translating the internal state of a model.
    - **`kv_cache_bridge.py`**: Attempts to translate the Key-Value (KV) cache from one model to another. The current `DirectKVCacheBridge` performs a direct, best-effort transfer that is most likely to work between models of the same family (e.g., Gemma 2B and Gemma 7B).
