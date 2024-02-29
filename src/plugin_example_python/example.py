import asyncio

from plugin_example_python.kernel import Kernel
from plugin_example_python.plugin import Plugin
from plugin_example_python.stencila_types import SoftwareApplication, SoftwareSourceCode


class ExampleKernel(Kernel):
    async def get_packages(self) -> list[SoftwareSourceCode]:
        return [
            SoftwareSourceCode(name="package1", programming_language="noodle"),
            SoftwareSourceCode(name="package2", programming_language="noodle"),
        ]


def run():
    """Expose this, as we use it as an entry point in pyproject.toml."""
    plugin = Plugin(kernels=[ExampleKernel])
    asyncio.run(plugin.run())


if __name__ == "__main__":
    """We also put it here, so we can invoke it for testing."""
    run()
