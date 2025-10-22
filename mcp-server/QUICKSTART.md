# GAMMA MCP Server - Quick Start Guide

Get GAMMA running as an MCP server in Claude Desktop in 5 minutes.

## Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/xyz/deco/gamma/mcp-server
./install.sh
```

Or manually:

```bash
# Activate GAMMA's virtual environment
cd /Users/xyz/deco/gamma
source venv/bin/activate

# Install MCP SDK
pip install "mcp[cli]>=1.2.0"

# Test the server
cd mcp-server
python3 server.py
```

If the server starts without errors, you're ready for Step 2!

Press Ctrl+C to stop the test server.

## Step 2: Configure Claude Desktop (1 minute)

### Find Your Config File

**macOS:**
```bash
open ~/Library/Application\ Support/Claude/
```

**Windows:**
```cmd
explorer %APPDATA%\Claude
```

Create or edit `claude_desktop_config.json`

### Add GAMMA Server

Copy this configuration (update the path!):

```json
{
  "mcpServers": {
    "gamma": {
      "command": "python3",
      "args": [
        "/Users/xyz/deco/gamma/mcp-server/server.py"
      ]
    }
  }
}
```

**⚠️ Important:** Replace `/Users/xyz/deco/gamma` with your actual path!

To find your path:
```bash
cd /Users/xyz/deco/gamma/mcp-server
pwd
```

Copy the output and use it in the config.

### For Multiple Servers

If you already have other MCP servers configured:

```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
    "gamma": {
      "command": "python3",
      "args": [
        "/Users/xyz/deco/gamma/mcp-server/server.py"
      ]
    }
  }
}
```

## Step 3: Restart Claude Desktop (30 seconds)

1. **Fully quit** Claude Desktop (Cmd+Q on macOS, not just close window)
2. **Wait** 5 seconds
3. **Relaunch** Claude Desktop

## Step 4: Verify Installation (30 seconds)

In Claude Desktop:

1. Look for the **🔨 hammer icon** (tools/search icon)
2. Click it
3. You should see GAMMA tools:
   - ✅ run_inference
   - ✅ compare_models
   - ✅ benchmark_model
   - ✅ select_optimal_model

If you see these, **installation successful!** 🎉

## Step 5: Test It! (1 minute)

Try these commands in Claude Desktop:

### Test 1: Model Discovery
```
Show me what LLM models are available on my system using GAMMA
```

### Test 2: Run Inference
```
Use GAMMA to generate a hello world program in Python
```

### Test 3: Get Recommendations
```
I need a code generation model with max 16GB VRAM, prioritizing speed.
What GAMMA model should I use?
```

## Troubleshooting

### "GAMMA tools not showing up"

**Check the config file:**
```bash
# macOS
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Windows
type %APPDATA%\Claude\claude_desktop_config.json
```

Verify:
- ✅ Valid JSON (use https://jsonlint.com/)
- ✅ Correct file path
- ✅ No typos in "mcpServers"

**Check the logs:**
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Windows
notepad %APPDATA%\Claude\logs\mcp.log
```

### "No models available"

Install Ollama and pull a model:

```bash
# Install Ollama from ollama.com
# Then pull a small model:
ollama pull gemma2:2b
```

Verify in GAMMA:
```bash
cd /Users/xyz/deco/gamma
python gamma.py game
```

### "Import errors when running server"

Make sure you're using GAMMA's virtual environment:

```bash
cd /Users/xyz/deco/gamma
source venv/bin/activate
python mcp-server/server.py
```

### "Server starts then immediately stops"

Check for Python errors:

```bash
cd /Users/xyz/deco/gamma/mcp-server
python3 server.py 2>&1 | tee error.log
```

Look for stack traces in `error.log`

## Next Steps

- Read the [full README](README.md) for advanced features
- Explore GAMMA prompts (model selection wizard, comparison setup)
- Try benchmarking your models
- Compare different models side-by-side

## Getting Help

1. **Check logs** - Most issues show up in Claude Desktop logs
2. **Test manually** - Run `python3 server.py` to see errors directly
3. **Verify GAMMA** - Make sure `python gamma.py game` works
4. **Check paths** - Ensure all paths in config are absolute

## Success Checklist

- ✅ `./install.sh` completed without errors
- ✅ `python3 server.py` starts successfully
- ✅ `claude_desktop_config.json` has correct path
- ✅ Claude Desktop fully restarted
- ✅ Tools icon appears in Claude Desktop
- ✅ GAMMA tools listed (4 tools total)
- ✅ Test command works ("Show me available models")

**All checked?** You're ready to use GAMMA through Claude! 🚀
