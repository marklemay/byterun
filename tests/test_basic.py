"""Basic tests for Byterun."""

from __future__ import print_function
from . import vmtest

import six


class TestIt(vmtest.VmTestCase):
    def test_constant(self):
        self.assert_ok("17")

    def test_multi_print(self):
        self.assert_ok("""
        print("hi")
        print("nice to meet you")
        print("bye")
        """)

    def test_unary_operators(self):
        self.assert_ok("""
            x = 8
            print(not x)
            """)


    def test_jump_if_true_or_pop(self):
        self.assert_ok("""
            def f(a, b):
                return a or b
            assert f(17, 0) == 17
            assert f(0, 23) == 23
            assert f(0, "") == ""
            """)

    def test_jump_if_false_or_pop(self):
        self.assert_ok("""
            def f(a, b):
                return not(a and b)
            print(f(17, 0))
            print(f(0, 23))
            print(f(0, ""))
            print(f(17, 23))
            """)

    def test_pop_jump_if_true(self):
        self.assert_ok("""
            def f(a):
                if not a:
                    return 'foo'
                else:
                    return 'bar'
            assert f(0) == 'foo'
            assert f(1) == 'bar'
            """)
