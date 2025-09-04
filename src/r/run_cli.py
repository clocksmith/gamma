#!/usr/bin/env python3
"""
A unified command-line interface for interacting with GGUF models.

This script loads a GGUF model and can be used in two modes:
1. Interactive Chat: If no prompt is provided, it enters a chat loop.
2. Single-Shot Inference: If a --prompt is provided, it runs a single
   inference and provides detailed performance metrics.
"""

import argparse
import os
import sys
import time
from typing import Any, Dict

from llama_cpp import Llama
import llm_utils


class ChatManager:
    """Manages the chat history and token counts for a conversation."""

    def __init__(self, llm: Llama, system_prompt: str):
        """Initializes the chat manager.

        Args:
            llm: The Llama instance used for tokenization and chat rendering.
            system_prompt: The initial system prompt to set the AI's behavior.
        """
        self._llm = llm
        self.history = [{"role": "system", "content": system_prompt}]

    def add_user_message(self, content: str) -> None:
        """Adds a user message to the history.

        Args:
            content: The text of the user's message.
        """
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Adds an assistant's message to the history.

        Args:
            content: The text of the assistant's response.
        """
        self.history.append({"role": "assistant", "content": content})

    def get_prompt_tokens(self) -> int:
        """Calculates the token count for the current prompt.

        Returns:
            The number of tokens in the conversation history.
        """
        if self._llm.chat_handler is None:
            prompt_str = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in self.history]
            )
        else:
            prompt_str = self._llm.chat_handler.render(self.history)

        tokens = self._llm.tokenize(prompt_str.encode("utf-8"), add_bos=True)
        return len(tokens)


# --- Single-Shot Inference Functions ---


def run_generation(llm: Llama, prompt: str, max_tokens: int) -> Dict[str, Any]:
    """Generates a response from the model and captures performance data.

    Args:
        llm: The loaded Llama model instance.
        prompt: The user prompt to send to the model.
        max_tokens: The maximum number of tokens to generate.

    Returns:
        The full response data dictionary from create_chat_completion.
    """
    messages = [{"role": "user", "content": prompt}]
    print(f"--- Generating Response for Prompt ---")
    print(f"\033[94mUser:\033[0m {prompt}")

    generation_start_time = time.time()
    response_data = llm.create_chat_completion(
        messages=messages, max_tokens=max_tokens, stream=False
    )
    generation_end_time = time.time()

    full_response = response_data["choices"][0]["message"]["content"]
    print(f"\033[92mAssistant:\033[0m {full_response}")
    print("\n--- End of Response ---")

    response_data["wall_time_seconds"] = generation_end_time - generation_start_time
    return response_data


def print_performance_stats(response_data: Dict[str, Any]) -> None:
    """Prints detailed performance statistics from a generation run.

    Args:
        response_data: The response dictionary containing usage stats.
    """
    print("\n--- Performance Statistics ---")
    usage = response_data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    wall_time = response_data.get("wall_time_seconds", 0)

    print(f"Prompt Tokens:     {prompt_tokens}")
    print(f"Completion Tokens: {completion_tokens}")
    print(f"Total Wall Time:   {wall_time:.2f} seconds")

    if completion_tokens > 0 and wall_time > 0:
        tps = completion_tokens / wall_time
        print(f"Tokens per Second (Total): {tps:.2f} TPS")
    else:
        print("Not enough data to calculate performance.")
    print("--------------------------\n")


# --- Interactive Chat Functions ---


def run_interactive_chat(llm: Llama, max_tokens: int) -> None:
    """Starts and manages the interactive chat loop.

    Args:
        llm: The loaded Llama model instance.
        max_tokens: The maximum number of tokens to generate per turn.
    """
    chat_manager = ChatManager(llm, "You are a helpful assistant.")
    print("\n--- Interactive Chat ---")
    print("Enter a prompt. Type 'exit' or 'quit' to end.")

    while True:
        try:
            prompt = input("\033[94m> User: \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if prompt.lower() in ["exit", "quit"]:
            break

        chat_manager.add_user_message(prompt)
        prompt_tokens = chat_manager.get_prompt_tokens()

        sys.stdout.write("\033[92m> Assistant: \033[0m")
        sys.stdout.flush()

        start_time = time.time()
        first_token_time = None
        assistant_response = ""
        stream = llm.create_chat_completion(
            messages=chat_manager.history, max_tokens=max_tokens, stream=True
        )

        for chunk in stream:
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content")
            if content is not None:
                if first_token_time is None:
                    first_token_time = time.time()
                sys.stdout.write(content)
                sys.stdout.flush()
                assistant_response += content

        end_time = time.time()
        chat_manager.add_assistant_message(assistant_response)

        ttft = (first_token_time - start_time) * 1000 if first_token_time else -1
        completion_tokens = len(llm.tokenize(assistant_response.encode("utf-8")))
        tps = (
            (completion_tokens - 1) / (end_time - first_token_time)
            if completion_tokens > 1 and first_token_time
            else 0
        )

        print("\n\n" + "=" * 20 + " METRICS " + "=" * 20)
        print(f"Context Tokens: {prompt_tokens}")
        print(f"Generated Tokens: {completion_tokens}")
        print(f"Time to First Token (TTFT): {ttft:.2f} ms")
        print(f"Tokens Per Second (generation): {tps:.2f} TPS")
        print("=" * 49 + "\n")

    print("\nSession ended.")


# --- Main Dispatcher ---


def main(args: argparse.Namespace) -> None:
    """The main execution function for the unified CLI.

    Dispatches to the correct mode (interactive or single-shot) based on
    the presence of the --prompt argument.

    Args:
        args: Command-line arguments parsed by argparse.
    """
    model_path = f"models/{args.model}"
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at '{model_path}'")
        return

    llm_utils.verify_and_report_gpu_support()

    llm = llm_utils.load_language_model(
        model_path=model_path,
        n_ctx=args.n_ctx,
        n_gpu_layers=args.n_gpu_layers,
        is_chat=True,
    )
    if not llm:
        return

    if args.prompt:
        # Single-shot inference mode
        response_data = run_generation(llm, args.prompt, args.max_tokens)
        print_performance_stats(response_data)
        print("Inference finished.")
    else:
        # Interactive chat mode
        run_interactive_chat(llm, args.max_tokens)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run inference or an interactive chat with a GGUF model."
    )
    llm_utils.add_common_cli_args(parser)
    parser.add_argument(
        "-p",
        "--prompt",
        type=str,
        default=None,
        help="The prompt to send to the model for single-shot inference. If omitted, starts interactive chat.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum number of tokens to generate.",
    )
    cli_args = parser.parse_args()
    main(cli_args)