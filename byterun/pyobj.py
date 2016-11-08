"""Implementations of Python fundamental objects for Byterun."""

import collections
import inspect
import types

from typing import Dict, Any, NamedTuple, Optional, List, Union, Tuple



class Function(object):
    __slots__ = [
        'func_code', 'func_name', 'func_defaults', 'func_globals',
        'func_locals', 'func_dict',
        '__name__', '__dict__', '__doc__',
        '_vm', '_func',
    ]

    def __init__(self,
                 name: str,
                 code: "code",
                 globs: Dict[str, Any],
                 defaults: List[Any],
                 vm: "VirtualMachine") -> None:  # TODO: dumb language can't handle circular dependencies!!!!!!!
        assert type(name) == str
        assert type(code).__name__ == "code"
        assert (type(globs) == dict and all(type(key) == str for key in globs)), globs
        assert type(defaults) == list, (defaults, type(defaults))
        assert type(vm).__name__ == "VirtualMachine"

        self._vm = vm
        self.func_code = code
        self.func_name = self.__name__ = name or code.co_name
        self.func_defaults = tuple(defaults)
        self.func_globals = globs
        self.func_locals = self._vm.frame.f_locals
        self.__dict__ = {}
        # self.func_closure = closure
        self.__doc__ = code.co_consts[0] if code.co_consts else None

        # Sometimes, we need a real Python function.  This is for that.
        kw = {
            'argdefs': self.func_defaults,
        }
        self._func = types.FunctionType(code, globs, **kw)

    def __repr__(self):  # pragma: no cover
        return '<Function %s at 0x%08x>' % (
            self.func_name, id(self)
        )


    def __call__(self, *args, **kwargs):

        callargs = inspect.getcallargs(self._func, *args, **kwargs)

        frame = self._vm.make_frame(
            self.func_code, callargs, self.func_globals, {}
        )

        retval = self._vm.run_frame(frame)
        return retval


Block = NamedTuple("Block", [('type', str), ('handler', Optional[int]), ('level', int)])


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

        self.block_stack = []  # TODO: what is this
        self.generator = None


