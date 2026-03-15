import asyncio
from tiangong.mcp_server import my_vault, vault_status, browse_quests

async def run_verify():
    print("Testing my_vault...")
    res1 = await my_vault()
    print("my_vault returned:", len(res1), "chars")
    
    print("Testing vault_status...")
    res2 = await vault_status()
    print("vault_status returned:", len(res2), "chars")
    
    print("Testing browse_quests...")
    res3 = await browse_quests()
    print("browse_quests returned:", len(res3), "chars")

    print("\n[SUCCESS] Basic core APIs responded without crash!")

if __name__ == "__main__":
    asyncio.run(run_verify())
