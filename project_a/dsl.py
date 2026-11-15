"""Safe interpreter for the compiled-rule DSL (implementation c). No eval(): a whitelisted AST walk over Fractions."""
import ast
from fractions import Fraction as F
from .common import slab_tax, sur_rate, thresh, round10


class DSLError(Exception):
    pass


class Machine:
    def __init__(self, tables):
        self.tables = tables
        self.funcs = {
            "min": min, "max": max, "round10": round10,
            "slab_tax": lambda t, x: slab_tax(x, self.tables[t]),
            "sur_rate": lambda t, x: sur_rate(x, self.tables[t]),
            "thresh": lambda t, x: thresh(x, self.tables[t]),
        }

    def ev(self, n, env):
        t = type(n)
        if t is ast.Expression:
            return self.ev(n.body, env)
        if t is ast.Constant:
            v = n.value
            if isinstance(v, float):
                return F(str(v))
            if isinstance(v, (int, str, bool)):
                return v
            raise DSLError(f"bad constant {v!r}")
        if t is ast.Name:
            if n.id not in env:
                raise DSLError(f"unknown name {n.id}")
            return env[n.id]
        if t is ast.BinOp:
            a, b = self.ev(n.left, env), self.ev(n.right, env)
            ops = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b, ast.Div: lambda: F(a) / F(b)}
            if type(n.op) not in ops:
                raise DSLError("operator not allowed")
            return ops[type(n.op)]()
        if t is ast.UnaryOp:
            v = self.ev(n.operand, env)
            if isinstance(n.op, ast.USub): return -v
            if isinstance(n.op, ast.Not): return not v
            raise DSLError("unary op not allowed")
        if t is ast.BoolOp:
            vals = [self.ev(v, env) for v in n.values]
            return all(vals) if isinstance(n.op, ast.And) else any(vals)
        if t is ast.Compare:
            l = self.ev(n.left, env)
            cmp = {ast.Lt: lambda a, b: a < b, ast.LtE: lambda a, b: a <= b, ast.Gt: lambda a, b: a > b,
                   ast.GtE: lambda a, b: a >= b, ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b}
            for op, c in zip(n.ops, n.comparators):
                r = self.ev(c, env)
                if type(op) not in cmp or not cmp[type(op)](l, r):
                    if type(op) not in cmp: raise DSLError("compare op not allowed")
                    return False
                l = r
            return True
        if t is ast.IfExp:
            return self.ev(n.body, env) if self.ev(n.test, env) else self.ev(n.orelse, env)
        if t is ast.Call:
            if not isinstance(n.func, ast.Name) or n.func.id not in self.funcs or n.keywords:
                raise DSLError("call not allowed")
            return self.funcs[n.func.id](*[self.ev(a, env) for a in n.args])
        raise DSLError(f"node {t.__name__} not allowed")

    def run(self, steps, env):
        env = dict(env); trace = []
        for s in steps:
            for k in ("id", "clause", "expr"):
                if not s.get(k):
                    raise DSLError(f"step missing {k}: {s}")
            v = self.ev(ast.parse(s["expr"], mode="eval"), env)
            env[s["id"]] = v
            if not isinstance(v, (str, bool)):
                from .common import num
                trace.append({"item": s["id"], "amount": num(v), "clause": s["clause"]})
        return env, trace
