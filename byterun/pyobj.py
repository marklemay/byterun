"""Implementations of Python fundamental objects for Byterun."""

import collections
import inspect
import types

from typing import Dict, Any, NamedTuple, Optional, List, Union, Tuple
# import code as Code  # TODO: pretty sure this isn't the right thing....

# from .pyvm2 import VirtualMachine

import six


# TODO: why int?
def make_cell(value: int) -> 'cell':
    assert type(value) == int, (value, type(value))
    # Thanks to Alex Gaynor for help with this bit of twistiness.
    # Construct an actual cell object by creating a closure right here,
    # and grabbing the cell object out of the function we create.
    fn = (lambda x: lambda: x)(value)

    c = fn.__closure__[0]
    assert type(c).__name__ == "cell", (c, type(c))
    return c


class Function(object):
    __slots__ = [
        'func_code', 'func_name', 'func_defaults', 'func_globals',
        'func_locals', 'func_dict', 'func_closure',
        '__name__', '__dict__', '__doc__',
        '_vm', '_func',
    ]

    def __init__(self,
                 name: str,
                 code: "code",
                 globs: Dict[str, Any],
                 defaults: List[Any],
                 closure,
                 vm: "VirtualMachine") -> None:  # TODO: dumb language can't handle circular dependencies!!!!!!!
        assert type(name) == str
        assert type(code).__name__ == "code"
        assert (type(globs) == dict and all(type(key) == str for key in globs)), globs
        assert type(defaults) == list, (defaults, type(defaults))
        # assert closure is not None, ("hi",closure,type(closure)) # TODO: WFT?
        assert type(vm).__name__ == "VirtualMachine"

        self._vm = vm
        self.func_code = code
        self.func_name = self.__name__ = name or code.co_name
        self.func_defaults = tuple(defaults)
        self.func_globals = globs
        self.func_locals = self._vm.frame.f_locals
        self.__dict__ = {}
        self.func_closure = closure
        self.__doc__ = code.co_consts[0] if code.co_consts else None

        # Sometimes, we need a real Python function.  This is for that.
        kw = {
            'argdefs': self.func_defaults,
        }
        if closure:
            kw['closure'] = tuple(make_cell(0) for _ in closure)
        self._func = types.FunctionType(code, globs, **kw)

    def __repr__(self):  # pragma: no cover
        return '<Function %s at 0x%08x>' % (
            self.func_name, id(self)
        )

    def __get__(self, instance, owner):
        if instance is not None:
            return Method(instance, owner, self)

        return self

    def __call__(self, *args, **kwargs):

        callargs = inspect.getcallargs(self._func, *args, **kwargs)

        frame = self._vm.make_frame(
            self.func_code, callargs, self.func_globals, {}
        )
        CO_GENERATOR = 32  # flag for "this code uses yield"
        if self.func_code.co_flags & CO_GENERATOR:
            gen = Generator(frame, self._vm)
            frame.generator = gen
            retval = gen
        else:
            retval = self._vm.run_frame(frame)
        return retval


class Method(object):
    pass
    # def __init__(self,
    #              obj,
    #              _class,
    #              func) -> None:
    #
    #     assert False  # , (obj,type(obj))
    #
    #     self.im_self = obj
    #     self.im_class = _class
    #     self.im_func = func
    #
    # def __repr__(self):  # pragma: no cover
    #     assert False
    #     name = "%s.%s" % (self.im_class.__name__, self.im_func.func_name)
    #     if self.im_self is not None:
    #         return '<Bound Method %s of %s>' % (name, self.im_self)
    #     else:
    #         return '<Unbound Method %s>' % (name,)
    #
    # def __call__(self, *args, **kwargs):
    #     assert False
    #     if self.im_self is not None:
    #         return self.im_func(self.im_self, *args, **kwargs)
    #     else:
    #         return self.im_func(*args, **kwargs)


class Cell(object):
    """A fake cell for closures.

    Closures keep names in scope by storing them not in a frame, but in a
    separate object called a cell.  Frames share references to cells, and
    the LOAD_DEREF and STORE_DEREF opcodes get and set the value from cells.

    This class acts as a cell, though it has to jump through two hoops to make
    the simulation complete:

        1. In order to create actual FunctionType functions, we have to have
           actual cell objects, which are difficult to make. See the twisty
           double-lambda in __init__.

        2. Actual cell objects can't be modified, so to implement STORE_DEREF,
           we store a one-element list in our cell, and then use [0] as the
           actual value.

    """

    def __init__(self, value: Any) -> None:
        self.contents = value

    def get(self) -> Any:
        return self.contents

    def set(self, value: Any) -> None:
        self.contents = value


Block = NamedTuple("Block", [('type', str), ('handler', Optional[int]), ('level', Any)])  # TODO: level ????


# Block = collections.namedtuple("Block", "type, handler, level")


class Frame(object):
    def __init__(self,
                 f_code: "code",
                 f_globals: Dict[str, Any],
                 f_locals: Dict[str, Any],
                 f_back: None
                 ) -> None:  # TODO: f_code is f_back?

        assert type(f_code).__name__ == "code"
        assert (type(f_globals) == dict and all(type(key) == str for key in f_globals)), f_globals
        assert (type(f_locals) == dict and all(type(key) == str for key in f_locals)), f_locals
        assert f_back is not False, (f_back, type(f_back))

        self.f_code = f_code
        self.f_globals = f_globals
        self.f_locals = f_locals
        self.f_back = f_back
        self.stack = []  # TODO: what is this GD type?
        if f_back:  # TODO: what? also why?
            self.f_builtins = f_back.f_builtins
        else:
            self.f_builtins = f_locals['__builtins__']
            if hasattr(self.f_builtins, '__dict__'):
                self.f_builtins = self.f_builtins.__dict__

        self.f_lineno = f_code.co_firstlineno  # TODO type!!!!
        self.f_lasti = 0  # type:int
        # TODO: i assume? TODO: but for real wtf is this
        if f_code.co_cellvars:
            self.cells = {}
            if not f_back.cells:
                f_back.cells = {}
            for var in f_code.co_cellvars:
                # Make a cell for the variable in our locals, or None.
                cell = Cell(self.f_locals.get(var))
                f_back.cells[var] = self.cells[var] = cell
        else:
            self.cells = None

        if f_code.co_freevars:
            if not self.cells:
                self.cells = {}
            for var in f_code.co_freevars:
                assert self.cells is not None
                assert f_back.cells, "f_back.cells: %r" % (f_back.cells,)
                self.cells[var] = f_back.cells[var]

        self.block_stack = []  # TODO: what is this
        self.generator = None

    def __repr__(self):  # pragma: no cover
        return '<Frame at 0x%08x: %r @ %d>' % (
            id(self), self.f_code.co_filename, self.f_lineno
        )

    def line_number(self):
        """Get the current line number the frame is executing."""

        assert False

        # We don't keep f_lineno up to date, so calculate it based on the
        # instruction address and the line number table.
        lnotab = self.f_code.co_lnotab
        byte_increments = six.iterbytes(lnotab[0::2])
        line_increments = six.iterbytes(lnotab[1::2])

        byte_num = 0
        line_num = self.f_code.co_firstlineno

        for byte_incr, line_incr in zip(byte_increments, line_increments):
            byte_num += byte_incr
            if byte_num > self.f_lasti:
                break
            line_num += line_incr

        return line_num


class Generator(object):
    def __init__(self,
                 g_frame: Frame,
                 vm: "VirtualMachine"
                 ) -> None:

        assert type(g_frame) == Frame
        assert type(vm).__name__ == "VirtualMachine"

        self.gi_frame = g_frame
        self.vm = vm
        self.started = False
        self.finished = False

    def __iter__(self):
        return self

    def next(self) -> None:
        return self.send()

    def send(self, value: None = None) -> Union[int, Tuple[int, int, int], Any]:
        assert value is None

        if not self.started and value is not None:
            raise TypeError("Can't send non-None value to a just-started generator")
        self.gi_frame.stack.append(value)
        self.started = True
        val = self.vm.resume_frame(self.gi_frame)
        if self.finished:
            raise StopIteration(val)

        # assert type(val) == int, (val, type(val))
        return val

    __next__ = next
