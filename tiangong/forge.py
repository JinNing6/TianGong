"""
⚒️ 天工 TianGong — 开炉炼器引擎
创建新 Agent，注册到本地仓库
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .config import config

logger = logging.getLogger("tiangong.forge")


@dataclass
class AgentSpec:
    """Agent 规格定义"""
    agent_id: str = ""                     # 唯一标识（自动生成）
    name: str = ""                         # Agent 名称
    description: str = ""                  # Agent 描述
    creator: str = ""                      # 创建者（GitHub username）
    agent_type: str = "general"            # 类型: general / chat / tool / workflow
    framework: str = ""                    # 使用的框架
    language: str = "python"               # 编程语言
    repo_url: str = ""                     # 代码仓库地址
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0               # 创建时间
    updated_at: float = 0.0               # 最后更新时间
    stars: int = 0                         # 星标数
    grade_level: int = 0                   # 品级等级
    is_natal: bool = False                 # 是否为本命法宝
    passed_trial: bool = False             # 是否通过试剑
    refinement_log: list[dict] = field(default_factory=list)  # 淬炼日志
    trial_log: list[dict] = field(default_factory=list)       # 试剑日志


def _load_registry() -> dict[str, dict]:
    """加载 Agent 注册表"""
    path = Path(config.REGISTRY_FILE)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_registry(data: dict[str, dict]) -> None:
    """保存 Agent 注册表"""
    path = Path(config.REGISTRY_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def forge_new_agent(
    name: str,
    description: str,
    creator: str,
    agent_type: str = "general",
    framework: str = "",
    language: str = "python",
    repo_url: str = "",
    tags: list[str] | None = None,
) -> AgentSpec:
    """
    ⚒️ 开炉炼器 — 创建新 Agent。

    生成唯一 ID，注册到本地仓库，创建 Agent 目录结构。
    """
    agent_id = f"tg-{uuid.uuid4().hex[:8]}"
    now = time.time()

    spec = AgentSpec(
        agent_id=agent_id,
        name=name,
        description=description,
        creator=creator,
        agent_type=agent_type,
        framework=framework,
        language=language,
        repo_url=repo_url,
        tags=tags or [],
        created_at=now,
        updated_at=now,
    )

    # 注册到注册表
    registry = _load_registry()
    registry[agent_id] = asdict(spec)
    _save_registry(registry)

    # 创建 Agent 目录
    agent_dir = Path(config.DATA_DIR) / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)

    # 写入 Agent 元数据
    meta_path = agent_dir / "agent.json"
    meta_path.write_text(
        json.dumps(asdict(spec), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(f"⚒️ 新法宝已锻造: {name} ({agent_id})")
    return spec


def get_agent(agent_id: str) -> AgentSpec | None:
    """获取 Agent 信息"""
    registry = _load_registry()
    d = registry.get(agent_id)
    if not d:
        return None

    return AgentSpec(**{
        k: v for k, v in d.items()
        if k in AgentSpec.__dataclass_fields__
    })


def refine_agent(
    agent_id: str,
    changes: str,
    refiner: str = "",
) -> tuple[bool, str]:
    """
    🔥 淬炼 Agent — 记录一次优化。

    每次淬炼都是对法宝的千锤百炼。
    """
    registry = _load_registry()
    if agent_id not in registry:
        return False, f"⚠️ 未找到法宝 `{agent_id}`。请检查法宝 ID。"

    d = registry[agent_id]
    now = time.time()

    # 添加淬炼日志
    refinement_log = d.get("refinement_log", [])
    refinement_log.append({
        "timestamp": now,
        "refiner": refiner or d.get("creator", "anonymous"),
        "changes": changes,
    })
    d["refinement_log"] = refinement_log
    d["updated_at"] = now

    registry[agent_id] = d
    _save_registry(registry)

    count = len(refinement_log)
    return True, (
        f"🔥 淬炼完成！\n\n"
        f"- **法宝**: {d.get('name', agent_id)}\n"
        f"- **淬炼次数**: 第 {count} 次\n"
        f"- **变化**: {changes}\n\n"
        f"千锤百炼，去其糟粕。此法宝正在变得更加通灵。"
    )


def list_agents(creator: str | None = None) -> list[AgentSpec]:
    """列出所有 Agent（可按创建者过滤）"""
    registry = _load_registry()
    agents = []

    for agent_id, d in registry.items():
        if creator and d.get("creator") != creator:
            continue
        agents.append(AgentSpec(**{
            k: v for k, v in d.items()
            if k in AgentSpec.__dataclass_fields__
        }))

    return agents


def format_agent_card(spec: AgentSpec) -> str:
    """格式化 Agent 展示卡片"""
    from .artifact_system import calculate_grade, format_grade_display

    grade = calculate_grade(getattr(spec, 'spirit_power', spec.stars), 0, spec.passed_trial)
    natal_mark = " 💠 **本命法宝**" if spec.is_natal else ""

    lines = [
        f"### {grade.symbol} {spec.name}{natal_mark}",
        f"*{spec.description}*",
        "",
        f"- **ID**: `{spec.agent_id}`",
        f"- **品级**: {format_grade_display(grade)}",
        f"- **类型**: {spec.agent_type}",
        f"- **框架**: {spec.framework or '未指定'}",
        f"- **语言**: {spec.language}",
        f"- **⭐ 星标**: {spec.stars}",
        f"- **🔥 淬炼**: {len(spec.refinement_log)} 次",
        f"- **⚔️ 试剑**: {len(spec.trial_log)} 次",
        f"- **创建者**: @{spec.creator}",
    ]

    if spec.repo_url:
        lines.append(f"- **仓库**: {spec.repo_url}")

    if spec.tags:
        lines.append(f"- **标签**: {', '.join(spec.tags)}")

    return "\n".join(lines)
