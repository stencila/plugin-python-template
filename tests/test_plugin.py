from stencila_plugin.kernel import KernelInstance
from stencila_plugin.testing import Harness
from stencila_types import types as T


async def test_kernel(harness: Harness):
    result = await harness.send_rpc("kernel_start", kernel="AnimalListKernel")
    ki = KernelInstance(**result)

    result, messages = await harness.invoke(
        "kernel_execute", instance=ki.instance, code="3"
    )
    assert messages == []
    assert isinstance(result, list)
    ls = result[0]
    assert isinstance(ls, T.List)
    assert len(ls.items) == 3
    for item in ls.items:
        assert isinstance(item, T.ListItem)

    result, messages = await harness.invoke(
        "kernel_execute", instance=ki.instance, code="abc"
    )
    assert messages != []
    m = messages[0]
    assert isinstance(m, T.ExecutionMessage)
    assert m.message == "Invalid input"
