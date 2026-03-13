"""
⚒️ 天工 TianGong — CLI 入口
python -m tiangong
"""

import sys


def main():
    """天工 MCP Server 入口"""
    from .mcp_server import main as mcp_main
    mcp_main()


if __name__ == "__main__":
    main()
