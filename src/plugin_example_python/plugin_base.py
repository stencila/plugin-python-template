# This will be moved out to its own package in the future.
import asyncio
import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from aiohttp import web

JSONDict = dict[str, Any]
IdType = Union[str, int, None]


@dataclass
class Request:
    method: str
    params: Any = None
    id: Optional[str] = None


class PluginBase(ABC):
    @abstractmethod
    async def health(self) -> JSONDict:
        ...

    async def handle_request(self, request_json: str) -> str:
        """Handle a JSON-RPC request and return a response.

        See https://www.jsonrpc.org/specification
        """
        try:
            request_dct: JSONDict = json.loads(request_json)
        except json.JSONDecodeError:
            return self.error_response(None, -32700, "Parse error")

        method = request_dct.get("method")
        if method is None:
            return self.error_response(None, -32601, "No method sent")

        # This can be None
        rid: IdType = request_dct.get("id")

        # According to the standard, the params can be an Array or an Object (a dict).
        params = request_dct.get("params")
        if params is None:
            args = []
            kwargs = {}
        elif isinstance(params, List):
            args = params
            kwargs = {}
        elif isinstance(params, Dict):
            args = []
            kwargs = params
        else:
            return self.error_response(None, -32700, "params are not Array or Object")

        func = getattr(self, method, None)
        if callable(func):
            try:
                result = await func(*args, **kwargs)
                return self.success_response(rid, result)
            except Exception:
                return self.error_response(rid, -32603, "Internal error")
        else:
            return self.error_response(rid, -32601, "Method not found")

    def success_response(self, rid: IdType, result: JSONDict) -> str:
        return json.dumps({"id": rid, "result": result})

    def error_response(self, rid: IdType, code: int, message: str) -> str:
        return json.dumps({"id": rid, "code": code, "message": message})

    async def listen_stdio(self) -> None:
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
            request_bytes = await reader.readline()
            if request_bytes == b"\n":
                break
            request_json = request_bytes.decode()
            response_json = await self.handle_request(request_json)
            writer.write(response_json.encode())
            writer.write(b"\n")
            await writer.drain()

    async def listen_http(self, port: int, token: str) -> None:
        async def handler(request: web.Request) -> web.Response:
            if request.remote != "127.0.0.1":
                return web.Response(status=403, text="Access denied")

            auth_header = request.headers.get("Authorization", "")
            received_token = (
                auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None
            )
            if received_token != token:
                return web.Response(status=401, text="Invalid or missing token")

            request_json = await request.text()
            response_json = await self.handle_request(request_json)
            return web.Response(text=response_json, content_type="application/json")

        app = web.Application()
        app.add_routes([web.post("/", handler)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", port)
        await site.start()

    async def run(self) -> None:
        protocol = os.environ.get("STENCILA_TRANSPORT")
        if protocol == "stdio":
            await self.listen_stdio()
        elif protocol == "http":
            port = int(os.environ.get("STENCILA_PORT", "0"))
            token = os.environ.get("STENCILA_TOKEN", "")
            await self.listen_http(port, token)
        else:
            raise Exception(f"Unknown protocol: {protocol}")
