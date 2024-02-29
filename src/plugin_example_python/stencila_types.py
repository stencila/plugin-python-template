"""Some very minimal Stencila Types, just to get us going."""
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

MessageLevel = Literal["Info", "Warning", "Error"]

Node: TypeAlias = Any


@dataclass
class KernelInstance:
    instance: str


@dataclass(kw_only=True)
class ExecutionMessage:
    type: Literal["ExecutionMessage"] = "ExecutionMessage"
    level: MessageLevel
    message: str
    error_type: str | None = None
    # Maybe
    # code_location: Optional[CodeLocation] = None
    # stack_trace: Optional[str] = None


@dataclass(kw_only=True)
class Thing:
    description: str | None = None
    name: str | None = None
    url: str | None = None


@dataclass(kw_only=True)
class CreativeWork(Thing):
    version: str | float | None = None


@dataclass(kw_only=True)
class SoftwareSourceCode(CreativeWork):
    type: Literal["SoftwareSourceCode"] = "SoftwareSourceCode"

    programming_language: str
    code_repository: str | None = None


@dataclass(kw_only=True)
class SoftwareApplication(CreativeWork):
    type: Literal["SoftwareApplication"] = "SoftwareApplication"

    software_version: str | None = None
    operating_system: str | None = None


# ValueType: TypeAlias = Literal["String", "Number", "Boolean", "Null"]
# For now, just these.
ValueNode: TypeAlias = str | float | int | bool | None


# TODO: Add Hinting
# Hint = Union[
#     ArrayHint,
#     DatatableHint,
#     Function,
#     ObjectHint,
#     StringHint,
#     Unknown,
#     bool,
#     int,
#     float,
# ]


@dataclass(kw_only=True)
class Variable:
    type: Literal["Variable"] = "Variable"

    name: str
    programming_language: str | None = None
    native_type: str | None = None
    node_type: str | None = None
    value: ValueNode | None = None
    # hint: Hint | None = None
