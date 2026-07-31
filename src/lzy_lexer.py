r"""
 __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
lzy - laziest programming language ever
created by gkugfk3 with ♡

licensed under MPL 2.0: https://www.mozilla.org/en-US/MPL/2.0/


# lzy_lexer.py
# turns raw source string into a flat list of tokens
"""

from lzy_tokens import TT, KEYWORDS, TYPE_NAMES, Token


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos    = 0

    def warn(self, msg):
        print(f"[warn] lexer: {msg}")

    def peek(self, offset=0):
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else None

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
                if has_dot:
                    break   # second dot, stop
                if self.peek(1) == ".":
                    break   # it's a .. range operator, not a decimal point
                has_dot = True
            result += self.advance()

        return float(result) if has_dot else int(result)

    def read_string(self):
        quote  = self.advance() # CONSUME opening quote
        result = ""

        while self.peek() is not None and self.peek() != quote:
            if self.peek() == "\\":
                self.advance()
                esc = self.advance()
                result += {"n": "\n", "t": "\t", "\\": "\\"}.get(esc, esc)
            else:
                result += self.advance()

        if self.peek() == quote:
            self.advance() # consume closing quote
        else:
            self.warn("unterminated string")

        return result


    def read_interp_string(self):
        # read a backtick string, split into ("str", text) and ("expr", src) parts
        self.advance()  # consume opening backtick
        parts = []
        current = ""

        while self.peek() is not None and self.peek() != "`":
            if self.peek() == "$" and self.peek(1) == "{":
                if current:
                    parts.append(("str", current))
                    current = ""
                self.advance()  # consume $
                self.advance()  # consume {
                depth = 1
                expr_src = ""
                while self.peek() is not None and depth > 0:
                    ch = self.peek()
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            self.advance()
                            break
                    expr_src += self.advance()
                parts.append(("expr", expr_src))
            elif self.peek() == "\\":
                self.advance()
                esc = self.advance()
                current += {"n": "\n", "t": "\t", "\\": "\\"}.get(esc, esc)
            else:
                current += self.advance()

        if current:
            parts.append(("str", current))

        if self.peek() == "`":
            self.advance()  # consume closing backtick
        else:
            self.warn("unterminated interpolated string")

        return parts

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

            # interpolated string
            elif ch == '`':
                tokens.append(Token(TT.INTERP, self.read_interp_string(), pos))

            # identifiers and keywords
            elif ch.isalpha() or ch == "_":
                word = self.read_identifier()
                if word in KEYWORDS:
                    tokens.append(Token(KEYWORDS[word], word, pos))
                elif word in TYPE_NAMES:
                    tokens.append(Token(TT.TYPE, word, pos))
                else:
                    tokens.append(Token(TT.IDENTIFIER, word, pos))

            # three-char operators first
            elif ch == "=" and self.peek(1) == "=" and self.peek(2) == "=":
                self.advance(); self.advance(); self.advance()
                tokens.append(Token(TT.SEQ, "===", pos))

            # two-char operators
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

            elif ch == "." and self.peek(1) == ".":
                self.advance(); self.advance()
                tokens.append(Token(TT.DOTDOT, "..", pos))

            elif ch == ".":
                self.advance(); tokens.append(Token(TT.DOT, ".", pos))

            # single-char operators
            elif ch == "=":  self.advance(); tokens.append(Token(TT.ASSIGN,  "=",  pos))
            elif ch == "<":  self.advance(); tokens.append(Token(TT.LT,      "<",  pos))
            elif ch == ">":  self.advance(); tokens.append(Token(TT.GT,      ">",  pos))
            elif ch == ":":  self.advance(); tokens.append(Token(TT.COLON,   ":",  pos))
            elif ch == "~":  self.advance(); tokens.append(Token(TT.TILDE,   "~",  pos))
            elif ch == "{":  self.advance(); tokens.append(Token(TT.LBRACE,  "{",  pos))
            elif ch == "}":  self.advance(); tokens.append(Token(TT.RBRACE,  "}",  pos))
            elif ch == "+":  self.advance(); tokens.append(Token(TT.PLUS,    "+",  pos))
            elif ch == "-":  self.advance(); tokens.append(Token(TT.MINUS,   "-",  pos))
            elif ch == "*":  self.advance(); tokens.append(Token(TT.STAR,    "*",  pos))
            elif ch == "/":  self.advance(); tokens.append(Token(TT.SLASH,   "/",  pos))
            elif ch == "%":  self.advance(); tokens.append(Token(TT.PERCENT, "%",  pos))
            elif ch == "(":  self.advance(); tokens.append(Token(TT.LPAREN,  "(",  pos))
            elif ch == ")":  self.advance(); tokens.append(Token(TT.RPAREN,  ")",  pos))
             # arrays
            elif ch == "[":  self.advance(); tokens.append(Token(TT.LBRACKET, "[", pos))
            elif ch == "]":  self.advance(); tokens.append(Token(TT.RBRACKET, "]", pos))
            elif ch == ",":  self.advance(); tokens.append(Token(TT.COMMA,    ",", pos))
            
            elif ch == "|": self.advance(); tokens.append(Token(TT.PIPE, "|", pos))
            elif ch == ";":  self.advance()   # semicolons are decorative, skip
            else:
                self.warn(f"unknown character '{ch}' at pos {pos}, skipping")
                self.advance()

        tokens.append(Token(TT.EOF, None, self.pos))
        return tokens
