r"""
 __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
lzy - laziest programming language ever
created by gkugfk3 with ♡

licensed under MPL 2.0: https://www.mozilla.org/en-US/MPL/2.0/


# lzy_types.py
# type inference, compatibility checking, and coercion
"""

TYPE_FAMILY = {}
for _t in ["int", "int2", "int4", "int8", "int16", "int32", "int64"]:
    TYPE_FAMILY[_t] = "int"
for _t in ["float", "float4", "float8", "float16", "float32", "float64", "float128"]:
    TYPE_FAMILY[_t] = "float"
for _t in ["string", "longstring", "tinystring"]:
    TYPE_FAMILY[_t] = "string"
TYPE_FAMILY["bin"]  = "bin"
TYPE_FAMILY["null"] = "null"

# shorthand defaults
TYPE_DEFAULTS = {
    "int":   "int32",
    "float": "float64",
}


def normalize_type(t):
    # int -> int32, float -> float64, int[] -> int32[], etc
    if isinstance(t, str) and t.endswith("[]"):
        base = t[:-2]
        return normalize_type(base) + "[]"
    return TYPE_DEFAULTS.get(t, t)
    
def is_array_type(t):
    return isinstance(t, str) and t.endswith("[]")

def array_element_type(t):
    # int32[] -> int32
    return t[:-2]


def infer_type(value):
    # infer lzy type name from a python value
    if value is None:                return "null"
    if isinstance(value, bool):      return "bin"    # bool before int - bool is int subclass
    if isinstance(value, int):       return "int32"
    if isinstance(value, float):     return "float64"
    if isinstance(value, str):       return "string"
    if isinstance(value, list):      return "array"
    return "unknown"


def types_compatible(declared, actual, strict=False):
    # check if actual type is acceptable for a declared type
    if normalize_type(declared) == normalize_type(actual):
        return True

    d_fam = TYPE_FAMILY.get(normalize_type(declared), declared)
    a_fam = TYPE_FAMILY.get(normalize_type(actual), actual)

    # numerics are compatible in lenient mode
    if not strict and d_fam in ("int", "float") and a_fam in ("int", "float"):
        return True

    # null compatible with anything in lenient
    if not strict and actual == "null":
        return True

    return False


def coerce_value(value, target_type):
    # attempt to coerce a value to fit a target type
    target_type = normalize_type(target_type)
    fam = TYPE_FAMILY.get(target_type, target_type)
    try:
        if fam == "int":    return int(value)
        if fam == "float":  return float(value)
        if fam == "string": return str(value)
        if fam == "bin":    return bool(value)
    except (ValueError, TypeError):
        pass
    return value   # return as-is if coercion fails
