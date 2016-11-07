"""Test functions etc, for Byterun."""

from __future__ import print_function
from . import vmtest
import six




class TestFunctions(vmtest.VmTestCase):
    def test_functions(self):
        self.assert_ok("""
            def fn(a, b=17, c="Hello", d=[]):
                d.append(99)
                print(a, b, c, d)
            fn(1)
            fn(2, 3)
            fn(3, c="Bye")
            fn(4, d=["What?"])
            fn(5, "b", "c")
            """)

    def test_nested_names(self):
        self.assert_ok("""
            def one():
                x = 1
                def two():
                    x = 2
                    print(x)
                two()
                print(x)
            one()
            """)

