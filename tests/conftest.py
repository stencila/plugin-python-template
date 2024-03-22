from pathlib import Path

import pytest

from stencila_plugin.testing import HttpHarness, StdioHarness
import plugin_example_python


@pytest.fixture()
def plugin_path():
    """Provide the path to the plugin."""
    path = Path(plugin_example_python.__file__).parent / "plugin.py"
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
def harness(request):
    """Roll up both harnesses together."""
    return request.getfixturevalue(request.param)
