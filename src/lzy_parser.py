r"""
 __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
lzy - laziest programming language ever
created by gkugfk3 with ♡

licensed under MPL 2.0: https://www.mozilla.org/en-US/MPL/2.0/


# lzy_parser.py
# turns a flat token list into an ast
"""

from lzy_tokens import TT, Token
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
)


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

    # program and blocks

    def parse_program(self):
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
        # after ~ : either { } block or a single statement
        if self.peek().type == TT.LBRACE:
            return self.parse_block()
        stmt = self.parse_statement()
        return BlockNode([stmt])

    # statements

    def parse_statement(self):

        # strict null declaration
        if self.peek().type == TT.STRICT and self.peek(1).type == TT.NULL:
            self.advance(); self.advance()
            return StrictNullNode()
        
        # nonstrict ~ { ... } block - temporarily lenient even under strict null
        if self.peek().type == TT.NONSTRICT and self.peek(1).type == TT.TILDE:
            self.advance(); self.advance()
            body = self.parse_block_or_single()
            return NonstrictNode(body)

        # if
        if self.peek().type == TT.IF:
            return self.parse_if()

        # loops
        if self.peek().type == TT.LOOP:
            return self.parse_loop()

        if self.peek().type == TT.FOREVER:
            return self.parse_forever()

        if self.peek().type == TT.DO:
            return self.parse_do()

        # stop and skip
        if self.peek().type == TT.STOP:
            self.advance()
            return StopNode()

        if self.peek().type == TT.SKIP:
            self.advance()
            return SkipNode()

        # function definition
        if self.peek().type == TT.FN:
            return self.parse_fn()

        # lazy definition
        if self.peek().type == TT.LAZY:
            return self.parse_lazy()

        # return statement
        if self.peek().type == TT.RETURN:
            self.advance()
            # optional return value
            if self.peek().type in (TT.RBRACE, TT.EOF):
                return ReturnNode(NullNode())
            return ReturnNode(self.parse_logical())

        # print / printl
        if self.peek().type in (TT.PRINT, TT.PRINTL):
            raw = self.peek().type == TT.PRINTL
            self.advance()
            self.expect(TT.LPAREN)
            expr = self.parse_logical()
            self.expect(TT.RPAREN)
            return PrintNode(expr, raw=raw)
            
        # debug timers: _start / _start "name" / _end / _end "name"
        if self.peek().type == TT.DSTART:
            self.advance()
            name = None
            if self.peek().type == TT.STRING:
                name = self.advance().value
            return TimerStartNode(name)

        if self.peek().type == TT.DEND:
            self.advance()
            name = None
            if self.peek().type == TT.STRING:
                name = self.advance().value
            return TimerEndNode(name)

        if self.peek().type == TT.DSLEEP:
            self.advance()
            self.expect(TT.LPAREN)
            expr = self.parse_logical()
            self.expect(TT.RPAREN)
            return SleepNode(expr)

        # variable modifiers: safe and/or strict -> must be assignment
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

        # assignment detection: IDENTIFIER followed by = or : or ::
        if self.peek().type == TT.IDENTIFIER:
            t1 = self.peek(1).type
            if t1 in (TT.ASSIGN, TT.COLON, TT.DCOLON):
                return self.parse_assignment()

            # index assignment: IDENTIFIER[index] = expr
            if t1 == TT.LBRACKET:
                checkpoint = self.pos
                target = self.parse_postfix()   # parses IDENTIFIER[index][index2]...
                if isinstance(target, IndexNode) and self.peek().type == TT.ASSIGN:
                    self.advance()   # consume =
                    expr = self.parse_logical()
                    return IndexAssignNode(target.array, target.index, expr)
                # not actually an assignment, rewind and fall through as expression
                self.pos = checkpoint

        # expression statement
        return self.parse_logical()


    def parse_fn(self):
        # fn name(param, param : type, ...) :: return_type ~ { body }
        self.expect(TT.FN)
        name = self.expect(TT.IDENTIFIER).value
        self.expect(TT.LPAREN)

        params = []   # list of (name, type_hint_or_None)
        while self.peek().type not in (TT.RPAREN, TT.EOF):
            param_name = self.expect(TT.IDENTIFIER).value
            param_type = None

            if self.peek().type == TT.COLON:
                self.advance()
                if self.peek().type == TT.TYPE:
                    param_type = self.advance().value
            elif self.peek().type == TT.DCOLON:
                self.advance()
                if self.peek().type in (TT.TYPE, TT.IDENTIFIER):
                    param_type = self.advance().value

            params.append((param_name, param_type))
            if self.peek().type == TT.COMMA:
                self.advance()

        self.expect(TT.RPAREN)

        # optional return type after params
        return_type = None
        if self.peek().type == TT.COLON:
            self.advance()
            if self.peek().type == TT.TYPE:
                return_type = self.advance().value
        elif self.peek().type == TT.DCOLON:
            self.advance()
            if self.peek().type in (TT.TYPE, TT.IDENTIFIER):
                return_type = self.advance().value

        self.expect(TT.TILDE)
        body = self.parse_block_or_single()
        return FunctionDefNode(name, params, return_type, body)


    def parse_lazy(self):
        # lazy name|param, param : type, ...| :: return_type ~ { body }
        self.expect(TT.LAZY)
        name = self.expect(TT.IDENTIFIER).value
        self.expect(TT.PIPE)

        params = []
        while self.peek().type not in (TT.PIPE, TT.EOF):
            if self.peek().type == TT.IDENTIFIER:
                param_name = self.advance().value
                param_type = None
                if self.peek().type == TT.COLON:
                    self.advance()
                    if self.peek().type == TT.TYPE:
                        param_type = self.advance().value
                elif self.peek().type == TT.DCOLON:
                    self.advance()
                    if self.peek().type in (TT.TYPE, TT.IDENTIFIER):
                        param_type = self.advance().value
                params.append((param_name, param_type))
                if self.peek().type == TT.COMMA:
                    self.advance()
            else:
                self.advance()

        self.expect(TT.PIPE)

        return_type = None
        if self.peek().type == TT.COLON:
            self.advance()
            if self.peek().type == TT.TYPE:
                return_type = self.advance().value
        elif self.peek().type == TT.DCOLON:
            self.advance()
            if self.peek().type in (TT.TYPE, TT.IDENTIFIER):
                return_type = self.advance().value

        self.expect(TT.TILDE)
        body = self.parse_block_or_single()
        return LazyDefNode(name, params, return_type, body)

    def parse_if(self):
        self.expect(TT.IF)
        condition = self.parse_logical()
        self.expect(TT.TILDE)
        body      = self.parse_block_or_single()

        elseifs   = []
        else_body = None

        while self.peek().type == TT.ELSE:
            self.advance()   # consume else

            if self.peek().type == TT.IF:
                self.advance()   # consume if
                elif_cond = self.parse_logical()
                self.expect(TT.TILDE)
                elif_body = self.parse_block_or_single()
                elseifs.append((elif_cond, elif_body))
            else:
                self.expect(TT.TILDE)
                else_body = self.parse_block_or_single()
                break

        return IfNode(condition, body, elseifs, else_body)

    def parse_loop(self):
        # loop iterable as varname ~ body
        self.expect(TT.LOOP)
        iterable = self.parse_range_or_expr()
        self.expect(TT.AS)
        var_name = self.expect(TT.IDENTIFIER).value
        self.expect(TT.TILDE)
        body     = self.parse_block_or_single()
        return LoopNode(iterable, var_name, body)

    def parse_forever(self):
        # forever ~ body
        self.expect(TT.FOREVER)
        self.expect(TT.TILDE)
        body = self.parse_block_or_single()
        return ForeverNode(body)

    def parse_do(self):
        # do condition ~ body
        self.expect(TT.DO)
        condition = self.parse_logical()
        self.expect(TT.TILDE)
        body      = self.parse_block_or_single()
        return DoNode(condition, body)

    def parse_assignment(self, strict=False, safe=False):
        name      = self.expect(TT.IDENTIFIER).value
        type_hint = None

        if self.peek().type == TT.COLON:
            self.advance()
            if self.peek().type == TT.TYPE:
                type_hint = self.advance().value
                if self.peek().type == TT.LBRACKET and self.peek(1).type == TT.RBRACKET:
                    self.advance(); self.advance()
                    type_hint = type_hint + "[]"
            else:
                self.warn("expected type name after ':'")

        elif self.peek().type == TT.DCOLON:
            self.advance()
            if self.peek().type in (TT.TYPE, TT.IDENTIFIER):
                type_hint = self.advance().value
                if self.peek().type == TT.LBRACKET and self.peek(1).type == TT.RBRACKET:
                    self.advance(); self.advance()
                    type_hint = type_hint + "[]"
            else:
                self.warn("expected type name after '::'")

        self.expect(TT.ASSIGN)
        expr = self.parse_logical()
        return AssignNode(name, expr, type_hint=type_hint, strict=strict, safe=safe)

    # range or expression (used in loop iterable position)

    def parse_range_or_expr(self):
        # parse an expression, then check if .. follows for a range
        left = self.parse_additive()

        if self.peek().type == TT.DOTDOT:
            self.advance()
            right = self.parse_additive()
            return RangeNode(left, right)

        return left

    # expression precedence chain
    # logical -> not -> comparison -> additive -> multiplicative
    # -> power -> unary -> primary

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
            operand = self.parse_not()
            return UnaryOpNode(op, operand)
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()
        while self.peek().type in (TT.EQEQ, TT.SEQ, TT.NEQ, TT.LT, TT.GT, TT.LTE, TT.GTE):
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
        # cast: <type>expr
        if (self.peek().type == TT.LT
                and self.peek(1).type == TT.TYPE
                and self.peek(2).type == TT.GT):
            self.advance()
            target_type = self.advance().value
            self.advance()
            operand = self.parse_unary()
            return CastNode(target_type, operand)

        if self.peek().type == TT.MINUS:
            op      = self.advance().value
            operand = self.parse_unary()
            return UnaryOpNode(op, operand)

        return self.parse_postfix()

    def parse_postfix(self):
        # handles arr[index], obj.field, obj.method(args)
        node = self.parse_primary()
        while True:
            if self.peek().type == TT.LBRACKET:
                self.advance()
                index = self.parse_logical()
                self.expect(TT.RBRACKET)
                node = IndexNode(node, index)
            elif self.peek().type == TT.DOT:
                self.advance()  # consume .
                field = self.expect(TT.IDENTIFIER).value
                if self.peek().type == TT.LPAREN:
                    self.advance()  # consume (
                    args = []
                    while self.peek().type not in (TT.RPAREN, TT.EOF):
                        args.append(self.parse_logical())
                        if self.peek().type == TT.COMMA:
                            self.advance()
                    self.expect(TT.RPAREN)
                    node = MethodCallNode(node, field, args)
                else:
                    node = FieldAccessNode(node, field)
            else:
                break
        return node

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
            self.advance()
            # function call: name(
            if self.peek().type == TT.LPAREN:
                self.advance()   # consume (
                args = []
                while self.peek().type not in (TT.RPAREN, TT.EOF):
                    args.append(self.parse_logical())
                    if self.peek().type == TT.COMMA:
                        self.advance()
                self.expect(TT.RPAREN)
                return FunctionCallNode(token.value, args)
            # lazyword call: name|args|
            if self.peek().type == TT.PIPE:
                self.advance()  # consume opening |
                args = []
                while self.peek().type not in (TT.PIPE, TT.EOF):
                    args.append(self.parse_logical())
                    if self.peek().type == TT.COMMA:
                        self.advance()
                self.expect(TT.PIPE)
                return LazyCallNode(token.value, args)
            return VarNode(token.value)

        if token.type == TT.LPAREN:
            self.advance()
            node = self.parse_logical()
            self.expect(TT.RPAREN)
            return node
            
        if token.type == TT.LBRACKET:
            self.advance()
            elements = []
            while self.peek().type not in (TT.RBRACKET, TT.EOF):
                elements.append(self.parse_logical())
                if self.peek().type == TT.COMMA:
                    self.advance()
            self.expect(TT.RBRACKET)
            return ArrayNode(elements)

        if token.type == TT.INTERP:
            self.advance()
            # re-lex and re-parse each expr segment
            parts = []
            for kind, content in token.value:
                if kind == "str":
                    parts.append(StringNode(content))
                else:
                    from lzy_lexer import Lexer as _Lexer
                    sub_tokens = _Lexer(content).tokenize()
                    sub_node   = Parser(sub_tokens).parse_logical()
                    parts.append(sub_node)
            return InterpStringNode(parts)

        self.warn(f"unexpected token {token}, using null")
        self.advance()
        return NullNode()
