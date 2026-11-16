"""
Streaming Conductor - Large model that orchestrates FunctionGemma ring.

The conductor:
1. Reasons about tasks (reads/writes code)
2. Dispatches queries to FnG ring with thresholds
3. Receives streaming results in real-time
4. Consolidates tools based on ring performance
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..ring.fng_ring import FunctionGemmaRing, NodeOutput, RingResult


@dataclass
class ConductorState:
    """Current state of conductor's reasoning."""
    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    gathered_info: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    memory_hits: str = ""


class StreamingConductor:
    """
    Large model conductor that streams with FnG ring.

    Flow:
    1. Conductor analyzes task, breaks into steps
    2. For each step, dispatch to ring with threshold
    3. Stream results back, react in real-time
    4. Write final patch/solution
    """

    PLAN_PROMPT = """Analyze this task and break it into information-gathering steps.

Task: {task}

Relevant memory (use if applicable, do not invent):
{memory}

For each step, specify:
1. What information is needed
2. Query to send to tool ring
3. Minimum confidence threshold (0.0-1.0)

Respond as JSON:
{{
    "steps": [
        {{"info_needed": "...", "query": "...", "threshold": 0.8}},
        ...
    ]
}}"""

    CONSOLIDATE_PROMPT = """Based on ring performance, should we consolidate tools?

Tools used this session:
{tool_usage}

Suggest consolidations (combine similar tools) or removals (unused tools).
Respond as JSON:
{{
    "consolidate": [{{"from": ["tool1", "tool2"], "into": "new_tool_name"}}],
    "remove": ["unused_tool"]
}}"""

    SOLUTION_PROMPT = """Given the gathered information, write the solution.

Task: {task}

Relevant memory (use if applicable, do not invent):
{memory}

Information gathered:
{gathered_info}

Write the code patch or solution."""

    def __init__(
        self,
        model,  # Large model (Claude, Llama 70B, etc.)
        ring: FunctionGemmaRing,
    ):
        self.model = model
        self.ring = ring
        self.state: Optional[ConductorState] = None
        self._tool_usage: Dict[str, int] = {}

    async def solve(self, task: str, memory_hits: Optional[List[Any]] = None) -> str:
        """
        Main entry point - solve a task.

        1. Plan steps
        2. Execute each step via ring
        3. Synthesize tools as needed
        4. Generate solution
        """
        formatted_memory = self._format_memory(memory_hits or [])
        self.state = ConductorState(task=task, memory_hits=formatted_memory)
        self._tool_usage.clear()

        # Step 1: Plan
        steps = await self._plan(task, formatted_memory)

        # Step 2: Execute each step
        for i, step in enumerate(steps):
            self.state.current_step = i
            result = await self._execute_step(step)
            self.state.gathered_info.append({
                "step": i,
                "query": step["query"],
                "result": result,
            })

        # Step 3: Consolidate tools based on usage
        await self._consolidate_tools()

        # Step 4: Generate solution
        solution = await self._generate_solution(formatted_memory)

        return solution

    async def _plan(self, task: str, memory: str) -> List[Dict[str, Any]]:
        """Break task into steps."""
        import json

        prompt = self.PLAN_PROMPT.format(task=task, memory=memory)
        response = await self.model.generate(prompt, max_tokens=1024)

        try:
            if "{" in response:
                json_str = response[response.index("{"):response.rindex("}")+1]
                parsed = json.loads(json_str)
                return parsed.get("steps", [])
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: single step
        return [{"info_needed": "all", "query": task, "threshold": 0.7}]

    async def _execute_step(self, step: Dict[str, Any]) -> Any:
        """Execute a step using the FnG ring with streaming."""
        query = step["query"]
        threshold = step.get("threshold", 0.8)

        best_result = None
        best_score = 0.0

        # Stream results from ring
        async for output in self.ring.search_streaming(query, threshold):
            # Track tool usage
            tool_name = output.tool_call.tool
            self._tool_usage[tool_name] = self._tool_usage.get(tool_name, 0) + 1

            # React to results in real-time
            if output.score > best_score:
                best_score = output.score
                best_result = output.result

        return best_result

    async def _consolidate_tools(self) -> None:
        """Consolidate tools based on usage patterns."""
        import json

        if not self._tool_usage:
            return

        # Format usage for prompt
        usage_str = "\n".join(
            f"- {tool}: used {count} times"
            for tool, count in sorted(self._tool_usage.items(), key=lambda x: -x[1])
        )

        prompt = self.CONSOLIDATE_PROMPT.format(tool_usage=usage_str)
        response = await self.model.generate(prompt, max_tokens=512)

        try:
            if "{" in response:
                json_str = response[response.index("{"):response.rindex("}")+1]
                parsed = json.loads(json_str)

                # Remove unused tools
                for tool_name in parsed.get("remove", []):
                    await self.ring.remove_tool_live(tool_name)

                # Note: actual consolidation would require more complex logic
                # to merge tool implementations
        except (json.JSONDecodeError, ValueError):
            pass

    async def _generate_solution(self, memory: str) -> str:
        """Generate final solution based on gathered info."""
        # Format gathered info
        info_str = "\n\n".join(
            f"Step {item['step']}: {item['query']}\nResult: {item['result']}"
            for item in self.state.gathered_info
        )

        prompt = self.SOLUTION_PROMPT.format(
            task=self.state.task,
            gathered_info=info_str,
            memory=memory,
        )

        response = await self.model.generate(prompt, max_tokens=4096)
        return response

    def _format_memory(self, memory_hits: List[Any]) -> str:
        """Format memory hits into a prompt-friendly string."""
        if not memory_hits:
            return "None"

        lines = []
        for score, entry in memory_hits:
            text = entry.text.replace("\n", " ")[:300]
            result_preview = ""
            if isinstance(entry.metadata, dict):
                result_preview = entry.metadata.get("result_preview", "")
            lines.append(
                f"- score={score:.2f} task={text} result={str(result_preview)[:300]}"
            )
        return "\n".join(lines)
