import asyncio

from tiangong.mcp_server import my_vault, quest


async def run_verify():
    print("Testing my_vault...")
    res1 = await my_vault()
    print("my_vault returned:", len(res1), "chars")

    print("Testing quest browse...")
    res2 = await quest(action="browse")
    print("quest browse returned:", len(res2), "chars")

    print("\n[SUCCESS] Basic core APIs responded without crash!")


if __name__ == "__main__":
    asyncio.run(run_verify())
