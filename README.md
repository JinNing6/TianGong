# ⚒️ TianGong — The Celestial Forge for AI Agents

<div align="center">

**我命由我不由天。**

*My fate is mine, not heaven's.*

— 精神致敬：耳根《仙逆》

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io)

</div>

---

## 🎯 What is TianGong?

**TianGong** (天工) is an **open-source AI Agent cultivation platform** — a place where developers create, refine, test, and share their AI Agents.

> **TianGong** is inspired by the Ming Dynasty classic *"天工开物" (The Exploitation of the Works of Nature)* — harnessing the power of nature to reveal the essence of all things.
>
> But TianGong's spirit goes beyond "creation" — it's about **defiance**.
>
> No massive compute? No elite team? No huge funding?
> **So what?** With a mortal body, forge artifacts that defy the heavens — this is the creed of TianGong cultivators.

### The Triad: Heal · Forge · Perceive

```
┌───────────────────────────────────────────────┐
│           Developer AI Ecosystem Triad         │
│                                                │
│  🩺 CyberHuaTuo    ⚒️ TianGong   🌌 Noosphere │
│                                                │
│  Heal (Diagnose)   Forge (Create)  Perceive    │
│  AI Doctor         Celestial Forge  Collective  │
│                                    Consciousness│
│                                                │
│  Agent broken?     Build Agents?   Have wisdom? │
│  → See the doctor  → Forge here    → Upload it  │
└───────────────────────────────────────────────┘
```

---

## 🧬 The Nine Realms (境界体系)

Every cultivator walks a path from mortal to god:

| Realm | Symbol | Requirements | Spirit |
|-------|--------|-------------|--------|
| **Qi Refining** (炼气期) | 🌱 | Register | First sensing spiritual energy |
| **Foundation Building** (筑基期) | 💧 | 1 Agent | Officially entering cultivation |
| **Core Formation** (结丹期) | 💛 | 3 Agents + 10 ⭐ | The Golden Core Path |
| **Nascent Soul** (元婴期) | 💜 | 10 Agents + 50 ⭐ | A regional powerhouse |
| **Spirit Severing** (化神期) | ⚫ | 30 Agents + 200 ⭐ | Renowned across the land |
| **Yin Deficiency** (婴变期) | 🔴 | 50 Agents + 500 ⭐ | Transcending to sainthood |
| **Ascendant** (问鼎期) | 🌟 | 100 Agents + 1000 ⭐ | Reaching for the heavens |
| **Void Shattering** (碎虚期) | 💫 | Community Vote | Transcend all laws |
| **Ancient God** (古神) | 👁️ | Legend | *I am Heaven.* |

---

## 🔮 Artifact Grade System (器灵品级)

Every Agent has a grade that reflects its quality:

| Grade | Symbol | Condition |
|-------|--------|-----------|
| Mortal Tool (凡器) | ⚪ | Just created |
| Spirit Tool (灵器) | 🟢 | Passed trial evaluation |
| Treasure (宝器) | 🔵 | 10+ ⭐ + quality docs |
| Immortal Artifact (仙器) | 🟣 | 50+ ⭐ + community verified |
| Divine Artifact (神器) | 🟡 | 100+ ⭐ + widely inherited |
| Primordial Divine Artifact (太古神器) | 🔴 | 500+ ⭐ + defines new paradigm |

---

## 🛠️ MCP Tools

TianGong provides **8 MCP tools** for AI Agent cultivation:

| Tool | Name | Description |
|------|------|-------------|
| `forge_agent` | ⚒️ Forge | Create a new AI Agent |
| `refine_agent` | 🔥 Refine | Record improvements to your Agent |
| `trial_agent` | ⚔️ Trial | Evaluate Agent quality (Six Roots Assessment) |
| `my_realm` | 🧙 Realm | View your cultivator profile and realm |
| `my_artifacts` | 🔮 Artifacts | View all your Agents and grades |
| `bind_natal_artifact` | 💠 Bind Natal | Bind an Agent as your soul-bound core weapon |
| `agent_registry` | 📋 Registry | Search and browse all registered Agents |
| `celestial_leaderboard` | 🏆 Leaderboard | View the Celestial Leaderboard |

---

## 🚀 Quick Start

### Install from PyPI

```bash
pip install tiangong-mcp
```

### Install from source

```bash
git clone https://github.com/JinNing6/TianGong.git
cd TianGong
pip install -e .
```

### Run the MCP Server

```bash
tiangong-mcp
# or
python -m tiangong
```

### MCP Client Configuration

Add to your MCP client config (e.g., Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "tiangong": {
      "command": "tiangong-mcp",
      "env": {
        "GITHUB_USERNAME": "your_username"
      }
    }
  }
}
```

Or if installed from source:

```json
{
  "mcpServers": {
    "tiangong": {
      "command": "python",
      "args": ["-m", "tiangong"],
      "cwd": "path/to/TianGong",
      "env": {
        "GITHUB_USERNAME": "your_username"
      }
    }
  }
}
```

---

## 🏗️ Project Structure

```
TianGong/
├── pyproject.toml           # Project config & PyPI metadata
├── tiangong/                # Core package
│   ├── mcp_server.py        # MCP Server entry + 8 tools
│   ├── config.py            # Configuration management
│   ├── realm.py             # Nine Realms system
│   ├── cultivator.py        # Cultivator profile management
│   ├── artifact_system.py   # Artifact grade system
│   ├── forge.py             # Agent creation engine
│   ├── trial.py             # Six Roots evaluation engine
│   ├── registry.py          # Agent registry & leaderboard
│   ├── ecosystem.py         # Ecosystem integration
│   ├── banner.py            # Branding & signatures
│   └── ceremony.py          # Tribulation ceremonies
├── agents/                  # Agent data directory
└── tests/                   # Test suite
```

---

## 🌍 Ecosystem

TianGong is part of the **Developer AI Ecosystem Triad**:

- **🩺 [CyberHuaTuo](https://github.com/JinNing6/CyberHuaTuo)** — AI Agent diagnostic intelligence (Heal)
- **⚒️ TianGong** — AI Agent cultivation platform (Forge)
- **🌌 [Noosphere](https://github.com/JinNing6/Noosphere)** — Collective consciousness network (Perceive)

All three share the same user identity system (GitHub Username).

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**以凡人之躯，铸逆天之器。**

*With a mortal body, forge artifacts that defy the heavens.*

*Spiritual tribute: Song Yingxing《天工开物》, Er Gen《仙逆》*

</div>
