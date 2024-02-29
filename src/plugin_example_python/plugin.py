import asyncio
from typing import Any

from plugin_example_python.kernel import Kernel
from plugin_example_python.plugin_base import PluginBase
from plugin_example_python.stencila_types import SoftwareApplication, SoftwareSourceCode


class ExampleKernel(Kernel):
    async def get_packages(self) -> list[SoftwareSourceCode]:
        return [
            SoftwareSourceCode(name="package1", programming_language="noodle"),
            SoftwareSourceCode(name="package2", programming_language="noodle"),
        ]
    


class ExamplePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.kernels["Example"] = ExampleKernel


def run():
    """Expose this, as we use it as an entry point in pyproject.toml."""
    plugin = ExamplePlugin()
    asyncio.run(plugin.run())


if __name__ == "__main__":
    """We also put it here, so we can invoke it for testing."""
    run()
