import asyncio
import time

from plugin_example_python.plugin_base import JSONDict, PluginBase


class ExamplePlugin(PluginBase):
    async def health(self) -> JSONDict:
        return {
            "timestamp": int(time.time()),
            "status": "OK",
        }

    async def add(self, x: int, y: int) -> JSONDict:
        return {"sum": x + y}


def run():
    plugin = ExamplePlugin()
    asyncio.run(plugin.run())


if __name__ == "__main__":
    run()
