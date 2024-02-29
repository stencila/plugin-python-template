"""Stencila plugins.

* This will be moved out to its own package in the future.
"""
import asyncio
import json
import os
import sys
import time
import uuid
from typing import Any

import cattrs
from aiohttp import web

from .kernel import Kernel, KernelId, KernelName
from .stencila_types import (
    ExecutionMessage,
    KernelInstance,
    SoftwareApplication,
    SoftwareSourceCode,
)

# This is the best we can do with 3.9.
# TODO: Fix this. It should be JSONABLE = Union[bool, int, float, str, list, dict, None]
JSONDict = dict[str, Any]
IdType = str | int | None
ParamsType = list | dict | None


# TODO: Make into IntEnum?
class ErrorCodes:
    """JSON-RPC error codes.

    See https://www.jsonrpc.org/specification
    """

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


def _success(id: IdType, result: JSONDict) -> JSONDict:
    return {
        "jsonrpc": "2.0",
        "id": id,
        "result": result,
    }


def _error(id: IdType, code: int, message: str) -> JSONDict:
    return {
        "jsonrpc": "2.0",
        "error": {"code": code, "message": message},
        "id": id,
    }


class Plugin:
    """A Stencila plugins."""

    def __init__(self, kernels: list[type[Kernel]] | None = None):
        kernels = kernels or []
        self.kernels: dict[KernelName, type[Kernel]] = {k.__name__: k for k in kernels}
        self.kernel_instances: dict[KernelId, Kernel] = {}

    async def health(self) -> JSONDict:
        """Minimal check that the plugin runs."""
        return {
            "timestamp": int(time.time()),
            "status": "OK",
        }

    async def kernel_start(self, kernel: KernelName):
        kernel_cls = self.kernels.get(kernel)
        if kernel_cls is None:
            return None

        uid = uuid.uuid4()
        kernel_id = f"{kernel}-{uid}"
        self.kernel_instances[kernel_id] = kernel_cls(kernel_id)

        return KernelInstance(kernel_id)

    async def kernel_stop(self, instance: KernelId):
        kernel = self.kernel_instances.pop(instance, None)
        if kernel:
            await kernel.on_stop()

    async def kernel_info(self, instance: KernelId) -> SoftwareApplication | None:
        kernel = self.kernel_instances.get(instance)
        if kernel:
            return await kernel.get_info()
        return None

    async def kernel_packages(self, instance: str) -> list[SoftwareSourceCode]:
        kernel = self.kernel_instances.get(instance)
        if kernel:
            return await kernel.get_packages()
        return []

    async def kernel_execute(self, code: str, instance: str):
        kernel = self.kernel_instances.get(instance)
        if kernel:
            return await kernel.execute(code)
        return [], [ExecutionMessage(message="Kernel not found", level="Error")]

    async def kernel_evaluate(self, code: str, instance: str):
        kernel = self.kernel_instances.get(instance)
        if kernel:
            return await kernel.evaluate(code)
        return [], [ExecutionMessage(message="Kernel not found", level="Error")]

    async def kernel_list(self, instance: str):
        kernel = self.kernel_instances.get(instance)
        if kernel:
            return await kernel.list_variables()
        return []

    async def kernel_get(self, name: str, instance: str):
        kernel = self.kernel_instances.get(instance)
        if kernel:
            return await kernel.get_variable(name)
        return None

    async def kernel_set(self, name: str, value: Any, instance: str):
        kernel = self.kernel_instances.get(instance)
        if kernel:
            await kernel.set_variable(name, value)

    async def kernel_remove(self, name: str, instance: str):
        kernel = self.kernel_instances.get(instance)
        if kernel:
            await kernel.remove_variable(name)

    async def run(self) -> None:
        """Invoke the plugin.

        This method should be called by the plugin's `__main__` module.
        """
        protocol = os.environ.get("STENCILA_TRANSPORT")
        if protocol == "stdio":
            await _listen_stdio(self)
        elif protocol == "http":
            port = int(os.environ.get("STENCILA_PORT", "0"))
            token = os.environ.get("STENCILA_TOKEN", "")
            await _listen_http(self, port, token)
        else:
            raise RuntimeError(f"Unknown protocol: {protocol}")


async def _handle_json(
    plugin: Plugin,
    request: JSONDict,
) -> JSONDict:
    """Interpret a JSON-RPC request and return a response.

    See https://www.jsonrpc.org/specification
    """
    rpc_version = request.get("jsonrpc")
    if rpc_version != "2.0":
        return _error(
            None, ErrorCodes.INVALID_REQUEST, "Invalid or missing JSON-RPC version"
        )

    method = request.get("method")
    if method is None:
        return _error(None, ErrorCodes.METHOD_NOT_FOUND, "No method sent")

    # This can be None
    id: IdType = request.get("id")  # noqa: A001

    # According to the standard, the params can be an Array or an Object (a dict).
    # We also handle None.
    params = request.get("params")

    return await _handle_rpc(plugin, method, params=params, id=id)


def _make_jsonable(result: Any):
    if isinstance(result, (bool, int, float, str)):
        return result

    dct = cattrs.unstructure(result)
    return dct


async def _handle_rpc(
    plugin: Plugin,
    method: str,
    *,
    params: ParamsType,
    id: IdType = None,
) -> JSONDict:
    """Forward the RPC request to a method and return the result."""
    if params is None:
        args = []
        kwargs = {}
    elif isinstance(params, list):
        # Note: Stencila should send named parameters.
        # This is here for completeness.
        args = params
        kwargs = {}
    elif isinstance(params, dict):
        args = []
        kwargs = params
    else:
        return _error(id, ErrorCodes.INVALID_PARAMS, "Params are not Array or Object")

    func = getattr(plugin, method, None)
    if callable(func):
        try:
            result = await func(*args, **kwargs)
            try:
                dct_result = _make_jsonable(result)
            except Exception as e:
                return _error(
                    id, ErrorCodes.INTERNAL_ERROR, f"Cannot convert result to JSON {e}"
                )
            return _success(id, dct_result)
        except Exception as e:
            return _error(id, ErrorCodes.INTERNAL_ERROR, f"Internal error: {e}")
    else:
        return _error(id, ErrorCodes.METHOD_NOT_FOUND, f"Method `{method}` not found")


async def _listen_stdio(plugin: Plugin) -> None:
    reader = asyncio.StreamReader()
    reader_protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_running_loop().connect_read_pipe(
        lambda: reader_protocol, sys.stdin
    )

    (
        writer_transport,
        writer_protocol,
    ) = await asyncio.get_running_loop().connect_write_pipe(
        lambda: asyncio.streams.FlowControlMixin(), sys.stdout
    )
    writer = asyncio.StreamWriter(
        writer_transport, writer_protocol, None, asyncio.get_running_loop()
    )

    while True:
        line = await reader.readline()
        # Exit on an empty line.
        if line == b"\n":
            break

        resp: JSONDict
        try:
            request: JSONDict = json.loads(line.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            resp = _error(None, ErrorCodes.PARSE_ERROR, "Parse error")
        else:
            resp = await _handle_json(plugin, request)

        writer.write(json.dumps(resp).encode())
        writer.write(b"\n")
        await writer.drain()


async def _listen_http(plugin: Plugin, port: int, token: str) -> None:
    async def handler(request: web.Request) -> web.Response:
        # We should only accept requests from localhost
        if request.remote not in ("127.0.0.1", "::1"):
            raise web.HTTPForbidden(reason="Local access only")

        # Check if the token is present and matches the expected value
        auth_header = request.headers.get("Authorization", "")
        received_token = (
            auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None
        )
        if received_token != token:
            raise web.HTTPUnauthorized(reason="Invalid or missing token")

        resp: JSONDict
        try:
            req_json = await request.json()
        except json.JSONDecodeError:
            resp = _error(None, ErrorCodes.PARSE_ERROR, "Cannot parse JSON")
        else:
            resp = await _handle_json(plugin, req_json)

        return web.Response(text=json.dumps(resp), content_type="application/json")

    app = web.Application()
    app.add_routes([web.post("/", handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", port)
    await site.start()

    # Now just serve forever; till you are killed.
    try:  # noqa: SIM105
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass  # Allow graceful exit on Ctrl+C
