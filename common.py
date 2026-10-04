"""Shared helpers: where charts go, and a consistent chart style for posts."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files, no window
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)


def save(fig: plt.Figure, name: str) -> Path:
    """Save a chart sized for social posts (1200x675, 16:9)."""
    path = OUT / f"{name}.png"
    fig.set_size_inches(12, 6.75)
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)
    return path


def style(ax: plt.Axes, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=18, fontweight="bold", loc="left")
    ax.set_xlabel(xlabel, fontsize=13)
    ax.set_ylabel(ylabel, fontsize=13)
    ax.grid(alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
