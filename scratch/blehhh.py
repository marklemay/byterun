# def fn():
#     fooey
#
#
# fn()

#NameError: name 'fooey' is not defined
from typing import Iterable

class Thing(object):
    z = 17

    def __init__(self):
        self.x = 23


t = Thing()
print(Thing.z)
print(t.z)
print(t.x)

v = 2

assert issubclass(type(v), Iterable[int])
