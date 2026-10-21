"""Python -> Cambridge IGCSE (0984) pseudocode, following the syllabus pseudocode guide.

Choices: 0-based arrays (ARRAY[0:n-1]) so indexes match the Python, DECLARE lines added
automatically, identifiers converted to PascalCase (single-letter loop counters kept).
The output is for reading, not running.
"""
import ast
import io
import json
import keyword as _kw
import tokenize

KEYWORDS = {"DECLARE", "CONSTANT", "INPUT", "OUTPUT", "IF", "THEN", "ELSE", "ELSEIF", "ENDIF", "CASE", "OF", "OTHERWISE",
            "ENDCASE", "FOR", "TO", "STEP", "NEXT", "REPEAT", "UNTIL", "WHILE", "DO", "ENDWHILE", "PROCEDURE",
            "ENDPROCEDURE", "FUNCTION", "ENDFUNCTION", "RETURNS", "RETURN", "CALL", "ARRAY", "INTEGER", "REAL",
            "CHAR", "STRING", "BOOLEAN", "TRUE", "FALSE", "AND", "OR", "NOT", "MOD", "DIV", "LENGTH", "LCASE",
            "UCASE", "SUBSTRING", "ROUND", "RANDOM", "OPENFILE", "READFILE", "WRITEFILE", "CLOSEFILE", "READ", "WRITE"}

INT, REAL, STR, BOOL = "INTEGER", "REAL", "STRING", "BOOLEAN"


def arr(t):
    return "ARRAY OF " + (t or INT)


def is_arr(t):
    return bool(t) and t.startswith("ARRAY")


def elem(t):
    return t[len("ARRAY OF "):] if is_arr(t) else None


class Unsupported(Exception):
    pass


def pascal(name):
    if len(name) == 1:
        return name if name in "ijk" else name.upper()
    parts = [p for p in name.split("_") if p]
    if not parts:
        return "Value"
    if name.isupper():                      # MAX_SIZE -> MaxSize
        parts = [p.lower() for p in parts]
    out = "".join(p[0].upper() + p[1:] for p in parts)
    if out.upper() in KEYWORDS:
        out += "Value"
    return out


# ---------------------------------------------------------------- scopes and types

class Scope:
    def __init__(self, name, params=(), parent=None):
        self.name = name
        self.types = {}          # python name -> pseudocode type
        self.params = list(params)
        self.parent = parent
        self.order = []          # first-assignment order
        self.sizes = {}          # array name -> size expression (pseudocode text)
        self.consts = {}         # python name -> literal text
        self.globals = set()

    def set(self, name, t):
        if name not in self.types:
            self.order.append(name)
        old = self.types.get(name)
        if t and (not old or old == "?" or (old == INT and t == REAL) or (old == arr("?") and is_arr(t))):
            self.types[name] = t
        elif name not in self.types or self.types[name] is None:
            self.types[name] = t or "?"

    def lookup(self, name):
        s = self
        while s:
            if name in s.types:
                return s.types[name]
            s = s.parent
        return None


class Translator:
    def __init__(self, src):
        self.src = src
        self.tree = ast.parse(src)
        self.lines = []           # (indent, text, pyline)
        self.notes = 0
        self.funcs = {}           # name -> FunctionDef
        self.func_info = {}       # name -> {"ret": type, "params": [types], "is_func": bool}
        self.files = {}           # python file variable -> filename text
        self.comments = self._comments(src)
        self.used_comments = set()
        self.all_consts = set()
        self.ctx = ("", 1)          # indent and Python line of the statement being written
        self.depth = 0              # nesting of "for x in <list/string>" loops (index names)
        self.explain = []           # short comments for the next line written, e.g. what a RANDOM gives

    # ---------- comments from the source (ast does not keep them)
    @staticmethod
    def _comments(src):
        out = []
        try:
            for tok in tokenize.generate_tokens(io.StringIO(src).readline):
                if tok.type == tokenize.COMMENT:
                    line_text = src.splitlines()[tok.start[0] - 1]
                    standalone = line_text[:tok.start[1]].strip() == ""
                    out.append((tok.start[0], tok.string.lstrip("#").strip(), standalone))
        except (tokenize.TokenError, IndentationError):
            pass
        return out

    def flush_comments(self, before_line, ind):
        for i, (ln, text, standalone) in enumerate(self.comments):
            if standalone and ln < before_line and i not in self.used_comments:
                self.used_comments.add(i)
                self.emit(ind, "// " + text if text else "//", ln)

    def trailing(self, line):
        for i, (ln, text, standalone) in enumerate(self.comments):
            if not standalone and ln == line and i not in self.used_comments:
                self.used_comments.add(i)
                return "    // " + text
        return ""

    def emit(self, ind, text, pyline):
        if self.explain and text and not text.startswith("//"):
            text += ("; " if "    // " in text else "    // ") + "; ".join(self.explain)
            self.explain = []
        self.lines.append((ind, text, pyline))

    def note(self, ind, text, pyline):
        self.notes += 1
        self.emit(ind, "// Note: " + text, pyline)

    # ---------- pass 1: work out types of variables, parameters and function results
    def infer(self):
        self.global_scope = Scope("<main>")
        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef):
                self.funcs[node.name] = node
        self.scopes = {}
        for _ in range(3):            # a few rounds so types flow between functions and calls
            self.global_scope.types.clear(); self.global_scope.order.clear()
            self.global_scope.sizes.clear(); self.global_scope.consts.clear()
            for name, fn in self.funcs.items():
                sc = Scope(name, [a.arg for a in fn.args.args], self.global_scope)
                self.scopes[name] = sc
                info = self.func_info.setdefault(name, {"ret": None, "params": [None] * len(fn.args.args)})
                for a, t in zip(fn.args.args, info["params"]):
                    sc.types[a.arg] = t or "?"
                info["is_func"] = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(fn))
            main = [n for n in self.tree.body if not isinstance(n, ast.FunctionDef)]
            self.scan_block(main, self.global_scope, top=True)
            for name, fn in self.funcs.items():
                self.scan_block(fn.body, self.scopes[name])
                rets = [self.etype(n.value, self.scopes[name]) for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value is not None]
                rets = [r for r in rets if r and r != "?"]
                if rets:
                    self.func_info[name]["ret"] = REAL if REAL in rets else rets[0]
                # parameter usage hints
                sc = self.scopes[name]
                for i, a in enumerate(fn.args.args):
                    if self.func_info[name]["params"][i]:
                        continue
                    for n in ast.walk(fn):
                        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == a.arg:
                            self.func_info[name]["params"][i] = arr(INT)
                        if isinstance(n, ast.For) and isinstance(n.iter, ast.Name) and n.iter.id == a.arg:
                            self.func_info[name]["params"][i] = arr(INT)

    def scan_block(self, body, sc, top=False):
        for node in body:
            self.scan(node, sc, top)

    def scan(self, node, sc, top=False):
        if isinstance(node, ast.Global):
            sc.globals.update(node.names)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                self.bind(t, node.value, sc, top and len(node.targets) == 1)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                self.bind(node.target, node.value, sc, False)
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            t = self.etype(node.value, sc)
            cur = sc.lookup(node.target.id)
            sc.set(node.target.id, REAL if REAL in (t, cur) or isinstance(node.op, ast.Div) else (cur if cur and cur != "?" else t))
        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                it = node.iter
                if self.is_range(it):
                    sc.set(node.target.id, INT)
                    self.scan_block(node.body, sc)
                else:
                    t = self.etype(it, sc)
                    sc.set(node.target.id, STR if t == STR else (elem(t) or "?"))
                    sc.set(self.index_name(), INT)
                    self.depth += 1
                    self.scan_block(node.body, sc)
                    self.depth -= 1
            else:
                self.scan_block(node.body, sc)
            self.scan_block(node.orelse, sc)
        elif isinstance(node, (ast.While, ast.If)):
            self.scan_block(node.body, sc)
            self.scan_block(node.orelse, sc)
        elif isinstance(node, ast.Match):
            for c in node.cases:
                self.scan_block(c.body, sc)
        elif isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.optional_vars, ast.Name):
                    self.file_open(item.context_expr, item.optional_vars.id)
            self.scan_block(node.body, sc)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            c = node.value
            if isinstance(c.func, ast.Attribute) and c.func.attr == "append" and isinstance(c.func.value, ast.Name) and c.args:
                t = self.etype(c.args[0], sc)
                if t and t != "?":
                    sc.set(c.func.value.id, arr(t))
        # calls anywhere: parameter types from arguments
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in self.funcs:
                info = self.func_info.setdefault(n.func.id, {"ret": None, "params": [None] * len(self.funcs[n.func.id].args.args)})
                for i, a in enumerate(n.args[:len(info["params"])]):
                    t = self.etype(a, sc)
                    if t and t != "?" and (not info["params"][i] or info["params"][i] == INT and t == REAL):
                        info["params"][i] = t

    def file_open(self, call, var):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "open" and call.args:
            self.files[var] = self.expr(call.args[0], None)

    def bind(self, target, value, sc, maybe_const):
        if isinstance(target, ast.Name):
            name = target.id
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "open":
                self.file_open(value, name)
                return
            t = self.etype(value, sc)
            if isinstance(value, ast.List):
                sc.sizes[name] = str(len(value.elts) - 1) if value.elts else None
                if value.elts and all(isinstance(e, ast.List) for e in value.elts):
                    sc.sizes[name] = (str(len(value.elts) - 1), str(len(value.elts[0].elts) - 1))
            elif isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mult) and isinstance(value.left, ast.List):
                try:
                    sc.sizes[name] = self.expr(self.minus1(value.right), sc)
                except Unsupported:
                    sc.sizes[name] = None
                sc.set(self.index_name(), INT)
            if maybe_const and name.isupper() and len(name) > 1 and isinstance(value, ast.Constant) and name not in sc.consts:
                sc.consts[name] = self.literal(value.value)
            sc.set(name, t)
        elif isinstance(target, (ast.Tuple, ast.List)):
            vals = value.elts if isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts) else [None] * len(target.elts)
            for tg, v in zip(target.elts, vals):
                if isinstance(tg, ast.Name):
                    sc.set(tg.id, self.etype(v, sc) if v is not None else "?")
            if self.is_swap(target, value):
                sc.set("temp", self.etype(target.elts[0], sc))
            elif isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts) and self.depends(target, value):
                for i, v in enumerate(value.elts):
                    sc.set(f"temp{i + 1}", self.etype(v, sc))
        elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
            t = self.etype(value, sc)
            if t and t != "?" and not sc.lookup(target.value.id):
                sc.set(target.value.id, arr(t))

    def etype(self, n, sc):
        if n is None:
            return None
        if isinstance(n, ast.Constant):
            v = n.value
            return BOOL if isinstance(v, bool) else INT if isinstance(v, int) else REAL if isinstance(v, float) else STR if isinstance(v, str) else None
        if isinstance(n, ast.JoinedStr):
            return STR
        if isinstance(n, ast.Name):
            return sc.lookup(n.id) if sc else None
        if isinstance(n, ast.List):
            ts = [self.etype(e, sc) for e in n.elts]
            ts = [t for t in ts if t and t != "?"]
            if ts and all(is_arr(t) for t in ts):
                return arr(elem(ts[0]))          # 2D: element type of the rows
            return arr(REAL if REAL in ts else (ts[0] if ts else "?"))
        if isinstance(n, ast.BinOp):
            a, b = self.etype(n.left, sc), self.etype(n.right, sc)
            if isinstance(n.op, ast.Mult) and isinstance(n.left, ast.List):
                return a
            if isinstance(n.op, ast.Div):
                return REAL
            if isinstance(n.op, (ast.FloorDiv, ast.Mod)):
                return INT
            if STR in (a, b):
                return STR
            if REAL in (a, b):
                return REAL
            return INT if a == INT or b == INT else (a or b)
        if isinstance(n, ast.UnaryOp):
            return BOOL if isinstance(n.op, ast.Not) else self.etype(n.operand, sc)
        if isinstance(n, (ast.Compare, ast.BoolOp)):
            return BOOL
        if isinstance(n, ast.Subscript):
            t = self.etype(n.value, sc)
            if t == STR:
                return STR
            if isinstance(n.slice, ast.Slice):
                return t
            if isinstance(n.value, ast.Subscript):
                return elem(self.etype(n.value.value, sc)) if is_arr(self.etype(n.value.value, sc)) else elem(t)
            return elem(t)
        if isinstance(n, ast.IfExp):
            return self.etype(n.body, sc)
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                if f.id == "input" or f.id == "str":
                    return STR
                if f.id in ("int", "len"):
                    return INT
                if f.id == "float":
                    return REAL
                if f.id == "round":
                    return REAL if len(n.args) > 1 else INT
                if f.id == "bool":
                    return BOOL
                if f.id in ("abs", "max", "min", "sum"):
                    ts = [self.etype(a, sc) for a in n.args]
                    if ts and is_arr(ts[0]):
                        return elem(ts[0])
                    return REAL if REAL in ts else INT
                if f.id in self.func_info:
                    return self.func_info[f.id]["ret"]
            if isinstance(f, ast.Attribute):
                if f.attr in ("upper", "lower", "strip", "title", "capitalize", "replace", "readline", "read"):
                    return STR
                if f.attr in ("randint", "randrange", "count", "index", "find"):
                    return INT
                if f.attr in ("random", "sqrt", "uniform"):
                    return REAL
                if f.attr in ("isdigit", "isalpha", "isupper", "islower", "startswith", "endswith"):
                    return BOOL
        return None

    # ---------- helpers
    @staticmethod
    def is_range(n):
        return isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "range"

    @staticmethod
    def is_swap(target, value):
        return (isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple) and len(target.elts) == 2 == len(value.elts)
                and ast.unparse(target.elts[0]) == ast.unparse(value.elts[1]) and ast.unparse(target.elts[1]) == ast.unparse(value.elts[0]))

    @staticmethod
    def depends(target, value):
        """a, b = b, a + b: does a later value use an earlier target? Then temporaries are needed."""
        names = {ast.unparse(t) for t in target.elts}
        return any(ast.unparse(x) in names for v in value.elts for x in ast.walk(v) if isinstance(x, (ast.Name, ast.Subscript)))

    @staticmethod
    def minus1(n, k=1):
        """n - k, folding constants: (x - 1) - 1 -> x - 2, (x + 1) - 1 -> x."""
        if isinstance(n, ast.Constant) and isinstance(n.value, int) and not isinstance(n.value, bool):
            return ast.Constant(n.value - k)
        if isinstance(n, ast.BinOp) and isinstance(n.right, ast.Constant) and isinstance(n.right.value, int):
            if isinstance(n.op, ast.Sub):
                return ast.BinOp(n.left, ast.Sub(), ast.Constant(n.right.value + k))
            if isinstance(n.op, ast.Add):
                c = n.right.value - k
                if c == 0:
                    return n.left
                return ast.BinOp(n.left, ast.Add() if c > 0 else ast.Sub(), ast.Constant(abs(c)))
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)):
            return ast.BinOp(Translator.minus1(n.left, k), n.op, n.right)
        return ast.BinOp(n, ast.Sub(), ast.Constant(k))

    @staticmethod
    def literal(v):
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, str):
            return '"' + v.replace('"', "'") + '"'
        if isinstance(v, float):
            r = repr(v)
            return r if "." in r or "e" in r else r + ".0"
        if v is None:
            return "NULL"
        return str(v)

    def name(self, n):
        return pascal(n)

    # ---------- expressions
    PREC = {ast.Or: 1, ast.And: 2, ast.Not: 3, "cmp": 4, ast.Add: 5, ast.Sub: 5, ast.Mult: 6, ast.Div: 6, ast.Pow: 8}

    def sx(self, n, sc, parent_prec=0):
        try:
            return self.expr(n, sc, parent_prec)
        except Unsupported:
            ind, line = self.ctx
            src = ast.unparse(n)
            self.note(ind, f"no Cambridge pseudocode for {src[:60]} — shown in < >", line)
            return "<" + src + ">"

    def index_name(self):
        return "Index" if self.depth == 0 else f"Index{self.depth + 1}"

    def expr(self, n, sc, parent_prec=0):
        text, prec = self._expr(n, sc)
        return "(" + text + ")" if prec < parent_prec else text

    def _expr(self, n, sc):
        E = self.expr
        if isinstance(n, ast.Constant):
            return self.literal(n.value), 10
        if isinstance(n, ast.Name):
            if sc and n.id in self.all_consts:
                return pascal(n.id), 10
            return self.name(n.id), 10
        if isinstance(n, ast.JoinedStr):
            return " + ".join(self.fparts(n, sc)), 5
        if isinstance(n, ast.BinOp):
            op = type(n.op)
            if op is ast.Mod:
                return f"MOD({E(n.left, sc)}, {E(n.right, sc)})", 10
            if op is ast.FloorDiv:
                return f"DIV({E(n.left, sc)}, {E(n.right, sc)})", 10
            sym = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Pow: "^"}.get(op)
            if sym is None:
                raise Unsupported(ast.unparse(n))
            p = self.PREC[op]
            right_p = p + 1 if op in (ast.Sub, ast.Div) else p
            return f"{E(n.left, sc, p)} {sym} {E(n.right, sc, right_p)}", p
        if isinstance(n, ast.UnaryOp):
            if isinstance(n.op, ast.Not):
                return "NOT " + E(n.operand, sc, 5), 3
            if isinstance(n.op, ast.USub):
                return "-" + E(n.operand, sc, 7), 7
            return E(n.operand, sc), 7
        if isinstance(n, ast.BoolOp):
            op, p = ("AND", 2) if isinstance(n.op, ast.And) else ("OR", 1)
            return f" {op} ".join(E(v, sc, p + 1) for v in n.values), p
        if isinstance(n, ast.Compare):
            parts, left = [], n.left
            for op, right in zip(n.ops, n.comparators):
                parts.append(self.compare(left, op, right, sc))
                left = right
            if len(parts) == 1:
                return parts[0], 4
            return " AND ".join("(" + p + ")" for p in parts), 2
        if isinstance(n, ast.IfExp):
            raise Unsupported(ast.unparse(n))
        if isinstance(n, ast.Subscript):
            return self.subscript(n, sc), 10
        if isinstance(n, ast.Call):
            return self.call(n, sc), 10
        if isinstance(n, ast.Attribute):
            raise Unsupported(ast.unparse(n))
        raise Unsupported(ast.unparse(n))

    def compare(self, left, op, right, sc):
        E = self.expr
        if isinstance(op, (ast.In, ast.NotIn)) and isinstance(right, (ast.List, ast.Tuple)) and right.elts:
            eq = " OR ".join(f"{E(left, sc, 5)} = {E(v, sc, 5)}" for v in right.elts)
            return f"NOT ({eq})" if isinstance(op, ast.NotIn) else (f"({eq})" if len(right.elts) > 1 else eq)
        sym = {ast.Eq: "=", ast.NotEq: "<>", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=",
               ast.Is: "=", ast.IsNot: "<>"}.get(type(op))
        if sym is None:
            raise Unsupported(ast.unparse(ast.Compare(left, [op], [right])))
        return f"{E(left, sc, 5)} {sym} {E(right, sc, 5)}"

    def subscript(self, n, sc):
        E = self.expr
        base_t = self.etype(n.value, sc)
        if isinstance(n.slice, ast.Slice):
            if base_t == STR or base_t is None:
                s = n.slice
                if s.step is not None:
                    raise Unsupported(ast.unparse(n))
                start = E(s.lower, sc) if s.lower is not None else "0"
                start1 = E(ast.BinOp(s.lower, ast.Add(), ast.Constant(1)), sc) if s.lower is not None else "1"
                if isinstance(s.lower, ast.Constant):
                    start1 = str(s.lower.value + 1)
                if s.upper is not None:
                    length = E(s.upper, sc, 6) if s.lower is None else E(ast.BinOp(s.upper, ast.Sub(), s.lower), sc)
                    if isinstance(s.upper, ast.Constant) and isinstance(s.lower, ast.Constant):
                        length = str(s.upper.value - s.lower.value)
                else:
                    length = f"LENGTH({E(n.value, sc)})" + (f" - {start}" if s.lower is not None else "")
                return f"SUBSTRING({E(n.value, sc)}, {start1}, {length})"
            raise Unsupported(ast.unparse(n))
        if base_t == STR:
            idx = n.slice
            pos = str(idx.value + 1) if isinstance(idx, ast.Constant) and isinstance(idx.value, int) else E(ast.BinOp(idx, ast.Add(), ast.Constant(1)), sc)
            return f"SUBSTRING({E(n.value, sc)}, {pos}, 1)"
        if isinstance(n.value, ast.Subscript) and not isinstance(n.value.slice, ast.Slice) and self.etype(n.value.value, sc) != STR:
            return f"{E(n.value.value, sc)}[{E(n.value.slice, sc)}, {E(n.slice, sc)}]"
        return f"{E(n.value, sc)}[{E(n.slice, sc)}]"

    def call(self, n, sc):
        E = self.expr
        f, args = n.func, n.args
        if isinstance(f, ast.Name):
            fn = f.id
            if fn == "len" and len(args) == 1:
                return f"LENGTH({E(args[0], sc)})"
            if fn in ("int", "float", "str") and len(args) == 1:
                if isinstance(args[0], ast.Call) and isinstance(args[0].func, ast.Name) and args[0].func.id == "input":
                    raise Unsupported("input() inside an expression")
                if fn == "int" and self.etype(args[0], sc) == REAL:
                    return f"ROUND({E(args[0], sc)}, 0)"
                return E(args[0], sc)
            if fn == "round":
                return f"ROUND({E(args[0], sc)}, {E(args[1], sc) if len(args) > 1 else '0'})"
            if fn == "input":
                raise Unsupported("input() inside an expression")
            if fn in self.funcs:
                return f"{pascal(fn)}({', '.join(E(a, sc) for a in args)})"
            if fn in ("abs", "max", "min", "sum"):
                return f"{fn.upper()}({', '.join(E(a, sc) for a in args)})"
            raise Unsupported(ast.unparse(n))
        if isinstance(f, ast.Attribute):
            obj, attr = f.value, f.attr
            if attr == "upper" and not args:
                return f"UCASE({E(obj, sc)})"
            if attr == "lower" and not args:
                return f"LCASE({E(obj, sc)})"
            if isinstance(obj, ast.Name) and obj.id == "random":
                if attr == "random":
                    return "RANDOM()"
                if attr == "randint" and len(args) == 2:
                    lo, hi = args
                    if isinstance(lo, ast.Constant) and isinstance(hi, ast.Constant):
                        span = str(hi.value - lo.value)
                    else:
                        span = E(ast.BinOp(hi, ast.Sub(), lo), sc, 6)
                    base = f"ROUND(RANDOM() * {span}, 0)"
                    self.explain.append(f"a whole number from {E(lo, sc)} to {E(hi, sc)}")
                    return base if isinstance(lo, ast.Constant) and lo.value == 0 else f"{base} + {E(lo, sc, 6)}"
            if isinstance(obj, ast.Name) and obj.id == "math":
                if attr == "sqrt" and len(args) == 1:
                    return f"{E(args[0], sc, 9)} ^ 0.5"
                if attr == "pi":
                    return "3.14159"
            if isinstance(obj, ast.Name) and obj.id in self.files and attr in ("readline", "read"):
                raise Unsupported("file read in expression")
        raise Unsupported(ast.unparse(n))

    def fparts(self, n, sc):
        parts = []
        for v in n.values:
            if isinstance(v, ast.Constant):
                parts.append(self.literal(v.value))
            elif isinstance(v, ast.FormattedValue):
                if v.format_spec is not None:
                    spec = "".join(c.value for c in v.format_spec.values if isinstance(c, ast.Constant))
                    if spec.startswith(".") and spec.endswith("f") and spec[1:-1].isdigit():
                        parts.append(f"ROUND({self.expr(v.value, sc)}, {spec[1:-1]})")
                        continue
                parts.append(self.expr(v.value, sc))
        return parts

    def output_items(self, args, sc):
        """print(a, b) -> OUTPUT items, adding the spaces print() puts between values."""
        items = []
        for i, a in enumerate(args):
            pieces = self.flatten_str(a, sc)
            if i > 0:
                if items and items[-1].startswith('"') and items[-1].endswith('"'):
                    items[-1] = items[-1][:-1] + ' "'
                elif pieces and pieces[0].startswith('"'):
                    pieces[0] = '" ' + pieces[0][1:]
                else:
                    items.append('" "')
            items.extend(pieces)
        return items or ['""']

    def flatten_str(self, n, sc):
        if isinstance(n, ast.JoinedStr):
            return [p for p in self.fparts(n, sc) if p != '""']
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add) and STR in (self.etype(n.left, sc), self.etype(n.right, sc)):
            return self.flatten_str(n.left, sc) + self.flatten_str(n.right, sc)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "str" and len(n.args) == 1:
            return self.flatten_str(n.args[0], sc)
        return [self.sx(n, sc)]

    # ---------- statements
    def block(self, body, ind, sc):
        for node in body:
            self.flush_comments(node.lineno, ind)
            self.ctx = (ind, node.lineno)
            try:
                self.stmt(node, ind, sc)
            except Unsupported as e:
                self.note(ind, f"no Cambridge pseudocode for: {ast.unparse(node).splitlines()[0][:70]}", node.lineno)

    def is_input(self, v):
        """input(...), int(input(...)) or float(input(...)) -> prompt node or None, ok flag"""
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Name):
            if v.func.id == "input":
                return True, (v.args[0] if v.args else None)
            if v.func.id in ("int", "float") and len(v.args) == 1:
                return self.is_input(v.args[0])
        return False, None

    def stmt(self, n, ind, sc):
        I = ind
        sub = ind + "    "
        tr = self.trailing(n.lineno)
        L = n.lineno
        if isinstance(n, ast.Assign):
            if len(n.targets) == 1 and self.is_swap(n.targets[0], n.value):
                a, b = n.targets[0].elts
                self.emit(I, f"Temp ← {self.expr(a, sc)}{tr}", L)
                self.emit(I, f"{self.expr(a, sc)} ← {self.expr(b, sc)}", L)
                self.emit(I, f"{self.expr(b, sc)} ← Temp", L)
                return
            for target in n.targets:
                self.assign(target, n.value, I, sc, L, tr)
                tr = ""
            return
        if isinstance(n, ast.AnnAssign):
            if n.value is not None:
                self.assign(n.target, n.value, I, sc, L, tr)
            return
        if isinstance(n, ast.AugAssign):
            op = ast.BinOp(n.target, n.op, n.value)
            self.emit(I, f"{self.expr(n.target, sc)} ← {self.sx(op, sc)}{tr}", L)
            return
        if isinstance(n, ast.Expr):
            self.expr_stmt(n.value, I, sc, L, tr)
            return
        if isinstance(n, ast.If):
            self.if_stmt(n, I, sc, tr)
            return
        if isinstance(n, ast.For):
            self.for_stmt(n, I, sc, tr)
            return
        if isinstance(n, ast.Match):
            self.match_stmt(n, I, sc, tr)
            return
        if isinstance(n, ast.While):
            self.while_stmt(n, I, sc, tr)
            return
        if isinstance(n, ast.Return):
            if n.value is None:
                self.note(I, "a PROCEDURE ends here (RETURN is only used in a FUNCTION)", L)
            else:
                self.emit(I, f"RETURN {self.sx(n.value, sc)}{tr}", L)
            return
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in n.names]
            if not all(x in ("random", "math", "time") for x in names) and getattr(n, "module", None) not in ("random", "math"):
                self.note(I, f"uses the Python module {', '.join(names)} (not part of pseudocode)", L)
            return
        if isinstance(n, ast.Pass):
            self.emit(I, "// do nothing" + tr, L)
            return
        if isinstance(n, ast.Break):
            self.note(I, "leave the loop here (Cambridge pseudocode has no BREAK)", L)
            return
        if isinstance(n, ast.Continue):
            self.note(I, "skip to the next time round the loop (no CONTINUE in pseudocode)", L)
            return
        if isinstance(n, ast.Global):
            return
        if isinstance(n, ast.With):
            items = n.items
            if len(items) == 1 and isinstance(items[0].optional_vars, ast.Name) and items[0].optional_vars.id in self.files:
                var = items[0].optional_vars.id
                self.emit(I, f"OPENFILE {self.files[var]} FOR {self.file_mode(items[0].context_expr)}{tr}", L)
                self.block(n.body, I, sc)
                self.emit(I, f"CLOSEFILE {self.files[var]}", L)
                return
            raise Unsupported("with")
        if isinstance(n, ast.FunctionDef):
            raise Unsupported("nested function")
        raise Unsupported(type(n).__name__)

    def file_mode(self, call):
        mode = call.args[1].value if len(call.args) > 1 and isinstance(call.args[1], ast.Constant) else "r"
        return "WRITE" if mode.startswith(("w", "a")) else "READ"

    def assign(self, target, value, I, sc, L, tr):
        ok, prompt = self.is_input(value)
        if ok and isinstance(target, (ast.Name, ast.Subscript)):
            if prompt is not None:
                self.emit(I, f"OUTPUT {', '.join(self.flatten_str(prompt, sc))}", L)
            self.emit(I, f"INPUT {self.expr(target, sc)}{tr}", L)
            return
        if isinstance(target, ast.Name):
            name = target.id
            if name in self.const_names(sc):
                return                                   # shown as CONSTANT at the top
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "open":
                self.emit(I, f"OPENFILE {self.files.get(name, self.expr(value.args[0], sc))} FOR {self.file_mode(value)}{tr}", L)
                return
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) and isinstance(value.func.value, ast.Name) \
                    and value.func.value.id in self.files and value.func.attr in ("readline", "read"):
                self.emit(I, f"READFILE {self.files[value.func.value.id]}, {pascal(name)}{tr}", L)
                return
            if isinstance(value, ast.List):
                self.list_literal(pascal(name), value, I, sc, L, tr)
                return
            if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mult) and isinstance(value.left, ast.List) and len(value.left.elts) == 1:
                fill = self.sx(value.left.elts[0], sc)
                idx = self.index_name()
                self.emit(I, f"FOR {idx} ← 0 TO {self.expr(self.minus1(value.right), sc)}{tr}", L)
                self.emit(I + "    ", f"{pascal(name)}[{idx}] ← {fill}", L)
                self.emit(I, f"NEXT {idx}", L)
                return
        elif isinstance(target, (ast.Tuple, ast.List)):
            if isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts):
                if self.depends(target, value):
                    for i, v in enumerate(value.elts):
                        self.emit(I, f"Temp{i + 1} ← {self.sx(v, sc)}" + (tr if i == 0 else ""), L)
                    for i, t in enumerate(target.elts):
                        self.emit(I, f"{self.expr(t, sc)} ← Temp{i + 1}", L)
                    return
                for t, v in zip(target.elts, value.elts):
                    self.emit(I, f"{self.expr(t, sc)} ← {self.sx(v, sc)}{tr}", L)
                    tr = ""
                return
            raise Unsupported("unpacking")
        self.emit(I, f"{self.expr(target, sc)} ← {self.sx(value, sc)}{tr}", L)

    def list_literal(self, name, value, I, sc, L, tr):
        """numbers = [1, 2, 3] -> Numbers ← [1, 2, 3] (one line; 2D lists as [[...], [...]])"""
        if not value.elts:
            self.note(I, f"{name} starts empty — Cambridge arrays have a fixed size", L)
            return
        def lit(n):
            if isinstance(n, ast.List):
                return "[" + ", ".join(lit(e) for e in n.elts) + "]"
            return self.sx(n, sc)
        self.emit(I, f"{name} ← {lit(value)}{tr}", L)

    def expr_stmt(self, v, I, sc, L, tr):
        if isinstance(v, ast.Constant) and isinstance(v.value, str):         # docstring
            for line in v.value.strip().splitlines():
                self.emit(I, "// " + line.strip(), L)
            return
        if not isinstance(v, ast.Call):
            raise Unsupported("expression")
        f = v.func
        if isinstance(f, ast.Name) and f.id == "print":
            self.emit(I, f"OUTPUT {', '.join(self.output_items(v.args, sc))}{tr}", L)
            return
        if isinstance(f, ast.Name) and f.id == "input":
            if v.args:
                self.emit(I, f"OUTPUT {', '.join(self.flatten_str(v.args[0], sc))}", L)
            self.emit(I, f"INPUT Dummy{tr}", L)
            return
        if isinstance(f, ast.Name) and f.id in self.funcs:
            args = ", ".join(self.sx(a, sc) for a in v.args)
            self.emit(I, f"CALL {pascal(f.id)}" + (f"({args})" if args or self.funcs[f.id].args.args else "") + tr, L)
            return
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            obj = f.value.id
            if obj in self.files:
                if f.attr == "write" and v.args:
                    self.emit(I, f"WRITEFILE {self.files[obj]}, {self.expr(v.args[0], sc)}{tr}", L)
                    return
                if f.attr == "close":
                    self.emit(I, f"CLOSEFILE {self.files[obj]}{tr}", L)
                    return
            if f.attr == "append" and v.args:
                self.note(I, f"add {self.expr(v.args[0], sc)} to the end of {pascal(obj)} (Cambridge arrays have a fixed size)", L)
                return
        raise Unsupported("call")

    def is_elif(self, node):
        """ast stores elif as else: [if ...]; tell them apart from the source line."""
        return self.src.splitlines()[node.lineno - 1].lstrip().startswith("elif")

    def if_stmt(self, n, I, sc, tr):
        # Layout: IF <condition> THEN / ELSEIF <condition> THEN / ELSE / ENDIF, bodies indented four spaces
        self.emit(I, f"IF {self.sx(n.test, sc)} THEN{tr}", n.lineno)
        self.block(n.body, I + "    ", sc)
        node = n
        while len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If) and self.is_elif(node.orelse[0]):
            e = node.orelse[0]
            self.flush_comments(e.lineno, I)
            self.ctx = (I, e.lineno)
            self.emit(I, f"ELSEIF {self.sx(e.test, sc)} THEN{self.trailing(e.lineno)}", e.lineno)
            self.block(e.body, I + "    ", sc)
            node = e
        if node.orelse:
            self.emit(I, "ELSE", node.orelse[0].lineno)
            self.block(node.orelse, I + "    ", sc)
        self.emit(I, "ENDIF", n.lineno)

    def match_stmt(self, n, I, sc, tr):
        """match / case -> CASE OF ... OTHERWISE ... ENDCASE"""
        self.emit(I, f"CASE OF {self.sx(n.subject, sc)}{tr}", n.lineno)
        for c in n.cases:
            p = c.pattern
            if c.guard is not None:
                raise Unsupported("case with if")
            if isinstance(p, ast.MatchAs) and p.pattern is None and p.name is None:
                label = "OTHERWISE"
            elif isinstance(p, ast.MatchValue):
                label = self.sx(p.value, sc) + " :"
            elif isinstance(p, ast.MatchOr) and all(isinstance(x, ast.MatchValue) for x in p.patterns):
                label = ", ".join(self.sx(x.value, sc) for x in p.patterns) + " :"
            else:
                raise Unsupported("case pattern")
            if len(c.body) == 1 and self.simple(c.body[0]):
                self.emit(I + "  ", f"{label} {self.inline(c.body[0], sc)}", c.body[0].lineno)
            else:
                self.emit(I + "  ", label, p.lineno if hasattr(p, "lineno") else n.lineno)
                self.block(c.body, I + "      ", sc)
        self.emit(I, "ENDCASE", n.lineno)

    def simple(self, s):
        if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], (ast.Name, ast.Subscript)) and not self.is_input(s.value)[0]:
            return True
        if isinstance(s, ast.AugAssign):
            return True
        return isinstance(s, ast.Expr) and isinstance(s.value, ast.Call) and isinstance(s.value.func, ast.Name) and s.value.func.id == "print"

    def inline(self, s, sc):
        saved = self.lines
        self.lines = []
        self.stmt(s, "", sc)
        text = self.lines[0][1]
        self.lines = saved
        return text

    def for_stmt(self, n, I, sc, tr):
        if n.orelse:
            raise Unsupported("for-else")
        if not isinstance(n.target, ast.Name):
            raise Unsupported("for with several variables")
        var = pascal(n.target.id)
        it = n.iter
        if self.is_range(it):
            a = it.args
            if len(a) == 1:
                start, stop, step = ast.Constant(0), a[0], None
            elif len(a) == 2:
                start, stop, step = a[0], a[1], None
            else:
                start, stop, step = a
            neg = step is not None and isinstance(step, ast.UnaryOp) and isinstance(step.op, ast.USub) or \
                (isinstance(step, ast.Constant) and isinstance(step.value, int) and step.value < 0)
            end = self.minus1(stop, -1) if neg else self.minus1(stop)
            text = f"FOR {var} ← {self.sx(start, sc)} TO {self.sx(end, sc)}"
            if step is not None and not (isinstance(step, ast.Constant) and step.value == 1):
                text += f" STEP {self.expr(step, sc)}"
            self.emit(I, text + tr, n.lineno)
            self.block(n.body, I + "    ", sc)
            self.emit(I, f"NEXT {var}", n.lineno)
            return
        t = self.etype(it, sc)
        if isinstance(it, ast.Name) and it.id in self.files:
            raise Unsupported("for line in file")
        if isinstance(it, (ast.Name, ast.Attribute, ast.Subscript)) or t in (STR,) or is_arr(t):
            idx = self.index_name()
            seq = self.sx(it, sc)
            if t == STR:
                self.emit(I, f"FOR {idx} ← 1 TO LENGTH({seq}){tr}", n.lineno)
                self.emit(I + "    ", f"{var} ← SUBSTRING({seq}, {idx}, 1)", n.lineno)
            else:
                self.emit(I, f"FOR {idx} ← 0 TO LENGTH({seq}) - 1{tr}", n.lineno)
                self.emit(I + "    ", f"{var} ← {seq}[{idx}]", n.lineno)
            self.depth += 1
            self.block(n.body, I + "    ", sc)
            self.depth -= 1
            self.emit(I, f"NEXT {idx}", n.lineno)
            return
        raise Unsupported("for")

    @staticmethod
    def uses_name(node, name):
        return any(isinstance(x, ast.Name) and x.id == name for x in ast.walk(node))

    def while_stmt(self, n, I, sc, tr):
        if n.orelse:
            raise Unsupported("while-else")
        body = n.body
        # while True: ... if <cond>: break   ->   REPEAT ... UNTIL <cond>
        if isinstance(n.test, ast.Constant) and n.test.value is True and body and isinstance(body[-1], ast.If) \
                and len(body[-1].body) == 1 and isinstance(body[-1].body[0], ast.Break) and not body[-1].orelse \
                and not any(isinstance(x, ast.Break) for s in body[:-1] for x in ast.walk(s)):
            self.emit(I, "REPEAT" + tr, n.lineno)
            self.block(body[:-1], I + "    ", sc)
            self.flush_comments(body[-1].lineno, I + "    ")
            self.emit(I, f"UNTIL {self.sx(body[-1].test, sc)}", body[-1].lineno)
            return
        self.emit(I, f"WHILE {self.sx(n.test, sc)} DO{tr}", n.lineno)
        self.block(body, I + "    ", sc)
        self.emit(I, "ENDWHILE", n.lineno)

    # ---------- declarations
    def const_names(self, sc):
        root = sc
        while root.parent:
            root = root.parent
        return root.consts

    def declares(self, sc, I, L, skip=()):
        for name in sc.order:
            if name in skip or name in sc.consts or name in sc.globals or name in self.files:
                continue
            t = sc.types.get(name)
            if t == "?" or not t:
                self.emit(I, f"DECLARE {pascal(name)} : INTEGER    // check the data type", L)
                continue
            if is_arr(t):
                size = sc.sizes.get(name)
                et = elem(t) if elem(t) != "?" else INT
                if isinstance(size, tuple):
                    self.emit(I, f"DECLARE {pascal(name)} : ARRAY[0:{size[0]}, 0:{size[1]}] OF {et}", L)
                elif size:
                    self.emit(I, f"DECLARE {pascal(name)} : ARRAY[0:{size}] OF {et}", L)
                else:
                    self.emit(I, f"DECLARE {pascal(name)} : ARRAY[0:99] OF {et}    // choose a size", L)
                continue
            self.emit(I, f"DECLARE {pascal(name)} : {t}", L)

    # ---------- whole program
    def run(self):
        self.infer()
        if self.tree.body:
            self.flush_comments(self.tree.body[0].lineno, "")      # heading comments first
        counts = {}
        for n in ast.walk(self.tree):
            if isinstance(n, (ast.Assign, ast.AugAssign)):
                for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                    if isinstance(t, ast.Name):
                        counts[t.id] = counts.get(t.id, 0) + 1
        for k in [k for k in self.global_scope.consts if counts.get(k) != 1]:
            del self.global_scope.consts[k]
        self.all_consts = set(self.global_scope.consts)
        g = self.global_scope
        for name, lit in g.consts.items():
            self.emit("", f"CONSTANT {pascal(name)} ← {lit}", self.first_line(name))
        # procedures and functions come first, as in the syllabus
        for name, fn in self.funcs.items():
            self.flush_comments(fn.lineno, "")
            info, sc = self.func_info[name], self.scopes[name]
            params = []
            for a, t in zip(fn.args.args, info["params"]):
                params.append(f"{pascal(a.arg)} : {t if t and t != '?' else 'INTEGER'}")
            p = f"({', '.join(params)})" if params else ""
            tr = self.trailing(fn.lineno)
            if info["is_func"]:
                rt = info["ret"] if info["ret"] and info["ret"] != "?" else "INTEGER"
                self.emit("", f"FUNCTION {pascal(name)}{p} RETURNS {rt}{tr}", fn.lineno)
            else:
                self.emit("", f"PROCEDURE {pascal(name)}{p}{tr}", fn.lineno)
            body = fn.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                self.stmt(body[0], "    ", sc)
                body = body[1:]
            self.declares(sc, "    ", fn.lineno, skip=set(sc.params) | sc.globals)
            self.block(body, "    ", sc)
            end_line = max(getattr(x, "end_lineno", fn.lineno) or fn.lineno for x in ast.walk(fn) if hasattr(x, "lineno"))
            self.flush_comments(end_line + 1, "    ")
            self.emit("", "ENDFUNCTION" if info["is_func"] else "ENDPROCEDURE", fn.lineno)
            self.emit("", "", fn.lineno)
        main = [n for n in self.tree.body if not isinstance(n, ast.FunctionDef)]
        if main:
            self.declares(g, "", main[0].lineno)
            if g.order:
                self.emit("", "", main[0].lineno)
            self.block(main, "", g)
        self.flush_comments(10 ** 9, "")
        while self.lines and not self.lines[-1][1]:
            self.lines.pop()
        return self.lines

    def first_line(self, name):
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
                return n.lineno
        return 1


def translate(src):
    """JSON: {"lines": [[text, pyline], ...], "notes": n} or {"error": msg, "line": n}"""
    if not src.strip():
        return json.dumps({"lines": [], "notes": 0})
    try:
        t = Translator(src)
    except SyntaxError as e:
        return json.dumps({"error": f"{e.msg}", "line": e.lineno})
    try:
        lines = t.run()
    except Exception as e:      # never break the page: show what went wrong
        return json.dumps({"error": f"Could not translate this code ({type(e).__name__}: {e})", "line": None})
    return json.dumps({"lines": [[ind + text, ln] for ind, text, ln in lines], "notes": t.notes})
