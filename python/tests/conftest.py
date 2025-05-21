from _pytest.nodes import Item
# this supposedly shortens the long traceback
def pytest_exception_interact(node, call, report):
    if not isinstance(node, Item):
        return
        
    excinfo = call.excinfo
    example_path = getattr(node, "funcargs", {}).get("example")
    if example_path:
        excinfo.traceback.cut(path=example_path)
    report.longrepr = node.repr_failure(excinfo)

import matplotlib
matplotlib.use('Agg')
