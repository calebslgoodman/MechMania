import sys
import asyncio
from pathlib import Path
from strategy.main import get_strategy
from core.ipc import EngineChannel

async def run() -> None:
    args = sys.argv
    if len(args) < 2:
        print("usage: [bin name] [shmem path]")
        return

    path = Path(args[1])
    chan = EngineChannel.from_path(path)

    team = await chan.handle_handshake()

    strat = get_strategy(team)

    while True:
        await chan.handle_msg(strat)

if __name__ == "__main__":
    asyncio.run(run())
