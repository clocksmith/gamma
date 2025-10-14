# GAMMA Tools

Command-line utilities for GAMMA.

---

## Available Tools

### view_sessions.py

View and analyze saved game sessions.

```bash
# List all sessions
python3 tools/view_sessions.py

# View specific session
python3 tools/view_sessions.py <session_id>

# Overall statistics
python3 tools/view_sessions.py --stats
```

### Other Tools

- **download_model.py** - Download HuggingFace models
- **run_mind_meld_cli.py** - Standalone Mind Meld CLI
- **run_api_server.py** - API server for GAMMA
- **run_router_cli.py** - Model router CLI
- **run_router_web_ui.py** - Web UI for router

---

## Usage

All tools accept `--help` flag:
```bash
python3 tools/<tool_name>.py --help
```

---

## See Also

- [Main README](../README.md)
- [Sessions](../sessions/README.md)
