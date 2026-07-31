r"""
 __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
lzy - laziest programming language ever
created by gkugfk3 with ♡

licensed under MPL 2.0: https://www.mozilla.org/en-US/MPL/2.0/


# lzy_run.py
# run(), run_file(), repl(), and main entry point
# (this is where all the fun happens)
"""

import sys
import os
import re

from lzy_env     import Environment, LzyModule, StrictError, StopSignal, SkipSignal, ReturnSignal
from lzy_lexer   import Lexer
from lzy_parser  import Parser
from lzy_eval    import Evaluator, format_value
from lzy_ast     import STMT_NODES

LOGO = """ __         ______     __  __    
/\ \       /\___  \   /\ \_\ \   
\ \ \____  \/_/  /__  \ \____ \  
 \ \_____\   /\_____\  \/\_____\ 
  \/_____/   \/_____/   \/_____/ 
                                 
"""
VERSION = "0.1"


def strip_comments(source):
    # remove lzy comments before running
    # multiline first: !* ... *!
    # then single line: !/ ... !/
    source = re.sub(r'!\*.*?\*!', '', source, flags=re.DOTALL)
    source = re.sub(r'!/.*?!/',   '', source)
    return source


def run(source, env, evaluator):
    source = strip_comments(source).strip()
    if not source:
        return

    tokens = Lexer(source).tokenize()
    stmts  = Parser(tokens).parse_program()

    for stmt in stmts:
        try:
            result = evaluator.evaluate(stmt)
        except StopSignal:
            # stop outside any loop - end the program
            print("[stop] program ended")
            raise
        except SkipSignal:
            # skip outside any loop - warn and ignore
            print("[warn] 'skip' used outside a loop, ignoring")
            continue
        except ReturnSignal:
            # return outside any function - warn and ignore
            print("[warn] 'return' used outside a function, ignoring")
            continue

        # auto-print expression results, not statement nodes
        if not isinstance(stmt, STMT_NODES):
            print(format_value(result))


def run_file(filepath, env, evaluator):
    if not os.path.exists(filepath):
        print(f"[error] file not found: {filepath}")
        return

    if not filepath.endswith(".lzy"):
        print(f"[warn] {filepath} does not have a .lzy extension, attempting anyway")

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        run(source, env, evaluator)
    except StrictError as e:
        print(f"[strict assert] {e}")
        print(f"  -> at file: {filepath}")
        print(f"  -> program terminated")
    except StopSignal:
        pass   # already printed "[stop] program ended"


def count_braces(text):
    # track unclosed braces to detect incomplete blocks in the repl
    return text.count("{") - text.count("}")


def show_vars(env):
    if not env.vars:
        print("  (no variables defined)")
        return
    for name, info in env.vars.items():
        flags    = []
        if info["strict"]: flags.append("strict")
        if info["safe"]:   flags.append("safe")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"  {name} : {info['type']}{flag_str} = {format_value(info['value'])}")



def build_io_module(format_value):
    import os as _os

    def _read(args):
        prompt = format_value(args[0]) if args else ""
        try:
            return input(prompt)
        except EOFError:
            return None

    def _write(args):
        text = format_value(args[0]) if args else ""
        print(text, end="")
        return None

    def _writeln(args):
        text = format_value(args[0]) if args else ""
        print(text)
        return None

    def _readnum(args):
        prompt = format_value(args[0]) if args else ""
        try:
            raw = input(prompt)
            try:
                return int(raw)
            except ValueError:
                try:
                    return float(raw)
                except ValueError:
                    print(f"[warn] io.readnum: could not parse {raw!r} as number, returning null")
                    return None
        except EOFError:
            return None

    def _exists(args):
        if not args:
            return False
        return _os.path.exists(str(args[0]))

    def _readfile(args):
        if not args:
            print("[warn] io.readfile: expected a path argument, returning null")
            return None
        path = str(args[0])
        if not _os.path.exists(path):
            print(f"[warn] io.readfile: file not found: {path}, returning null")
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read()
        except Exception as e:
            print(f"[warn] io.readfile: {e}, returning null")
            return None

    def _writefile(args):
        if len(args) < 2:
            print("[warn] io.writefile: expected (path, content), returning null")
            return None
        path    = str(args[0])
        content = format_value(args[1])
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            return True
        except Exception as e:
            print(f"[warn] io.writefile: {e}, returning null")
            return None

    return LzyModule("io", {
        "read":      _read,
        "write":     _write,
        "writeln":   _writeln,
        "readnum":   _readnum,
        "exists":    _exists,
        "readfile":  _readfile,
        "writefile": _writefile,
    })


def repl(env, evaluator):
    print(f"lzy interpreter v{VERSION}")
    print("loops: loop/as, forever, do  |  ops: + - * / % ** == === != < > <= >= and or not")
    print("type 'vars' to inspect variables, 'exit' to quit\n")

    buffer = ""

    while True:
        try:
            prompt = "lzy> " if not buffer else "  -> "
            line   = input(prompt)

            if not buffer:
                if line.strip() == "exit":  break
                if line.strip() == "vars":  show_vars(env); continue

            buffer += line + "\n"

            # keep reading until all braces are closed
            if count_braces(buffer) > 0:
                continue

            try:
                run(buffer, env, evaluator)
            except StrictError as e:
                print(f"[strict assert] {e}")
                input("  -> press enter to continue  ")
            except StopSignal:
                pass   # already printed "[stop] program ended"

            buffer = ""

        except KeyboardInterrupt:
            print("\nexiting")
            break


if __name__ == "__main__":
    env       = Environment()
    evaluator = Evaluator(env)
    env.vars["io"] = {"value": build_io_module(format_value), "type": "module", "strict": False, "safe": False}
    args      = sys.argv[1:]

    if len(args) >= 2 and args[0] == "-f":
        run_file(args[1], env, evaluator)

    elif len(args) == 1 and args[0].endswith(".lzy"):
        run_file(args[0], env, evaluator)

    elif len(args) == 0:
        repl(env, evaluator)

    else:
        print(LOGO)
        print("the laziest programming language")
        print("version",VERSION)
        print("usage:")
        print("  python lzy_run.py               -> start repl")
        print("  python lzy_run.py -f file.lzy   -> run a file")
        print("  python lzy_run.py file.lzy      -> shorthand")
