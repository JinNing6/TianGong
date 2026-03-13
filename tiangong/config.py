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

        # === 数据目录 ===
        _default_data = str(Path(__file__).parent.parent / "agents")
        self.DATA_DIR: str = os.getenv("TIANGONG_DATA_DIR", _default_data)

        # === Agent 注册表 ===
        self.REGISTRY_FILE: str = os.path.join(self.DATA_DIR, "_registry.json")
        self.CULTIVATORS_FILE: str = os.path.join(self.DATA_DIR, "_cultivators.json")

        # === 生态联动 ===
        self.CYBERHUATUO_ENABLED: bool = os.getenv("CYBERHUATUO_ENABLED", "true").lower() == "true"
        self.NOOSPHERE_ENABLED: bool = os.getenv("NOOSPHERE_ENABLED", "true").lower() == "true"

        # === 本命法宝限制 ===
        self.MAX_NATAL_ARTIFACTS: int = 3  # 每个修仙者最多绑定 3 件本命法宝

        # === 确保数据目录存在 ===
        Path(self.DATA_DIR).mkdir(parents=True, exist_ok=True)


# 全局单例
config = TianGongConfig()
