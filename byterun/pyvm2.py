"""A pure-Python Python bytecode interpreter."""
# Based on:
# pyvm2 by Paul Swartz (z3p), from http://www.twistedmatrix.com/users/z3p/

# TODO: with internet
# branch
# get the imports
# get tests running
# remove python 2 support,
#      can remove dependency on six?

# TODO: wihout internest
# begin typing
# use this to drive the type operator
# how would modles work, need to define infinite precision ints and such
# how to keep track of practical things, like stack overflows
# add messages to asserts

from __future__ import print_function, division
import dis
import inspect
import linecache
import logging
import operator
import sys

from typing import Optional, Dict, Any, Tuple, Iterable, Union, List, Callable
# import range_iterator

# import code as Code

import six
from six.moves import reprlib

from .pyobj import Frame, Function

log = logging.getLogger(__name__)

# Create a repr that won't overflow.
repr_obj = reprlib.Repr()
repr_obj.maxother = 120
repper = repr_obj.repr


class VirtualMachineError(Exception):
    """For raising errors in the operation of the VM."""
    pass


class VirtualMachine(object):
    def __init__(self):
        # The call stack of frames.
        self.frames = []  # type: List[Frame]
        # The current frame.
        self.frame = None  # type: Optional[Frame]
        self.return_value = None
        self.last_exception = None

    def top(self) -> Union[Function, Any]:  # TODO: WTF??? #,range_iterator]:  # TODO: indexing like this just throws an exception, right? Optional[Frame]
        """Return the value at the top of the stack, with no changes."""
        # assert type(self.frame.stack[-1]) == Function, type(self.frame.stack[-1])
        return self.frame.stack[-1]

    def pop(self, i: int = 0) -> Union[Function, Any]:  # TODO: WTF???
        """Pop a value from the stack.

        Default to the top of the stack, but `i` can be a count from the top
        instead.
        """
        assert type(i) == int
        return self.frame.stack.pop(-1 - i)

    def push(self, *vals: Iterable[Union[int, bool, Any]]):  # TODO: also code triples
        """Push values onto the value stack."""
        assert issubclass(type(vals), Iterable[int])
        # assert all(type(val) == int for val in vals), list(vals) #becuse is subclass does not get this

        self.frame.stack.extend(vals)

    def popn(self, n: int) -> List[Any]:
        """Pop a number of values from the value stack.

        A list of `n` values is returned, the deepest value first.
        """
        assert type(n) == int

        if n:
            ret = self.frame.stack[-n:]
            self.frame.stack[-n:] = []
            return ret
        else:
            return []

    def jump(self, jump: int) -> None:
        """Move the bytecode pointer to `jump`, so it will execute next."""
        assert type(jump) == int

        self.frame.f_lasti = jump

    def make_frame(self,
                   code,  #: TODO: what is the type that compile returns
                   callargs: Optional[Dict[str, Any]] = {},  # TODO: WTF is this?
                   f_globals: Optional[Dict[str, Any]] = None,  # TODO: not sure we can make a more specific type
                   f_locals: Optional[Dict[str, Any]] = None
                   ) -> Frame:
        assert type(callargs) == dict and all(type(key) == str for key in callargs)
        assert f_globals is None or (type(f_globals) == dict and all(type(key) == str for key in f_globals))
        assert f_locals is None or (type(f_locals) == dict and all(type(key) == str for key in f_locals))

        log.info("make_frame: code=%r, callargs=%s" % (code, repper(callargs)))
        if f_globals is not None:
            f_globals = f_globals
            if f_locals is None:
                f_locals = f_globals
        elif self.frames:
            f_globals = self.frame.f_globals
            f_locals = {}
        else:
            f_globals = f_locals = {
                '__builtins__': __builtins__,
                '__name__': '__main__',
                '__doc__': None,
                '__package__': None,
            }
        f_locals.update(callargs)
        frame = Frame(code, f_globals, f_locals, self.frame)
        return frame

    def push_frame(self, frame: Frame) -> None:
        self.frames.append(frame)
        self.frame = frame

    def pop_frame(self) -> None:
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None

    def run_code(self,
                 code,  #: Code, ????
                 f_globals: Optional[Dict[str, Any]] = None,
                 f_locals: Optional[Dict[str, Any]] = None
                 ) -> None:  # does't seem right, but whatevs?
        assert f_globals is None or (type(f_globals) == dict and all(type(key) == str for key in f_globals))
        assert f_locals is None or (type(f_locals) == dict and all(type(key) == str for key in f_locals))

        frame = self.make_frame(code, f_globals=f_globals, f_locals=f_locals)
        val = self.run_frame(frame)
        # Check some invariants
        if self.frames:  # pragma: no cover
            raise VirtualMachineError("Frames left over!")
        if self.frame and self.frame.stack:  # pragma: no cover
            raise VirtualMachineError("Data left on stack! %r" % self.frame.stack)

        assert val is None, (val, type(val))
        return val

    def parse_byte_and_args(self) -> Tuple[str, Any, int]:  # TODO: code in the middle of that
        """ Parse 1 - 3 bytes of bytecode into
        an instruction and optionally arguments."""
        f = self.frame
        opoffset = f.f_lasti
        byteCode = f.f_code.co_code[opoffset]  # type: int
        assert type(byteCode) == int

        f.f_lasti += 1
        byteName = dis.opname[byteCode]
        arg = None  # type: Optional[bytes]
        arguments = []

        if byteCode >= dis.HAVE_ARGUMENT:
            arg, f.f_lasti = f.f_code.co_code[f.f_lasti:f.f_lasti + 2], f.f_lasti + 2
            assert type(arg) == bytes, type(arg)

            intArg = arg[0] + (arg[1] << 8)
            if byteCode in dis.hasconst:
                arg = f.f_code.co_consts[intArg]
            elif byteCode in dis.hasname:
                arg = f.f_code.co_names[intArg]
            elif byteCode in dis.hasjrel:
                arg = f.f_lasti + intArg
            elif byteCode in dis.hasjabs:
                arg = intArg
            elif byteCode in dis.haslocal:
                arg = f.f_code.co_varnames[intArg]
            else:
                arg = intArg
            arguments = [arg]

        assert type(byteName) == str, (byteName, type(byteName))
        # assert False, (arguments, type(arguments)) #TODO:object triples
        assert type(opoffset) == int, (opoffset, type(opoffset))

        return byteName, arguments, opoffset

    def log(self,
            byteName: str,
            arguments,  # code
            opoffset: int
            ) -> None:
        """ Log arguments, block stack, and data stack for each opcode."""

        assert type(byteName) == str, (byteName, type(byteName))
        # assert False, (arguments, type(arguments)) #TODO:object triples
        assert type(opoffset) == int, (opoffset, type(opoffset))

        op = "%d: %s" % (opoffset, byteName)
        if arguments:
            op += " %r" % (arguments[0],)
        indent = "    " * (len(self.frames) - 1)
        stack_rep = repper(self.frame.stack)
        block_stack_rep = repper(self.frame.block_stack)

        log.info("  %sdata: %s" % (indent, stack_rep))
        log.info("  %sblks: %s" % (indent, block_stack_rep))
        log.info("%s%s" % (indent, op))

    def dispatch(self,
                 byteName: str,
                 arguments: List[Any]  # list of code
                 ) -> Optional[str]:
        """ Dispatch by bytename to the corresponding methods.
        Exceptions are caught and set on the virtual machine."""
        assert type(byteName) == str, (byteName, type(byteName))
        assert type(arguments) == list, (arguments, type(arguments))

        why = None  # type: Optional[str]
        try:
            if byteName.startswith('UNARY_'):
                self.unaryOperator(byteName[6:])
            elif byteName.startswith('BINARY_'):
                self.binaryOperator(byteName[7:])
            elif byteName.startswith('INPLACE_'):
                self.inplaceOperator(byteName[8:])
            elif 'SLICE+' in byteName:
                self.sliceOperator(byteName)
            else:
                # dispatch
                bytecode_fn = getattr(self, 'byte_%s' % byteName, None)
                if not bytecode_fn:  # pragma: no cover
                    raise VirtualMachineError(
                        "unknown bytecode type: %s" % byteName
                    )
                why = bytecode_fn(*arguments)

        except:
            # deal with exceptions encountered while executing the op.
            self.last_exception = sys.exc_info()[:2] + (None,)
            log.exception("Caught exception during execution")
            why = 'exception'

        assert why is None or type(why) == str, (why, type(why))
        return why

    # TODO: see usage!
    def run_frame(self, frame: Frame) -> Any:  # can return anything!!!
        """Run a frame until it returns (somehow).
        Exceptions are raised, the return value is returned.
        """
        assert type(frame) == Frame
        self.push_frame(frame)
        while True:
            byteName, arguments, opoffset = self.parse_byte_and_args()
            if log.isEnabledFor(logging.INFO):
                self.log(byteName, arguments, opoffset)

            # When unwinding the block stack, we need to keep track of why we
            # are doing it.
            why = self.dispatch(byteName, arguments)
            if why == 'exception':
                # TODO: ceval calls PyTraceBack_Here, not sure what that does.
                pass

            if why == 'reraise':
                why = 'exception'

            if why != 'yield':
                while why and frame.block_stack:
                    # Deal with any block management we need to do.
                    why = self.manage_block_stack(why)

            if why:
                break

        # TODO: handle generator exception state

        self.pop_frame()

        if why == 'exception':
            six.reraise(*self.last_exception)

        # assert self.return_value is None, (self.return_value, type(self.return_value))
        return self.return_value

    ## Stack manipulation

    def byte_LOAD_CONST(self, const):
        self.push(const)

    def byte_POP_TOP(self):
        self.pop()

    ## Names

    def byte_LOAD_NAME(self, name: str) -> None:
        assert type(name) == str

        frame = self.frame
        if name in frame.f_locals:
            val = frame.f_locals[name]
        elif name in frame.f_globals:
            val = frame.f_globals[name]
        elif name in frame.f_builtins:  # need this for print!
            val = frame.f_builtins[name]
        else:
            raise NameError("name '%s' is not defined" % name)
        self.push(val)

    def byte_STORE_NAME(self, name: str) -> None:
        assert type(name) == str
        self.frame.f_locals[name] = self.pop()

    def byte_LOAD_FAST(self, name: str) -> None:
        assert type(name) == str

        if name in self.frame.f_locals:
            val = self.frame.f_locals[name]
        else:
            raise UnboundLocalError(
                "local variable '%s' referenced before assignment" % name
            )
        self.push(val)

    def byte_STORE_FAST(self, name: str) -> None:
        assert type(name) == str

        self.frame.f_locals[name] = self.pop()

    def byte_LOAD_GLOBAL(self, name: str) -> None:
        assert type(name) == str

        f = self.frame
        if name in f.f_globals:
            val = f.f_globals[name]
        elif name in f.f_builtins:
            val = f.f_builtins[name]
        else:
            raise NameError("global name '%s' is not defined" % name)
        self.push(val)

    ## Operators

    UNARY_OPERATORS = {
        # 'POSITIVE': operator.pos,
        # 'NEGATIVE': operator.neg,
        'NOT': operator.not_,
        # 'CONVERT': repr,
        # 'INVERT': operator.invert,
    }

    # TODO:
    def unaryOperator(self, op: str) -> None:
        assert type(op) == str, op

        x = self.pop()
        self.push(self.UNARY_OPERATORS[op](x))

    BINARY_OPERATORS = {
        'AND': operator.and_,
        'XOR': operator.xor,
        'OR': operator.or_,
    }

    def binaryOperator(self, op: str) -> None:
        assert type(op) == str, op

        x, y = self.popn(2)
        self.push(self.BINARY_OPERATORS[op](x, y))

    def byte_COMPARE_OP(self, opnum: int) -> None:
        assert type(opnum) == int, opnum

        x, y = self.popn(2)

        if opnum == 2:
            self.push(x == y)
        elif opnum == 3:
            self.push(x != y)
        else:
            assert False

    ## Jumps #TODO: more jumps

    def byte_POP_JUMP_IF_TRUE(self, jump: int) -> None:
        assert type(jump) == int, jump
        val = self.pop()
        if val:
            self.jump(jump)

    def byte_JUMP_IF_TRUE_OR_POP(self, jump: int) -> None:
        assert type(jump) == int, jump
        val = self.top()
        if val:
            self.jump(jump)
        else:
            self.pop()

    def byte_JUMP_IF_FALSE_OR_POP(self, jump: int) -> None:
        assert type(jump) == int, jump
        val = self.top()
        if not val:
            self.jump(jump)
        else:
            self.pop()

    ## Functions

    def byte_MAKE_FUNCTION(self, argc: int) -> None:
        assert type(argc) == int

        name = self.pop()  # type: str
        assert type(name) == str

        code = self.pop()  # type: code
        # assert type(code) == str,code

        defaults = self.popn(argc)  # type: List
        assert type(defaults) == list, (defaults, type(defaults))

        globs = self.frame.f_globals
        assert type(globs) == dict

        fn = Function(name, code, globs, defaults, self)
        self.push(fn)

    def byte_CALL_FUNCTION(self, arg: int) -> None:
        assert type(arg) == int

        lenKw, lenPos = divmod(arg, 256)  # type: (int,int)
        namedargs = {}
        for i in range(lenKw):
            key, val = self.popn(2)
            namedargs[key] = val
        posargs = self.popn(lenPos)

        func = self.pop()  # type: Callable
        # assert type(func) == Function,func

        retval = func(*posargs, **namedargs)
        self.push(retval)

    def byte_RETURN_VALUE(self):
        self.return_value = self.pop()
        if self.frame.generator:
            self.frame.generator.finished = True
        return "return"

    ## And the rest...

    ## Printing

    # NEED TO KEEP THIS AROUND so testing can happen, becuase there's no way to get stuff out eval

    def byte_PRINT_ITEM(self) -> None:
        item = self.pop()
        self.print_item(item)

    def byte_PRINT_ITEM_TO(self) -> None:
        to = self.pop()
        item = self.pop()
        self.print_item(item, to)

    def byte_PRINT_NEWLINE(self) -> None:
        self.print_newline()

    def byte_PRINT_NEWLINE_TO(self) -> None:
        to = self.pop()
        self.print_newline(to)
