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

    def test_for_loop(self):
        self.assert_ok("""
            out = ""
            for i in range(5):
                out = out + str(i)
            print(out)
            """)

    def test_inplace_operators(self):
        self.assert_ok("""
            x, y = 2, 3
            x **= y
            assert x == 8 and y == 3
            x *= y
            assert x == 24 and y == 3
            x //= y
            assert x == 8 and y == 3
            x %= y
            assert x == 2 and y == 3
            x += y
            assert x == 5 and y == 3
            x -= y
            assert x == 2 and y == 3
            x <<= y
            assert x == 16 and y == 3
            x >>= y
            assert x == 2 and y == 3

            x = 0x8F
            x &= 0xA5
            assert x == 0x85
            x |= 0x10
            assert x == 0x95
            x ^= 0x33
            assert x == 0xA6
            """)

    def test_inplace_division(self):
        self.assert_ok("""
            x, y = 24, 3
            x /= y
            assert x == 8.0 and y == 3
            assert isinstance(x, float)
            x /= y
            assert x == (8.0/3.0) and y == 3
            assert isinstance(x, float)
            """)

    def test_slice(self):
        self.assert_ok("""
            print("hello, world"[3:8])
            """)
        self.assert_ok("""
            print("hello, world"[:8])
            """)
        self.assert_ok("""
            print("hello, world"[3:])
            """)
        self.assert_ok("""
            print("hello, world"[:])
            """)
        self.assert_ok("""
            print("hello, world"[::-1])
            """)
        self.assert_ok("""
            print("hello, world"[3:8:2])
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

    def test_subscripting(self):
        self.assert_ok("""
            l = list(range(10))
            print("%s %s %s" % (l[0], l[3], l[9]))
            """)
        self.assert_ok("""
            l = list(range(10))
            l[5] = 17
            print(l)
            """)
        self.assert_ok("""
            l = list(range(10))
            del l[5]
            print(l)
            """)

    def test_unary_operators(self):
        self.assert_ok("""
            x = 8
            print(-x, ~x, not x)
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

    def test_exec_statement(self):
        self.assert_ok("""
            g = {}
            exec("a = 11", g, g)
            assert g['a'] == 11
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
            assert f(17, 0) is True
            assert f(0, 23) is True
            assert f(0, "") is True
            assert f(17, 23) is False
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

    def test_continue(self):
        # fun fact: this doesn't use CONTINUE_LOOP
        self.assert_ok("""
            for i in range(10):
                if i % 3 == 0:
                    continue
                print(i)
            print("done")
            """)


class TestComparisons(vmtest.VmTestCase):
    def test_in(self):
        self.assert_ok("""
            assert "x" in "xyz"
            assert "x" not in "abc"
            assert "x" in ("x", "y", "z")
            assert "x" not in ("a", "b", "c")
            """)

    def test_less(self):
        self.assert_ok("""
            assert 1 < 3
            assert 1 <= 2 and 1 <= 1
            assert "a" < "b"
            assert "a" <= "b" and "a" <= "a"
            """)

    def test_greater(self):
        self.assert_ok("""
            assert 3 > 1
            assert 3 >= 1 and 3 >= 3
            assert "z" > "a"
            assert "z" >= "a" and "z" >= "z"
            """)
