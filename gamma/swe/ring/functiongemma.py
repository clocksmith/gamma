"""
FunctionGemma native format support.

FunctionGemma uses special tokens for function calling:
- <start_function_declaration> / <end_function_declaration> for tool definitions
- <start_function_call> / <end_function_call> for tool invocations
- <escape> for escaping string values in arguments

This module provides proper formatting for FunctionGemma inference,
following Google's official guide:
https://ai.google.dev/gemma/docs/functiongemma/fine-tuning
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FunctionGemmaConfig:
    """Configuration for FunctionGemma formatting."""
    system_msg: str = "You are a code assistant that uses tools to help developers."
    max_new_tokens: int = 128


class FunctionGemmaFormatter:
    """
    Formats prompts and parses outputs in FunctionGemma's native format.

    FunctionGemma expects:
    1. Tool declarations in system turn with special markers
    2. User query in user turn
    3. Model responds with <start_function_call>call:name{args}<end_function_call>
    """

    # Special tokens used by FunctionGemma
    START_TURN = "<start_of_turn>"
    END_TURN = "<end_of_turn>"
    START_FUNC_DECL = "<start_function_declaration>"
    END_FUNC_DECL = "<end_function_declaration>"
    START_FUNC_CALL = "<start_function_call>"
    END_FUNC_CALL = "<end_function_call>"
    START_FUNC_RESP = "<start_function_response>"
    END_FUNC_RESP = "<end_function_response>"
    ESCAPE = "<escape>"

    def __init__(self, config: Optional[FunctionGemmaConfig] = None):
        self.config = config or FunctionGemmaConfig()

    def format_tool_declaration(self, name: str, description: str, parameters: Dict[str, Any]) -> str:
        """
        Format a single tool declaration.

        Output format:
        <start_function_declaration>declaration:tool_name{description:<escape>...<escape>,parameters:{...}}<end_function_declaration>
        """
        # Format parameters
        props = parameters.get("properties", {})
        required = parameters.get("required", [])

        param_parts = []
        for param_name, param_info in props.items():
            param_type = param_info.get("type", "string").upper()
            param_desc = param_info.get("description", param_name)
            param_parts.append(
                f"{param_name}:{{description:{self.ESCAPE}{param_desc}{self.ESCAPE},type:{self.ESCAPE}{param_type}{self.ESCAPE}}}"
            )

        params_str = "{" + ",".join(param_parts) + "}"
        required_str = "[" + ",".join(f"{self.ESCAPE}{r}{self.ESCAPE}" for r in required) + "]"

        declaration = (
            f"{self.START_FUNC_DECL}declaration:{name}{{"
            f"description:{self.ESCAPE}{description}{self.ESCAPE},"
            f"parameters:{{properties:{params_str},required:{required_str},type:{self.ESCAPE}OBJECT{self.ESCAPE}}}"
            f"}}{self.END_FUNC_DECL}"
        )

        return declaration

    def format_prompt(
        self,
        query: str,
        tools: List[Dict[str, Any]],
        prior_result: Optional[Tuple[str, Any]] = None,
    ) -> str:
        """
        Format a complete prompt for FunctionGemma.

        Args:
            query: User's query
            tools: List of tool schemas in FunctionGemma format
            prior_result: Optional (tool_name, result) from previous call

        Returns:
            Formatted prompt string ready for tokenizer
        """
        parts = []

        # Developer/system turn with tool declarations
        parts.append(f"{self.START_TURN}developer")
        parts.append(self.config.system_msg)

        for tool in tools:
            func = tool.get("function", tool)
            decl = self.format_tool_declaration(
                name=func["name"],
                description=func["description"],
                parameters=func.get("parameters", {}),
            )
            parts.append(decl)

        parts.append(self.END_TURN)

        # If there's a prior result, include it
        if prior_result:
            tool_name, result = prior_result
            parts.append(f"{self.START_TURN}model")
            parts.append(f"{self.START_FUNC_CALL}call:{tool_name}{{...}}{self.END_FUNC_CALL}")
            parts.append(f"{self.START_FUNC_RESP}")
            result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
            parts.append(f"{self.ESCAPE}{result_str[:500]}{self.ESCAPE}")
            parts.append(f"{self.END_FUNC_RESP}")
            parts.append(self.END_TURN)

        # User turn
        parts.append(f"{self.START_TURN}user")
        parts.append(query)
        parts.append(self.END_TURN)

        # Model turn (generation prompt)
        parts.append(f"{self.START_TURN}model")

        return "\n".join(parts)

    def parse_tool_call(self, output: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Parse FunctionGemma's output to extract tool call.

        Input format:
        <start_function_call>call:tool_name{arg1:<escape>value1<escape>,arg2:<escape>value2<escape>}<end_function_call>

        Returns:
            (tool_name, args_dict) or None if parsing fails
        """
        # Find function call block
        match = re.search(
            rf'{re.escape(self.START_FUNC_CALL)}call:(\w+)\{{(.+?)\}}{re.escape(self.END_FUNC_CALL)}',
            output,
            re.DOTALL
        )

        if not match:
            # Try simpler pattern
            match = re.search(r'call:(\w+)\{(.+?)\}', output, re.DOTALL)
            if not match:
                return None

        tool_name = match.group(1)
        args_str = match.group(2)

        # Parse arguments
        args = {}
        # Pattern: key:<escape>value<escape>
        arg_pattern = rf'(\w+):{re.escape(self.ESCAPE)}(.+?){re.escape(self.ESCAPE)}'
        for arg_match in re.finditer(arg_pattern, args_str):
            key = arg_match.group(1)
            value = arg_match.group(2)

            # Try to parse as JSON for complex types
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass  # Keep as string

            args[key] = value

        return tool_name, args

    def format_tool_call(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Format a tool call in FunctionGemma format.

        Used for training data generation.
        """
        args_parts = []
        for key, value in args.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            args_parts.append(f"{key}:{self.ESCAPE}{value_str}{self.ESCAPE}")

        args_str = ",".join(args_parts)
        return f"{self.START_FUNC_CALL}call:{tool_name}{{{args_str}}}{self.END_FUNC_CALL}"


class FunctionGemmaNode:
    """
    FunctionGemma node using native format.

    Replaces the generic prompt-based approach with proper
    FunctionGemma chat template formatting.
    """

    def __init__(
        self,
        node_id: int,
        model,
        tokenizer=None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Args:
            node_id: Node identifier in ring
            model: Model with generate() method
            tokenizer: HuggingFace tokenizer (optional, for native format)
            tools: Tool schemas in FunctionGemma format
        """
        self.node_id = node_id
        self.model = model
        self.tokenizer = tokenizer
        self.tools = tools or []
        self.formatter = FunctionGemmaFormatter()

    def set_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Update available tools."""
        self.tools = tools

    async def execute(
        self,
        query: str,
        prior_result: Optional[Tuple[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Execute FunctionGemma to select a tool.

        Args:
            query: User's query
            prior_result: Optional (tool_name, result) from prior call

        Returns:
            (tool_name, args) tuple
        """
        if self.tokenizer is not None:
            return await self._execute_native(query, prior_result)
        else:
            return await self._execute_formatted(query, prior_result)

    async def _execute_native(
        self,
        query: str,
        prior_result: Optional[Tuple[str, Any]],
    ) -> Tuple[str, Dict[str, Any]]:
        """Execute using HuggingFace tokenizer's apply_chat_template."""
        # Build messages
        messages = [
            {"role": "user", "content": query},
        ]

        # If we have prior result, add it
        if prior_result:
            tool_name, result = prior_result
            messages.insert(0, {
                "role": "assistant",
                "tool_calls": [{
                    "type": "function",
                    "function": {"name": tool_name, "arguments": {"result": str(result)[:200]}}
                }]
            })

        # Apply chat template
        inputs = self.tokenizer.apply_chat_template(
            messages,
            tools=self.tools,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )

        # Generate
        outputs = await self.model.generate_tokens(
            inputs,
            max_new_tokens=128,
        )

        output_text = self.tokenizer.decode(
            outputs[0][len(inputs["input_ids"][0]):],
            skip_special_tokens=False,
        )

        # Parse result
        result = self.formatter.parse_tool_call(output_text)
        if result:
            return result
        return ("noop", {})

    async def _execute_formatted(
        self,
        query: str,
        prior_result: Optional[Tuple[str, Any]],
    ) -> Tuple[str, Dict[str, Any]]:
        """Execute using manual formatting (for Ollama/API models)."""
        prompt = self.formatter.format_prompt(
            query=query,
            tools=self.tools,
            prior_result=prior_result,
        )

        response = await self.model.generate(prompt, max_tokens=128)

        # Parse result
        result = self.formatter.parse_tool_call(response)
        if result:
            return result

        # Fallback: try to parse JSON
        try:
            if "{" in response:
                json_str = response[response.index("{"):response.rindex("}")+1]
                parsed = json.loads(json_str)
                return (parsed.get("tool", "noop"), parsed.get("args", {}))
        except (json.JSONDecodeError, ValueError):
            pass

        return ("noop", {})


def _get_tool_schema(executor) -> Dict[str, Any]:
    """Build a tool schema from a Python function signature."""
    import inspect
    from typing import get_args, get_origin, get_type_hints

    sig = inspect.signature(executor)
    doc = inspect.getdoc(executor) or executor.__name__
    hints = get_type_hints(executor)

    properties = {}
    required = []

    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    def to_json_type(annotation) -> str:
        if annotation in type_map:
            return type_map[annotation]
        origin = get_origin(annotation)
        if origin in type_map:
            return type_map[origin]
        if origin is list:
            return "array"
        if origin is dict:
            return "object"
        return "string"

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        annotation = hints.get(name, str)
        properties[name] = {"type": to_json_type(annotation), "description": name}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": executor.__name__,
            "description": doc.split("\n")[0],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def convert_tools_to_functiongemma(tools: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert our simple tool dict to FunctionGemma format.

    Input: {"grep": <callable>, "read_file": <callable>}
    Output: [{"type": "function", "function": {"name": "grep", ...}}, ...]
    """
    result = []
    for name, executor in tools.items():
        try:
            schema = _get_tool_schema(executor)
            schema["function"]["name"] = name
            result.append(schema)
        except Exception:
            # Fallback for functions without proper annotations
            result.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": f"Execute {name} tool",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                }
            })

    return result
