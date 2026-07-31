r"""
 __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
lzy - laziest programming language ever
created by gkugfk3 with ♡

licensed under MPL 2.0: https://www.mozilla.org/en-US/MPL/2.0/


# lzy_env.py
# environment (symbol table) and control flow signals
## the things that says: "screw you, your code is ass"
"""

from lzy_types import (
    infer_type, normalize_type, types_compatible, coerce_value,
    is_array_type, array_element_type,
)

# signals - used for loop control flow
# raised by stop/skip statements, caught by loop evaluators

class StrictError(Exception):
    # raised on a strict type violation
    pass

class StopSignal(Exception):
    # raised by "stop" (break) inside a loop
    pass

class SkipSignal(Exception):
    # raised by "skip" (continue) inside a loop
    pass

class ReturnSignal(Exception):
    # raised by "return" inside a function, carries the return value
    def __init__(self, value=None):
        self.value = value
    

def check_array(value, elem_type, name, strict):
    # warn-and-recover: bad elements get removed in lenient mode
    # strict mode raises instead
    elem_type = normalize_type(elem_type)
    result = []

    for i, item in enumerate(value):
        item_type = infer_type(item)

        if types_compatible(elem_type, item_type, strict):
            result.append(coerce_value(item, elem_type))
        else:
            msg = f"array {name}: element {i} expected {elem_type}, got {item_type}"
            if strict:
                raise StrictError(msg)
            print(f"[warn] {msg}")
            print(f"  -> recovered by: removing element")

    return result


# built-in module/namespace type

class LzyModule:
    # represents a built-in namespace like io
    # methods is a dict of name -> callable(args_list) -> value
    def __init__(self, name, methods):
        self.name    = name
        self.methods = methods

    def call(self, method, args):
        if method not in self.methods:
            print(f"[warn] {self.name}.{method}() is not defined, returning null")
            return None
        return self.methods[method](args)

    def __repr__(self):
        return f"<module:{self.name}>"



# environment
# please kill me

class Environment:
    def __init__(self):
        self.vars        = {}     # name -> { value, type, strict, safe }
        self.functions   = {}     # name -> FunctionDefNode
        self.lazywords   = {}     # name -> LazyDefNode
        self.strict_null = False  # set by "strict null" at file level
        self.parent      = None   # set when creating a function scope

    def _is_strict(self, var_strict):
        # variable is strict if declared strict OR file has strict null
        return var_strict or self.strict_null

    def define(self, name, value, type_hint=None, strict=False, safe=False):
        is_strict = self._is_strict(strict)

        # explicit array type hint, e.g. int[] or string[]
        if type_hint and is_array_type(normalize_type(type_hint)):
            declared  = normalize_type(type_hint)
            elem_type = array_element_type(declared)

            if not isinstance(value, list):
                print(f"[warn] variable {name}: expected {declared}, got {infer_type(value)}")
                value = []

            value = check_array(value, elem_type, name, is_strict)

            self.vars[name] = {
                "value":  value,
                "type":   declared,
                "strict": strict,
                "safe":   safe,
            }
            return value

        # inferred array, e.g. numbers = [1, 2, 3]
        if type_hint is None and isinstance(value, list):
            if len(value) > 0:
                elem_type = normalize_type(infer_type(value[0]))
                value     = check_array(value, elem_type, name, is_strict)
                declared  = elem_type + "[]"
            else:
                declared = "array"

            self.vars[name] = {
                "value":  value,
                "type":   declared,
                "strict": strict,
                "safe":   safe,
            }
            return value

        # stupid scalar
        inferred = infer_type(value)
        declared = normalize_type(type_hint) if type_hint else inferred

        if type_hint and not types_compatible(declared, inferred, is_strict):
            msg = f"variable {name}: expected {declared}, got {inferred}"
            if is_strict:
                raise StrictError(msg)
            else:
                print(f"[warn] {msg}")
                print(f"  -> coercing to {declared}")
                value = coerce_value(value, declared)

        self.vars[name] = {
            "value":  value,
            "type":   declared,
            "strict": strict,
            "safe":   safe,
        }
        return value

    def assign(self, name, value):
        if name not in self.vars:
            return self.define(name, value)

        var = self.vars[name]

        # fast path: type unchanged, no checks needed at all

        new_type = infer_type(value)
        if ( ## this sucks
            new_type == "array"
            and is_array_type(var["type"])
        ):
            new_type = var["type"]
        # print(
            # "[debug] ",
            # repr(value),
            # " new_type=", new_type,
            # " expected=", var["type"]
        # )
        if new_type == var["type"] and not var["safe"]:
            var["value"] = value
            return value

        # only runs on actual type changes
        is_strict = self._is_strict(var["strict"])

        if var["safe"]:
            var["type"]  = new_type
            var["value"] = value
            return value

        if not types_compatible(var["type"], new_type, is_strict):
            msg = f"variable {name}: expected {var['type']}, got {new_type}"
            if is_strict:
                raise StrictError(msg)
            else:
                print(f"[warn] {msg}")
                print(f"  -> keeping existing value: {var['value']!r}")
                return var["value"]

        var["value"] = coerce_value(value, var["type"])
        return var["value"]

    def get(self, name):
        if name in self.vars:
            return self.vars[name]["value"]
        if self.parent is not None:
            return self.parent.get(name)
        print(f"[warn] variable '{name}' is not defined, returning null")
        return None

    def info(self, name):
        # full variable record, used for debugging/vars command
        return self.vars.get(name)