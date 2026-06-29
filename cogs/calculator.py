import json
import multiprocessing
import pathlib
import socket
import time
from static import utcs, hpsh
from typing import List, Literal, Optional, Tuple
from types import CodeType
import requests
from bs4 import BeautifulSoup

import discord
from discord.ext import commands, tasks
from discord import app_commands, ForumChannel
import os
import random
import ast
import math
import cmath
import io
from PIL import Image, ImageDraw

# module constants
_EXPR_NAME = "<expression>"
_SAMPLES_PREFIX = "samples: "

class Calculator(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    # ---------- Helpers for Fourier ----------
    @staticmethod
    def _parse_series(text: str) -> List[float]:
        parts = [p for p in text.replace("\n", " ").replace("\t", " ").replace(";", ",").replace(" ", ",").split(",") if p]
        if not parts:
            return []
        out: List[float] = []
        for p in parts:
            out.append(float(p))
        return out

    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        return n > 0 and (n & (n - 1)) == 0

    @staticmethod
    def _dft(x: List[complex]) -> List[complex]:
        N = len(x)
        two_pi_over_n = 2 * math.pi / N
        out = []
        for k in range(N):
            s = 0j
            for n in range(N):
                angle = -two_pi_over_n * k * n
                s += x[n] * complex(math.cos(angle), math.sin(angle))
            out.append(s)
        return out

    @staticmethod
    def _idft(X: List[complex]) -> List[complex]:
        N = len(X)
        two_pi_over_n = 2 * math.pi / N
        out = []
        for n in range(N):
            s = 0j
            for k in range(N):
                angle = two_pi_over_n * k * n
                s += X[k] * complex(math.cos(angle), math.sin(angle))
            out.append(s / N)
        return out

    @staticmethod
    def _fft(x: List[complex]) -> List[complex]:
        N = len(x)
        if N == 1:
            return [x[0]]
        if not Calculator._is_power_of_two(N):
            # fallback to DFT if not radix-2 size
            return Calculator._dft(x)
        even = Calculator._fft(x[0::2])
        odd = Calculator._fft(x[1::2])
        out = [0j] * N
        for k in range(N // 2):
            t = cmath.exp(-2j * math.pi * k / N) * odd[k]
            out[k] = even[k] + t
            out[k + N // 2] = even[k] - t
        return out

    @staticmethod
    def _ifft(X: List[complex]) -> List[complex]:
        N = len(X)
        if N == 1:
            return [X[0]]
        if not Calculator._is_power_of_two(N):
            return Calculator._idft(X)
        # conjugate, FFT, conjugate, scale
        conj = [z.conjugate() for z in X]
        y = Calculator._fft(conj)
        return [z.conjugate() / N for z in y]

    # ---------- Shared safe-eval helpers ----------
    @staticmethod
    def _allowed_names() -> dict:
        names = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        # prefer math over cmath for real; expose cmath under same keys for complex support
        for k in dir(cmath):
            if not k.startswith("_") and k not in names:
                names[k] = getattr(cmath, k)
        names.update({
            "abs": abs, "min": min, "max": max, "pow": pow,
            "complex": complex, "pi": math.pi, "e": math.e, "tau": math.tau,
            "inf": math.inf, "nan": math.nan,
        })
        return names

    @staticmethod
    def _compile_expr(expr: str) -> CodeType:
        forbidden = ("__", "import", "exec", "eval", "open", "os.", "sys.", "subprocess", "shutil", ";", "lambda")
        if any(tok in expr for tok in forbidden):
            raise ValueError("不允許的表達式內容")
        return compile(expr, _EXPR_NAME, "eval")

    @staticmethod
    def _eval_expr(code: CodeType, vars: dict) -> complex:
        env: dict[str, object] = {"__builtins__": None}
        env.update(Calculator._allowed_names())
        env.update(vars)
        val = eval(code, env)
        if isinstance(val, (int, float)):
            return complex(val, 0.0)
        if isinstance(val, complex):
            return val
        raise ValueError("表達式應回傳數值")

    # ---------- Parsers ----------
    @staticmethod
    def _parse_numbers(text: str) -> List[float]:
        t = text.strip()
        if not t:
            return []
        # strip code block fences if present
        if t.startswith("```") and t.endswith("```"):
            t = t.strip("`\n ")
        # split by comma/space/semicolon
        parts = [p for p in t.replace("\n", " ").replace("\t", " ").replace(";", ",").replace(" ", ",").split(",") if p]
        return [float(p) for p in parts]

    @staticmethod
    def _parse_matrix(text: str) -> List[List[float]]:
        # rows separated by ';' or newline, cols by space/comma
        t = text.strip().strip("`")
        t = t.replace("\t", " ")
        rows = [r for r in t.replace(";", "\n").splitlines() if r.strip()]
        matrix: List[List[float]] = []
        for r in rows:
            parts = [p for p in r.replace(",", " ").split(" ") if p]
            matrix.append([float(p) for p in parts])
        # validate rectangular
        if not matrix:
            return []
        w = len(matrix[0])
        if any(len(row) != w for row in matrix):
            raise ValueError("矩陣每列的長度需相同")
        return matrix

    # ---------- Numeric calculus ----------
    @staticmethod
    def _derivative(expr_code: CodeType, x: float, h: float = 1e-5) -> complex:
        f1 = Calculator._eval_expr(expr_code, {"x": x + h})
        f2 = Calculator._eval_expr(expr_code, {"x": x - h})
        return (f1 - f2) / (2.0 * h)

    @staticmethod
    def _adaptive_simpson(expr_code: CodeType, a: float, b: float, tol: float = 1e-6, max_depth: int = 16) -> complex:
        def f(x):
            return Calculator._eval_expr(expr_code, {"x": x})
        def simpson(fa, fm, fb, a, b):
            return (b - a) * (fa + 4 * fm + fb) / 6.0
        def recurse(a, b, fa, fm, fb, area, depth):
            m = (a + b) / 2.0
            fml = f((a + m) / 2.0)
            fmr = f((m + b) / 2.0)
            left = simpson(fa, fml, fm, a, m)
            right = simpson(fm, fmr, fb, m, b)
            if depth <= 0 or abs(left + right - area) < 15 * tol:
                return left + right + (left + right - area) / 15.0
            return recurse(a, m, fa, fml, fm, left, depth - 1) + recurse(m, b, fm, fmr, fb, right, depth - 1)
        fa = f(a)
        fb = f(b)
        m = (a + b) / 2.0
        fm = f(m)
        area = (b - a) * (fa + 4 * fm + fb) / 6.0
        return recurse(a, b, fa, fm, fb, area, max_depth)

    # ---------- Linear algebra ----------
    @staticmethod
    def _mat_shape(a_mat: List[List[float]]) -> Tuple[int, int]:
        return (len(a_mat), len(a_mat[0]) if a_mat else 0)

    @staticmethod
    def _mat_mul(a_mat: List[List[float]], b_mat: List[List[float]]) -> List[List[float]]:
        n, m = Calculator._mat_shape(a_mat)
        m2, p = Calculator._mat_shape(b_mat)
        if m != m2:
            raise ValueError("維度不相容")
        out = [[0.0] * p for _ in range(n)]
        for i in range(n):
            for k in range(m):
                aik = a_mat[i][k]
                for j in range(p):
                    out[i][j] += aik * b_mat[k][j]
        return out

    @staticmethod
    def _mat_det(a_mat: List[List[float]]) -> float:
        n, m = Calculator._mat_shape(a_mat)
        if n != m:
            raise ValueError("需為方陣")
        # copy
        M = [row[:] for row in a_mat]
        det = 1.0
        for i in range(n):
            # pivot
            piv = i
            for r in range(i, n):
                if abs(M[r][i]) > abs(M[piv][i]):
                    piv = r
            if abs(M[piv][i]) < 1e-12:
                return 0.0
            if piv != i:
                M[i], M[piv] = M[piv], M[i]
                det *= -1
            pivval = M[i][i]
            det *= pivval
            # eliminate
            for r in range(i + 1, n):
                if M[r][i] == 0:
                    continue
                factor = M[r][i] / pivval
                for c in range(i, n):
                    M[r][c] -= factor * M[i][c]
        return det

    @staticmethod
    def _mat_inv(a_mat: List[List[float]]) -> List[List[float]]:
        n, m = Calculator._mat_shape(a_mat)
        if n != m:
            raise ValueError("需為方陣")
        M = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(a_mat)]
        # Gauss-Jordan
        for i in range(n):
            piv = i
            for r in range(i, n):
                if abs(M[r][i]) > abs(M[piv][i]):
                    piv = r
            if abs(M[piv][i]) < 1e-12:
                raise ValueError("矩陣不可逆")
            if piv != i:
                M[i], M[piv] = M[piv], M[i]
            pivval = M[i][i]
            for c in range(2 * n):
                M[i][c] /= pivval
            for r in range(n):
                if r == i:
                    continue
                factor = M[r][i]
                if factor == 0:
                    continue
                for c in range(2 * n):
                    M[r][c] -= factor * M[i][c]
        return [row[n:] for row in M]

    @staticmethod
    def _mat_solve(a_mat: List[List[float]], b: List[float]) -> List[float]:
        n, m = Calculator._mat_shape(a_mat)
        if n != m:
            raise ValueError("需為方陣")
        if len(b) != n:
            raise ValueError("b 維度不相容")
        M = [a_mat[i][:] + [b[i]] for i in range(n)]
        for i in range(n):
            piv = i
            for r in range(i, n):
                if abs(M[r][i]) > abs(M[piv][i]):
                    piv = r
            if abs(M[piv][i]) < 1e-12:
                raise ValueError("奇異矩陣")
            if piv != i:
                M[i], M[piv] = M[piv], M[i]
            pivval = M[i][i]
            for c in range(i, n + 1):
                M[i][c] /= pivval
            for r in range(i + 1, n):
                factor = M[r][i]
                if factor == 0:
                    continue
                for c in range(i, n + 1):
                    M[r][c] -= factor * M[i][c]
        # back-substitution
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            s = M[i][n]
            for c in range(i + 1, n):
                s -= M[i][c] * x[c]
            x[i] = s
        return x

    # ---------- Stats ----------
    @staticmethod
    def _percentile(data: List[float], p: float) -> float:
        if not data:
            raise ValueError("空資料")
        if not (0 <= p <= 100):
            raise ValueError("百分位需在 0..100")
        xs = sorted(data)
        if len(xs) == 1:
            return xs[0]
        k = (len(xs) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return xs[int(k)]
        return xs[f] * (c - k) + xs[c] * (k - f)

    # ---------- Probability ----------
    @staticmethod
    def _norm_pdf(x: float, mu: float, sigma: float) -> float:
        return (1.0 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma) ** 2)

    @staticmethod
    def _norm_cdf(x: float, mu: float, sigma: float) -> float:
        z = (x - mu) / (sigma * math.sqrt(2))
        return 0.5 * (1 + math.erf(z))

    @staticmethod
    def _comb(n: int, k: int) -> int:
        if k < 0 or k > n:
            return 0
        k = min(k, n - k)
        num = 1
        den = 1
        for i in range(1, k + 1):
            num *= n - (k - i)
            den *= i
        return num // den

    @staticmethod
    def _binom_pmf(k: int, n: int, p: float) -> float:
        return Calculator._comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

    @staticmethod
    def _binom_cdf(k: int, n: int, p: float) -> float:
        k = int(k)
        return sum(Calculator._binom_pmf(i, n, p) for i in range(0, k + 1))

    @staticmethod
    def _poisson_pmf(k: int, lam: float) -> float:
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    @staticmethod
    def _poisson_cdf(k: int, lam: float) -> float:
        return sum(Calculator._poisson_pmf(i, lam) for i in range(0, int(k) + 1))

    # ---------- Conversions ----------
    _unit_maps = {
        "length": {
            "m": 1.0, "cm": 0.01, "mm": 0.001, "km": 1000.0,
            "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344,
        },
        "mass": {
            "kg": 1.0, "g": 0.001, "lb": 0.45359237, "oz": 0.028349523125,
        },
        "time": {
            "s": 1.0, "ms": 0.001, "min": 60.0, "h": 3600.0, "day": 86400.0,
        },
        "angle": {
            "rad": 1.0, "deg": math.pi / 180.0,
        },
    }

    # ---------- Commands ----------
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="導數", with_app_command=True)
    @app_commands.rename(expr="函數", x="在_x", h="步長")
    @app_commands.default_permissions(administrator=True)
    async def 導數(self, ctx: commands.Context, expr: str, x: float, h: float = 1e-5):
        try:
            code = self._compile_expr(expr)
            d = self._derivative(code, x, h)
            msg = f"f'(x) | x={x} ≈ {d.real:.12g}" if abs(d.imag) < 1e-12 else f"f'(x) | x={x} ≈ {d:.12g}"
            await ctx.reply(msg)
        except Exception as e:
            await ctx.reply(f"計算錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="定積分", with_app_command=True)
    @app_commands.rename(expr="函數", a="下限", b="上限", tol="誤差")
    @app_commands.default_permissions(administrator=True)
    async def 定積分(self, ctx: commands.Context, expr: str, a: float, b: float, tol: float = 1e-6):
        try:
            code = self._compile_expr(expr)
            val = self._adaptive_simpson(code, a, b, tol=tol)
            msg = f"∫[{a},{b}] f(x) dx ≈ {val.real:.12g}" if abs(val.imag) < 1e-12 else f"∫[{a},{b}] f(x) dx ≈ {val:.12g}"
            await ctx.reply(msg)
        except Exception as e:
            await ctx.reply(f"計算錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="極限", with_app_command=True)
    @app_commands.rename(expr="函數", x0="趨近於", side="方向")
    @app_commands.default_permissions(administrator=True)
    async def 極限(self, ctx: commands.Context, expr: str, x0: float, side: Literal["雙側", "左", "右"] = "雙側"):
        try:
            code = self._compile_expr(expr)
            xs = []
            hs = [10.0 ** (-k) for k in range(1, 9)]
            vals: List[complex] = []
            for h in hs:
                pts = []
                if side in ("雙側",):
                    pts = [x0 - h, x0 + h]
                elif side == "左":
                    pts = [x0 - h]
                else:
                    pts = [x0 + h]
                for x in pts:
                    try:
                        v = self._eval_expr(code, {"x": x})
                        vals.append(v)
                        xs.append(x)
                    except Exception:
                        continue
            if not vals:
                raise ValueError("無法評估函數")
            # use median of last few values as estimate
            take = vals[-6:]
            re = sorted(v.real for v in take)
            im = sorted(v.imag for v in take)
            est = complex(re[len(re)//2], im[len(im)//2])
            msg = f"lim_(x→{x0}) f(x) ≈ {est.real:.12g}" if abs(est.imag) < 1e-12 else f"lim_(x→{x0}) f(x) ≈ {est:.12g}"
            await ctx.reply(msg)
        except Exception as e:
            await ctx.reply(f"計算錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="矩陣", with_app_command=True)
    @app_commands.rename(a="矩陣a", b_mat="矩陣b", b="向量v", op="操作")
    @app_commands.describe(
        a="矩陣A，如: '1 2; 3 4'",
        b_mat="可選矩陣B，用於乘法",
        b="可選向量v，如: '3, 7' 用於求解 Ax=b",
        op="操作: det/inv/mul/solve"
    )
    @app_commands.default_permissions(administrator=True)
    async def 矩陣(self, ctx: commands.Context, a: str, op: Literal["det", "inv", "mul", "solve"], b_mat: str = "", b: str = ""):
        try:
            mat_a = self._parse_matrix(a)
            if not mat_a:
                raise ValueError("無法解析矩陣A")
            if op == "det":
                d = self._mat_det(mat_a)
                await ctx.reply(f"det(A) = {d:.12g}")
                return
            if op == "inv":
                inv = self._mat_inv(mat_a)
                pretty = "\n".join(["[" + ", ".join(f"{v:.6g}" for v in row) + "]" for row in inv])
                await ctx.reply("A^{-1} =\n" + pretty)
                return
            if op == "mul":
                if not b_mat:
                    raise ValueError("缺少矩陣B")
                mat_b = self._parse_matrix(b_mat)
                C = self._mat_mul(mat_a, mat_b)
                pretty = "\n".join(["[" + ", ".join(f"{v:.6g}" for v in row) + "]" for row in C])
                await ctx.reply("A·B =\n" + pretty)
                return
            if op == "solve":
                if not b:
                    raise ValueError("缺少向量v")
                vb = self._parse_numbers(b)
                x = self._mat_solve(mat_a, vb)
                await ctx.reply("x = [" + ", ".join(f"{v:.6g}" for v in x) + "]")
                return
        except Exception as e:
            await ctx.reply(f"計算錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="統計", with_app_command=True)
    @app_commands.rename(data="數列", y="數列y", op="操作", p="百分位")
    @app_commands.describe(op="sum/mean/median/std/min/max/percentile/corr/regress")
    @app_commands.default_permissions(administrator=True)
    async def 統計(self, ctx: commands.Context, data: str, op: Literal["sum", "mean", "median", "std", "min", "max", "percentile", "corr", "regress"], y: str = "", p: float = 50.0):
        try:
            xs = self._parse_numbers(data)
            if not xs:
                raise ValueError("無法解析數列")
            if len(xs) > 100000:
                xs = xs[:100000]
            if op == "sum":
                await ctx.reply(f"sum = {sum(xs):.12g}")
                return
            if op == "mean":
                await ctx.reply(f"mean = {sum(xs)/len(xs):.12g}")
                return
            if op == "median":
                s = sorted(xs)
                n = len(s)
                med = (s[n//2] if n % 2 == 1 else 0.5*(s[n//2-1]+s[n//2]))
                await ctx.reply(f"median = {med:.12g}")
                return
            if op == "std":
                m = sum(xs)/len(xs)
                var = sum((v-m)**2 for v in xs)/len(xs)
                await ctx.reply(f"std = {math.sqrt(var):.12g}")
                return
            if op == "min":
                await ctx.reply(f"min = {min(xs):.12g}")
                return
            if op == "max":
                await ctx.reply(f"max = {max(xs):.12g}")
                return
            if op == "percentile":
                val = self._percentile(xs, p)
                await ctx.reply(f"p{p} = {val:.12g}")
                return
            if op == "corr":
                ys = self._parse_numbers(y)
                if len(ys) != len(xs):
                    raise ValueError("X 與 Y 長度需相同")
                n = len(xs)
                mx = sum(xs)/n
                my = sum(ys)/n
                num = sum((xs[i]-mx)*(ys[i]-my) for i in range(n))
                den = math.sqrt(sum((xi-mx)**2 for xi in xs) * sum((yi-my)**2 for yi in ys))
                r = num/den if den != 0 else float('nan')
                await ctx.reply(f"pearson r = {r:.12g}")
                return
            if op == "regress":
                ys = self._parse_numbers(y)
                if len(ys) != len(xs):
                    raise ValueError("X 與 Y 長度需相同")
                n = len(xs)
                sx = sum(xs); sy = sum(ys)
                sxx = sum(x*x for x in xs); sxy = sum(xs[i]*ys[i] for i in range(n))
                denom = n*sxx - sx*sx
                if denom == 0:
                    raise ValueError("無法回歸 (X 恰為常數)")
                slope = (n*sxy - sx*sy)/denom
                intercept = (sy - slope*sx)/n
                await ctx.reply(f"y ≈ {slope:.6g} x + {intercept:.6g}")
                return
        except Exception as e:
            await ctx.reply(f"計算錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="機率", with_app_command=True)
    @app_commands.describe(dist="normal/binomial/poisson", op="pdf/cdf/sample")
    @app_commands.default_permissions(administrator=True)
    async def 機率(self, ctx: commands.Context, dist: Literal["normal", "binomial", "poisson"], op: Literal["pdf", "cdf", "sample"], x: float = 0.0, mu: float = 0.0, sigma: float = 1.0, n: int = 1, p: float = 0.5, lam: float = 1.0, size: int = 1):
        try:
            if dist == "normal":
                if op == "pdf":
                    await ctx.reply(f"pdf = {self._norm_pdf(x, mu, sigma):.12g}")
                elif op == "cdf":
                    await ctx.reply(f"cdf = {self._norm_cdf(x, mu, sigma):.12g}")
                else:
                    import random
                    size = max(1, min(int(size), 10000))
                    vals = [random.gauss(mu, sigma) for _ in range(size)]
                    await ctx.reply(_SAMPLES_PREFIX + ", ".join(f"{v:.6g}" for v in vals[:20]) + (" ..." if size>20 else ""))
            elif dist == "binomial":
                if op == "pdf":
                    k = int(x)
                    await ctx.reply(f"pmf = {self._binom_pmf(k, int(n), p):.12g}")
                elif op == "cdf":
                    k = int(x)
                    await ctx.reply(f"cdf = {self._binom_cdf(k, int(n), p):.12g}")
                else:
                    import random
                    size = max(1, min(int(size), 10000))
                    out = []
                    for _ in range(size):
                        s = 0
                        for _ in range(int(n)):
                            if random.random() < p:
                                s += 1
                        out.append(s)
                    await ctx.reply(_SAMPLES_PREFIX + ", ".join(str(v) for v in out[:20]) + (" ..." if size>20 else ""))
            else:  # poisson
                if op == "pdf":
                    k = int(x)
                    await ctx.reply(f"pmf = {self._poisson_pmf(k, lam):.12g}")
                elif op == "cdf":
                    k = int(x)
                    await ctx.reply(f"cdf = {self._poisson_cdf(k, lam):.12g}")
                else:
                    import random
                    size = max(1, min(int(size), 10000))
                    out = []
                    for _ in range(size):
                        L = math.exp(-lam)
                        k = 0
                        pval = 1.0
                        while pval > L and k < 100000:
                            k += 1
                            pval *= random.random()
                        out.append(k - 1)
                    await ctx.reply(_SAMPLES_PREFIX + ", ".join(str(v) for v in out[:20]) + (" ..." if size>20 else ""))
        except Exception as e:
            await ctx.reply(f"計算錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="進制", with_app_command=True)
    @app_commands.rename(x="數值", base_from="來源進制", base_to="目標進制")
    @app_commands.default_permissions(administrator=True)
    async def 進制(self, ctx: commands.Context, x: str, base_from: int = 10, base_to: int = 16):
        try:
            v = int(x, base=base_from)
            if base_to == 2:
                s = bin(v)
            elif base_to == 8:
                s = oct(v)
            elif base_to == 10:
                s = str(v)
            elif base_to == 16:
                s = hex(v)
            else:
                if not (2 <= base_to <= 36):
                    raise ValueError("目標進制需在 2..36")
                digits = "0123456789abcdefghijklmnopqrstuvwxyz"
                neg = v < 0
                v = abs(v)
                if v == 0:
                    s = "0"
                else:
                    out = []
                    while v > 0:
                        out.append(digits[v % base_to])
                        v //= base_to
                    s = ("-" if neg else "") + "".join(reversed(out))
            await ctx.reply(f"{s}")
        except Exception as e:
            await ctx.reply(f"轉換錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="單位", with_app_command=True)
    @app_commands.rename(value="數值", unit_from="來源單位", unit_to="目標單位", category="類別")
    @app_commands.describe(category="length/mass/time/angle")
    @app_commands.default_permissions(administrator=True)
    async def 單位(self, ctx: commands.Context, value: float, unit_from: str, unit_to: str, category: Literal["length", "mass", "time", "angle"] = "length"):
        try:
            mp = self._unit_maps[category]
            if unit_from not in mp or unit_to not in mp:
                raise ValueError("不支援的單位")
            base = value * mp[unit_from]
            out = base / mp[unit_to]
            await ctx.reply(f"{value} {unit_from} = {out:.12g} {unit_to}")
        except Exception as e:
            await ctx.reply(f"轉換錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="方程", with_app_command=True)
    @app_commands.rename(expr="方程", x0="初始值", a="左端", b="右端")
    @app_commands.describe(method="newton/secant/bisection")
    @app_commands.default_permissions(administrator=True)
    async def 方程(self, ctx: commands.Context, expr: str, method: Literal["newton", "secant", "bisection"] = "newton", x0: Optional[float] = None, a: Optional[float] = None, b: Optional[float] = None):
        try:
            code = self._compile_expr(expr)
            def f(x: float) -> float:
                v = self._eval_expr(code, {"x": x})
                return v.real
            root: Optional[complex] = None
            max_iter = 100
            if method == "bisection":
                if a is None or b is None:
                    raise ValueError("需提供區間 [a,b]")
                fa = f(a).real
                fb = f(b).real
                if fa == 0:
                    root = complex(a, 0)
                elif fb == 0:
                    root = complex(b, 0)
                elif fa * fb > 0:
                    raise ValueError("區間端點需異號")
                else:
                    lo, hi = a, b
                    for _ in range(max_iter):
                        mid = (lo + hi) / 2
                        fm = f(mid).real
                        if abs(fm) < 1e-10 or (hi - lo) < 1e-10:
                            root = complex(mid, 0)
                            break
                        if fa * fm <= 0:
                            hi = mid
                            fb = fm
                        else:
                            lo = mid
                            fa = fm
            elif method == "secant":
                if a is None or b is None:
                    raise ValueError("需提供兩個初始點 a,b")
                x_prev, x_curr = a, b
                f_prev, f_curr = f(x_prev), f(x_curr)
                for _ in range(max_iter):
                    denom = (f_curr - f_prev)
                    if abs(denom) < 1e-14:
                        break
                    x_next = x_curr - (x_curr - x_prev) * f_curr / denom
                    if abs(x_next - x_curr) < 1e-12:
                        root = complex(x_next, 0.0)
                        break
                    x_prev, f_prev = x_curr, f_curr
                    x_curr, f_curr = x_next, f(x_next)
                if root is None:
                    root = complex(x_curr, 0.0)
            else:  # newton
                if x0 is None:
                    raise ValueError("需提供初始值 x0")
                x = x0
                for _ in range(max_iter):
                    fx = f(x)
                    d = (f(x + 1e-6) - f(x - 1e-6)) / 2e-6
                    if abs(d) < 1e-14:
                        break
                    x_new = x - fx / d
                    if abs(x_new - x) < 1e-12:
                        root = complex(x_new, 0.0)
                        break
                    x = x_new
                if root is None:
                    root = complex(x, 0.0)
            if root is None:
                raise ValueError("未收斂")
            rr = root.real if isinstance(root, complex) else float(root)
            await ctx.reply(f"root ≈ {rr:.12g}")
        except Exception as e:
            await ctx.reply(f"求解錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="繪圖", with_app_command=True)
    @app_commands.rename(expr="函數", x_min="最小x", x_max="最大x", width="寬度", height="高度", samples="取樣點")
    @app_commands.default_permissions(administrator=True)
    async def 繪圖(self, ctx: commands.Context, expr: str, x_min: float = -10.0, x_max: float = 10.0, width: int = 800, height: int = 400, samples: int = 800):
        try:
            width = max(200, min(width, 2000))
            height = max(200, min(height, 2000))
            samples = max(50, min(samples, 5000))
            code = self._compile_expr(expr)
            xs = [x_min + (x_max - x_min) * i / (samples - 1) for i in range(samples)]
            ys: List[float] = []
            for x in xs:
                try:
                    v = self._eval_expr(code, {"x": x})
                    yv = v.real if abs(v.imag) < 1e-12 else float('nan')
                    ys.append(yv)
                except Exception:
                    ys.append(float('nan'))
            # determine y-range ignoring NaNs
            ys_valid = [y for y in ys if not math.isnan(y) and math.isfinite(y)]
            if not ys_valid:
                raise ValueError("無法在範圍內繪製")
            y_min = min(ys_valid); y_max = max(ys_valid)
            if y_min == y_max:
                y_min -= 1.0; y_max += 1.0
            # image
            img = Image.new("RGB", (width, height), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            # axes
            def x_to_px(x):
                return int((x - x_min) / (x_max - x_min) * (width - 1))
            def y_to_px(y):
                return int((1 - (y - y_min) / (y_max - y_min)) * (height - 1))
            # draw axes if in range
            if x_min <= 0 <= x_max:
                x0 = x_to_px(0)
                draw.line([(x0, 0), (x0, height-1)], fill=(220, 220, 220))
            if y_min <= 0 <= y_max:
                y0 = y_to_px(0)
                draw.line([(0, y0), (width-1, y0)], fill=(220, 220, 220))
            # plot
            last = None
            for i, (x, y) in enumerate(zip(xs, ys)):
                if math.isnan(y) or not math.isfinite(y):
                    last = None
                    continue
                pt = (x_to_px(x), y_to_px(y))
                if last is not None:
                    draw.line([last, pt], fill=(52, 120, 246), width=2)
                last = pt
            # send
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            await ctx.reply(file=discord.File(buf, filename="plot.png"))
        except Exception as e:
            await ctx.reply(f"繪圖錯誤: {e}")

    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="計算機", with_app_command=True)
    @app_commands.rename(a="表達式")
    @app_commands.default_permissions(administrator=True)
    async def 計算機(self, ctx: commands.Context, a: str = ""):
        """
        Safe calculator: supports numbers, + - * / // % **, parentheses,
        unary +/-, and math module functions/constants (sin, cos, pi, e, etc.),
        plus builtins abs, round, pow.
        """

        if not a:
            await ctx.reply("請提供要計算的表達式，例如: `/計算 2+2`。", ephemeral=True)
            return

        # build allowed names (math module + a few builtins)
        allowed_names = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
        allowed_names.update({"abs": abs, "round": round, "pow": pow})

        # AST evaluator
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant):  # Python 3.8+
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError("不支援的常數類型")
            if isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                op = node.op
                if isinstance(op, ast.Add):
                    return left + right
                if isinstance(op, ast.Sub):
                    return left - right
                if isinstance(op, ast.Mult):
                    return left * right
                if isinstance(op, ast.Div):
                    return left / right
                if isinstance(op, ast.FloorDiv):
                    return left // right
                if isinstance(op, ast.Mod):
                    return left % right
                if isinstance(op, ast.Pow):
                    return left ** right
                raise ValueError("不支援的二元運算子")
            if isinstance(node, ast.UnaryOp):
                operand = _eval(node.operand)
                if isinstance(node.op, ast.UAdd):
                    return +operand
                if isinstance(node.op, ast.USub):
                    return -operand
                raise ValueError("不支援的一元運算子")
            if isinstance(node, ast.Call):
                # only allow direct calls to allowed names, no attribute access
                if not isinstance(node.func, ast.Name):
                    raise ValueError("不支援的函式呼叫方式")
                func_name = node.func.id
                if func_name not in allowed_names:
                    raise ValueError(f"不允許的函式: {func_name}")
                func = allowed_names[func_name]
                args = [_eval(arg) for arg in node.args]
                # no kwargs allowed
                if node.keywords:
                    raise ValueError("不支援關鍵字參數")
                return func(*args)
            if isinstance(node, ast.Name):
                if node.id in allowed_names:
                    return allowed_names[node.id]
                raise ValueError(f"不允許的名稱: {node.id}")
            if isinstance(node, ast.Tuple):
                return tuple(_eval(elt) for elt in node.elts)
            raise ValueError("不支援的語法")

        try:
            parsed = ast.parse(a, mode="eval")
            # ensure no disallowed nodes (like import, lambda, comprehensions, attributes)
            for n in ast.walk(parsed):
                if isinstance(n, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.Lambda,
                                  ast.ClassDef, ast.FunctionDef, ast.Assign, ast.Attribute,
                                  ast.Subscript, ast.DictComp, ast.ListComp, ast.SetComp, ast.GeneratorExp)):
                    raise ValueError("不允許的語法元素")
            result = _eval(parsed)
            # format result nicely
            if isinstance(result, float):
                # limit float precision to avoid huge reprs
                result_str = str(round(result, 12)).rstrip('0').rstrip('.') if '.' in str(round(result, 12)) else str(result)
            else:
                result_str = str(result)
            await ctx.reply(f"`{a}` = {result_str}")
        except Exception as e:
            await ctx.reply(f"計算錯誤: {e}")
            
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="傅立葉", with_app_command=True)
    @app_commands.rename(data="數列", mode="模式", top="顯示前幾項", expr="函數", sample_rate="取樣率", duration="時長")
    @app_commands.describe(
        data="以逗號或空白分隔的數列，如: 1,0,-1,0",
        mode="dft/fft/idft/ifft",
        top="顯示的頻率成分數量 (預設16)",
        expr="可選: 以 t 為變數的函數表達式，如 sin(2*pi*t)",
        sample_rate="當使用函數取樣時的取樣率 (預設128)",
        duration="當使用函數取樣時的秒數 (預設1.0)"
    )
    @app_commands.default_permissions(administrator=True)
    async def 傅立葉(
        self,
        ctx: commands.Context,
        data: str = "",
        mode: Literal["dft", "fft", "idft", "ifft"] = "fft",
        top: int = 16,
        expr: str = "",
        sample_rate: int = 128,
        duration: float = 1.0,
    ):
        """
        Fourier Transform 工具：
        - 提供 DFT/FFT 與其反變換 (IDFT/IFFT)
        - 可對數列或對函數表達式 f(t) 取樣後進行變換
        """

        # guard and inputs
        if not data and not expr:
            await ctx.reply("請提供數列或函數表達式，例如: /傅立葉 數列:'1,0,-1,0' 或 /傅立葉 函數:'sin(2*pi*t)'。", ephemeral=True)
            return

        # build signal
        signal: List[complex] = []
        max_len = 4096

        if expr:
            # safety: restrict names
            forbidden = ("__", "import", "exec", "eval", "open", "os.", "sys.", "subprocess", "shutil", ";", "lambda")
            if any(tok in expr for tok in forbidden):
                await ctx.reply("不允許的表達式內容。", ephemeral=True)
                return
            allowed_names = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
            allowed_names.update({"abs": abs, "min": min, "max": max, "pow": pow, "pi": math.pi})
            try:
                code = compile(expr, _EXPR_NAME, "eval")
            except Exception as e:
                await ctx.reply(f"函數解析錯誤: {e}")
                return
            try:
                sample_rate = int(sample_rate)
                if sample_rate <= 0:
                    raise ValueError("取樣率須為正整數")
                N = min(int(sample_rate * float(duration)), max_len)
                if N <= 1:
                    raise ValueError("樣本數過少")
                for i in range(N):
                    t = i / sample_rate
                    g: dict[str, object] = {"__builtins__": None}
                    g.update(allowed_names)
                    g["t"] = t
                    val = eval(code, g)
                    signal.append(complex(float(val), 0.0))
            except Exception as e:
                await ctx.reply(f"取樣錯誤: {e}")
                return
        else:
            try:
                realvals = self._parse_series(data)
                if not realvals:
                    raise ValueError("無法解析數列")
                if len(realvals) > max_len:
                    realvals = realvals[:max_len]
                signal = [complex(v, 0.0) for v in realvals]
            except Exception as e:
                await ctx.reply(f"數列解析錯誤: {e}")
                return

        N = len(signal)
        if N == 0:
            await ctx.reply("沒有有效的資料可供變換。", ephemeral=True)
            return

        # choose transform
        try:
            if mode == "dft":
                spectrum = self._dft(signal)
            elif mode == "fft":
                # zero-pad to next power of two for better FFT if needed (cap at max_len)
                if not self._is_power_of_two(N):
                    p = 1
                    while p < N and p < max_len:
                        p <<= 1
                    if p <= max_len and p != N:
                        signal = signal + [0j] * (p - N)
                    N = len(signal)
                spectrum = self._fft(signal)
            elif mode == "idft":
                spectrum = self._idft(signal)
            elif mode == "ifft":
                # same padding rule for completeness
                if not self._is_power_of_two(N):
                    p = 1
                    while p < N and p < max_len:
                        p <<= 1
                    if p <= max_len and p != N:
                        signal = signal + [0j] * (p - N)
                    N = len(signal)
                spectrum = self._ifft(signal)
            else:
                await ctx.reply("模式需為 dft/fft/idft/ifft。", ephemeral=True)
                return
        except Exception as e:
            await ctx.reply(f"計算錯誤: {e}")
            return

        # format output
        try:
            top = max(1, min(int(top), N))
        except Exception:
            top = min(16, N)

        if mode in ("dft", "fft"):
            # forward transform: report largest magnitudes
            mags = [(k, abs(z), z) for k, z in enumerate(spectrum)]
            mags.sort(key=lambda t: t[1], reverse=True)
            chosen = mags[:top]
            lines = []
            for k, m, z in chosen:
                phase = math.degrees(math.atan2(z.imag, z.real)) if m > 0 else 0.0
                lines.append(f"k={k}: |X|={m:.5g}, phase={phase:.2f}°")
            header = f"N={N}, 模式={mode.upper()}\n前 {len(chosen)} 個幅度最大頻率元：\n"
            await ctx.reply(header + "\n".join(lines))
        else:
            # inverse transform: show first few time-domain samples
            vals = [spectrum[i] for i in range(min(top, N))]
            lines = [f"n={i}: x={v.real:.6g}" + (f"+{v.imag:.6g}j" if abs(v.imag) > 1e-12 else "") for i, v in enumerate(vals)]
            header = f"N={N}, 模式={mode.upper()}\n前 {len(vals)} 個時間序列樣本：\n"
            await ctx.reply(header + "\n".join(lines))
        
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="微分方程", with_app_command=True)
    @app_commands.rename(eq="方程式", x0="起始_x", y0="起始_y", x="目標_x", steps="步數")
    async def 微分方程(self, ctx: commands.Context, eq: str, x0: float, y0: float, x: float, steps: int = 100):
        """
        Solve an initial value problem dy/dx = f(x, y) with RK4.
        Usage example: /微分方程 "x + y" 0 1 2 100
        Arguments:
        - eq: expression for dy/dx in terms of x and y (e.g. "x + y", "sin(x) - y")
        - x0, y0: initial condition y(x0) = y0
        - x: target x to integrate to
        - steps: number of RK4 steps (default 100)
        """
        if not eq:
            await ctx.reply("請提供 dy/dx 的表達式，例如: `/微分方程 \"x+y\" 0 1 2`。", ephemeral=True)
            return

        # simple safety checks
        forbidden = ("__", "import", "exec", "eval", "open", "os.", "sys.", "subprocess", "shutil", ";", "lambda")
        if any(tok in eq for tok in forbidden):
            await ctx.reply("不允許的表達式內容。", ephemeral=True)
            return

        # allowed math names
        allowed_names = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
        allowed_names.update({"abs": abs, "min": min, "max": max, "pow": pow})

        # compile expression once
        try:
            code = compile(eq, _EXPR_NAME, "eval")
        except Exception as e:
            await ctx.reply(f"表達式解析錯誤: {e}")
            return

        # evaluation helper using restricted globals
        def eval_f(xv, yv):
            g = {"__builtins__": None}
            g.update(allowed_names)
            g["x"] = xv
            g["y"] = yv
            return eval(code, g)

        # RK4 integration
        try:
            steps = int(steps)
            if steps <= 0:
                raise ValueError("步數必須為正整數")
            h = (x - x0) / steps
            xi = float(x0)
            yi = float(y0)
            for _ in range(steps):
                k1 = float(eval_f(xi, yi))
                k2 = float(eval_f(xi + 0.5 * h, yi + 0.5 * h * k1))
                k3 = float(eval_f(xi + 0.5 * h, yi + 0.5 * h * k2))
                k4 = float(eval_f(xi + h, yi + h * k3))
                yi += (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
                xi += h
        except Exception as e:
            await ctx.reply(f"計算過程出錯: {e}")
            return

        await ctx.reply(f"從 x={x0}, y={y0} 積分到 x={x} 的結果: y ≈ {yi}")
        
    


async def setup(bot: commands.Bot):
    await bot.add_cog(Calculator(bot))