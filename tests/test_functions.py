"""Test functions etc, for Byterun."""

from __future__ import print_function
from . import vmtest
import six


class TestFunctions(vmtest.VmTestCase):
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
