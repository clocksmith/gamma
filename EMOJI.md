# Emoji Policy: STRICT NO EMOJIS (with a narrow game-only exception)

This codebase follows a **strict no-emoji policy**. Use Unicode symbols for visual indicators.

**Exception (game CLI only):** The interactive CLI game may use a very limited set of celebratory/status emojis in runtime UI messages. Approved for game flow only (use sparingly):
- 🎉 Party popper (celebration)
- ✅ Success/loaded
- ❌ Failure/error
- ⚠️ Warning
- 🎮 Game welcome/title
- 🧠 Mind Meld/processing
- ⭐ Achievement highlight
- 🔥 Streaks/heat

Notes:
- Prefer the symbols above for runtime game UI. The hourglass ⏳ is discouraged; use 🧠/🎮 + text instead for loading states.
- Do not use emojis elsewhere (docs, logs, errors, tests, benchmarks, or non-game tooling).

## Approved Unicode Symbols

### Status & System
| Symbol | Usage |
|--------|-------|
| ● | Ready, success, completed |
| ☒ | Error, failure |
| ▲ | Warning |
| ☛ | Info, pointer |
| ○ | In progress, active |
| ☖ | Build |
| ☁ | Cloud/network |
| ☨ | Debug |

### File System & Data
| Symbol | Usage |
|--------|-------|
| ☗ | Folder |
| ☐ | Document |
| ⎈ | Settings |
| ☰ | Code file |
| ☷ | Data/JSON |
| ☊ | HTML |
| ☲ | CSS |
| ☻ | Media |
| ⛝ | Package |
| ☙ | Text/log |

### Actions & Controls
| Symbol | Usage |
|--------|-------|
| ⚲ | Search |
| ✎ | Edit |
| ✄ | Delete |
| ☩ | Add/create |
| ☇ | Execute |
| ♺ | Refresh |
| ⚿ | Lock/auth |
| ☈ | Clear |
| ✓ | Confirm |

## Checkboxes

```markdown
- [x] Completed
- [ ] Pending
```

## Why No Emojis?

1. **Terminal compatibility** - Unicode symbols render consistently
2. **Professional appearance** - Cleaner, more technical aesthetic
3. **Accessibility** - Better screen reader support
4. **Consistency** - Same symbols across all platforms
