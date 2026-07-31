#!/usr/bin/env python3

# lzy interpreter - step 3
# adds: comparison operators, logical operators, if/else if/else, blocks, multiline repl
#
# new in this version:
#   comparison ops   == != < > <= >=
#   logical ops      and or not
#   control flow     if / else if / else
#   blocks           ~ { ... } and single line ~ stmt
#   multiline repl   accumulates lines until braces are balanced
#
# pipeline:
#   source string -> lexer -> tokens -> parser -> ast list -> evaluator -> result

import math


# ----------------------------------------------------------------
# token types
# ----------------------------------------------------------------

class TT:
    # literals
    NUMBER      = "NUMBER"
    STRING      = "STRING"

    # arithmetic operators
    PLUS        = "PLUS"
    MINUS       = "MINUS"
    STAR        = "STAR"
    SLASH       = "SLASH"
    PERCENT     = "PERCENT"
    POWER       = "POWER"

    # comparison operators
    EQEQ        = "EQEQ"       # ==
    NEQ         = "NEQ"        # !=
    LT          = "LT"         # <
    GT          = "GT"         # >
    LTE         = "LTE"        # <=
    GTE         = "GTE"        # >=
    SEQ         = "TEQ"        # ===

    # assignment and type hints
    ASSIGN      = "ASSIGN"     # =
    COLON       = "COLON"      # :
    DCOLON      = "DCOLON"     # ::

    # block syntax
    TILDE       = "TILDE"      # ~
    LBRACE      = "LBRACE"     # {
    RBRACE      = "RBRACE"     # }

    # grouping
    LPAREN      = "LPAREN"     # (
    RPAREN      = "RPAREN"     # )

    # keywords - control flow
    IF          = "IF"
    ELSE        = "ELSE"

    # keywords - logical
    AND         = "AND"
    OR          = "OR"
    NOT         = "NOT"

    # keywords - modifiers
    STRICT      = "STRICT"
    NONSTRICT   = "NONSTRICT"
    SAFE        = "SAFE"

    # keywords - values
    NULL        = "NULL"
    NAN         = "NAN"
    TRUE        = "TRUE"
    FALSE       = "FALSE"
    T           = "T"
    F           = "F"

    # built-in functions
    PRINT       = "PRINT"

    # type keyword and identifier
    TYPE        = "TYPE"
    IDENTIFIER  = "IDENTIFIER"
    EOF         = "EOF"


KEYWORDS = {
    "if":        TT.IF,
    "else":      TT.ELSE,
    "and":       TT.AND,
    "or":        TT.OR,
    "not":       TT.NOT,
    "strict":    TT.STRICT,
    "nonstrict": TT.NONSTRICT,
    "safe":      TT.SAFE,
    "null":      TT.NULL,
    "NaN":       TT.NAN,
    "true":      TT.TRUE,
    "false":     TT.FALSE,
    "t":         TT.T,
    "f":         TT.F,
    "print":     TT.PRINT,
}

TYPE_NAMES = {
    "int", "int2", "int4", "int8", "int16", "int32", "int64",
    "float", "float4", "float8", "float16", "float32", "float64", "float128",
    "string", "longstring", "tinystring",
    "bin", "evilass"
}


class Token:
    def __init__(self, type, value, pos=0):
        self.type  = type
        self.value = value
        self.pos   = pos

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


# ----------------------------------------------------------------
# type system
# ----------------------------------------------------------------

TYPE_FAMILY = {}
for _t in ["int", "int2", "int4", "int8", "int16", "int32", "int64"]:
    TYPE_FAMILY[_t] = "int"
for _t in ["float", "float4", "float8", "float16", "float32", "float64", "float128"]:
    TYPE_FAMILY[_t] = "float"
for _t in ["string", "longstring", "tinystring"]:
    TYPE_FAMILY[_t] = "string"
TYPE_FAMILY["bin"]  = "bin"
TYPE_FAMILY["null"] = "null"
TYPE_FAMILY["evilass"] = "null"

TYPE_DEFAULTS = {
    "int":   "int32",
    "float": "float64",
}

def normalize_type(t):
    return TYPE_DEFAULTS.get(t, t)

def infer_type(value):
    if value is None:                              return "null"
    if isinstance(value, bool):                    return "bin"
    if isinstance(value, int):                     return "int32"
    if isinstance(value, float):                   return "float64"
    if isinstance(value, str):                     return "string"
    return "unknown"

def types_compatible(declared, actual, strict=False):
    if normalize_type(declared) == normalize_type(actual):
        return True
    d_fam = TYPE_FAMILY.get(normalize_type(declared), declared)
    a_fam = TYPE_FAMILY.get(normalize_type(actual), actual)
    if not strict and d_fam in ("int", "float") and a_fam in ("int", "float"):
        return True
    if not strict and actual == "null":
        return True
    return False

def coerce_value(value, target_type):
    target_type = normalize_type(target_type)
    fam = TYPE_FAMILY.get(target_type, target_type)
    try:
        if fam == "int":    return int(value)
        if fam == "float":  return float(value)
        if fam == "string": return str(value)
        if fam == "bin":    return bool(value)
    except (ValueError, TypeError):
        pass
    return value


# ----------------------------------------------------------------
# environment
# ----------------------------------------------------------------

class StrictError(Exception):
    pass # TODO: do

class Environment:
    def __init__(self):
        self.vars        = {}
        self.strict_null = False

    def _is_strict(self, var_strict):
        return var_strict or self.strict_null

    def define(self, name, value, type_hint=None, strict=False, safe=False):
        inferred = infer_type(value)
        declared = normalize_type(type_hint) if type_hint else inferred

        if type_hint and not types_compatible(declared, inferred, self._is_strict(strict)):
            msg = f"variable {name}: expected {declared}, got {inferred}"
            if self._is_strict(strict):
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

        var       = self.vars[name]
        new_type  = infer_type(value)
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
        if name not in self.vars:
            print(f"[warn] variable '{name}' is not defined, returning null")
            return None
        return self.vars[name]["value"]

    def info(self, name):
        return self.vars.get(name)


# ----------------------------------------------------------------
# lexer
# ----------------------------------------------------------------

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos    = 0

    def warn(self, msg):
        print(f"[warn] lexer: {msg}")

    def peek(self, offset=0):
        i = self.pos + offset
        if i < len(self.source):
            return self.source[i]
        return None

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        return ch

    def skip_whitespace(self):
        while self.peek() is not None and self.peek().isspace():
            self.advance()

    def read_number(self):
        result  = ""
        has_dot = False
        while self.peek() is not None and (self.peek().isdigit() or self.peek() == "."):
            if self.peek() == ".":
                if has_dot: break
                has_dot = True
            result += self.advance()
        return float(result) if has_dot else int(result)

    def read_string(self):
        quote  = self.advance()
        result = ""
        while self.peek() is not None and self.peek() != quote:
            if self.peek() == "\\":
                self.advance()
                esc = self.advance()
                result += {"n": "\n", "t": "\t", "\\": "\\"}.get(esc, esc)
            else:
                result += self.advance()
        if self.peek() == quote:
            self.advance()
        else:
            self.warn("unterminated string")
        return result

    def read_identifier(self):
        result = ""
        while self.peek() is not None and (self.peek().isalnum() or self.peek() == "_"):
            result += self.advance()
        return result

    def tokenize(self):
        tokens = []

        while self.pos < len(self.source):
            self.skip_whitespace()
            ch = self.peek()
            if ch is None:
                break

            pos = self.pos

            # numbers
            if ch.isdigit() or (ch == "." and self.peek(1) is not None and self.peek(1).isdigit()):
                tokens.append(Token(TT.NUMBER, self.read_number(), pos))

            # strings
            elif ch in ('"', "'"):
                tokens.append(Token(TT.STRING, self.read_string(), pos))

            # identifiers and keywords
            elif ch.isalpha() or ch == "_":
                word = self.read_identifier()
                if word in KEYWORDS:
                    tokens.append(Token(KEYWORDS[word], word, pos))
                elif word in TYPE_NAMES:
                    tokens.append(Token(TT.TYPE, word, pos))
                else:
                    tokens.append(Token(TT.IDENTIFIER, word, pos))

            # tri-char first
            elif ch == "=" and self.peek(1) == "=" and self.peek(2) == "=":
                self.advance(); self.advance(); self.advance()
                tokens.append(Token(TT.SEQ, "===", pos))
                
            # two-char second
            elif ch == "=" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TT.EQEQ, "==", pos))

            elif ch == "!" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TT.NEQ, "!=", pos))

            elif ch == "<" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TT.LTE, "<=", pos))

            elif ch == ">" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TT.GTE, ">=", pos))

            elif ch == ":" and self.peek(1) == ":":
                self.advance(); self.advance()
                tokens.append(Token(TT.DCOLON, "::", pos))

            elif ch == "*" and self.peek(1) == "*":
                self.advance(); self.advance()
                tokens.append(Token(TT.POWER, "**", pos))

            # single-char operators
            elif ch == "=":
                self.advance(); tokens.append(Token(TT.ASSIGN,   "=",  pos))
            elif ch == "<":
                self.advance(); tokens.append(Token(TT.LT,       "<",  pos))
            elif ch == ">":
                self.advance(); tokens.append(Token(TT.GT,       ">",  pos))
            elif ch == ":":
                self.advance(); tokens.append(Token(TT.COLON,    ":",  pos))
            elif ch == "~":
                self.advance(); tokens.append(Token(TT.TILDE,    "~",  pos))
            elif ch == "{":
                self.advance(); tokens.append(Token(TT.LBRACE,   "{",  pos))
            elif ch == "}":
                self.advance(); tokens.append(Token(TT.RBRACE,   "}",  pos))
            elif ch == "+":
                self.advance(); tokens.append(Token(TT.PLUS,     "+",  pos))
            elif ch == "-":
                self.advance(); tokens.append(Token(TT.MINUS,    "-",  pos))
            elif ch == "*":
                self.advance(); tokens.append(Token(TT.STAR,     "*",  pos))
            elif ch == "/":
                self.advance(); tokens.append(Token(TT.SLASH,    "/",  pos))
            elif ch == "%":
                self.advance(); tokens.append(Token(TT.PERCENT,  "%",  pos))
            elif ch == "(":
                self.advance(); tokens.append(Token(TT.LPAREN,   "(",  pos))
            elif ch == ")":
                self.advance(); tokens.append(Token(TT.RPAREN,   ")",  pos))
            elif ch == ";":
                self.advance()   # semicolons are decorative, just skip
            else:
                self.warn(f"unknown character '{ch}' at pos {pos}, skipping")
                self.advance()

        tokens.append(Token(TT.EOF, None, self.pos))
        return tokens


# ----------------------------------------------------------------
# ast nodes
# ----------------------------------------------------------------

class NumberNode:
    def __init__(self, value):           self.value = value

class StringNode:
    def __init__(self, value):           self.value = value

class NullNode:
    pass

class NaNNode:
    pass

class BinNode:
    def __init__(self, value):           self.value = value

class VarNode:
    def __init__(self, name):            self.name = name

class AssignNode:
    def __init__(self, name, expr, type_hint=None, strict=False, safe=False):
        self.name      = name
        self.expr      = expr
        self.type_hint = type_hint
        self.strict    = strict
        self.safe      = safe

class StrictNullNode:
    pass

class PrintNode:
    def __init__(self, expr):            self.expr = expr

class BinaryOpNode:
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op
        self.right = right

class UnaryOpNode:
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand

class BlockNode:
    # a sequence of statements inside { }
    def __init__(self, stmts):           self.stmts = stmts

class IfNode:
    def __init__(self, condition, body, elseifs=None, else_body=None):
        self.condition = condition
        self.body      = body
        self.elseifs   = elseifs or []   # list of (condition, body) tuples
        self.else_body = else_body


# ----------------------------------------------------------------
# parser
# ----------------------------------------------------------------

# node types that are "statements" and should not auto-print in the repl
STMT_NODES = (AssignNode, PrintNode, StrictNullNode, IfNode, BlockNode)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def warn(self, msg):
        print(f"[warn] parser: {msg}")

    def peek(self, offset=0):
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else self.tokens[-1]

    def advance(self):
        token = self.tokens[self.pos]
        if token.type != TT.EOF:
            self.pos += 1
        return token

    def expect(self, type):
        if self.peek().type != type:
            self.warn(f"expected {type} but got {self.peek().type} ({self.peek().value!r})")
            return Token(type, None)
        return self.advance()

    # ---- program and blocks ----

    def parse_program(self):
        # parse all statements until EOF
        stmts = []
        while self.peek().type != TT.EOF:
            stmt = self.parse_statement()
            if stmt is not None:
                stmts.append(stmt)
        return stmts

    def parse_block(self):
        # parse { stmt stmt ... }
        self.expect(TT.LBRACE)
        stmts = []
        while self.peek().type not in (TT.RBRACE, TT.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                stmts.append(stmt)
        self.expect(TT.RBRACE)
        return BlockNode(stmts)

    def parse_block_or_single(self):
        # after ~ : either a full { } block or a single statement
        if self.peek().type == TT.LBRACE:
            return self.parse_block()
        else:
            stmt = self.parse_statement()
            return BlockNode([stmt])

    # ---- statements ----

    def parse_statement(self):
        # strict null declaration
        if self.peek().type == TT.STRICT and self.peek(1).type == TT.NULL:
            self.advance(); self.advance()
            return StrictNullNode()

        # if statement
        if self.peek().type == TT.IF:
            return self.parse_if()

        # print
        if self.peek().type == TT.PRINT:
            self.advance()
            self.expect(TT.LPAREN)
            expr = self.parse_logical()
            self.expect(TT.RPAREN)
            return PrintNode(expr)

        # modifiers: safe, strict (then must be assignment)
        safe   = False
        strict = False
        while self.peek().type in (TT.SAFE, TT.STRICT):
            if self.peek().type == TT.SAFE:
                safe = True
            else:
                strict = True
            self.advance()

        if safe or strict:
            return self.parse_assignment(strict=strict, safe=safe)

        # assignment: IDENTIFIER = or IDENTIFIER : type = or IDENTIFIER :: type =
        if self.peek().type == TT.IDENTIFIER:
            t1 = self.peek(1).type
            if t1 in (TT.ASSIGN, TT.COLON, TT.DCOLON):
                return self.parse_assignment()

        # expression
        return self.parse_logical()

    def parse_if(self):
        self.expect(TT.IF)
        condition = self.parse_logical()
        self.expect(TT.TILDE)
        body = self.parse_block_or_single()

        elseifs   = []
        else_body = None

        # keep consuming else / else if chains
        while self.peek().type == TT.ELSE:
            self.advance()   # consume 'else'

            if self.peek().type == TT.IF:
                self.advance()   # consume 'if'
                elif_cond = self.parse_logical()
                self.expect(TT.TILDE)
                elif_body = self.parse_block_or_single()
                elseifs.append((elif_cond, elif_body))

            else:
                # plain else
                self.expect(TT.TILDE)
                else_body = self.parse_block_or_single()
                break   # nothing can follow a plain else

        return IfNode(condition, body, elseifs, else_body)

    def parse_assignment(self, strict=False, safe=False):
        name      = self.expect(TT.IDENTIFIER).value
        type_hint = None

        if self.peek().type == TT.COLON:
            self.advance()
            if self.peek().type == TT.TYPE:
                type_hint = self.advance().value
            else:
                self.warn("expected type name after ':'")

        elif self.peek().type == TT.DCOLON:
            self.advance()
            if self.peek().type in (TT.TYPE, TT.IDENTIFIER):
                type_hint = self.advance().value
            else:
                self.warn("expected type name after '::'")

        self.expect(TT.ASSIGN)
        expr = self.parse_logical()
        return AssignNode(name, expr, type_hint=type_hint, strict=strict, safe=safe)

    # ---- expression precedence chain ----
    # logical (and/or)  <- lowest precedence
    # not
    # comparison (== != < > <= >=)
    # additive (+ -)
    # multiplicative (* / %)
    # power (**)
    # unary (-)
    # primary          <- highest precedence

    def parse_logical(self):
        left = self.parse_not()
        while self.peek().type in (TT.AND, TT.OR):
            op    = self.advance().value
            right = self.parse_not()
            left  = BinaryOpNode(left, op, right)
        return left

    def parse_not(self):
        if self.peek().type == TT.NOT:
            op      = self.advance().value
            operand = self.parse_not()   # right associative: not not x
            return UnaryOpNode(op, operand)
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()
        while self.peek().type in (TT.EQEQ, TT.NEQ, TT.LT, TT.GT, TT.LTE, TT.GTE):
            op    = self.advance().value
            right = self.parse_additive()
            left  = BinaryOpNode(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek().type in (TT.PLUS, TT.MINUS):
            op    = self.advance().value
            right = self.parse_multiplicative()
            left  = BinaryOpNode(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_power()
        while self.peek().type in (TT.STAR, TT.SLASH, TT.PERCENT):
            op    = self.advance().value
            right = self.parse_power()
            left  = BinaryOpNode(left, op, right)
        return left

    def parse_power(self):
        base = self.parse_unary()
        if self.peek().type == TT.POWER:
            op  = self.advance().value
            exp = self.parse_power()
            return BinaryOpNode(base, op, exp)
        return base

    def parse_unary(self):
        if self.peek().type == TT.MINUS:
            op      = self.advance().value
            operand = self.parse_unary()
            return UnaryOpNode(op, operand)
        return self.parse_primary()

    def parse_primary(self):
        token = self.peek()

        if token.type == TT.NUMBER:
            self.advance(); return NumberNode(token.value)

        if token.type == TT.STRING:
            self.advance(); return StringNode(token.value)

        if token.type == TT.NULL:
            self.advance(); return NullNode()

        if token.type == TT.NAN:
            self.advance(); return NaNNode()

        if token.type in (TT.TRUE, TT.FALSE):
            self.advance(); return BinNode(token.type == TT.TRUE)

        if token.type == TT.T:
            self.advance(); return BinNode(True)

        if token.type == TT.F:
            self.advance(); return BinNode(False)

        if token.type == TT.IDENTIFIER:
            self.advance(); return VarNode(token.value)

        if token.type == TT.LPAREN:
            self.advance()
            node = self.parse_logical()
            self.expect(TT.RPAREN)
            return node

        self.warn(f"unexpected token {token}, using null")
        self.advance()
        return NullNode()


# ----------------------------------------------------------------
# evaluator
# ----------------------------------------------------------------

def is_truthy(value):
    # lzy truthiness rules
    if value is None:                              return False
    if isinstance(value, bool):                    return value
    if isinstance(value, float) and math.isnan(value): return False
    if isinstance(value, (int, float)):            return value != 0
    if isinstance(value, str):                     return len(value) > 0
    return True


class Evaluator:
    def __init__(self, env):
        self.env = env

    def evaluate(self, node):

        if isinstance(node, NumberNode):  return node.value
        if isinstance(node, StringNode):  return node.value
        if isinstance(node, NullNode):    return None
        if isinstance(node, NaNNode):     return math.nan
        if isinstance(node, BinNode):     return node.value

        if isinstance(node, VarNode):
            return self.env.get(node.name)

        if isinstance(node, StrictNullNode):
            self.env.strict_null = True
            return None

        if isinstance(node, AssignNode):
            value = self.evaluate(node.expr)
            if node.name in self.env.vars:
                return self.env.assign(node.name, value)
            else:
                return self.env.define(
                    node.name, value,
                    type_hint = node.type_hint,
                    strict    = node.strict,
                    safe      = node.safe,
                )

        if isinstance(node, PrintNode):
            value = self.evaluate(node.expr)
            print(format_value(value))
            return None

        if isinstance(node, BlockNode):
            # blocks do not create a new scope - variables leak out (lzy design)
            result = None
            for stmt in node.stmts:
                result = self.evaluate(stmt)
            return result

        if isinstance(node, IfNode):
            if is_truthy(self.evaluate(node.condition)):
                return self.evaluate(node.body)
            for elif_cond, elif_body in node.elseifs:
                if is_truthy(self.evaluate(elif_cond)):
                    return self.evaluate(elif_body)
            if node.else_body:
                return self.evaluate(node.else_body)
            return None

        if isinstance(node, UnaryOpNode):
            val = self.evaluate(node.operand)

            if node.op == "not":
                return not is_truthy(val)

            # null and NaN are infectious for arithmetic
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

            # null infectious for all non-logical ops
            if left is None or right is None:
                return None

            # NaN infectious for arithmetic
            if op not in ("==", "!=") and (
                (isinstance(left, float) and math.isnan(left)) or
                (isinstance(right, float) and math.isnan(right))
            ):
                return math.nan

            # arithmetic
            if op == "+":   return left + right
            if op == "-":   return left - right
            if op == "*":   return left * right
            if op == "%":   return left % right
            if op == "**":  return left ** right
            if op == "/":
                if right == 0:
                    print("[warn] division by zero, returning null")
                    return None
                return left / right

            # comparison
            if op == "==":  return left == right
            if op == "!=":  return left != right
            if op == "<":   return left < right
            if op == ">":   return left > right
            if op == "<=":  return left <= right
            if op == ">=":  return left >= right

        print(f"[warn] evaluator: unknown node {type(node).__name__}")
        return None


# ----------------------------------------------------------------
# formatting
# ----------------------------------------------------------------

def format_value(value):
    if value is None:            return "null"
    if isinstance(value, bool):  return "true" if value else "false"
    if isinstance(value, float):
        if math.isnan(value):    return "NaN"
        if value.is_integer():   return str(int(value))
        return str(value)
    return str(value)


# ----------------------------------------------------------------
# run
# ----------------------------------------------------------------

def run(source, env, evaluator):
    source = source.strip()
    if not source:
        return

    tokens = Lexer(source).tokenize()
    stmts  = Parser(tokens).parse_program()

    for stmt in stmts:
        result = evaluator.evaluate(stmt)
        # auto-print expression results, not statements
        if not isinstance(stmt, STMT_NODES):
            print(format_value(result))


# ----------------------------------------------------------------
# repl
# ----------------------------------------------------------------

def count_braces(text):
    # returns open - close brace count to detect incomplete blocks
    return text.count("{") - text.count("}")

if __name__ == "__main__":
    env       = Environment()
    evaluator = Evaluator(env)

    print("lzy interpreter v0.3")
    print("operators: + - * / % ** == != < > <= >= and or not")
    print("control flow: if / else if / else")
    print("type 'vars' to inspect variables, 'exit' to quit\n")

    buffer = ""

    while True:
        try:
            prompt = "lzy> " if not buffer else "  -> "
            line   = input(prompt)

            if not buffer and line.strip() == "exit":
                break

            if not buffer and line.strip() == "vars":
                if not env.vars:
                    print("  (no variables defined)")
                else:
                    for name, info in env.vars.items():
                        flags    = []
                        if info["strict"]: flags.append("strict")
                        if info["safe"]:   flags.append("safe")
                        flag_str = f" [{', '.join(flags)}]" if flags else ""
                        print(f"  {name} : {info['type']}{flag_str} = {format_value(info['value'])}")
                continue

            buffer += line + "\n"

            # keep reading if there are unclosed braces
            if count_braces(buffer) > 0:
                continue

            try:
                run(buffer, env, evaluator)
            except StrictError as e:
                print(f"[strict assert] {e}")
                input("  -> press enter to continue  ")

            buffer = ""

        except KeyboardInterrupt:
            print("\nexiting")
            break
