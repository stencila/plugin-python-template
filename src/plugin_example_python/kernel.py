from typing import Any, TypeAlias

from .stencila_types import (
    ExecutionMessage,
    Node,
    SoftwareApplication,
    SoftwareSourceCode,
    Variable,
)

KernelId: TypeAlias = str
KernelName: TypeAlias = str


class Kernel:
    def __init__(self, ident: KernelId):
        self.ident = ident

    async def on_start(self):
        pass

    async def on_stop(self):
        pass

    async def get_info(self) -> SoftwareApplication:
        return SoftwareApplication(
            name=self.__class__.__name__,
        )

    async def get_packages(self) -> list[SoftwareSourceCode]:
        return []

    async def execute(self, code: str) -> tuple[list[Node], list[ExecutionMessage]]:
        return [], []

    async def evaluate(self, code: str) -> tuple[list[Node], list[ExecutionMessage]]:
        return [], []

    async def list_variables(self) -> list[Variable]:
        return []

    async def get_variable(self, name: str) -> Variable | None:
        return None

    async def set_variable(self, name: str, value: Any):
        pass

    async def remove_variable(self, name: str):
        pass
