import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from asyncio.subprocess import Process


class StdioHarness:
    """Test harness for Stdio Transport"""

    def __init__(self, path: Path):
        self.path = path
        self.process: Optional[Process] = None

    async def __aenter__(self):
        env = {"STENCILA_TRANSPORT": "stdio"}

        self.process = await asyncio.create_subprocess_exec(
            sys.executable,
            self.path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        if self.process.returncode is not None:
            raise RuntimeError(
                f"Plugin process exited with code {self.process.returncode}"
            )
        return self

    async def handle_request(self, request: str, timeout: int = 1) -> str:
        await self.send(request)
        return await self.receive(timeout)

    async def send(self, request: str):
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("cannot send")

        self.process.stdin.write(request.encode() + b"\n")
        await self.process.stdin.drain()

    async def receive(self, timeout: int = 1) -> str:
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("cannot recieve")

        response_line = await asyncio.wait_for(
            self.process.stdout.readline(), timeout=timeout
        )
        if not response_line:
            # If readline returns an empty string, it means the stream was
            # closed. Try seeing if stderr has some info (wrong path for
            # example).
            if self.process.stderr is None:
                error_line = b""
            else:
                error_line = await self.process.stderr.readline()

            if error_line:
                err = "Error from subprocess:" + error_line.decode()
            else:
                err = "No response from plugin, possibly crashed."
            raise RuntimeError(err)
        return response_line.decode()

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
        if exc_type is not None:
            # TODO: Maybe log the error?
            print(f"exc_type: {exc_type}, exc: {exc}, tb: {tb}")
        if self.process:
            self.process.terminate()
            await self.process.wait()
