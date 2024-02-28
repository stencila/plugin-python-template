import asyncio

from plugin_example_python.plugin_base import JSONDict, PluginBase


class ExamplePlugin(PluginBase):
    async def add(self, x: int, y: int) -> JSONDict:
        return {"sum": x + y}


def run():
    """Expose this, as we use it as an entry point in pyproject.toml."""
    plugin = ExamplePlugin()
    asyncio.run(plugin.run())


if __name__ == "__main__":
    """We also put it here, so we can invoke it for testing."""
    run()
