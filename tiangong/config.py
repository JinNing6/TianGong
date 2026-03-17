"""
⚒️ 天工 TianGong — 配置管理
集中管理环境变量和默认配置
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class TianGongConfig:
    """天工全局配置"""

    def __init__(self):
        # === GitHub 配置 ===
        self.GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", os.getenv("USER", "anonymous"))
        self.GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

        # === GitHub 仓库配置（分发平台） ===
        self.GITHUB_REPO_OWNER: str = os.getenv("TIANGONG_REPO_OWNER", "JinNing6")
        self.GITHUB_REPO_NAME: str = os.getenv("TIANGONG_REPO_NAME", "TianGong")
        self.MARKETPLACE_DIR: str = "marketplace"  # 仓库中的法宝目录

        # === 数据目录（本地 Agent 注册表，Phase 1 兼容） ===
        _default_data = str(Path(__file__).parent.parent / "agents")
        self.DATA_DIR: str = os.getenv("TIANGONG_DATA_DIR", _default_data)

        # === Agent 注册表 ===
        self.REGISTRY_FILE: str = os.path.join(self.DATA_DIR, "_registry.json")
        self.CULTIVATORS_FILE: str = os.path.join(self.DATA_DIR, "_cultivators.json")

        # === 洞府路径（Phase 2 分发平台） ===
        _default_cave = str(Path.home() / ".tiangong")
        self.CAVE_DIR: str = os.getenv("TIANGONG_CAVE_DIR", _default_cave)
        self.FORGE_DIR: str = os.path.join(self.CAVE_DIR, "forge")    # 自己创作的法宝
        self.VAULT_DIR: str = os.path.join(self.CAVE_DIR, "vault")    # 拉取的别人的法宝
        self.CAVE_CONFIG: str = os.path.join(self.CAVE_DIR, "config.yaml")
        self.CAVE_PROFILE: str = os.path.join(self.CAVE_DIR, "cultivator.json")
        self.CAVE_REGISTRY: str = os.path.join(self.CAVE_DIR, "registry.json")
        self.CAVE_LOGS_DIR: str = os.path.join(self.CAVE_DIR, "logs")
        self.VAULT_ARCHIVE_DIR: str = os.path.join(self.VAULT_DIR, ".archive")

        # === 生态联动 ===
        self.CYBERHUATUO_ENABLED: bool = os.getenv("CYBERHUATUO_ENABLED", "true").lower() == "true"
        self.NOOSPHERE_ENABLED: bool = os.getenv("NOOSPHERE_ENABLED", "true").lower() == "true"

        # === 本命法宝限制 ===
        self.MAX_NATAL_ARTIFACTS: int = 3  # 每个修仙者最多绑定 3 件本命法宝

        # === 评价限制 ===
        self.MAX_REVIEWS_PER_DAY: int = 10        # 每人每天最多评价 10 件法宝
        self.REVIEW_MODIFY_WINDOW_DAYS: int = 7    # 评价后 7 天内可修改
        self.GRADE_PROTECTION_DAYS: int = 30       # 品阶晋升后 30 天保护期

        # === 宗门限制 ===
        self.SECT_CREATE_MIN_REALM: int = 3         # 创建宗门最低境界（3=结丹期）
        self.SECT_LEAVE_COOLDOWN_DAYS: int = 7      # 退出宗门冷却天数
        self.SECT_MAX_ELDERS: int = 5               # 每个宗门最多长老数

        # === 依赖安装配置 ===
        self.PYTHON_ENV: str = os.getenv("TIANGONG_PYTHON_ENV", "system")  # system / venv / 路径
        self.AUTO_INSTALL_DEPS: bool = os.getenv("TIANGONG_AUTO_INSTALL", "true").lower() == "true"

        # === 确保数据目录存在 ===
        Path(self.DATA_DIR).mkdir(parents=True, exist_ok=True)


# 全局单例
config = TianGongConfig()
