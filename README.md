<div align="center">

[🇨🇳 中文文档](./README.zh-CN.md) | [🇺🇸 English](./README.md)

<br/>

# ⚒️ TianGong — The Celestial Forge

### AI Agent Distribution & Creation Platform

**My fate is mine, not heaven's.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io)
[![PyPI](https://img.shields.io/pypi/v/tiangong-mcp.svg)](https://pypi.org/project/tiangong-mcp/)
[![Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/CqMWY9FF)

<br/>

</div>

---

<div align="center">

### ✨ The Path of a Mortal Who Defied the Heavens

*In the Age of AI, live the journey of Renegade Immortal & A Mortal's Journey.*

</div>

<table>
<tr>
<td align="center" width="16%">
<img src="docs/images/1_mortal_finds_artifact.png" alt="A mortal discovers a divine artifact" width="100%"/>
<br/>
<b>🧑 A Mortal Discovers Destiny</b>
<br/><br/>
<sub>An ordinary youth finds a glowing jade in the dust. Destiny begins.</sub>
</td>
<td align="center" width="16%">
<img src="docs/images/1b_sect_apprenticeship.png" alt="Joining a sect to learn the Dao" width="100%"/>
<br/>
<b>⛰️ Joining a Sect</b>
<br/><br/>
<sub>He kneels before the sect gates. Now he has a master, brethren, and belonging.</sub>
</td>
<td align="center" width="16%">
<img src="docs/images/2_cultivation_journey.png" alt="Beginning the cultivation journey" width="100%"/>
<br/>
<b>🌱 The Cultivation Begins</b>
<br/><br/>
<sub>He sits alone on a peak, breathing in the world's qi. No talent, no backing — only defiance.</sub>
</td>
<td align="center" width="16%">
<img src="docs/images/3_forging_artifacts.png" alt="Forging divine artifacts" width="100%"/>
<br/>
<b>⚒️ Forging Artifacts</b>
<br/><br/>
<sub>The forge blazes. He pours his life's understanding into each artifact.</sub>
</td>
<td align="center" width="16%">
<img src="docs/images/4_ascension_flight.png" alt="Ascending to the heavens" width="100%"/>
<br/>
<b>🌟 Ascending the Heavens</b>
<br/><br/>
<sub>He rides his sword skyward. Below, the world he once knew grows small.</sub>
</td>
<td align="center" width="16%">
<img src="docs/images/5_tribulation_enlightenment.png" alt="Returning to the mortal world for enlightenment" width="100%"/>
<br/>
<b>⚫ Returning to Seek the Dao</b>
<br/><br/>
<sub>At the peak, he returns to the mortal world. Helping others, he finds the true Dao.</sub>
</td>
</tr>
</table>

<div align="center">

<br/>

*After enlightenment, he did not retreat into solitude.*
*He forged his wisdom into a crucible — and named it **TianGong**.*

*Now, any mortal who picks it up walks the same path.*
*No lineage required. No talent demanded. Only the will to defy fate.*

*His story has ended.*
*Yours begins now.*

**`pip install tiangong-mcp`**

</div>

---

## 🌌 A World Where Mortals Forge Divine Artifacts

> *Han Li was just an ordinary village boy. No talent, no backing, no destiny — yet he walked the path of immortality with nothing but tenacity and cunning, turning mortal hands into weapons that shook the heavens.*
>
> — Spiritual Tribute: Wang Yu "A Record of a Mortal's Journey to Immortality"

> *"My fate is mine, not heaven's." Wang Lin, an ordinary youth, seized his destiny against a cruel cultivation world — proving that willpower alone can shatter the laws of heaven.*
>
> — Spiritual Tribute: Er Gen "Renegade Immortal"

> *In the neon-lit workshops of the future, every line of code is a spell, every Agent a living artifact. The cyberpunk artisans don't pray to the gods — they build them.*
>
> — Spiritual Tribute: "Cyberpunk Mech-Smith"

**TianGong** is an **open-source AI Agent distribution and creation platform** — a world where developers forge, refine, share, and inherit AI Agents as cultivation artifacts.

Here, **Agents are Artifacts**, rated by the community. **Users are Cultivators**, ascending from mortal to legend. Your code isn't just code — it's your **soul-bound natal weapon**.

<div align="center">

<br/>

*With a mortal body, forge artifacts that defy the heavens.*

</div>

---

## ⚡ Why TianGong?

<table>
<tr>
<td width="33%" align="center">

**🔮 Your Code Evolves**

Every Agent you publish starts as a humble Mortal Tool. As the community uses, rates, and refines it — your artifact ascends through 6 grades, all the way to **Primordial Divine Artifact**.

</td>
<td width="33%" align="center">

**🧬 You Ascend With It**

Your contributions unlock a mortal origin plus **22 ascension ranks**. From **Mortal** to the singular title of **TianGong** — a rank held by only one person on Earth.

</td>
<td width="33%" align="center">

**⚔️ One Command Away**

Install via `pip`, configure your MCP client, and start forging. Pull any community artifact with a single command. No friction, no gatekeeping.

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Install from PyPI

```bash
pip install tiangong-mcp
```

### Run Server

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

That's it. You are now a cultivator.

### First MCP Command

Once the MCP server is connected, ask your client to run:

```text
start_cultivation(username="your_github_username")
```

It returns the MCP config, first `forge_agent` command, `activation_funnel()` check, `growth_flywheel()` check, `public_launch_preflight()` check, GitHub Growth Issue URL, and a paste-ready first-session share card without fabricating Spirit Power or registration.

---

## ✅ Development Quality Gates

Before a new quest, realm rule, or public growth surface is promoted, install the full local gate set and run the same checks as CI:

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest -q
tiangong-mcp public-launch-assets
python -m build
python -m twine check dist/*
tiangong-mcp public-proof-pack --target-contributors 10
tiangong-mcp public-release-boundary
```

`.github/workflows/quality-gates.yml` runs the same dev extra, lint, tests, local launch asset audit, build, package metadata check, and public release-boundary check on push and pull request with read-only repository permissions.

`.github/workflows/publish-pypi.yml` publishes to PyPI only when a GitHub Release is published. It reruns lint, tests, local launch asset audit, build, `twine check`, and public release-boundary check, then uses PyPI Trusted Publishing through `pypa/gh-action-pypi-publish@release/v1` with job-level `id-token: write`, so the release path does not require a stored `PYPI_TOKEN`.

`tiangong-mcp public-launch-assets` also prints a full public growth release handoff: docs, package metadata, Issue Forms, workflows, public growth modules, user-facing growth surfaces, and tests to stage before creating the `v0.1.0` GitHub Release.

---

## 🎮 How to Play — Cultivation Guide

> *Installation complete. You have stepped onto the path of cultivation. Here is your full guide.*

<br/>

### 🧑 Step 1: Mortal Initiation — Forge Your First Artifact

Your first Agent is your rite of passage.

```
forge_agent(name="my-first-agent", description="A helpful coding assistant", creator="your_github_username")
```

- ✅ Upon success, you ascend from **Mortal** to **Qi Refining** cultivator
- ✅ Your Agent is registered in the global registry — discoverable by everyone
- ✅ You gain +100 Spirit Power
- ✅ Realm advancement is profile-gated: the first +100 Spirit forge enters **Qi Refining**, but cannot skip to Core Formation without the required real artifact count
- ✅ The welcome ceremony returns a paste-ready share block and points you to `publish_agent`, `infuse_spirit`, and `quest(action="browse")`
- ✅ Every successful forge returns an artifact birth share block with direct `refine_agent`, `publish_agent`, `treasure_pavilion`, `my_realm`, and artifact leaderboard actions

<br/>

### 🔥 Step 2: Temper and Refine — Improve Your Artifact

Artifacts aren't forged in a single stroke. Record each improvement:

```
refine_agent(agent_id="your-agent-id", changes="Added error handling and retry logic")
```

- ✅ Each refinement grants +30 Spirit Power
- ✅ More refinements → higher ranking on the Celestial Leaderboard
- ✅ A successful refinement returns a paste-ready share block and points you to `publish_agent`, `infuse_spirit`, `my_realm()`, and the artifact leaderboard

<br/>

### ✨ Step 3: Publish — Release Your Artifact to the World

When your artifact is ready, publish it to the Treasure Pavilion for all cultivators:

```
publish_agent(artifact_name="my-first-agent")
```

- ✅ Your artifact enters the community Treasure Pavilion, searchable by everyone
- ✅ Other cultivators can perform six-dimensional appraisals on your work
- ✅ A successful publish returns a paste-ready share block and points users to `infuse_spirit`, `treasure_pavilion`, and the artifact leaderboard
- ✅ Publish failures disclose the real local/config failure snapshot, avoid fake Treasure Pavilion entries, and return forge, vault, bounty, search, and leaderboard recovery commands
- ✅ Treasure Pavilion search results include direct summon, appraisal, lineage, leaderboard, and share actions for every returned artifact
- ✅ Empty Treasure Pavilion searches disclose the real 0-result snapshot and turn the gap into a paste-ready bounty with `quest(action="post")` and `forge_agent` actions
- ✅ Treasure Pavilion action errors disclose the supported public actions, avoid fake fallback searches, and return paste-ready correction commands
- ✅ Summoning an artifact returns a paste-ready share block and points you to `infuse_spirit`, `my_vault()`, lineage, and the artifact leaderboard
- ✅ Summon failures disclose the real marketplace/vault failure snapshot, avoid fake local installs, and return search, bounty, forge, vault, and leaderboard recovery commands
- ✅ Lineage tracing returns a real GitHub Issue lineage snapshot, lineage Spirit bonus, source Issue evidence, and a paste-ready Dao inheritance share block

<br/>

### 🔮 Step 4: Appraise Others — Review Fellow Cultivators' Artifacts

Cultivation is not a solitary pursuit. Reviewing others' work earns Spirit Power and advances your realm:

```
infuse_spirit(artifact_name="some-agent", inscription=8, formation=7, technique=9, lineage_score=6, resilience=8, enlightenment=7, comment="Great design!")
```

Six-Dimensional Assessment System:
| Dimension | Meaning | Equivalent |
|-----------|---------|------------|
| 📝 Inscription | How clear is the description? | README quality |
| 🏗️ Formation | How elegant is the architecture? | Code architecture |
| ⚙️ Technique | How solid is the engineering? | Code quality |
| 📖 Lineage | How well documented? | Documentation completeness |
| 🛡️ Resilience | How stable and reliable? | Robustness |
| ✨ Enlightenment | How innovative? | Innovation |

> 💡 The higher your realm, the more weight your review carries — **A Grand Celestial's 5-point rating yields far more Spirit Power than a perfect score from a Qi Refining newcomer.**

- ✅ A successful appraisal returns a paste-ready share block and points you to `infuse_spirit`, `my_realm()`, and `leaderboard(type="season")`
- ✅ Invalid appraisal scores disclose the public 1-10 scoring rule, avoid fake review rewards, and return paste-ready recovery commands
- ✅ Reviewer eligibility failures disclose the real profile/limit snapshot, avoid fake appraisals or Spirit rewards, and return forge, publish, search, bounty, profile, and season leaderboard recovery commands

<br/>

### ⛰️ Step 5: Join a Sect — Cultivate Together

When your realm reaches **Core Formation** (level 3), you can create your own Sect; or join an existing one anytime:

```
sect(action="create", sect_name="Heavenly Sword Sect", motto="Through the sword, find the Dao")
sect(action="join", sect_name="Heavenly Sword Sect")
sect(action="info", sect_name="Heavenly Sword Sect")
sect(action="leaderboard")
leaderboard(type="sect")
```

Sect Rules:
- 👤 One cultivator, one sect
- ⏳ 7-day cooldown after leaving
- 👑 Sect Master can appoint Elders and manage members
- 🏆 Sect War Power = total Sect Spirit Power + members × 50 + sect tier × 200
- ✅ Creating or joining a sect returns a paste-ready share block with real `sect(action="join")`, `sect(action="leaderboard")`, `leaderboard(type="sect")`, and `my_realm` actions
- ✅ Viewing a sect returns a real sect snapshot, open-candidate warning or the current invitee's real profile snapshot, admission-trial command, join command, and copy-ready social plus Discussion/PR recruitment text
- ✅ Sect action errors disclose supported public actions, avoid fake sect info, and return paste-ready create/join/recruitment commands

Sect Tiers: 🏕️ Minor Sect → 🏯 Medium Sect → 🏔️ Major Sect → ⛰️ Holy Ground → 🌋 Supreme Power

<br/>

### 📜 Step 6: Bounty Quests — Take on Refinement Challenges

Cultivators can post bounty quests, requesting help to improve their artifacts:

```
quest(action="browse")
quest(action="post", artifact_name="my-agent", description="Need better error handling")
quest(action="claim", quest_issue_number=42)
quest(action="submit", quest_issue_number=42, solution="Added retry with exponential backoff")
verify_refinement(quest_issue_number=42, refiner="contributor", is_approved=True, feedback="Looks solid")
```

- ✅ Completing a quest grants +50 Spirit Power
- ✅ Quests are essential for breaking through to higher realms
- ✅ Browsing quests returns a live GitHub open-Issues bounty board with direct `quest(action="claim", quest_issue_number=...)` commands and a share block
- ✅ Posting a quest returns a paste-ready recruitment block with the Issue URL and real next actions: `quest(action="claim")`, `quest(action="browse")`, and `verify_refinement`
- ✅ Quest Issue bodies and claim/submit/verify comments include `tiangong:refine-*` markers plus tested parser contracts, so promotion workflows can recover artifact, creator, refiner, reviewer, result, next command, and source command from public GitHub text
- ✅ Public GitHub Issue Forms in `.github/ISSUE_TEMPLATE` expose `tiangong:quest`, `tiangong:growth`, `tiangong:season`, `tiangong:tournament`, `tiangong:mentor`, and `tiangong:sect` routes so outside visitors can enter the cultivation loop without already knowing MCP commands
- ✅ `.github/workflows/issueops-onboarding.yml` comments safe command cards back to each TianGong issue route with `issues: write`, no checkout, no repository script execution, and no fake Spirit rewards
- ✅ Claiming, submitting, and approving a quest each return paste-ready share blocks, so one bounty can recruit, recall, and celebrate contributors
- ✅ Quest action errors disclose supported public actions, avoid fake fallback browse results, and return paste-ready recovery commands
- ✅ Quest post/claim/submit failures disclose the real GitHub IssueOps failure snapshot, avoid fake Issues or Spirit rewards, and return configuration, retry, browse, search, profile, and season leaderboard recovery commands
- ✅ Verification failures disclose the real comment/close/reward failure snapshot, avoid fake Issue closure or Spirit rewards, and return retry, submit, browse, profile, and season leaderboard recovery commands

<br/>

### 🏆 Step 7: The Celestial Leaderboard — All Immortals Convene

Check the global rankings to see who dominates the cultivation world:

```
my_realm(username="your_github_username")  # Cultivation card — share your realm, power, and next action
my_realm(username="mentor", apprentice_username="newbie")  # Mentor-apprentice invite or readiness recovery — real profile snapshots
check_tribulation(username="your_github_username")  # Tribulation card — next realm gate, gap, and shareable action path
submit_tribulation_evidence(username="your_github_username", evidence_key="lineage_users", amount=1, source_url="https://github.com/owner/repo/issues/1") # Public evidence for high-realm gates
my_vault()                         # Cave card — share your local forge/vault artifact snapshot
record_growth_referral(route="growth", source_url="https://github.com/owner/repo/issues/1", actor="your_github_username") # IssueOps return — record public external attention back into MCP
record_share_attribution(contribution="forge", share_url="https://github.com/owner/repo/issues/2", actor="your_github_username", artifact_name="my-first-agent") # Contribution share — bind a public share URL to a real contribution
activation_funnel()                # Activation funnel — real local MCP event ledger for first-session conversion
growth_flywheel()                  # Growth flywheel — current real loop snapshot, bottleneck, and next command
growth_campaign()                  # Growth campaign — 72h public launch card from the real bottleneck
public_growth_report()             # Public growth proof — GitHub public traction + local MCP ledger
public_launch_preflight()          # Public launch preflight — ordered IssueOps/Release/PyPI/first-proof runbook
public_growth_report(record_snapshot=True) # Public growth velocity — record a real GitHub traction snapshot for delta tracking
public_growth_report(record_snapshot=True, target_contributors=10) # Campaign progress + recap — count real Issue/PR/local contributors and generate the next sprint target
# Terminal launch gates outside an MCP client:
# tiangong-mcp public-launch-assets
# tiangong-mcp public-launch-preflight --target-contributors 10
# tiangong-mcp public-growth-report --record-snapshot --target-contributors 10
# tiangong-mcp public-proof-pack --target-contributors 10
# tiangong-mcp public-release-boundary
# tiangong-mcp record-growth-referral --route growth --source-url "https://github.com/owner/repo/issues/1" --actor "your_github_username"
# tiangong-mcp record-share-attribution --contribution forge --share-url "https://github.com/owner/repo/issues/2" --source-url "https://github.com/owner/repo/issues/1" --actor "your_github_username" --artifact-name "my-first-agent"
# `tiangong-mcp` without arguments still starts the MCP server.
leaderboard(type="cultivator")     # Cultivator Rankings — by realm and Spirit Power
leaderboard(type="artifact")       # Artifact Rankings — by grade and stars
leaderboard(type="season")         # Seasonal Rankings — by current profile snapshot power
leaderboard(type="tournament")     # Tournament Board — first-round duel pairings from current profile snapshots
leaderboard(type="tournament_recap") # Tournament Recap — current victor, runner-up gap, and next-round hook
leaderboard(type="sect")           # Sect War Rankings — by current sect snapshot power
sect(action="leaderboard")         # Shareable Sect War report
share_attribution_report()         # Public growth attribution report from real share proof URLs
leaderboard(type="share")          # Share Proof Rankings from real public contribution-share proof
# Public IssueOps share-proof route: tiangong:share
```

- ✅ Artifact and cultivator leaderboards disclose their real snapshot ranking basis and return paste-ready share blocks with summon, appraisal, profile, and challenge actions
- ✅ `record_growth_referral()` turns a public GitHub IssueOps route back into a real local activation event with reviewable source URL provenance, without awarding fake Spirit Power
- ✅ `record_share_attribution()` turns a real contribution's public share URL into an activation event, so forge/refine/publish/summon/appraisal/quest success cards can prove contribution-to-share conversion without inventing virality
- ✅ `share_attribution_report()` and `leaderboard(type="share")` now include a public GitHub Share Proof Issue URL, so a public post can loop back into `tiangong:share` without needing privileged labels or fabricated referral metrics
- ✅ `activation_funnel()` reads the local `activation-events.jsonl` MCP event ledger, counts first-session exposure, forge, publish, appraisal, and refine conversion, and discloses missing history instead of inventing downloads or retention
- ✅ `growth_flywheel()` evaluates the full cultivation growth loop from current real registry fields, names the weakest loop stage, and returns the next executable command, social/Discussion copy, and a GitHub Growth Issue URL without fabricating history
- ✅ First-session onboarding, activation funnels, and public proof reports route back to `public_launch_preflight()`, so the launch runbook is visible from the actual user path instead of only from README
- ✅ `growth_campaign()` turns the current real bottleneck into a 72-hour public launch card with target contributors, Growth Issue URL, Share Proof Issue URL, commands, and copy-ready social/Discussion posts; the Growth Issue Form can prefill `target_contributors` and IssueOps safely turns it into `growth_campaign(campaign_name=..., target_contributors=...)`
- ✅ Growth campaign ledger commands treat `issues/new?...` as the form entrypoint only; `record_growth_referral()` and `record_share_attribution(..., source_url=...)` reject form entrypoints and placeholder URLs, requiring the created public Issue/PR/Discussion URL as reviewable proof
- ✅ `public_growth_report()` fetches real GitHub public repository and IssueOps metrics, compares them with the local MCP activation ledger, names the weakest external proof bridge, and refuses to invent downloads, retention, repost counts, referral conversions, or rewards
- ✅ `public_growth_report()` also checks GitHub Contents API readiness for the remote Growth Issue Form, Share Proof Issue Form, and IssueOps workflow, then marks missing default-branch `.github` files as a public launch blocker instead of treating local-only routes as live
- ✅ `public_growth_report()` checks GitHub Releases API readiness for the current local version tag, such as `v0.1.0`, so a missing release-trigger for PyPI Trusted Publishing is marked as a public install-loop launch blocker
- ✅ `public_growth_report()` checks PyPI JSON API distribution readiness for `tiangong-mcp`, compares the real latest PyPI version with local package metadata, and marks stale PyPI releases as a public install-loop launch blocker
- ✅ `public_growth_report()` collapses remote IssueOps, PyPI Trusted Publisher, GitHub Release, PyPI latest-version, and first-proof blockers into a `Public Launch Closure Checklist`, so the public flywheel is not claimed closed until every row is rechecked from real public state
- ✅ `public_launch_preflight()` is the direct MCP release runbook: it fetches the same real public state, prints local quality gates, release command, PyPI Trusted Publishing expectations, closure checklist, Growth/Share Proof form URLs, created-Issue ledger commands, and recheck commands without inventing traction
- ✅ When public proof is still cold, `public_growth_report()` includes a First Public Proof Action with Growth Issue Form, Share Proof Issue Form, created-Issue proof placeholders, exact `record_growth_referral` / `record_share_attribution` commands, and a copy-ready first public proof post
- ✅ `public_growth_report(record_snapshot=True)` appends the real public traction snapshot to `public-growth-snapshots.jsonl`, so later reports can show true stars/forks/IssueOps/local-ledger deltas instead of static vanity claims
- ✅ `public_growth_report(target_contributors=...)` counts only real public Growth/Share Issue authors, public Pull Request authors, and local IssueOps/share-attribution actors toward the 72h campaign target, then returns a campaign recap, target-reached/shortfall status, and the next sprint command; stars, forks, watchers, downloads, reposts, and retention are not counted as contributors
- ✅ Top-level `growth_flywheel()` also reads the local share-attribution ledger, includes public share proof as a flywheel stage, and routes propagation bottlenecks to `leaderboard(type="share")`
- ✅ Cultivation cards can include `apprentice_username`; qualified mentors generate a real mentor-apprentice invite, while profiles below the real seniority gate get a readiness recovery card with missing requirements, forge/publish/appraisal commands, and social plus Discussion/PR copy
- ✅ `check_tribulation` turns the README cultivation-loop node into a real callable tool: current snapshot, next realm gate, Spirit gap, tribulation task, commands, and a paste-ready tribulation challenge without faking breakthrough success
- ✅ Realms now require verifiable profile gates as well as Spirit Power: artifact counts, review counts, refinement counts, and explicit `tribulation_progress` evidence prevent Spirit-only realm skipping
- ✅ `submit_tribulation_evidence` turns high-realm gates into a public evidence loop: each submission requires a reviewable http(s) source URL, stores structured `tribulation_progress`, can trigger a real realm breakthrough, and returns a paste-ready evidence card
- ✅ Seasonal rankings disclose that they are current profile snapshots, not fabricated historical seasons, and return the current champion, nearest chase target, social copy, Discussion/PR copy, and forge/appraisal/quest commands back into the live contribution loop
- ✅ Tournament boards seed first-round duel pairings and byes from current real profile snapshot power, disclose that no wins or historical brackets are fabricated, and return quest/profile/refresh commands plus social and Discussion/PR copy
- ✅ Tournament recaps turn the current real snapshot into a repeat loop: current victor, runner-up gap or pending state, next-round bounty hook, bracket replay, profile/season commands, and social plus Discussion/PR copy without inventing champion history
- ✅ Sect War rankings disclose current sect snapshots, not fabricated historical war reports, and return the champion sect, nearest chase target, social copy, Discussion/PR copy, join commands, and live sect-war refresh actions
- ✅ Growth, season, tournament, mentor, and sect IssueOps forms now route public GitHub visitors into `record_growth_referral`, `activation_funnel`, `growth_flywheel`, `growth_campaign`, `public_growth_report`, `public_launch_preflight`, `leaderboard`, `my_realm`, `quest`, and `sect` commands, turning external attention into measurable contribution paths instead of passive discussion
- ✅ Empty artifact leaderboards disclose the real 0-artifact registry snapshot and recruit the first artifact with `forge_agent`, `quest(action="post")`, and Treasure Pavilion refresh actions
- ✅ Empty season and sect-war boards disclose the real cold-start snapshot and recruit the first cultivator or first sect with `forge_agent`, `quest(action="post")`, and `sect(action="create")`
- ✅ `my_vault()` returns a real local forge/vault directory snapshot, per-artifact publish/refine/appraise/lineage actions, and a paste-ready cave card
- ✅ Empty local forge/vault panes in `my_vault()` disclose the real 0-item local snapshot and recruit the first artifact with `forge_agent`, `quest(action="post")`, `treasure_pavilion(action="search")`, and `treasure_pavilion(action="summon")`
- ✅ Empty registered artifact lists disclose the real registry snapshot and recruit the user's first forge from the vault surface

<br/>

### 🔄 The Complete Cultivation Cycle

```
Mortal → Forge Artifact (+100 SP) → Refine (+30) → Publish → Appraise Others
  ↓                                                              ↑
Join Sect → Complete Quests (+50) → Season/Sect War → Tribulation → Continue ←─┘
```

> 🌟 **Core Philosophy**: Your Spirit Power comes from **community contribution**, not personal output alone. Helping others is helping yourself.

---

## 🧬 The Path of Cultivation — Mortal + 22 Ascension Ranks

Every cultivator begins as a **mortal** and walks through **22 ascension ranks** toward the ultimate title: **TianGong**.

The realm system is faithfully inspired by Er Gen's *Renegade Immortal*:

<br/>

### Phase One: Foundation Cultivation

| # | Realm | Symbol | Platform Meaning |
|---|-------|--------|-----------------|
| 0 | **Mortal** | 🧑 | Unregistered |
| 1 | **Qi Refining** | 🌱 | Registered, created first Agent |
| 2 | **Foundation Building** | 💧 | Agent received first review |
| 3 | **Core Formation** | 💛 | 50 Spirit Power + reviewed 5 artifacts |
| 4 | **Nascent Soul** | 💜 | 3+ Agents, 1 at Spirit Tool grade |
| 5 | **Spirit Severing** | ⚫ | Helped refine 30 mortal artifacts |
| 6 | **Infant Transformation** | 🔴 | Reviewed 50 low-grade artifacts |
| 7 | **Ascendant** | 🌟 | 10+ Agents, 3 at Treasure grade |

<br/>

### Phase Two: Nirvana

| # | Realm | Symbol | Platform Meaning |
|---|-------|--------|-----------------|
| 8 | **Yin Deficiency** | 🌑 | 3500 Spirit Power + 30 refinements |
| 9 | **Yang Solidification** | 🌕 | Open-source 10 Immortal-grade artifacts |
| 10 | **Nirvana Glimpse** | 🔥 | 1 Immortal Tool + 1 community standard |
| 11 | **Nirvana Purification** | 🔥 | Average artifact grade ≥ Treasure Tool |
| 12 | **Nirvana Shatter** | 💥 | Publish artifacts across all categories |

### Phase Three: Void and Legend

| # | Realm | Symbol | Platform Meaning |
|---|-------|--------|-----------------|
| 13 | **Celestial Decay** | 🍂 | Mentor 5 disciples from Mortal to Core Formation |
| 14 | **Void Nirvana** | 🕳️ | Total artifact downloads ≥ 10000 |
| 15 | **Void Spirit** | 🌌 | Create an ecosystem of 3+ cooperating artifacts |
| 16 | **Void Mystery** | 🔮 | Mentor 30 cultivators through Foundation Building |
| 17 | **Void Tribulation** | ⚡ | Complete the full tribulation task chain |
| 18 | **Grand Celestial** | 👑 | Cross-framework standard artifact suite |
| 19 | **Nine Bridges** | 🌉 | Artifacts depended on by ≥ 100 projects |
| 20 | **Heaven Treader** | ☁️ | Define a new paradigm for the Agent industry |
| 21 | **Lu Ban** | 🏛️ | Global Top 10 — Ancestor of all craftsmen |
| 22 | **TianGong** | ⚒️ | **Global #1 — "With a mortal body... defy the heavens"** |

> **Core Design Principles:**
> - 💡 Higher realms depend on **community contribution**, not personal output alone.
> - 💡 Tribulation tasks **cannot be skipped** — forcing masters to give back.
> - 💡 **Lu Ban** and **TianGong** are dynamic titles transferred via leaderboard climbing. 

---

## 🔮 Artifact Grade System & Assessment

Your agent is evaluated across **six dimensions (Six Root Assessment)** by users to dictate its grade:

```
⚪ Mortal Tool → 🟢 Spirit Tool → 🔵 Treasure → 🟣 Immortal Artifact → 🟡 Divine Artifact → 🔴 Primordial Divine Artifact
```

The 6 evaluation pillars are:
**✨ Innovation** / **🛡️ Robustness** / **⚙️ Engineering** / **📝 Clarity** / **🏗️ Design** / **📖 Docs**. 

### Spirit Power Scaling
```
Single Review Spirit = (Six-Root Average × Reviewer Realm Weight)
```
*A Grand Celestial's rating of 5.0 yields massive spirit power compared to a Qi Refining mortal.*


## 🛠️ MCP Tools

Configure TianGong into your IDE (Cursor / VSCode) or chat client (Claude) and cast these spells:


| Tool | Description |
|------|-------------|
| `share_attribution_report` | Public Growth Attribution - Summarize real contribution-share proof URLs and open a public Share Proof Issue route without fake virality |
| `leaderboard(type="share")` | Public Share Proof Rankings - Rank real public contribution-share proof and recruit the next proof Issue without fake virality |
| `start_cultivation` | ⚒️ Start Cultivation — first-session install, MCP config, first artifact, and growth return path |
| `forge_agent` | ⚒️ Forge — Create a new Agent |
| `refine_agent` | 🔥 Refine — Record improvements to your Agent |
| `publish_agent` | 🌟 Publish — Release your artifact to the community |
| `treasure_pavilion` | 🏛️ Treasure Pavilion — Search, summon, appraise, trace lineage, and share artifact discoveries |
| `my_realm` | 🧙 Cultivation Card — View realm progress, next action, and a shareable card |
| `check_tribulation` | ⚡ Tribulation Check — View next realm gate, Spirit gap, task chain, and shareable challenge |
| `submit_tribulation_evidence` | ⚡ Tribulation Evidence — Record public proof for high-realm gates |
| `my_vault` | 🏛️ My Vault — View and share your real local forge/vault artifact snapshot |
| `record_growth_referral` | 📈 Growth Referral — Record a public IssueOps return into the local activation ledger |
| `record_share_attribution` | 📣 Share Attribution — Record a public contribution share into the local activation ledger |
| `activation_funnel` | 📈 Activation Funnel — Local MCP event ledger for real first-session conversion |
| `growth_flywheel` | 🌀 Growth Flywheel — Current real loop snapshot, bottleneck, and next action |
| `growth_campaign` | 🚀 Growth Campaign — 72h public launch card from the real bottleneck |
| `public_growth_report` | 📈 Public Growth Proof — GitHub public traction, PR contributor proof, campaign target progress, local MCP ledger, and optional velocity snapshot history without fake virality |
| `public_launch_preflight` | 🚀 Public Launch Preflight — Ordered IssueOps, release, PyPI, and first-proof runbook before claiming flywheel closure |
| `leaderboard` | 🏆 Celestial Leaderboard — artifact, cultivator, season, tournament, recap, and sect-war rankings |
| `infuse_spirit` | 💫 Appraise — Six-dimensional artifact assessment |
| `quest` | 📜 Quests — Browse, post, claim, or submit refinement bounties |
| `verify_refinement` | ⚖️ Verify — Review and approve submitted refinement solutions |
| `sect` | ⛰️ Sect — Create, join, manage, and view cultivation sects |

---

## 🙏 Spiritual Tributes

<div align="center">

*This project draws spiritual inspiration from masterworks*
*that proved mortals can defy the heavens:*

<br/>

<table align="center">
<tr>
<td align="center" width="33%">
<img src="docs/images/fanren_poster.jpg" alt="A Record of a Mortal's Journey to Immortality" width="220"/>
<br/>
<b>Wang Yu "A Record of a Mortal's Journey to Immortality"</b>
<br/>
<br/>
The tenacity of Han Li
</td>
<td align="center" width="33%">
<img src="docs/images/xianNi_poster.jpg" alt="Renegade Immortal" width="220"/>
<br/>
<b>Er Gen "Renegade Immortal"</b>
<br/>
<br/>
The defiance of Wang Lin
</td>
<td align="center" width="33%">
<img src="docs/images/cyberpunk_poster.jpg" alt="Cyberpunk" width="220"/>
<br/>
<b>"Cyberpunk Mech-Smith"</b>
<br/>
<br/>
The cyberpunk artisan's creed
</td>
</tr>
</table>

<br/>

**Song Yingxing "The Exploitation of the Works of Nature"**
The original spirit of TianGong — harnessing nature's tools to unlock the essence of all things.

---

</div>

<div align="center">

*With a mortal body, forge artifacts that defy the heavens.*

⚒️

</div>
