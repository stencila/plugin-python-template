from pathlib import Path

import plugin_example_python as plug
import pytest
from plugin_example_python import ExamplePlugin
from plugin_example_python.plugin_base import ErrorCodes
from plugin_example_python.testing import (
    Harness,
    HttpHarness,
    StdioHarness,
    TestHttpError,
    TestRPCError,
)


@pytest.fixture()
def plugin_path():
    path = Path(plug.__file__).parent / "plugin.py"
    assert path.exists()
    return path


@pytest.fixture()
async def stdio_harness(plugin_path: Path):
    async with StdioHarness(plugin_path) as harness:
        yield harness


@pytest.fixture()
async def http_harness(plugin_path: Path):
    async with HttpHarness(plugin_path) as harness:
        yield harness


@pytest.fixture(params=["stdio_harness", "http_harness"])
def harness(request):  # noqa: ANN001
    return request.getfixturevalue(request.param)


def test_exists(plugin_path: Path):
    assert plugin_path.exists()


async def test_direct_method_not_found():
    plugin = ExamplePlugin()
    request_json = {
        "jsonrpc": "2.0",
        "id": "test",
        "method": "non_existent_method",
        "params": {},
    }
    response = await plugin._handle_json(request_json)
    assert "error" in response
    assert response["error"].get("code") == ErrorCodes.METHOD_NOT_FOUND


async def test_token_works(http_harness: HttpHarness):
    # Mess with the headers
    http_harness.headers = {"Authorization": "Bearer xxx"}
    with pytest.raises(TestHttpError):
        await http_harness.send_rpc("health")
    http_harness.headers = {}
    with pytest.raises(TestHttpError):
        await http_harness.send_rpc("health")


async def test_both(harness: Harness):
    res = await harness.send_rpc("health")
    assert res["status"] == "OK"
    res = await harness.send_rpc("add", params=dict(x=1, y=2))
    assert res["sum"] == 3
    res = await harness.send_rpc("add", params=[1, 50])
    assert res["sum"] == 51

    with pytest.raises(TestRPCError):
        await harness.send_raw({"x": 1})
