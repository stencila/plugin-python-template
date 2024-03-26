from stencila_plugin.kernel import KernelInstance
from stencila_plugin.testing import Harness
from stencila_types import types as T


async def test_kernel(harness: Harness):
    """This will be run multiple times under the different test harnesses."""
    result = await harness.send_rpc("kernel_start", kernel="echo-python")

    # TODO: Fix the typing problems here.
    ki = KernelInstance(**result)  # type: ignore

    result, messages = await harness.invoke(
        "kernel_execute", instance=ki.instance, code="This is a message"
    )

    for r in result:
        assert isinstance(r, T.Paragraph)

    for m in messages:
        assert m.level == T.MessageLevel.Info
