<div align="center">

![lzy logo](https://raw.githubusercontent.com/lzy-language/lzy/refs/heads/0.1/src/repl_assets/logo.png)
# lzy
**the laziest programming language ever**

*warn instead of crash · structural typing · built-in strictness control*

![Made with Python](https://forthebadge.com/badges/made-with-python.svg)
![🦈](https://forthebadge.com/api/badges/generate?panels=2&primaryLabel=FOR&secondaryLabel=SHARKS&primaryBGColor=%23A7BFC1&primaryTextColor=%23FFFFFF&secondaryBGColor=%235593C8&secondaryTextColor=%23FFFFFF&primaryFontSize=12&primaryFontWeight=600&primaryLetterSpacing=2&primaryFontFamily=Roboto&primaryTextTransform=uppercase&secondaryFontSize=12&secondaryFontWeight=900&secondaryLetterSpacing=2&secondaryFontFamily=Montserrat&secondaryTextTransform=uppercase)
![🦈](https://forthebadge.com/api/badges/generate?panels=2&primaryLabel=BY&secondaryLabel=SHARKS&primaryBGColor=%23A7BFC1&primaryTextColor=%23FFFFFF&secondaryBGColor=%235593C8&secondaryTextColor=%23FFFFFF&primaryFontSize=12&primaryFontWeight=600&primaryLetterSpacing=2&primaryFontFamily=Roboto&primaryTextTransform=uppercase&secondaryFontSize=12&secondaryFontWeight=900&secondaryLetterSpacing=2&secondaryFontFamily=Montserrat&secondaryTextTransform=uppercase)

</div>

---

## what is lzy?

lzy (pronounced *lazy*) is a dynamically typed, non-strict scripting language that prioritizes getting things done over enforcing rules. instead of crashing on type mismatches, lzy warns you and recovers. when you *do* want strictness, you opt in, surgically.

```r
!/ hello world !/
print("hello from lzy!")

!/ arrays warn instead of crash !/
numbers : int[] = [1, 2, "three", 4]
!/ [warn] array numbers: element 2 expected int32, got string
   recovered by: removing element !/

print(numbers)  !/ [1, 2, 4] !/

!/ opt into strictness where it matters !/
strict name : string = "lzy"
```

---

## features

- **warn and recover** — type mismatches remove the bad element and keep running
- **opt-in strictness** — `strict`, `nonstrict`, and `safe` modifiers per variable or per file
- **structural equality** — `==` checks shape, `===` checks name and type
- **lazywords** — built-in convenience functions with `|` call syntax
- **string interpolation** — `` `hello ${name}!` ``
- **`~` block syntax** — `if x > 5 ~ { ... }`
- **scope leaking** — variables defined inside `if`/`loop` blocks are visible outside
- **built-in debug tools** — `_start`, `_end`, `_sleep`
- ~~**`io` module** — file and terminal i/o built in~~ <sub>this isnt implemented in 0.1 yet</sub>

---

## installation

1. download the repo as zip or run
`git clone https://github.com/lzy-language/lzy`
2. install python or PyPy3 for better performance
3. to run the repl, run
```bash
pypy3 src/lzy_run.py
```
or to run a file..
```bash
pypy3 src/lzy_run.py path/to/file.lzy
```

---

## quick syntax

```r
!/ this is a comment !/

!*
    this is a
    multiline comment
*!

!/ variables - type is inferred !/
x = 5
name = "lzy"
active = true

!/ type hints !/
hp : int16 = 100
tag :: tinystring = "idle"

!/ arrays !/
scores : int[] = [10, 20, 30]
print(scores[0])   !/ 10 !/

!/ functions !/
fn add(a, b) ~ {
    return a + b
}
print(add(3, 4))   !/ 7 !/

!/ lazywords !/
lazy double|n : int| : int ~ { return n * 2 }
print(double|5|)   !/ 10 !/

!/ loops !/
loop 0..5 as i ~ {
    print(`iteration ${i}`)
}

do x < 10 ~ {
    x = x + 1
}

forever ~ {
    input = io.read("> ") !/ doesnt work in 0.1 atm !/
    if input == "quit" ~ stop
    print(`you said: ${input}`)
}

!/ strictness !/
strict null             !/ whole file is now strict !/

nonstrict ~ {
    messy = [1, "two", 3]   !/ this block is lenient !/
}

safe score = 0
score = "not available"     !/ safe variables can change type !/
```

---

## types

| type | description |
|---|---|
| `int` / `int8` / `int16` / `int32` / `int64` | integers (default: `int32`) |
| `float` / `float32` / `float64` / `float128` | floats (default: `float64`) |
| `string` / `longstring` / `tinystring` | strings |
| `bin` | boolean — `true` / `false` (or `t` / `f` in lenient mode) |
| `int[]` / `string[]` etc | typed arrays |

---

## project structure

```
src/
  lzy_run.py      entry point, repl, file runner
  lzy_lexer.py    tokenizer
  lzy_parser.py   ast builder
  lzy_eval.py     tree-walking interpreter
  lzy_ast.py      ast node classes
  lzy_env.py      environment, symbol table, signals
  lzy_tokens.py   token types and keywords
  lzy_types.py    type inference, coercion, compatibility
test_files/
  ...             files created by the main dev or others to test functionality
old/
  0.0.3           older versions of lzy
```

---

## file extensions

| extension | purpose |
|---|---|
| `.lzy` | source code |
| `.lzp` | project / config file (written in lzy syntax) |
| `.lz.*` | typed data files (e.g. `.lz.json`, `.lz.csv`) |

---

## license

licensed under [MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/)

created by [gkugfk3](https://github.com/gkugfk3) with ♡
> <sub>this markdown file was NOT written by generative ai</sub>
