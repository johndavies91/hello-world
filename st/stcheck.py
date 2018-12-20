from pytest import * # pylint: disable=unused-wildcard-import,wildcard-import,redefined-builtin
from unittest.mock import Mock
import gc

# hack from https://github.com/pytest-dev/pytest/issues/1830 maybe keep it in stcheck
from contextlib import contextmanager
tmp = raises
def raises(error): # pylint: disable=function-redefined
    """Wrapper around pytest.raises to support None."""
    if error:
        if isinstance(error, Exception):
            match = str(error)
            error = error.__class__
        else:
            match = None
        return tmp(error, match=match)

    @contextmanager
    def not_raises():
        try:
            yield
        except Exception as e:
            raise e
    return not_raises()

def createMockMethod(func):
    class mockMethod():
        def __init__(self):
            if "." in func:
                module = func.split(".")[0]
                globals()[module] = __import__(module)
            exec("self.original = %s"%func) in globals(), locals() # pylint: disable=expression-not-assigned,exec-used

        def __enter__(self):
            return Mock()

        def __exit__(self, typ, value, tb):
            exec("%s = self.original"%(func)) in globals(), locals() # pylint: disable=expression-not-assigned,exec-used
            gc.collect(generation=1) # Explicitly clear up the mock stuff, otherwise if another test uses it straight away we might get an unexpected slowdown when GC kicks in. generation=1 is much faster than the default
    return mockMethod()
