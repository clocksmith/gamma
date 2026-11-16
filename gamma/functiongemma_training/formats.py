"""
FunctionGemma training format utilities.

Standalone utilities for converting tool calls and traces into
FunctionGemma's expected chat template format.
"""

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, get_type_hints, get_origin


@dataclass
class ToolSchema:
    """Schema for a tool function."""
    name: str
    description: str
    parameters: Dict[str, Any]
    return_type: str = "string"

    def to_functiongemma_format(self) -> Dict[str, Any]:
        """Convert to FunctionGemma tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
                "return": {"type": self.return_type},
            },
        }


def _annotation_to_json_type(annotation: Any) -> str:
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    if annotation in type_map:
        return type_map[annotation]
    origin = get_origin(annotation)
    if origin in type_map:
        return type_map[origin]
    return "string"


def get_tool_schema(func: Callable) -> ToolSchema:
    """
    Extract schema from a Python function (type hints + docstring).

    Args:
        func: Function with type hints and docstring

    Returns:
        ToolSchema for the function
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}
    doc = inspect.getdoc(func) or ""
    description = doc.split("\n\n")[0] if doc else func.__name__

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        param_type = hints.get(param_name, str)
        json_type = _annotation_to_json_type(param_type)

        param_desc = param_name
        if "Args:" in doc:
            args_section = doc.split("Args:")[1].split("Returns:")[0]
            for line in args_section.split("\n"):
                if param_name in line:
                    param_desc = line.split(":", 1)[-1].strip() if ":" in line else param_name
                    break

        properties[param_name] = {
            "type": json_type,
            "description": param_desc,
        }

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return ToolSchema(
        name=func.__name__,
        description=description,
        parameters={
            "type": "object",
            "properties": properties,
            "required": required,
        },
    )


def experience_to_functiongemma_messages(
    query: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    tools: List[ToolSchema],
    system_msg: str = "You are a model that can do function calling with the following functions",
) -> Dict[str, Any]:
    """
    Convert a trace item to FunctionGemma conversation format.
    """
    return {
        "messages": [
            {"role": "developer", "content": system_msg},
            {"role": "user", "content": query},
            {
                "role": "assistant",
                "tool_calls": [{
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": tool_args,
                    }
                }],
            },
        ],
        "tools": [t.to_functiongemma_format() for t in tools],
    }


def experiences_to_dataset(
    experiences: List[Dict[str, Any]],
    tools: List[ToolSchema],
    system_msg: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convert list of experiences to FunctionGemma dataset format.
    """
    dataset = []
    for exp in experiences:
        try:
            item = experience_to_functiongemma_messages(
                query=exp["query"],
                tool_name=exp["tool"],
                tool_args=exp.get("args", {}),
                tools=tools,
                system_msg=system_msg or "You are a model that can do function calling",
            )
            dataset.append(item)
        except Exception:
            continue
    return dataset


def infer_expert_group(tool_name: str) -> str:
    """
    Infer expert group from tool name.
    """
    name = tool_name.lower()
    if name in {"grep", "rg_context", "find_refs", "find"}:
        return "search"
    if name in {"read_file", "list_dir", "git_blame", "read_tests"}:
        return "read"
    if name in {"write_file", "git_apply"}:
        return "write"
    if name in {"run_tests"}:
        return "test"
    return "search"


def experiences_to_expert_datasets(
    experiences: List[Dict[str, Any]],
    expert_groups: Dict[str, List[int]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Split experiences by expert group for per-expert LoRA training.
    """
    datasets = {group: [] for group in expert_groups}
    for exp in experiences:
        group = exp.get("expert_group") or infer_expert_group(exp.get("tool", ""))
        if group in datasets:
            datasets[group].append(exp)
    return datasets


class FunctionGemmaFormatter:
    """
    Formats traces into FunctionGemma training examples.
    """

    def __init__(self, system_msg: Optional[str] = None):
        self.system_msg = system_msg or (
            "You are a code assistant that can search files, read code, and make edits. "
            "Use the available tools to accomplish the task."
        )
        self.tools: List[ToolSchema] = []
        self._tool_map: Dict[str, ToolSchema] = {}

    def register_tool(self, func: Callable, name: Optional[str] = None) -> None:
        """Register a tool function."""
        schema = get_tool_schema(func)
        if name:
            schema.name = name
        self.tools.append(schema)
        self._tool_map[schema.name] = schema

    def register_tool_schema(self, schema: ToolSchema) -> None:
        """Register a pre-built schema."""
        self.tools.append(schema)
        self._tool_map[schema.name] = schema

    def format_experiences(
        self,
        experiences: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Convert experiences to FunctionGemma dataset format."""
        return experiences_to_dataset(
            experiences,
            self.tools,
            system_msg=self.system_msg,
        )

    def to_raw_format(
        self,
        query: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_result: Optional[Any] = None,
    ) -> str:
        """
        Convert a single interaction to raw FunctionGemma special-token format.
        """
        from swe.ring.functiongemma import FunctionGemmaFormatter as RawFormatter

        tools = [t.to_functiongemma_format() for t in self.tools]
        raw = RawFormatter()

        prior_result = None
        if tool_result is not None:
            prior_result = (tool_name, tool_result)

        return raw.format_prompt(
            query=query,
            tools=tools,
            prior_result=prior_result,
        )
