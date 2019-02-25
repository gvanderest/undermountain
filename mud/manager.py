from mud import module
import asyncio


class Manager(module.Module):
    DELAY = 1.0

    async def start(self):
        await super().start()

        while self.running:
            await asyncio.sleep(self.DELAY)
            await self.tick()

    async def tick(self):
        pass
