r"""
 __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
lzy - laziest programming language ever
created by gkugfk3 with ♡

licensed under MPL 2.0: https://www.mozilla.org/en-US/MPL/2.0/


# lzy_tokens.py
# token types, keyword map, type names
"""

class TT:
    # literals
    NUMBER      = "NUMBER"
    STRING      = "STRING"

    # arithmetic
    PLUS        = "PLUS"        # +
    MINUS       = "MINUS"       # -
    STAR        = "STAR"        # *
    SLASH       = "SLASH"       # /
    PERCENT     = "PERCENT"     # %
    POWER       = "POWER"       # ^

    # comparison
    EQEQ        = "EQEQ"        # ==  value equality
    SEQ         = "SEQ"         # === strict equality (value + type, no coercion)
    NEQ         = "NEQ"         # !=
    LT          = "LT"          # <
    GT          = "GT"          # >
    LTE         = "LTE"         # <=
    GTE         = "GTE"         # >=

    # assignment and type hints
    ASSIGN      = "ASSIGN"      # =
    COLON       = "COLON"       # :   primitive type hint
    DCOLON      = "DCOLON"      # ::  struct type hint

    # block syntax
    TILDE       = "TILDE"       # ~
    LBRACE      = "LBRACE"      # {
    RBRACE      = "RBRACE"      # }

    # range
    DOTDOT      = "DOTDOT"      # ..
    DOT         = "DOT"         # .  field access

    # lazywords
    PIPE        = "PIPE"        # |
    LAZY        = "LAZY"        # lazy keyword

    # string interpolation
    INTERP      = "INTERP"      # backtick string with ${} segments

    # grouping
    LPAREN      = "LPAREN"      # (
    RPAREN      = "RPAREN"      # )
    LBRACKET    = "LBRACKET"     # [
    RBRACKET    = "RBRACKET"     # ]
    COMMA       = "COMMA"        # ,

    # control flow
    IF          = "IF"
    ELSE        = "ELSE"
    LOOP        = "LOOP"
    FOREVER     = "FOREVER"
    DO          = "DO"
    AS          = "AS"
    STOP        = "STOP"        # break
    SKIP        = "SKIP"        # continue
    RETURN      = "RETURN"
    FN          = "FN"

    # logical
    AND         = "AND"
    OR          = "OR"
    NOT         = "NOT"

    # variable modifiers
    STRICT      = "STRICT"
    NONSTRICT   = "NONSTRICT"
    SAFE        = "SAFE"

    # value keywords
    NULL        = "NULL"
    NAN         = "NAN"
    TRUE        = "TRUE"
    FALSE       = "FALSE"
    T           = "T"
    F           = "F"

    # built-ins
    PRINT       = "PRINT"
    PRINTL      = "PRINTL"
    
    ## DEBUG
    DSTART      = "DSTART"
    DEND        = "DEND"
    DSLEEP      = "DSLEEP"    # _sleep

    # type name and identifier
    TYPE        = "TYPE"
    IDENTIFIER  = "IDENTIFIER"
    EOF         = "EOF"


KEYWORDS = {
    "if":        TT.IF,
    "else":      TT.ELSE,
    "loop":      TT.LOOP,
    "forever":   TT.FOREVER,
    "do":        TT.DO,
    "as":        TT.AS,
    "stop":      TT.STOP,
    "skip":      TT.SKIP,
    "return":    TT.RETURN,
    "fn":        TT.FN,
    "lazy":      TT.LAZY,
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
    "printl":    TT.PRINTL,
    "_start":    TT.DSTART,
    "_end":      TT.DEND,
    "_sleep":    TT.DSLEEP,
}

TYPE_NAMES = {
    "int", "int2", "int4", "int8", "int16", "int32", "int64",
    "float", "float4", "float8", "float16", "float32", "float64", "float128",
    "string", "longstring", "tinystring",
    "bin",
}


class Token:
    def __init__(self, type, value, pos=0):
        self.type  = type
        self.value = value
        self.pos   = pos

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

