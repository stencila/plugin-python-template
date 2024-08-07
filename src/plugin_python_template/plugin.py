import asyncio
from collections.abc import Sequence

from stencila_plugin import (
    Model,
    ModelOutput,
    ModelTask,
    Kernel,
    Plugin,
)
from stencila_types import shortcuts as S
from stencila_types import types as T
from stencila_types.utilities import to_json


class EchoKernel(Kernel):
    """
    A simple kernel that just echoes back the code sent.

    To do this, we implement two functions:
        - `get_name` to return the name of the kernel
        - `execute`, which returns:
            - a list of `ExecutionMessage`.
            - a Stencila `Node`. See the `stencila_types.types` module for options.

    The Kernel interface is defined in `stencila_plugin.kernel.Kernel`, and has
    a number of additional methods that can be overridden. See the docstrings for more
    information.

        - `async def on_start(self): ...`
        - `async def on_stop(self): ...`
        - `async def get_info(self) -> SoftwareApplication: ...`
        - `async def get_packages(self) -> list[SoftwareSourceCode]: ...`
        - `async def evaluate(self, code: str) -> tuple[list[Node],
            list[ExecutionMessage]]: ...`
        - `async def list_variables(self) -> list[Variable]: ...`
        - `async def get_variable(self, name: str) -> Variable | None: ...`
        - `async def set_variable(self, name: str, value: Any): ...`
        - `async def remove_variable(self, name: str): ...`

    The `execute` and `evaluate` methods do the real work, but the others are used to
    provide additional information about the kernel, so that AI assistants can generate
    code for the kernel.
    """

    @classmethod
    def get_name(cls) -> str:
        """
        The name of the kernel.

        This name be referenced in the stencila_plugin.toml file.
        """
        return "echo-python"

    async def execute(
        self, code: str
    ) -> tuple[Sequence[T.Node], list[T.ExecutionMessage]]:
        """
        Actually *do something*.

        Here, we just echo back the code, and provide an information message.
        We make use of the `stencila_types` module to create the messages and
        nodes. To make it easier to work with, we import the
        `stencila_types.shortcuts as S`
        """
        # Instead of this...
        # nodes = [T.Paragraph(content=[T.Text(value=code)])]
        # ... we can do this:
        nodes = [S.p(code)]
        messages = [
            T.ExecutionMessage(message="Echoing back", level=T.MessageLevel.Info)
        ]
        return nodes, messages


class EchoModel(Model):
    """
    A very simple model that just echos back the task given to it.
    """

    @classmethod
    def get_name(cls) -> str:
        return "stencila/echo-python"

    async def perform_task(self, task: ModelTask) -> ModelOutput:
        return ModelOutput(format="json", content=to_json(task), authors=[])


def run():
    """
    Expose this, as we use it as an entry point in pyproject.toml.

    We're using poetry to manage this project, and so you'll find this
    in the `tool.poetry.scripts` section in the `pyproject.toml` file.
    """
    plugin = Plugin(kernels=[EchoKernel], models=[EchoModel])
    asyncio.run(plugin.run())


if __name__ == "__main__":
    """We need a main, as we run this file as a script in the testing."""
    run()
