r"""
 __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
lzy - laziest programming language ever
created by gkugfk3 with ♡

licensed under MPL 2.0: https://www.mozilla.org/en-US/MPL/2.0/


# lzy_eval.py
# walks the ast and executes it
"""

import math
import time
from lzy_ast import (
    NumberNode, StringNode, NullNode, NaNNode, BinNode,
    VarNode, AssignNode, StrictNullNode, PrintNode, NonstrictNode,
    TimerStartNode, TimerEndNode, SleepNode, CastNode,
    ArrayNode, IndexNode,
    BinaryOpNode, UnaryOpNode, RangeNode,
    BlockNode, IfNode,
    LoopNode, ForeverNode, DoNode, StopNode, SkipNode,
    FunctionDefNode, FunctionCallNode, ReturnNode, IndexAssignNode,
    InterpStringNode, FieldAccessNode, MethodCallNode,
    LazyDefNode, LazyCallNode,
) # the holy wall of imports
from lzy_env import Environment, LzyModule, StrictError, StopSignal, SkipSignal, ReturnSignal
from lzy_types import infer_type, coerce_value


# helpers

def is_truthy(value):
    if value is None:                                   return False
    if isinstance(value, bool):                         return value
    if isinstance(value, float) and math.isnan(value):  return False
    if isinstance(value, (int, float)):                 return value != 0
    if isinstance(value, str):                          return len(value) > 0
    if isinstance(value, list):                         return len(value) > 0
    return True

def format_value(value):
    if value is None:            return "null"
    if isinstance(value, bool):  return "true" if value else "false"
    if isinstance(value, list):  return "[" + ", ".join(format_value(v) for v in value) + "]"
    if isinstance(value, float):
        if math.isnan(value):    return "NaN"
        if value.is_integer():   return str(int(value))
        return str(value)
    return str(value)
    
def format_value_raw(value):
    # like format_value but evil 😈
    if value is None:            return "null"
    if isinstance(value, bool):  return "true" if value else "false"
    if isinstance(value, list):  return "[" + ", ".join(format_value_raw(v) for v in value) + "]"
    if isinstance(value, float):
        if math.isnan(value):    return "NaN"
        return str(value)
    return str(value)
    
def format_duration(seconds): # used for _start and _end
    ns = seconds * 1_000_000_000
    us = seconds * 1_000_000
    ms = seconds * 1_000

    return (
        f"{seconds:.6f}s "
        f"({ms:.3f}ms / {us:.1f}us / {ns:.0f}ns)"
    )


# evaluator

class Evaluator:
    def __init__(self, env):
        self.env = env
        self.timers = {} # debug

    def _find_lazyword(self, name):
        env = self.env
        while env is not None:
            if name in env.lazywords:
                return env.lazywords[name]
            env = env.parent
        return None

    def _find_function(self, name):
        # walk the env parent chain to find a function definition
        env = self.env
        while env is not None:
            if name in env.functions:
                return env.functions[name]
            env = env.parent
        return None

    def evaluate(self, node):
        # literals
        if isinstance(node, NumberNode):  return node.value
        if isinstance(node, StringNode):  return node.value
        if isinstance(node, NullNode):    return None
        if isinstance(node, NaNNode):     return math.nan
        if isinstance(node, BinNode):     return node.value
        
        # variables
        
        if isinstance(node, VarNode):
            return self.env.get(node.name)
        
        if isinstance(node, AssignNode):
            value = self.evaluate(node.expr)
            if node.name in self.env.vars:
                return self.env.assign(node.name, value)
            return self.env.define(
                node.name, value,
                type_hint = node.type_hint,
                strict    = node.strict,
                safe      = node.safe,
            )
        
        # declarations
        if isinstance(node, StrictNullNode):
            self.env.strict_null = True
            return None
            
        if isinstance(node, NonstrictNode):
            old_strict = self.env.strict_null
            self.env.strict_null = False
            try:
                return self.evaluate(node.body)
            finally:
                self.env.strict_null = old_strict
                
        # built-ins
        if isinstance(node, PrintNode):
            value = self.evaluate(node.expr)
            if node.raw:
                print(format_value_raw(value))
            else:
                print(format_value(value))
            return None
            
        if isinstance(node, TimerStartNode):
            key = node.name or "default"
            self.timers[key] = time.perf_counter()
            label = f" '{key}'" if node.name else ""
            print(f"[timer] started{label}")
            return None
        
        if isinstance(node, TimerEndNode):
            key = node.name or "default"
            if key not in self.timers:
                print(f"[warn] timer{' ' + repr(key) if node.name else ''} was never started")
                return None
            elapsed = time.perf_counter() - self.timers[key]
            del self.timers[key]
            label = f" '{key}'" if node.name else ""
            print(f"[timer] ended{label}: {format_duration(elapsed)}")
            return None

        if isinstance(node, SleepNode):
            duration = self.evaluate(node.expr)
            if duration is None or (isinstance(duration, float) and math.isnan(duration)):
                print("[warn] _sleep: invalid duration, skipping")
                return None
            time.sleep(float(duration))
            return None
            
        # blocks
        if isinstance(node, BlockNode):
            # im too lzy to code in scopes
            result = None
            for stmt in node.stmts:
                result = self.evaluate(stmt)
            return result
            
        # control flow
        
        if isinstance(node, IfNode):
            if is_truthy(self.evaluate(node.condition)):
                return self.evaluate(node.body)
            for elif_cond, elif_body in node.elseifs:
                if is_truthy(self.evaluate(elif_cond)):
                    return self.evaluate(elif_body)
            if node.else_body:
                return self.evaluate(node.else_body)
            return None
        
        # loops
        
        if isinstance(node, LoopNode):
            iterable = self.evaluate(node.iterable)
            if isinstance(iterable, (list, range)): # was isinstance(iterable, list)
                for item in iterable:
                    self.env.assign(node.var_name, item)
                    try:
                        self.evaluate(node.body)
                    except SkipSignal:
                        continue
                    except StopSignal:
                        break
            else:
                print(f"[warn] loop: expected array or range, got {type(iterable).__name__}")
            return None
        
        if isinstance(node, RangeNode):
            start = self.evaluate(node.start)
            end   = self.evaluate(node.end)
            if not isinstance(start, int) or not isinstance(end, int):
                start = int(start)
                end   = int(end)
            return range(start, end) #the old implemntation was ass
        
        if isinstance(node, ForeverNode):
            while True:
                try:
                    self.evaluate(node.body)
                except SkipSignal:
                    continue
                except StopSignal:
                    break
            return None
        
        if isinstance(node, DoNode):
            while is_truthy(self.evaluate(node.condition)):
                try:
                    self.evaluate(node.body)
                except SkipSignal:
                    continue
                except StopSignal:
                    break
            return None
        
        if isinstance(node, StopNode):
            raise StopSignal()
        
        if isinstance(node, SkipNode):
            raise SkipSignal()
        
        # expressions
        
        if isinstance(node, CastNode):
            value = self.evaluate(node.expr)
            return coerce_value(value, node.target_type)
            
        if isinstance(node, ArrayNode):
            return [self.evaluate(e) for e in node.elements]
            
        if isinstance(node, IndexNode):
            arr = self.evaluate(node.array)
            idx = self.evaluate(node.index)
        
            if not isinstance(arr, list):
                print(f"[warn] cannot index non-array value, returning null")
                return None
            
            if not isinstance(idx, int):
                idx = int(idx)
            
            if idx < 0:
                idx += len(arr) # negative indexing, `arr[-1]`
            
            if 0 <= idx < len(arr):
                return arr[idx]
            
            print(f"[warn] array index {idx} out of bounds (length {len(arr)}), returning null")
            return None

        if isinstance(node, IndexAssignNode):
            arr = self.evaluate(node.array)
            idx = self.evaluate(node.index)
            val = self.evaluate(node.expr)

            if not isinstance(arr, list):
                print(f"[warn] cannot index-assign on non-array value")
                return None

            if not isinstance(idx, int):
                idx = int(idx)

            if idx < 0:
                idx += len(arr)

            if 0 <= idx < len(arr):
                arr[idx] = val
                return val

            if idx == len(arr):
                # one past the end
                arr.append(val)
                return val

            print(f"[warn] array index {idx} out of bounds (length {len(arr)}), assignment ignored")
            return None
            
        # functions
        if isinstance(node, FunctionDefNode):
            # store function in the current environment
            self.env.functions[node.name] = node
            return None

        if isinstance(node, ReturnNode):
            value = self.evaluate(node.expr)
            raise ReturnSignal(value)

        if isinstance(node, FunctionCallNode):
            # built-in functions
            if node.name == "len":
                if len(node.args) != 1:
                    print("[warn] len() expects exactly 1 argument, returning null")
                    return None
                val = self.evaluate(node.args[0])
                if isinstance(val, (list, str)):
                    return len(val)
                print(f"[warn] len() expected array or string, got {type(val).__name__}, returning null")
                return None

            # look up function - check current env and parent chain
            func_def = self._find_function(node.name)
            if func_def is None:
                print(f"[warn] function '{node.name}' is not defined, returning null")
                return None

            # evaluate arguments in the CURRENT scope before switching
            arg_values = [self.evaluate(a) for a in node.args]

            # check arity
            if len(arg_values) != len(func_def.params):
                print(f"[warn] {node.name}() expected {len(func_def.params)} args, got {len(arg_values)}, returning null")
                return None

            # create a child environment for the function scope
            local_env = Environment()
            local_env.strict_null = self.env.strict_null
            local_env.parent      = self.env
            local_env.functions   = self.env.functions   # share function table

            # bind params as local variables
            for (param_name, param_type), arg_val in zip(func_def.params, arg_values):
                local_env.define(param_name, arg_val, type_hint=param_type)

            # swap to local scope, run body, restore
            outer_env  = self.env
            self.env   = local_env
            result     = None
            try:
                result = self.evaluate(func_def.body)
            except ReturnSignal as ret:
                result = ret.value
            finally:
                self.env = outer_env

            return result

        # string interpolation
        if isinstance(node, InterpStringNode):
            result = ""
            for part in node.parts:
                val = self.evaluate(part)
                result += format_value(val)
            return result

        # dot field access
        if isinstance(node, FieldAccessNode):
            obj = self.evaluate(node.obj)
            if isinstance(obj, LzyModule):
                print(f"[warn] {obj.name}.{node.field} is not callable without (), returning null")
                return None
            if isinstance(obj, dict):
                return obj.get(node.field, None)
            print(f"[warn] cannot access field '{node.field}' on {type(obj).__name__}, returning null")
            return None

        # method call
        if isinstance(node, MethodCallNode):
            obj  = self.evaluate(node.obj)
            args = [self.evaluate(a) for a in node.args]
            if isinstance(obj, LzyModule):
                return obj.call(node.method, args)
            print(f"[warn] cannot call method '{node.method}' on {type(obj).__name__}, returning null")
            return None

        # lazyword definition
        if isinstance(node, LazyDefNode):
            self.env.lazywords[node.name] = node
            return None

        # lazyword call
        if isinstance(node, LazyCallNode):
            lazy_def = self._find_lazyword(node.name)
            if lazy_def is None:
                print(f"[warn] lazyword '{node.name}' is not defined, returning null")
                return None

            arg_values = [self.evaluate(a) for a in node.args]

            if len(arg_values) != len(lazy_def.params):
                print(f"[warn] {node.name}|| expected {len(lazy_def.params)} args, got {len(arg_values)}, returning null")
                return None

            local_env = Environment()
            local_env.strict_null = self.env.strict_null
            local_env.parent      = self.env
            local_env.functions   = self.env.functions
            local_env.lazywords   = self.env.lazywords

            for (param_name, param_type), arg_val in zip(lazy_def.params, arg_values):
                local_env.define(param_name, arg_val, type_hint=param_type)

            outer_env = self.env
            self.env  = local_env
            result    = None
            try:
                result = self.evaluate(lazy_def.body)
            except ReturnSignal as ret:
                result = ret.value
            finally:
                self.env = outer_env

            return result

        if isinstance(node, UnaryOpNode):
            val = self.evaluate(node.operand)
            
            if node.op == "not":
                return not is_truthy(val)
            
            # null and NaN are infectious
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return val
            
            if node.op == "-":
                return -val
            
        if isinstance(node, BinaryOpNode):
            op = node.op
            
            # short-circuit logical operators
            if op == "and":
                left = self.evaluate(node.left)
                return left if not is_truthy(left) else self.evaluate(node.right)
            if op == "or":
                left = self.evaluate(node.left)
                return left if is_truthy(left) else self.evaluate(node.right)

            left  = self.evaluate(node.left)
            right = self.evaluate(node.right)

            # == and != handle null directly (null == null is true)
            if op == "==":   return left == right
            if op == "!=":   return left != right

            # === strict equality: value AND python type must match, no coercion
            # 877.0 === 877 is false because float != int
            if op == "===":
                return (left == right) and (type(left) is type(right))
            
            # null is infectious for all other ops
            if left is None or right is None:
                return None
            
            # tobu - infectious
            if (isinstance(left, float) and math.isnan(left)) or \
               (isinstance(right, float) and math.isnan(right)):
                return math.nan
            
            # arithmetic
            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return format_value(left) + format_value(right) #im not sure if this should be even put here, TODO: remove this and implement it better
                return left + right
            if op == "-":    return left - right
            if op == "*":    return left * right
            if op == "%":    return left % right
            if op == "**":   return left ** right
            if op == "/":
                if right == 0:
                    print("[warn] division by zero, returning null")
                    return None
                return left / right
            
            # ordering
            if op == "<":    return left < right
            if op == ">":    return left > right
            if op == "<=":   return left <= right
            if op == ">=":   return left >= right
         
        print(f"[warn] evaluator: unknown node {type(node).__name__}")
        return None