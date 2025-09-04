#!/usr/bin/env python3
"""
A web server to provide an API for interacting with a loaded LLM.

This server loads a GGUF model once on startup and serves a basic frontend.
"""

import argparse
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from llama_cpp import Llama
import llm_utils


class GenerationRequest(BaseModel):
    """Defines the structure for an API request to generate text."""
    prompt: str
    max_tokens: int = 512


class GenerationResponse(BaseModel):
    """Defines the structure for an API response after generating text."""
    text: str
    tokens_per_second: float


llm_store: Dict[str, Any] = {"model": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles server startup and shutdown events.

    This context manager loads the specified model into memory when the
    server starts and reports the GPU status.

    Args:
        app: The FastAPI application instance.
    """
    print("--- Server Starting ---")
    args = app.state.args
    model_path = f"models/{args.model}"
    if not os.path.exists(model_path):
        print(f"FATAL: Model file not found at '{model_path}'")
        raise FileNotFoundError(f"Model {model_path} not found")

    llm_utils.verify_and_report_gpu_support()

    llm = llm_utils.load_language_model(
        model_path=model_path,
        n_ctx=args.n_ctx,
        n_gpu_layers=args.n_gpu_layers,
        is_chat=True,
    )
    if not llm:
        raise RuntimeError("Failed to load language model. Check logs.")

    llm_store["model"] = llm
    print("--- Model Loaded and Server Ready ---")
    yield
    print("--- Server Shutting Down ---")
    llm_store["model"] = None


app = FastAPI(lifespan=lifespan)


@app.post("/api/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest) -> GenerationResponse:
    """API endpoint to generate text from the loaded model.

    Args:
        request: The request body containing the prompt and parameters.

    Returns:
        A response containing the generated text and performance stats.
    """
    llm = llm_store["model"]
    if not llm:
        raise RuntimeError("Model is not loaded.")

    messages = [{"role": "user", "content": request.prompt}]
    start_time = time.time()
    response_data = llm.create_chat_completion(
        messages=messages, max_tokens=request.max_tokens, stream=False
    )
    end_time = time.time()

    completion_tokens = response_data["usage"]["completion_tokens"]
    wall_time = end_time - start_time
    tps = (completion_tokens / wall_time) if wall_time > 0 else 0

    return GenerationResponse(
        text=response_data["choices"][0]["message"]["content"],
        tokens_per_second=round(tps, 2),
    )


app.mount("/static", StaticFiles(directory="web_ui"), name="static")


@app.get("/", include_in_schema=False)
async def read_index() -> FileResponse:
    """Serves the main index.html file for the root path."""
    return FileResponse("web_ui/index.html")


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="Run a web server for LLM inference.")
    llm_utils.add_common_cli_args(parser)
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the server to."
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the server on."
    )
    args = parser.parse_args()

    app.state.args = args
    uvicorn.run(app, host=args.host, port=args.port)