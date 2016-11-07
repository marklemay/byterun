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

    def test_slice_assignment(self):
        self.assert_ok("""
            l = list(range(10))
            l[3:8] = ["x"]
            print(l)
            """)
        self.assert_ok("""
            l = list(range(10))
            l[:8] = ["x"]
            print(l)
            """)
        self.assert_ok("""
            l = list(range(10))
            l[3:] = ["x"]
            print(l)
            """)
        self.assert_ok("""
            l = list(range(10))
            l[:] = ["x"]
            print(l)
            """)

    def test_slice_deletion(self):
        self.assert_ok("""
            l = list(range(10))
            del l[3:8]
            print(l)
            """)
        self.assert_ok("""
            l = list(range(10))
            del l[:8]
            print(l)
            """)
        self.assert_ok("""
            l = list(range(10))
            del l[3:]
            print(l)
            """)
        self.assert_ok("""
            l = list(range(10))
            del l[:]
            print(l)
            """)
        self.assert_ok("""
            l = list(range(10))
            del l[::2]
            print(l)
            """)

    def test_unary_operators(self):
        self.assert_ok("""
            x = 8
            print(not x)
            """)

    def test_attributes(self):
        self.assert_ok("""
            l = lambda: 1   # Just to have an object...
            l.foo = 17
            print(hasattr(l, "foo"), l.foo)
            del l.foo
            print(hasattr(l, "foo"))
            """)

    def test_callback(self):
        self.assert_ok("""
            def lcase(s):
                return s.lower()
            l = ["xyz", "ABC"]
            l.sort(key=lcase)
            print(l)
            assert l == ["ABC", "xyz"]
            """)

    def test_unpacking(self):
        self.assert_ok("""
            a, b, c = (1, 2, 3)
            assert a == 1
            assert b == 2
            assert c == 3
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


class TestLoops(vmtest.VmTestCase):
    def test_for(self):
        self.assert_ok("""
            for i in range(10):
                print(i)
            print("done")
            """)

    def test_break(self):
        self.assert_ok("""
            for i in range(10):
                print(i)
                if i == 7:
                    break
            print("done")
            """)
