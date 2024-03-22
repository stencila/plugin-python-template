import asyncio

import coolname
from stencila_plugin import Kernel, Plugin
from stencila_types import shortcuts as S
from stencila_types import types as T


class AnimalListKernel(Kernel):
    async def execute(self, code: str) -> tuple[list[T.Node], list[T.ExecutionMessage]]:
        """Generate some names.

        The code should just be a number, for the number of lines.
        """
        try:
            number = int(code)
        except ValueError:
            return [], [
                T.ExecutionMessage(message="Invalid input", level=T.MessageLevel.Error),
            ]

        items = []
        for _ in range(number):
            nms = " ".join(x.capitalize() for x in coolname.generate())
            items.append(S.li(nms))

        lst = T.List(items=items, order=T.ListOrder.Ascending)
        return [lst], []


class CapitalKernel(Kernel):
    async def execute(self, code: str) -> tuple[list[T.Node], list[T.ExecutionMessage]]:
        """Capitalize the input."""
        return [S.p(code.upper())], []


def run():
    """Expose this, as we use it as an entry point in pyproject.toml."""
    plugin = Plugin(kernels=[AnimalListKernel, CapitalKernel])
    asyncio.run(plugin.run())


if __name__ == "__main__":
    """We also put it here, so we can invoke it for testing."""
    run()
