"""
Comparison chart generation: 4 side-by-side charts for two assets.
"""
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

from config import CHARTS_DIR as _CHARTS_DIR

logger = logging.getLogger(__name__)

CHARTS_DIR = Path(_CHARTS_DIR)
DPI = 150

COLOR_A   = "#2563EB"   # blue  — asset A
COLOR_B   = "#EA580C"   # orange — asset B
GREY_LINE = "#6B7280"

sns.set_theme(style="whitegrid")


def _out(symbol_a: str, symbol_b: str, name: str) -> Path:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    return CHARTS_DIR / f"CMP_{symbol_a}_vs_{symbol_b}_{name}.png"


def _save(fig, path: Path) -> str:
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", path)
    return str(path)


def _load_df(records: list, date_col: str = "date") -> pd.DataFrame:
    df = pd.DataFrame(records)
    df[date_col] = pd.to_datetime(df[date_col])
    return df.set_index(date_col)


# ── 1. Cumulative Return ───────────────────────────────────────────────────────

def _cmp_cumulative_return(comparison: dict) -> str:
    sym_a, sym_b = comparison["symbol_a"], comparison["symbol_b"]
    name_a, name_b = comparison["name_a"], comparison["name_b"]

    df = _load_df(comparison["cum_returns"])
    final_a = df[sym_a].iloc[-1]
    final_b = df[sym_b].iloc[-1]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df[sym_a], color=COLOR_A, linewidth=1.8,
            label=f"{sym_a} ({final_a:+.1f}%)")
    ax.plot(df.index, df[sym_b], color=COLOR_B, linewidth=1.8,
            label=f"{sym_b} ({final_b:+.1f}%)")
    ax.axhline(0, color=GREY_LINE, linewidth=0.8, linestyle="--")

    ax.set_title(f"{name_a} vs {name_b} — Cumulative Return (%)",
                 fontsize=13, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    ax.legend(frameon=True)
    fig.tight_layout()
    return _save(fig, _out(sym_a, sym_b, "cumulative_return"))


# ── 2. Normalised Price (base 100) ────────────────────────────────────────────

def _cmp_price_performance(comparison: dict) -> str:
    sym_a, sym_b = comparison["symbol_a"], comparison["symbol_b"]
    name_a, name_b = comparison["name_a"], comparison["name_b"]

    df = _load_df(comparison["combined_prices"])
    rebased = df / df.iloc[0] * 100

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(rebased.index, rebased[sym_a], color=COLOR_A, linewidth=1.8, label=sym_a)
    ax.plot(rebased.index, rebased[sym_b], color=COLOR_B, linewidth=1.8, label=sym_b)
    ax.axhline(100, color=GREY_LINE, linewidth=0.8, linestyle="--")

    ax.set_title(f"{name_a} vs {name_b} — Normalised Price (base 100)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Indexed Price (base = 100)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}"))
    ax.legend(frameon=True)
    fig.tight_layout()
    return _save(fig, _out(sym_a, sym_b, "price_performance"))


# ── 3. Return Correlation Scatter ─────────────────────────────────────────────

def _cmp_correlation(comparison: dict) -> str:
    sym_a, sym_b = comparison["symbol_a"], comparison["symbol_b"]

    df = _load_df(comparison["combined_prices"])
    daily_rets = df.pct_change().dropna() * 100

    x = daily_rets[sym_a].values
    y = daily_rets[sym_b].values

    colors = [
        "#BBF7D0" if xi >= 0 and yi >= 0 else
        "#FECACA" if xi < 0 and yi < 0 else
        "#E5E7EB"
        for xi, yi in zip(x, y)
    ]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(x, y, c=colors, alpha=0.65, s=14, edgecolors="none")

    z = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 200)
    ax.plot(x_line, np.poly1d(z)(x_line), color="#1D4ED8", linewidth=1.5, alpha=0.85)

    r_val = comparison["correlation"]["value"]
    r_label = comparison["correlation"]["label"]
    ax.text(0.05, 0.95, f"Pearson r = {r_val} ({r_label})",
            transform=ax.transAxes, fontsize=10, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="#D1D5DB", alpha=0.9))

    ax.axhline(0, color=GREY_LINE, linewidth=0.6, linestyle="--")
    ax.axvline(0, color=GREY_LINE, linewidth=0.6, linestyle="--")
    ax.set_xlabel(f"{sym_a} Daily Return (%)")
    ax.set_ylabel(f"{sym_b} Daily Return (%)")
    ax.set_title(f"{sym_a} vs {sym_b} — Return Correlation",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _save(fig, _out(sym_a, sym_b, "correlation"))


# ── 4. Dual Drawdown ──────────────────────────────────────────────────────────

def _cmp_drawdown(comparison: dict) -> str:
    sym_a, sym_b = comparison["symbol_a"], comparison["symbol_b"]
    name_a, name_b = comparison["name_a"], comparison["name_b"]

    df = _load_df(comparison["combined_prices"])

    def _dd(s):
        return (s - s.cummax()) / s.cummax() * 100

    dd_a = _dd(df[sym_a])
    dd_b = _dd(df[sym_b])

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.fill_between(dd_a.index, dd_a, 0, color=COLOR_A, alpha=0.4, label=sym_a)
    ax.plot(dd_a.index, dd_a, color=COLOR_A, linewidth=0.9)
    ax.fill_between(dd_b.index, dd_b, 0, color=COLOR_B, alpha=0.4, label=sym_b)
    ax.plot(dd_b.index, dd_b, color=COLOR_B, linewidth=0.9)
    ax.axhline(0, color=GREY_LINE, linewidth=0.6, linestyle="--")

    ax.set_title(f"{name_a} vs {name_b} — Drawdown from Peak (%)",
                 fontsize=13, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    ax.legend(frameon=True)
    fig.tight_layout()
    return _save(fig, _out(sym_a, sym_b, "drawdown"))


# ── Public API ────────────────────────────────────────────────────────────────

def generate_comparison_charts(
    config_a: dict, config_b: dict, comparison: dict
) -> list:
    """Generate all 4 comparison charts. Returns list of saved file paths."""
    generators = [
        _cmp_cumulative_return,
        _cmp_price_performance,
        _cmp_correlation,
        _cmp_drawdown,
    ]
    saved = []
    for fn in generators:
        try:
            path = fn(comparison)
            saved.append(path)
        except Exception as exc:
            logger.warning("Failed to generate %s: %s", fn.__name__, exc)
    return saved
