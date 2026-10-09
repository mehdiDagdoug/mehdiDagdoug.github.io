"""Generate the small paper illustrations in assets/fig/*.svg.

Each figure is a 240x160 SVG drawn with CSS classes (fi = ink, fa = accent,
fs = soft accent fill, fm = muted) so it follows the site's light/dark colours
when inlined. Run:  python3 figures.py
"""
from pathlib import Path
import numpy as np

W, H = 240, 160
OUT = Path(__file__).parent / "assets" / "fig"


def svg(body):
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{body}</svg>\n'


def poly(xs, ys, cls="fa", width=1.6, dash=None):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline class="{cls} line" points="{pts}" stroke-width="{width}"{d}/>'


def dot(x, y, r=2.2, cls="fi"):
    return f'<circle class="{cls} dot" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'


def ring(x, y, r=2.6, cls="fa"):
    return f'<circle class="{cls} ring" cx="{x:.1f}" cy="{y:.1f}" r="{r}" stroke-width="1.3"/>'


def line(x1, y1, x2, y2, cls="fm", width=1, dash=None, opacity=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<line class="{cls} line" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke-width="{width}"{d}{o}/>'


def rect(x, y, w, h, cls="fs", opacity=None, rx=0):
    o = f' opacity="{opacity:.3f}"' if opacity is not None else ""
    return f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}"{o}/>'


def axes(x0=18, y0=142, x1=226, y1=14):
    return line(x0, y0, x1, y0, "fm", 1) + line(x0, y0, x0, y1, "fm", 1)


# ------------------------------------------------------------------ figures

def agnostic():
    r = np.random.default_rng(3)
    x = np.sort(r.uniform(0, 1, 46))
    f = lambda t: 0.5 + 0.28 * np.sin(5.5 * t) + 0.18 * t
    y = f(x) + r.normal(0, 0.07, x.size)
    X = lambda t: 22 + 200 * t
    Y = lambda v: 146 - 125 * v
    b = axes()
    b += "".join(dot(X(a), Y(c), 2, "fm") for a, c in zip(x, y))
    g = np.linspace(0, 1, 120)
    b += poly(X(g), Y(np.polyval(np.polyfit(x, y, 1), g)), "fi", 1.2, "3 3")
    steps = np.linspace(0, 1, 7)
    sx, sy = [], []
    for a, c in zip(steps[:-1], steps[1:]):
        m = y[(x >= a) & (x < c)].mean()
        sx += [X(a), X(c)]
        sy += [Y(m), Y(m)]
    b += poly(sx, sy, "fi", 1.2)
    b += poly(X(g), Y(f(g)), "fa", 2)
    return svg(b)


def greg_variance():
    b = axes()
    t = np.linspace(0, 0.9, 80)
    X = lambda v: 22 + 222 * v
    Y = lambda v: 142 - 110 * v
    b += line(X(0), Y(1), X(0.9), Y(1), "fm", 1, "4 3")
    b += poly(X(t), Y(1 - t * 0.95), "fi", 1.4)
    b += poly(X(t), Y(1 + 0.04 * np.sin(9 * t) * t), "fa", 2)
    r = np.random.default_rng(5)
    for v in np.linspace(0.08, 0.86, 10):
        b += dot(X(v), Y(1 - v * 0.95 + r.normal(0, 0.04)), 2, "fi")
        b += dot(X(v), Y(1 + r.normal(0, 0.04)), 2.2, "fa")
    return svg(b)


def population():
    r = np.random.default_rng(11)
    nx, ny = 18, 10
    b = ""
    picks = r.random((ny, nx)) < 0.22
    for j in range(ny):
        for i in range(nx):
            x, y = 20 + i * 11.8, 22 + j * 13
            b += dot(x, y, 2.6, "fa") if picks[j, i] else ring(x, y, 2.2, "fm")
    return svg(b)


def lasso_path():
    b = axes()
    r = np.random.default_rng(7)
    lam = np.linspace(0, 1, 60)
    X = lambda v: 22 + 200 * v
    for k in range(8):
        beta = r.normal(0, 0.9)
        stop = r.uniform(0.25, 0.95)
        path = beta * np.clip(1 - lam / stop, 0, None) ** 1.3
        cls, wd = ("fa", 1.8) if abs(beta) > 0.9 else ("fi", 1.1)
        b += poly(X(lam), 80 - 55 * path, cls, wd)
    b += line(22, 80, 222, 80, "fm", 0.8, "2 3")
    return svg(b)


def rkhs_kernel():
    r = np.random.default_rng(2)
    n, T = 26, 60
    x = np.sort(r.uniform(0, 1, n))
    K = np.zeros((n, n))
    for _ in range(T):
        cuts = np.sort(r.uniform(0, 1, r.integers(2, 6)))
        leaf = np.searchsorted(cuts, x)
        K += leaf[:, None] == leaf[None, :]
    K /= T
    s = 140 / n
    x0 = (W - 140) / 2
    b = "".join(rect(x0 + j * s, 10 + i * s, s + 0.2, s + 0.2, "fa", K[i, j] ** 1.4 * 0.95)
                for i in range(n) for j in range(n))
    return svg(b)


def spectrum():
    b = axes()
    q = 0.35
    lo, hi = (1 - np.sqrt(q)) ** 2, (1 + np.sqrt(q)) ** 2
    r = np.random.default_rng(4)
    p, n = 140, 400
    Z = r.normal(size=(n, p))
    ev = np.linalg.eigvalsh(Z.T @ Z / n)
    bins = np.linspace(0, 2.8, 29)
    h, _ = np.histogram(ev, bins, density=True)
    X = lambda v: 22 + 200 * v / 2.8
    Y = lambda v: 142 - 110 * v / 1.15
    for k in range(len(h)):
        if h[k] > 0:
            b += rect(X(bins[k]) + 0.8, Y(h[k]), X(bins[1]) - X(0) - 1.6, 142 - Y(h[k]), "fs")
    g = np.linspace(lo + 1e-4, hi - 1e-4, 160)
    dens = np.sqrt((hi - g) * (g - lo)) / (2 * np.pi * q * g)
    b += poly(X(g), Y(dens), "fa", 2)
    return svg(b)


def _partition(r, box, depth, out):
    x0, y0, x1, y1 = box
    if depth == 0 or (x1 - x0) * (y1 - y0) < 900:
        return
    if (x1 - x0) >= (y1 - y0):
        c = r.uniform(x0 + 0.3 * (x1 - x0), x1 - 0.3 * (x1 - x0))
        out.append((c, y0, c, y1))
        _partition(r, (x0, y0, c, y1), depth - 1, out)
        _partition(r, (c, y0, x1, y1), depth - 1, out)
    else:
        c = r.uniform(y0 + 0.3 * (y1 - y0), y1 - 0.3 * (y1 - y0))
        out.append((x0, c, x1, c))
        _partition(r, (x0, y0, x1, c), depth - 1, out)
        _partition(r, (x0, c, x1, y1), depth - 1, out)


def tree_imputation():
    r = np.random.default_rng(8)
    box = (40, 12, 200, 148)
    cuts = []
    _partition(r, box, 4, cuts)
    b = rect(40, 12, 160, 136, "fs", 0.55, 2)
    b += "".join(line(*c, "fi", 1.1) for c in cuts)
    pts = r.uniform([44, 16], [196, 144], (55, 2))
    miss = r.random(55) < 0.22
    for (x, y), m in zip(pts, miss):
        b += ring(x, y, 2.8, "fa") if m else dot(x, y, 2, "fi")
    return svg(b)


def nonresponse():
    r = np.random.default_rng(12)
    b = line(120, 10, 120, 150, "fm", 1, "3 3")
    for k in range(7):
        y = 20 + k * 19.5
        centre = r.normal(0, 22) * (1 if k > 1 else 2.2)
        spread = r.uniform(8, 20)
        xs = 120 + centre + r.normal(0, spread, 18)
        cls = "fa" if abs(centre) < 12 else "fi"
        b += line(xs.min(), y, xs.max(), y, "fm", 1)
        b += "".join(dot(x, y + r.uniform(-2.5, 2.5), 1.7, cls) for x in xs)
    return svg(b)


def high_dim():
    b = axes()
    p = np.linspace(0, 1, 90)
    X = lambda v: 22 + 200 * v
    b += poly(X(p), 132 - 18 * p - 105 * p ** 6, "fi", 1.4)
    b += poly(X(p), 130 - 12 * p + 4 * np.sin(6 * p), "fa", 2)
    b += line(X(0.72), 18, X(0.72), 142, "fm", 0.8, "2 3")
    return svg(b)


def forest_partition():
    r = np.random.default_rng(21)
    b = rect(40, 12, 160, 136, "fs", 0.5, 2)
    for t in range(6):
        cuts = []
        _partition(r, (40, 12, 200, 148), 3, cuts)
        b += "".join(line(*c, "fa", 1.2, opacity=0.45) for c in cuts)
    pts = r.uniform([44, 16], [196, 144], (40, 2))
    b += "".join(dot(x, y, 2, "fi") for x, y in pts)
    return svg(b)


def imputation_compare():
    r = np.random.default_rng(17)
    b = line(14, 80, 226, 80, "fm", 0.8, "3 3")
    for k in range(9):
        x = 28 + k * 23.5
        c = 80 + r.normal(0, 16) * (0.3 if k in (2, 6) else 1)
        s = r.uniform(10, 26)
        q1, q3 = c - s / 2, c + s / 2
        cls = "fa" if k in (2, 6) else "fi"
        b += line(x, q1 - s * 0.9, x, q1, cls, 1) + line(x, q3, x, q3 + s * 0.9, cls, 1)
        b += f'<rect class="{cls} box" x="{x-6:.1f}" y="{q1:.1f}" width="12" height="{s:.1f}" stroke-width="1.3" rx="1.5"/>'
        b += line(x - 6, c, x + 6, c, cls, 1.6)
    return svg(b)


FIGS = {
    "agnostic": agnostic, "greg-variance": greg_variance, "population": population,
    "lasso-path": lasso_path, "rkhs-kernel": rkhs_kernel, "spectrum": spectrum,
    "tree-imputation": tree_imputation, "nonresponse": nonresponse, "high-dim": high_dim,
    "forest-partition": forest_partition, "imputation-compare": imputation_compare,
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGS.items():
        (OUT / f"{name}.svg").write_text(fn())
    print(f"wrote {len(FIGS)} figures to {OUT}")
