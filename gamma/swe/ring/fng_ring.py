"""
FunctionGemma Spatial Ring - Parallel tool search with streaming.

Architecture:
- N FunctionGemma nodes run in PARALLEL
- Each node's output feeds into next node (ring topology)
- Results stream to conductor in real-time
- Ring iterates until score >= threshold
- Conductor can inject tool changes mid-flight
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional
from enum import Enum


class NodeStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class ToolCall:
    tool: str
    args: Dict[str, Any]
    node_id: int


@dataclass
class NodeOutput:
    node_id: int
    tool_call: ToolCall
    result: Any
    score: float
    round: int


@dataclass
class RingResult:
    outputs: List[NodeOutput]
    best_output: NodeOutput
    best_score: float
    rounds: int
    threshold_met: bool


@dataclass
class RingConfig:
    num_nodes: int = 4
    max_rounds: int = 10
    default_threshold: float = 0.8
    max_retries: int = 1
    retry_backoff_seconds: float = 0.25
    allow_fallback_tool: bool = True
    plateau_patience: int = 2
    plateau_epsilon: float = 0.02
    shard_max_items: int = 5
    preview_limit: int = 200
    full_result_top_k: int = 2
    full_result_limit: int = 1000


class FunctionGemmaNode:
    """
    Single FunctionGemma node in the ring.

    Uses FunctionGemma's native format with special tokens:
    - <start_function_declaration> for tool definitions
    - <start_function_call>call:name{args}<end_function_call> for calls
    """

    def __init__(self, node_id: int, model, tokenizer=None):
        self.node_id = node_id
        self.model = model  # FunctionGemma instance
        self.tokenizer = tokenizer  # Optional: for native format
        self.status = NodeStatus.IDLE

        # Import formatter
        from .functiongemma import FunctionGemmaFormatter, convert_tools_to_functiongemma
        self.formatter = FunctionGemmaFormatter()
        self._convert_tools = convert_tools_to_functiongemma
        self._tool_schemas: List[Dict[str, Any]] = []

    async def execute(
        self,
        query: str,
        prior_output: Optional[NodeOutput],
        tools: Dict[str, Any],
    ) -> ToolCall:
        """Decide which tool to call based on query and prior results."""
        self.status = NodeStatus.RUNNING

        # Convert tools to FunctionGemma format if needed
        if not self._tool_schemas or set(tools.keys()) != set(t["function"]["name"] for t in self._tool_schemas):
            self._tool_schemas = self._convert_tools(tools)

        # Build prior result tuple if available
        prior_result = None
        if prior_output:
            prior_result = (prior_output.tool_call.tool, prior_output.result)

        # Use native format if tokenizer available, else formatted prompt
        if self.tokenizer is not None:
            tool_name, args = await self._execute_native(query, prior_result)
        else:
            tool_name, args = await self._execute_formatted(query, prior_result)

        self.status = NodeStatus.DONE
        return ToolCall(tool=tool_name, args=args, node_id=self.node_id)

    async def _execute_native(
        self,
        query: str,
        prior_result: Optional[tuple],
    ) -> tuple:
        """Execute using HuggingFace tokenizer's apply_chat_template."""
        messages = [{"role": "user", "content": query}]

        if prior_result:
            tool_name, result = prior_result
            messages.insert(0, {
                "role": "assistant",
                "tool_calls": [{
                    "type": "function",
                    "function": {"name": tool_name, "arguments": {"result": str(result)[:200]}}
                }]
            })

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tools=self._tool_schemas,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )

        # Generate (assuming model has generate_tokens for tensor input)
        if hasattr(self.model, 'generate_tokens'):
            outputs = await self.model.generate_tokens(inputs, max_new_tokens=128)
            output_text = self.tokenizer.decode(
                outputs[0][len(inputs["input_ids"][0]):],
                skip_special_tokens=False,
            )
        else:
            # Fallback: decode input and use text generation
            input_text = self.tokenizer.decode(inputs["input_ids"][0])
            output_text = await self.model.generate(input_text, max_tokens=128)

        return self._parse_output(output_text)

    async def _execute_formatted(
        self,
        query: str,
        prior_result: Optional[tuple],
    ) -> tuple:
        """Execute using manual FunctionGemma formatting."""
        prompt = self.formatter.format_prompt(
            query=query,
            tools=self._tool_schemas,
            prior_result=prior_result,
        )

        response = await self.model.generate(prompt, max_tokens=128)
        return self._parse_output(response)

    def _parse_output(self, output: str) -> tuple:
        """Parse FunctionGemma output to extract tool call."""
        # Try native FunctionGemma format first
        result = self.formatter.parse_tool_call(output)
        if result:
            return result

        # Fallback: try JSON format
        import json
        try:
            if "{" in output:
                json_str = output[output.index("{"):output.rindex("}")+1]
                parsed = json.loads(json_str)
                return (parsed.get("tool", "noop"), parsed.get("args", {}))
        except (json.JSONDecodeError, ValueError):
            pass

        return ("noop", {})


class FunctionGemmaRing:
    """
    Spatial ring of FunctionGemma nodes.

    All nodes run in parallel, passing results around the ring.
    Streams results to conductor in real-time.

    Uses FunctionGemma's native format with:
    - <start_function_declaration> for tool definitions
    - <start_function_call>call:name{args}<end_function_call> for calls
    """

    def __init__(
        self,
        models: List[Any],  # List of FunctionGemma model instances
        config: Optional[RingConfig] = None,
        tokenizers: Optional[List[Any]] = None,  # Optional tokenizers for native format
    ):
        self.config = config or RingConfig()

        # Create nodes with optional tokenizers
        if tokenizers and len(tokenizers) == len(models):
            self.nodes = [
                FunctionGemmaNode(i, model, tokenizer)
                for i, (model, tokenizer) in enumerate(zip(models, tokenizers))
            ]
        else:
            self.nodes = [
                FunctionGemmaNode(i, model)
                for i, model in enumerate(models)
            ]

        self.tools: Dict[str, Callable] = {}
        self._stream_callback: Optional[Callable[[NodeOutput], None]] = None
        self._tool_lock = asyncio.Lock()
        self._scorer: Optional[Callable[[str, Any], Any]] = None

    def register_tool(self, name: str, executor: Callable) -> None:
        """Register a tool executor."""
        self.tools[name] = executor

    def set_stream_callback(self, callback: Callable[[NodeOutput], None]) -> None:
        """Set callback for streaming results to conductor."""
        self._stream_callback = callback

    def set_scorer(self, scorer: Callable[[str, Any], float]) -> None:
        """Override the default scoring function."""
        self._scorer = scorer

    async def add_tool_live(self, name: str, executor: Callable) -> None:
        """Add tool while ring is running (conductor consolidation)."""
        async with self._tool_lock:
            self.tools[name] = executor

    async def remove_tool_live(self, name: str) -> None:
        """Remove tool while ring is running."""
        async with self._tool_lock:
            self.tools.pop(name, None)

    async def search(
        self,
        query: str,
        threshold: float,
    ) -> RingResult:
        """
        Run ring until threshold met or max rounds.

        All nodes execute in parallel each round.
        Results pass around ring: node[i] output -> node[i+1] input.
        """
        all_outputs: List[NodeOutput] = []
        best_output: Optional[NodeOutput] = None
        best_score = 0.0
        last_best_score = 0.0
        plateau_rounds = 0

        # Initialize: no prior outputs
        prior_outputs: List[Optional[NodeOutput]] = [None] * len(self.nodes)

        for round_num in range(self.config.max_rounds):
            # PARALLEL: all nodes execute simultaneously
            async with self._tool_lock:
                current_tools = dict(self.tools)

            tool_calls = await asyncio.gather(*[
                node.execute(query, prior_outputs[i], current_tools)
                for i, node in enumerate(self.nodes)
            ])

            if self.config.allow_fallback_tool:
                tool_calls = [
                    self._maybe_fallback_tool(query, tc, current_tools)
                    for tc in tool_calls
                ]

            # Execute tools in parallel
            results = await asyncio.gather(*[
                self._execute_tool(tc, current_tools)
                for tc in tool_calls
            ])

            # Score and create outputs
            round_outputs = []
            for i, (tc, result) in enumerate(zip(tool_calls, results)):
                score = await self._score_result(query, result)
                output = NodeOutput(
                    node_id=i,
                    tool_call=tc,
                    result=result,
                    score=score,
                    round=round_num,
                )
                round_outputs.append(output)
                all_outputs.append(output)

                # Stream to conductor
                if self._stream_callback:
                    self._stream_callback(output)

                # Track best
                if score > best_score:
                    best_score = score
                    best_output = output

            # Check threshold
            if best_score >= threshold:
                return RingResult(
                    outputs=all_outputs,
                    best_output=best_output,
                    best_score=best_score,
                    rounds=round_num + 1,
                    threshold_met=True,
                )

            # Plateau detection
            if round_num > 0:
                improvement = best_score - last_best_score
                if improvement < self.config.plateau_epsilon:
                    plateau_rounds += 1
                else:
                    plateau_rounds = 0
                if plateau_rounds >= self.config.plateau_patience:
                    return RingResult(
                        outputs=all_outputs,
                        best_output=best_output,
                        best_score=best_score,
                        rounds=round_num + 1,
                        threshold_met=False,
                    )
            last_best_score = best_score

            prior_outputs = self._next_prior_outputs(round_outputs, best_output, round_num)

        return RingResult(
            outputs=all_outputs,
            best_output=best_output,
            best_score=best_score,
            rounds=self.config.max_rounds,
            threshold_met=False,
        )

    async def search_streaming(
        self,
        query: str,
        threshold: float,
    ) -> AsyncIterator[NodeOutput]:
        """
        Async generator that yields results as they come.

        Conductor can consume this stream and react in real-time.
        """
        prior_outputs: List[Optional[NodeOutput]] = [None] * len(self.nodes)
        best_score = 0.0
        last_best_score = 0.0
        plateau_rounds = 0

        for round_num in range(self.config.max_rounds):
            async with self._tool_lock:
                current_tools = dict(self.tools)

            # Parallel execution
            tool_calls = await asyncio.gather(*[
                node.execute(query, prior_outputs[i], current_tools)
                for i, node in enumerate(self.nodes)
            ])

            if self.config.allow_fallback_tool:
                tool_calls = [
                    self._maybe_fallback_tool(query, tc, current_tools)
                    for tc in tool_calls
                ]

            results = await asyncio.gather(*[
                self._execute_tool(tc, current_tools)
                for tc in tool_calls
            ])

            round_outputs = []
            for i, (tc, result) in enumerate(zip(tool_calls, results)):
                score = await self._score_result(query, result)
                output = NodeOutput(
                    node_id=i,
                    tool_call=tc,
                    result=result,
                    score=score,
                    round=round_num,
                )
                round_outputs.append(output)
                best_score = max(best_score, score)

                # Yield to conductor
                yield output

            if best_score >= threshold:
                return

            if round_num > 0:
                improvement = best_score - last_best_score
                if improvement < self.config.plateau_epsilon:
                    plateau_rounds += 1
                else:
                    plateau_rounds = 0
                if plateau_rounds >= self.config.plateau_patience:
                    return
            last_best_score = best_score

            prior_outputs = self._next_prior_outputs(round_outputs, None, round_num)

    async def _execute_tool(
        self,
        tool_call: ToolCall,
        tools: Dict[str, Callable],
    ) -> Any:
        """Execute a tool call."""
        if tool_call.tool not in tools:
            return {"error": f"Unknown tool: {tool_call.tool}"}

        executor = tools[tool_call.tool]
        attempts = max(self.config.max_retries + 1, 1)
        for attempt in range(attempts):
            try:
                if asyncio.iscoroutinefunction(executor):
                    return await executor(**tool_call.args)
                return executor(**tool_call.args)
            except Exception as e:
                if attempt < attempts - 1:
                    await asyncio.sleep(self.config.retry_backoff_seconds * (attempt + 1))
                    continue
                return {"error": str(e), "attempts": attempts}

    async def _score_result(self, query: str, result: Any) -> float:
        """
        Score a tool result's relevance to query.

        Simple heuristic - can be enhanced with learned scorer.
        """
        if self._scorer:
            try:
                return float(await self._call_scorer(query, result))
            except Exception:
                return 0.0

        if isinstance(result, dict) and "error" in result:
            return 0.0

        if result is None:
            return 0.1

        # Convert to string for simple scoring
        result_str = str(result).lower()
        query_words = query.lower().split()

        # Count query term matches
        matches = sum(1 for word in query_words if word in result_str)
        base_score = min(matches / max(len(query_words), 1), 1.0)

        # Use explicit scores if provided
        if isinstance(result, dict):
            if "score" in result:
                try:
                    base_score = max(base_score, float(result["score"]))
                except (TypeError, ValueError):
                    pass
            elif "confidence" in result:
                try:
                    base_score = max(base_score, float(result["confidence"]))
                except (TypeError, ValueError):
                    pass
            if "count" in result:
                try:
                    base_score += min(float(result["count"]) / 50.0, 0.2)
                except (TypeError, ValueError):
                    pass

        if isinstance(result, list):
            base_score += min(len(result) / 50.0, 0.2)

        # Bonus for substantial results
        if len(result_str) > 100:
            base_score += 0.1
        if len(result_str) > 500:
            base_score += 0.1

        return min(base_score, 1.0)

    async def _call_scorer(self, query: str, result: Any) -> float:
        """Call scorer with async support."""
        score = self._scorer(query, result)
        if asyncio.iscoroutine(score):
            return await score
        return score

    def _next_prior_outputs(
        self,
        round_outputs: List[NodeOutput],
        best_output: Optional[NodeOutput],
        round_num: int,
    ) -> List[Optional[NodeOutput]]:
        """Compute prior outputs for the next round."""
        if not round_outputs:
            return [None] * len(self.nodes)
        return self._build_all_reduce_context(round_outputs, round_num)

    def _build_all_reduce_context(
        self,
        round_outputs: List[NodeOutput],
        round_num: int,
    ) -> List[Optional[NodeOutput]]:
        """Build ring context with gather + scatter summary."""
        aggregate = self._aggregate_round(round_outputs)
        shards = self._scatter_round(round_outputs)

        contexts: List[Optional[NodeOutput]] = []
        for i, shard in enumerate(shards):
            payload = {
                "round": round_num,
                "aggregate": aggregate,
                "shard": shard,
            }
            contexts.append(self._wrap_ring_state(payload, node_id=i, round_num=round_num))
        return contexts

    def _aggregate_round(self, round_outputs: List[NodeOutput]) -> Dict[str, Any]:
        """Aggregate outputs for all-reduce."""
        if not round_outputs:
            return {}

        best = max(round_outputs, key=lambda o: o.score)
        scores = [o.score for o in round_outputs]
        tool_counts: Dict[str, int] = {}
        for o in round_outputs:
            tool_counts[o.tool_call.tool] = tool_counts.get(o.tool_call.tool, 0) + 1

        top_full = sorted(round_outputs, key=lambda o: o.score, reverse=True)
        top_full = top_full[: self.config.full_result_top_k]
        full_results = [
            {
                "tool": o.tool_call.tool,
                "score": o.score,
                "result": self._full_result(o.result),
            }
            for o in top_full
        ]

        return {
            "best": {
                "tool": best.tool_call.tool,
                "score": best.score,
                "result_preview": self._preview_result(best.result),
            },
            "mean_score": sum(scores) / max(len(scores), 1),
            "max_score": max(scores),
            "min_score": min(scores),
            "tool_counts": tool_counts,
            "top_results": full_results,
        }

    def _scatter_round(self, round_outputs: List[NodeOutput]) -> List[List[Dict[str, Any]]]:
        """Scatter round outputs into node shards."""
        shards: List[List[Dict[str, Any]]] = [[] for _ in range(len(self.nodes))]
        for i, output in enumerate(round_outputs):
            shard_id = i % len(self.nodes)
            shards[shard_id].append({
                "tool": output.tool_call.tool,
                "score": output.score,
                "result_preview": self._preview_result(output.result),
            })
        shards = [s[: self.config.shard_max_items] for s in shards]
        return shards

    def _wrap_ring_state(
        self,
        payload: Dict[str, Any],
        node_id: int,
        round_num: int,
    ) -> NodeOutput:
        """Wrap ring state as a NodeOutput for passing to nodes."""
        return NodeOutput(
            node_id=node_id,
            tool_call=ToolCall(tool="ring_state", args={}, node_id=node_id),
            result=payload,
            score=0.0,
            round=round_num,
        )

    def _preview_result(self, result: Any) -> str:
        """Preview result string for ring context."""
        text = str(result)
        limit = self.config.preview_limit
        return text[:limit] + ("..." if len(text) > limit else "")

    def _full_result(self, result: Any) -> str:
        """Full result string for top results, capped to limit."""
        text = str(result)
        limit = self.config.full_result_limit
        return text[:limit] + ("..." if len(text) > limit else "")

    def _maybe_fallback_tool(
        self,
        query: str,
        tool_call: ToolCall,
        tools: Dict[str, Callable],
    ) -> ToolCall:
        """Fallback to a heuristic tool choice when the model picks poorly."""
        if tool_call.tool in tools and tool_call.tool != "noop":
            return tool_call

        fallback = self._fallback_tool_call(query, tools, tool_call.node_id)
        return fallback or tool_call

    def _fallback_tool_call(
        self,
        query: str,
        tools: Dict[str, Callable],
        node_id: int,
    ) -> Optional[ToolCall]:
        """Choose a tool based on query keywords and tool tags."""
        import re

        q = query.lower()
        query_words = set(re.findall(r"[a-z0-9_./-]+", q))

        def tool_score(name: str) -> int:
            info = getattr(tools[name], "tool_info", {})
            tags = set(info.get("tags", []))
            return len(tags & query_words)

        if "list_dir" in tools and ("list" in query_words or "dir" in query_words):
            return ToolCall(tool="list_dir", args={"path": "."}, node_id=node_id)

        match = re.search(r"([a-z0-9_./-]+\.[a-z0-9_]+)", q)
        if match and "read_file" in tools:
            return ToolCall(tool="read_file", args={"path": match.group(1)}, node_id=node_id)

        safe_tools = [t for t in ("grep", "rg_context", "find_refs", "list_dir") if t in tools]
        if safe_tools:
            ranked = sorted(safe_tools, key=tool_score, reverse=True)
            best = ranked[0]
            if best in ("grep", "rg_context", "find_refs"):
                pattern = query if len(query) <= 200 else query[:200]
                args = {"pattern": pattern, "path": "."}
                if best == "rg_context":
                    args["context"] = 2
                return ToolCall(tool=best, args=args, node_id=node_id)
            if best == "list_dir":
                return ToolCall(tool="list_dir", args={"path": "."}, node_id=node_id)

        return None
