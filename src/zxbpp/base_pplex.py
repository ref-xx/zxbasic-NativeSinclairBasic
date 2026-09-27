# --------------------------------------------------------------------
# SPDX-License-Identifier: AGPL-3.0-or-later
# © Copyright 2008-2024 José Manuel Rodríguez de la Rosa and contributors.
# See the file CONTRIBUTORS.md for copyright details.
# See https://www.gnu.org/licenses/agpl-3.0.html for details.
# --------------------------------------------------------------------

import os
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum, unique

from src.api import lex, utils
from src.api.config import OPTIONS
from src.zxbpp.prepro import output
from src.zxbpp.prepro.builtinmacro import BuiltinMacro
from src.zxbpp.prepro.definestable import DefinesTable

EOL = "\n"


def filter_basinc_metadata(text: str) -> str:
    """Filters BasInc metadata lines (Check, Auto, #Note, Var, # Run-time Variables, etc.)
    replacing them with empty lines to preserve line numbers.
    """
    lines = text.splitlines(keepends=True)
    new_lines = []
    in_runtime_vars = False

    for line in lines:
        s = line.strip()
        lower = s.lower()
        if lower.startswith("# run-time variables"):
            in_runtime_vars = True
            new_lines.append("\n")
            continue
        if lower.startswith("# end run-time variables"):
            in_runtime_vars = False
            new_lines.append("\n")
            continue
        if in_runtime_vars:
            new_lines.append("\n")
            continue
        if (
            lower.startswith("check ")
            or lower.startswith("auto ")
            or lower.startswith("var ")
            or lower.startswith("#note ")
            or (
                s.startswith("#")
                and not re.match(
                    r"^#\s*(include|define|undef|ifdef|ifndef|else|elif|endif|line|init|pragma)\b", s, re.IGNORECASE
                )
            )
        ):
            new_lines.append("\n")
            continue
        new_lines.append(line)
    return "".join(new_lines)


def split_dim_items(dims_str: str) -> list[str]:
    """Splits comma-separated DIM items taking nested parentheses into account."""
    items = []
    cur = []
    paren_depth = 0
    for ch in dims_str:
        if ch == '(':
            paren_depth += 1
            cur.append(ch)
        elif ch == ')':
            paren_depth -= 1
            cur.append(ch)
        elif ch == ',' and paren_depth == 0:
            item = ''.join(cur).strip()
            if item:
                items.append(item)
            cur = []
        else:
            cur.append(ch)
    if cur:
        item = ''.join(cur).strip()
        if item:
            items.append(item)
    return items


def parse_dim_item(item: str) -> tuple[str | None, list[str] | None]:
    """Parses an item like 'a$(10)' or 'a$(10, 20)' or 'n(5)'."""
    m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*\$?)\s*\((.*)\)$', item.strip())
    if not m:
        return None, None
    name = m.group(1)
    inner = m.group(2).strip()
    dims = split_dim_items(inner)
    return name, dims


def transform_dim_statement(dim_stmt: str) -> str:
    """Transforms a single DIM statement (e.g. '10 DIM a$(10)' or 'DIM a$(10, 20)')."""
    m = re.match(r'^(\s*(?:\d+\s+)?)DIM\s+(.*)$', dim_stmt.strip(), re.IGNORECASE)
    if not m:
        return dim_stmt

    prefix = m.group(1) or ""
    rest = m.group(2).strip()

    raw_items = split_dim_items(rest)
    if not raw_items:
        return dim_stmt

    has_string_array = any(
        (parse_dim_item(it)[0] or "").endswith("$") for it in raw_items
    )
    if not has_string_array:
        return dim_stmt

    transformed_parts = []
    numeric_dims = []

    for raw_item in raw_items:
        name, dims = parse_dim_item(raw_item)
        if not name or not dims or not name.endswith("$"):
            numeric_dims.append(raw_item)
            continue

        if len(dims) == 1:
            # 1D string array in Sinclair BASIC = single fixed-length string of dims[0]
            length = dims[0].strip()
            transformed_parts.append(f"LET {name} = SPACE$({length})")
        elif len(dims) == 2:
            # 2D string array in Sinclair BASIC = dims[0] strings of length dims[1]
            count = dims[0].strip()
            length = dims[1].strip()
            transformed_parts.append(
                f"DIM {name}({count}): FOR __zxb_dim_k = LBOUND({name}) TO ({count}): LET {name}(__zxb_dim_k) = SPACE$({length}): NEXT __zxb_dim_k"
            )
        else:
            outer_dims = ", ".join(d.strip() for d in dims[:-1])
            transformed_parts.append(f"DIM {name}({outer_dims})")

    statements = []
    if numeric_dims:
        statements.append(f"DIM {', '.join(numeric_dims)}")
    statements.extend(transformed_parts)

    return prefix + ": ".join(statements)


def transform_sinclair_dim(text: str) -> str:
    """Transforms Sinclair BASIC 'DIM v$(...)' statements for --basinc mode."""
    lines = text.splitlines(keepends=True)
    out_lines = []

    for line in lines:
        line_ending = "\n" if line.endswith("\n") else ""
        raw_line = line.rstrip("\r\n")

        # Split line into segments: string literals, REM comments, and code
        segments = []
        i = 0
        n = len(raw_line)
        in_str = False
        cur = []

        while i < n:
            ch = raw_line[i]
            if not in_str:
                if ch == '"':
                    if cur:
                        segments.append(("code", "".join(cur)))
                        cur = []
                    in_str = True
                    cur.append(ch)
                    i += 1
                    continue
                elif (
                    raw_line[i:i + 4].upper() == "REM "
                    or raw_line[i:i + 4].upper() == "REM\t"
                    or raw_line[i:].upper() == "REM"
                ):
                    if cur:
                        segments.append(("code", "".join(cur)))
                        cur = []
                    segments.append(("rem", raw_line[i:]))
                    cur = []
                    i = n
                    break
                else:
                    cur.append(ch)
                    i += 1
            else:
                cur.append(ch)
                if ch == '"':
                    if i + 1 < n and raw_line[i + 1] == '"':
                        cur.append('"')
                        i += 2
                        continue
                    else:
                        in_str = False
                        segments.append(("str", "".join(cur)))
                        cur = []
                i += 1

        if cur:
            segments.append(("str" if in_str else "code", "".join(cur)))

        # Process code segments
        new_segments = []
        for seg_type, seg_val in segments:
            if seg_type != "code" or "DIM" not in seg_val.upper() or "$" not in seg_val:
                new_segments.append(seg_val)
                continue

            parts = seg_val.split(":")
            new_parts = []
            for part in parts:
                if re.search(r'\bDIM\b', part, re.IGNORECASE) and "$" in part:
                    new_parts.append(transform_dim_statement(part))
                else:
                    new_parts.append(part)
            new_segments.append(": ".join(new_parts))

        out_lines.append("".join(new_segments) + line_ending)

    return "".join(out_lines)


def transform_sinclair_deffn(text: str) -> str:
    """Transforms Sinclair BASIC 'DEF FN' definitions and 'FN' calls
    into Boriel ZX Basic compatible 'FUNCTION FN... / END FUNCTION'.
    Prefixes function name with 'FN' to avoid conflicts with arrays.
    Preserves line numbers, string literals, and REM comments.
    """
    lines = text.splitlines(keepends=True)
    out_lines = []

    for line in lines:
        line_ending = "\n" if line.endswith("\n") else ""
        raw_line = line.rstrip("\r\n")

        # Split line into segments: string literals, REM comments, and code
        segments = []
        i = 0
        n = len(raw_line)
        in_str = False
        cur = []

        while i < n:
            ch = raw_line[i]
            if not in_str:
                if ch == '"':
                    if cur:
                        segments.append(("code", "".join(cur)))
                        cur = []
                    in_str = True
                    cur.append(ch)
                    i += 1
                    continue
                elif (
                    raw_line[i:i + 4].upper() == "REM "
                    or raw_line[i:i + 4].upper() == "REM\t"
                    or raw_line[i:].upper() == "REM"
                ):
                    if cur:
                        segments.append(("code", "".join(cur)))
                        cur = []
                    segments.append(("rem", raw_line[i:]))
                    cur = []
                    i = n
                    break
                else:
                    cur.append(ch)
                    i += 1
            else:
                cur.append(ch)
                if ch == '"':
                    if i + 1 < n and raw_line[i + 1] == '"':
                        cur.append('"')
                        i += 2
                        continue
                    else:
                        in_str = False
                        segments.append(("str", "".join(cur)))
                        cur = []
                i += 1

        if cur:
            segments.append(("str" if in_str else "code", "".join(cur)))

        # Process code segments
        new_segments = []
        for seg_type, seg_val in segments:
            if seg_type != "code":
                new_segments.append(seg_val)
                continue

            parts = seg_val.split(":")
            new_parts = []
            for part in parts:
                m_def = re.match(
                    r'^(\s*(?:\d+\s+)?)DEF\s+FN\s+([a-zA-Z_][a-zA-Z0-9_]*\$?)\s*(?:\((.*?)\))?\s*=\s*(.*)$',
                    part,
                    re.IGNORECASE,
                )
                if m_def:
                    prefix = m_def.group(1) or ""
                    fname = m_def.group(2)
                    params = m_def.group(3)
                    params_str = f"({params})" if params is not None else "()"
                    expr = m_def.group(4).strip()
                    fn_name = f"FN{fname}"
                    part = f"{prefix}FUNCTION {fn_name}{params_str}: RETURN {expr}: END FUNCTION"
                else:
                    part = re.sub(
                        r'\bFN\s+([a-zA-Z_][a-zA-Z0-9_]*\$?)',
                        r'FN\1',
                        part,
                        flags=re.IGNORECASE,
                    )
                new_parts.append(part)
            new_segments.append(":".join(new_parts))

        out_lines.append("".join(new_segments) + line_ending)

    return "".join(out_lines)

# Names for std input/output
STDERR = "(stderr)"
STDIN = "(stdin)"
STDOUT = "(stdout)"


@unique
class ReservedDirectives(StrEnum):
    INCLUDE = "INCLUDE"
    ONCE = "ONCE"
    DEFINE = "DEFINE"
    UNDEF = "UNDEF"
    IF = "IF"
    IFDEF = "IFDEF"
    IFNDEF = "IFNDEF"
    ELSE = "ELSE"
    ELIF = "ELIF"
    ENDIF = "ENDIF"
    INIT = "INIT"
    LINE = "LINE"
    REQUIRE = "REQUIRE"
    PRAGMA = "PRAGMA"
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class LexerState:
    filename: str
    lineno: int
    lex: lex.Lexer | None
    input_data: str


class BaseLexer:
    """Own class lexer to allow multiple instances.
    This lexer is just a wrapper of the current FILESTACK[-1] lexer
    It's the base class for the asm and basic preprocessor lexers.
    """

    reserved_directives = {x.value.lower(): x.value for x in ReservedDirectives}

    builtin_macros = {
        "__ABS_FILE__": lambda token: f'"{utils.get_absolute_filename_path(token.fname)}"',
        "__BASE_FILE__": lambda token: f'"{os.path.basename(token.fname)}"',
        "__FILE__": lambda token: f'"{token.fname}"',
        "__LINE__": lambda token: str(token.lineno),
    }

    def __init__(
        self, tokens: Iterable[str], states: Iterable[tuple[str, str]], defines_table: DefinesTable | None = None
    ):
        """Creates a new GLOBAL lexer instance"""
        self.lex: lex.Lexer | None = None
        self.filestack: list[LexerState] = []  # Current filename, and line number being parsed
        self.input_data: str = ""
        self.tokens = tuple(tokens)
        self.states = tuple(states)
        self.next_token = None  # if set to something, this will be returned once
        self.defines_table = defines_table

        if self.defines_table is None:
            return

        for macro_name, macro_func in self.builtin_macros.items():
            self.defines_table[macro_name] = BuiltinMacro(macro_name=macro_name, func=macro_func)

    def set_macro(self, macro_name: str, func: Callable[[str], str]) -> None:
        assert self.defines_table is not None
        self.defines_table[macro_name] = func

    def put_current_line(self, prefix: str = "", suffix: str = "") -> str:
        """Returns line and file for include / end of include sequences."""
        assert self.lex is not None
        return '%s#line %i "%s"%s' % (prefix, self.lineno, self.current_file, suffix)

    def include(self, filename: str) -> str:
        """Changes FILENAME and line count"""
        if filename != STDIN and filename in {x.filename for x in self.filestack}:  # Already included?
            self.warning("Recursive inclusion")

        self.filestack.append(LexerState(filename, 1, self.lex, self.input_data))

        if self.lex is None:
            self.lex = lex.lex(object=self)
        else:
            self.lex = self.lex.clone()
            self.lex.lineno = 1  # resets line number

        result = self.put_current_line()  # First #line start with \n (EOL)

        try:
            if filename == STDIN:
                self.input_data = sys.stdin.read()
            else:
                self.input_data = utils.read_txt_file(filename)
            if filename == STDIN or filename.lower().endswith(".bas"):
                if getattr(OPTIONS, "basinc", False):
                    self.input_data = filter_basinc_metadata(self.input_data)
                    self.input_data = transform_sinclair_dim(self.input_data)
                self.input_data = transform_sinclair_deffn(self.input_data)
            if len(self.input_data) and self.input_data[-1] != EOL:
                self.input_data += EOL
        except IOError:
            self.input_data = EOL

        self.lex.input(self.input_data)
        return result

    def include_end(self):
        """Performs and end of include."""
        old_lineno = self.lex.lineno
        old_lexpos = self.lex.lexpos
        self.lex = self.filestack[-1].lex
        self.input_data = self.filestack[-1].input_data
        self.filestack.pop()

        if not self.filestack:  # End of input?
            return None

        self.filestack[-1].lineno += 1  # Increment line counter of previous file

        result = lex.LexToken()  # create token
        result.value = self.put_current_line(suffix="\n")
        result.type = "_ENDFILE_"
        result.lineno = old_lineno
        result.lexpos = old_lexpos
        result.fname = self.current_file

        return result

    def input(self, str_: str, filename: str = "", lexpos: int = 0):
        """Defines input string, removing current lexer."""
        self.filestack.append(LexerState(filename, 1, self.lex, self.input_data))
        self.input_data = str_
        self.set_state(str_, lexpos)

    def set_state(self, new_input: str, new_lexpos: int = 0):
        self.lex = lex.lex(object=self)
        self.lex.input(new_input)
        self.lexpos = new_lexpos

    @property
    def lexpos(self) -> int:
        if self.lex is None:
            return 0

        return self.lex.lexpos

    @lexpos.setter
    def lexpos(self, value: int):
        assert self.lex is not None
        self.lex.lexpos = value

    @property
    def lineno(self) -> int:
        if self.lex is None:
            return 0

        return self.lex.lineno

    @lineno.setter
    def lineno(self, value: int):
        assert self.lex is not None
        self.lex.lineno = value

    def token(self) -> lex.LexToken | None:
        """Returns a token from the current input. If tok is None
        from the current input, it means we are at end of current input
        (e.g. at end of include file). If so, closes the current input
        and discards it; then pops the previous input and lexer from
        the input stack, and gets another token.

        If new token is again None, repeat the process described above
        until the token is either not None, or self.lex is None, wich
        means we must effectively return None, because parsing has
        ended.
        """
        tok = None
        if self.next_token is not None:
            tok = lex.LexToken()
            tok.value = ""
            tok.lineno = self.lex.lineno
            tok.lexpos = self.lex.lexpos
            tok.type = self.next_token
            tok.fname = self.current_file
            self.next_token = None

        while self.lex is not None and tok is None:
            tok = self.lex.token()
            if tok is not None:
                tok.fname = self.current_file
                break

            tok = self.include_end()

        return tok

    def find_column(self, token) -> int:
        """Compute column:
        - token is a token instance
        """
        i = token.lexpos
        while i > 0:
            if self.input_data[i - 1] == "\n":
                break
            i -= 1

        column = token.lexpos - i + 1
        return column

    def error(self, msg: str, lineno: int = None):
        """Prints an error msg and continues execution."""
        if lineno is None:
            lineno = self.lineno
        output.error(lineno, msg)

    def warning(self, msg: str, lineno: int = None):
        """Emits a warning and continue execution."""
        if lineno is None:
            lineno = self.lineno
        output.warning(lineno, msg)

    @property
    def current_file(self) -> str | None:
        if not self.filestack:
            return None

        return self.filestack[-1].filename

    @current_file.setter
    def current_file(self, new_fname: str):
        assert self.filestack
        self.filestack[-1].filename = new_fname
