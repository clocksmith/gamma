#!/usr/bin/env python3
"""
Web server for the R-Eval / Routing Mode.
Provides a simple web interface to interact with the routing logic.
"""

import argparse
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to the path to allow importing from src
try:
    from tools._path_setup import ensure_project_root_on_path
except ImportError:
    from _path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from src.core.menu.routing_logic import get_responses, route_responses

app = FastAPI()

class RouteRequest(BaseModel):
    prompt: str
    models: list[str]
    router: str

@app.post("/api/route")
def handle_route_request(request: RouteRequest):
    """API endpoint to handle a routing request."""
    print(f"Received API request: {request}")
    
    candidate_models = []
    for model_spec in request.models:
        if ":" in model_spec:
            engine, model = model_spec.split(":", 1)
        else:
            engine = "pytorch"
            model = model_spec
        candidate_models.append({"engine": engine, "model": model})

    # For now, common_args is empty. This could be expanded.
    common_args = {}
    
    responses = get_responses(request.prompt, candidate_models, common_args)
    best_response = route_responses(request.prompt, responses, request.router)
    
    return {"best_response": best_response, "all_responses": responses}

# Mount the static UI files
# The path is relative to this script file
ui_path = os.path.join(os.path.dirname(__file__), "web_router_ui")
app.mount("/", StaticFiles(directory=ui_path, html=True), name="static")

def main():
    parser = argparse.ArgumentParser(description="R-Eval Web Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on.")
    args = parser.parse_args()

    print(f"Starting R-Eval Web Server at http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
