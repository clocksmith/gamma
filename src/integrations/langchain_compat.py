"""
LangChain compatibility layer for GAMMA engines.

Provides LangChain LLM wrappers so GAMMA engines can be used with LangChain
chains, agents, and other components.

Note: Requires langchain package to be installed.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Iterator, TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.schema.output import GenerationChunk

try:
    from langchain.llms.base import LLM
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create dummy base class if LangChain not installed
    class LLM:
        pass
    # Dummy types for type hints
    CallbackManagerForLLMRun = Any  # type: ignore
    GenerationChunk = Any  # type: ignore


class GAMMALangChainLLM(LLM):
    """
    LangChain-compatible wrapper for GAMMA engines.

    Example:
        from src.engines.pytorch_engine import PyTorchEngine
        from src.integrations.langchain_compat import GAMMALangChainLLM

        engine = PyTorchEngine("gpt2")
        engine.load()

        llm = GAMMALangChainLLM(engine=engine, max_tokens=50)

        # Use with LangChain
        result = llm("What is the capital of France?")
        print(result)

        # Use in chains
        from langchain.chains import LLMChain
        from langchain.prompts import PromptTemplate

        prompt = PromptTemplate(
            input_variables=["question"],
            template="Question: {question}\\nAnswer:"
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain.run(question="What is Python?")
    """

    engine: Any = None
    """GAMMA engine instance."""

    max_tokens: int = 100
    """Maximum number of tokens to generate."""

    temperature: float = 0.7
    """Sampling temperature."""

    top_p: float = 0.9
    """Nucleus sampling threshold."""

    top_k: int = 50
    """Top-k sampling."""

    stop: Optional[List[str]] = None
    """Stop sequences."""

    streaming: bool = False
    """Whether to stream responses."""

    def __init__(
        self,
        engine: Any,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        stop: Optional[List[str]] = None,
        streaming: bool = False,
        **kwargs
    ):
        """
        Initialize LangChain-compatible LLM.

        Args:
            engine: GAMMA engine instance (must have encode, predict_next, decode)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling
            stop: Stop sequences
            streaming: Whether to stream responses
            **kwargs: Additional parameters
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. Install it with: pip install langchain"
            )

        super().__init__(**kwargs)
        self.engine = engine
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.stop = stop or []
        self.streaming = streaming

    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "gamma"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters."""
        return {
            "model_name": getattr(self.engine, 'model_name', 'unknown'),
            "engine_type": self.engine.__class__.__name__,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k
        }

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> str:
        """
        Call the LLM with a prompt.

        Args:
            prompt: Input prompt
            stop: Stop sequences (overrides instance stop)
            run_manager: Callback manager
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        # Merge stop sequences
        all_stop = list(set((stop or []) + (self.stop or [])))

        # Generate
        generated_text = self._generate_text(prompt, all_stop)

        return generated_text

    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> Iterator[GenerationChunk]:
        """
        Stream the LLM output.

        Args:
            prompt: Input prompt
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Yields:
            GenerationChunk objects
        """
        all_stop = list(set((stop or []) + (self.stop or [])))

        for token_text in self._generate_stream(prompt, all_stop):
            chunk = GenerationChunk(text=token_text)
            yield chunk

            if run_manager:
                run_manager.on_llm_new_token(token_text, chunk=chunk)

    def _generate_text(self, prompt: str, stop: List[str]) -> str:
        """Internal generation method."""
        # Encode prompt
        input_ids, attention_mask = self.engine.encode(prompt)

        # Generate tokens
        generated_tokens = []
        current_input_ids = input_ids
        current_attention_mask = attention_mask

        for _ in range(self.max_tokens):
            # Predict next token
            output = self.engine.predict_next(
                current_input_ids,
                current_attention_mask,
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p
            )

            next_token_id = output["next_token_id"]
            generated_tokens.append(next_token_id)

            # Check for EOS token
            if hasattr(self.engine, 'tokenizer') and hasattr(self.engine.tokenizer, 'eos_token_id'):
                if next_token_id == self.engine.tokenizer.eos_token_id:
                    break

            # Update input for next iteration
            current_input_ids = output.get("input_ids_updated", current_input_ids)
            current_attention_mask = output.get("attention_mask_updated", current_attention_mask)

            # Check stop sequences
            if stop:
                partial_text = self.engine.decode(generated_tokens)
                if any(stop_seq in partial_text for stop_seq in stop):
                    break

        # Decode generated tokens
        generated_text = self.engine.decode(generated_tokens)

        # Remove stop sequences from end
        for stop_seq in stop:
            if generated_text.endswith(stop_seq):
                generated_text = generated_text[:-len(stop_seq)]

        return generated_text

    def _generate_stream(self, prompt: str, stop: List[str]) -> Iterator[str]:
        """Internal streaming generation method."""
        input_ids, attention_mask = self.engine.encode(prompt)

        current_input_ids = input_ids
        current_attention_mask = attention_mask

        for _ in range(self.max_tokens):
            output = self.engine.predict_next(
                current_input_ids,
                current_attention_mask,
                temperature=self.temperature,
                top_k=self.top_k,
                top_p=self.top_p
            )

            next_token_id = output["next_token_id"]

            # Check for EOS
            if hasattr(self.engine, 'tokenizer') and hasattr(self.engine.tokenizer, 'eos_token_id'):
                if next_token_id == self.engine.tokenizer.eos_token_id:
                    break

            # Decode token
            token_text = self.engine.decode([next_token_id])

            # Check stop sequences
            should_stop = False
            for stop_seq in stop:
                if stop_seq in token_text:
                    should_stop = True
                    # Return only part before stop sequence
                    if stop_seq in token_text:
                        token_text = token_text.split(stop_seq)[0]

            yield token_text

            if should_stop:
                break

            # Update input
            current_input_ids = output.get("input_ids_updated", current_input_ids)
            current_attention_mask = output.get("attention_mask_updated", current_attention_mask)


class GAMMAEmbeddings:
    """
    LangChain-compatible embeddings for GAMMA engines.

    Note: Not all GAMMA engines support embeddings. This requires an engine
    that can extract hidden states (typically transformer models).

    Example:
        from src.engines.pytorch_engine import PyTorchEngine
        from src.integrations.langchain_compat import GAMMAEmbeddings

        engine = PyTorchEngine("sentence-transformers/all-MiniLM-L6-v2")
        engine.load()

        embeddings = GAMMAEmbeddings(engine=engine)

        # Embed documents
        doc_embeddings = embeddings.embed_documents([
            "This is a document",
            "This is another document"
        ])

        # Embed query
        query_embedding = embeddings.embed_query("This is a query")
    """

    def __init__(self, engine: Any, pooling: str = "mean"):
        """
        Initialize embeddings.

        Args:
            engine: GAMMA engine instance
            pooling: Pooling strategy ("mean", "max", "cls")
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. Install it with: pip install langchain"
            )

        self.engine = engine
        self.pooling = pooling

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.

        Args:
            texts: List of documents to embed

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        embeddings = []

        for text in texts:
            embedding = self._embed_single(text)
            embeddings.append(embedding)

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text: Query text

        Returns:
            Embedding as list of floats
        """
        return self._embed_single(text)

    def _embed_single(self, text: str) -> List[float]:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding as list of floats
        """
        # Check if engine supports embeddings
        if not hasattr(self.engine, 'get_hidden_states'):
            raise NotImplementedError(
                f"Engine {self.engine.__class__.__name__} does not support embeddings. "
                f"The engine must implement a get_hidden_states() method."
            )

        # Encode text
        input_ids, attention_mask = self.engine.encode(text)

        # Get hidden states
        hidden_states = self.engine.get_hidden_states(input_ids, attention_mask)

        # Pool hidden states
        if self.pooling == "mean":
            # Mean pooling (considering attention mask)
            import numpy as np
            mask_expanded = np.expand_dims(attention_mask, -1)
            sum_embeddings = np.sum(hidden_states * mask_expanded, axis=1)
            sum_mask = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)
            embedding = (sum_embeddings / sum_mask)[0]

        elif self.pooling == "max":
            # Max pooling
            import numpy as np
            embedding = np.max(hidden_states, axis=1)[0]

        elif self.pooling == "cls":
            # Use [CLS] token (first token)
            embedding = hidden_states[0, 0, :]

        else:
            raise ValueError(f"Unknown pooling strategy: {self.pooling}")

        return embedding.tolist()


# Convenience functions

def create_langchain_llm(
    engine: Any,
    max_tokens: int = 100,
    temperature: float = 0.7,
    **kwargs
) -> GAMMALangChainLLM:
    """
    Create a LangChain-compatible LLM from a GAMMA engine.

    Args:
        engine: GAMMA engine instance
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        **kwargs: Additional parameters

    Returns:
        GAMMALangChainLLM instance
    """
    if not LANGCHAIN_AVAILABLE:
        warnings.warn(
            "LangChain is not installed. This function will raise an error. "
            "Install it with: pip install langchain"
        )

    return GAMMALangChainLLM(
        engine=engine,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )


def create_langchain_embeddings(engine: Any, pooling: str = "mean") -> GAMMAEmbeddings:
    """
    Create LangChain-compatible embeddings from a GAMMA engine.

    Args:
        engine: GAMMA engine instance
        pooling: Pooling strategy

    Returns:
        GAMMAEmbeddings instance
    """
    if not LANGCHAIN_AVAILABLE:
        warnings.warn(
            "LangChain is not installed. This function will raise an error. "
            "Install it with: pip install langchain"
        )

    return GAMMAEmbeddings(engine=engine, pooling=pooling)
