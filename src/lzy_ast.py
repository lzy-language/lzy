r"""
 __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
lzy - laziest programming language ever
created by gkugfk3 with ♡

licensed under MPL 2.0: https://www.mozilla.org/en-US/MPL/2.0/


# lzy_ast.py
# all ast node classes
"""

# literals

class NumberNode:
    def __init__(self, value):      self.value = value

class StringNode:
    def __init__(self, value):      self.value = value

class NullNode:
    pass

class NaNNode:
    pass

class BinNode:
    def __init__(self, value):      self.value = value


# variables

class VarNode:
    # variable reference e.g. x
    def __init__(self, name):       self.name = name

class AssignNode:
    # variable assignment e.g. x : int = 5
    def __init__(self, name, expr, type_hint=None, strict=False, safe=False):
        self.name      = name
        self.expr      = expr
        self.type_hint = type_hint
        self.strict    = strict
        self.safe      = safe


# declarations

class StrictNullNode:
    # the "strict null" file-level strictness declaration
    pass


# built-ins

class PrintNode:
    def __init__(self, expr, raw=False):
        self.expr = expr
        self.raw  = raw   # true for printl
        
class TimerStartNode:
    # _start  or  _start "name"
    def __init__(self, name=None):  self.name = name

class TimerEndNode:
    # _end  or  _end "name"
    def __init__(self, name=None):  self.name = name

class SleepNode:
    # _sleep(seconds)
    def __init__(self, expr):   self.expr = expr

# expressions

class BinaryOpNode:
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op
        self.right = right

class UnaryOpNode:
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand

class RangeNode:
    # 0..10 range literal used in loop
    def __init__(self, start, end):
        self.start = start
        self.end   = end
        
class ArrayNode:
    # [1, 2, 3] - array literal
    def __init__(self, elements):   self.elements = elements

class IndexNode:
    # arr[0] - array indexing
    def __init__(self, array, index):
        self.array = array
        self.index = index

class IndexAssignNode:
    # arr[i] = value
    def __init__(self, array, index, expr):
        self.array = array
        self.index = index
        self.expr  = expr


# blocks and control flow

class BlockNode:
    # sequence of statements inside { }
    # does NOT create a new scope
    def __init__(self, stmts):      self.stmts = stmts

class IfNode:
    def __init__(self, condition, body, elseifs=None, else_body=None):
        self.condition = condition
        self.body      = body
        self.elseifs   = elseifs or [] # list of (condition, body) tuples
        self.else_body = else_body


# loops

class LoopNode:
    # loop arr as item ~ { }   or   loop 0..10 as i ~ { }
    def __init__(self, iterable, var_name, body):
        self.iterable = iterable    # expression: array var or RangeNode
        self.var_name = var_name    # loop variable name string
        self.body     = body

class ForeverNode:
    # forever ~ { }  =  basically while True
    def __init__(self, body):       self.body = body

class DoNode:
    # do <condition> ~ { }  = just while <condition>
    def __init__(self, condition, body):
        self.condition = condition
        self.body      = body

class StopNode:
    # stop = break
    pass

class SkipNode:
    # skip = continue
    pass
    
# functions

class FunctionDefNode:
    # fn name(params) :: return_type ~ { body }
    def __init__(self, name, params, return_type, body):
        self.name        = name
        self.params      = params # list of (param_name, type_hint_or_None)
        self.return_type = return_type # optional return type hint string
        self.body        = body

class FunctionCallNode:
    # name(args)
    def __init__(self, name, args):
        self.name = name
        self.args = args # list of expression nodes

class ReturnNode:
    # return expr
    def __init__(self, expr):   self.expr = expr


# string interpolation

class InterpStringNode:
    # `hello ${name}!` - list of StringNode or expression nodes
    def __init__(self, parts):   self.parts = parts


# dot access and method calls

class FieldAccessNode:
    # obj.field
    def __init__(self, obj, field):
        self.obj   = obj
        self.field = field

class MethodCallNode:
    # obj.method(args)
    def __init__(self, obj, method, args):
        self.obj    = obj
        self.method = method
        self.args   = args


# lazywords
# (function reskin)

class LazyDefNode:
    # lazy name|params| :: return_type ~ { body }
    def __init__(self, name, params, return_type, body):
        self.name        = name
        self.params      = params # list of (param_name, type_hint_or_None)
        self.return_type = return_type
        self.body        = body

class LazyCallNode:
    # name|args|
    def __init__(self, name, args):
        self.name = name
        self.args = args


# misc


class CastNode:
    # <float64>x  -  explicit cast, no coercion warnings
    __slots__ = ("target_type", "expr")
    def __init__(self, target_type, expr):
        self.target_type = target_type
        self.expr        = expr
        
class NonstrictNode:
    # nonstrict ~ { ... } - temporarily disables strict_null for this block
    def __init__(self, body):       self.body = body


# node types that are "statements" and should not auto-print in repl

STMT_NODES = (
    AssignNode,
    PrintNode,
    StrictNullNode,
    IfNode,
    BlockNode,
    LoopNode,
    ForeverNode,
    DoNode,
    StopNode,
    SkipNode,
    TimerStartNode,
    NonstrictNode,
    TimerEndNode,
    SleepNode,
    FunctionDefNode,
    FunctionCallNode,
    ReturnNode,
    IndexAssignNode,
    LazyDefNode,
    LazyCallNode,
    MethodCallNode,
)
