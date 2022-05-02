from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from footmav import fb
import pandas as pd
import matplotlib.pyplot as plt

from data_models.constants import LEAGUE_NAME_TRANSLATIONS

plt.style.use("dark_background")


def npxg_rolling_plot(data, team, season, comp, rolling_window):
    fig = Figure(figsize=(10, 8))
    # _ = FigureCanvasAgg(fig)
    ax = fig.add_subplot(1, 1, 1)

    pos = np.array(data[fb.NPXG.N].values >= data[fb.NPXG.N + "_opp"])
    neg = np.array(data[fb.NPXG.N].values < data[fb.NPXG.N + "_opp"])
    ax.fill_between(
        data["round"].values,
        data[fb.NPXG.N],
        y2=data[fb.NPXG.N + "_opp"],
        where=pos,
        color="blue",
        alpha=0.5,
        interpolate=True,
        edgecolor="ivory",
    )
    ax.plot(
        data["round"].values,
        data[fb.NPXG.N],
        color="ivory",
        label=f"{team.replace('_',' ').title()} NPxG",
    )
    ax.fill_between(
        data["round"].values,
        data[fb.NPXG.N],
        y2=data[fb.NPXG.N + "_opp"],
        where=neg,
        color="red",
        alpha=0.5,
        interpolate=True,
        edgecolor="ivory",
    )
    ax.plot(
        data["round"].values,
        data[fb.NPXG.N + "_opp"],
        color="grey",
        label="Opponent NPxG",
    )

    ax.set_xlabel("Date")
    ax.legend()
    ax.set_title(
        f"{team.replace('_',' ').title()} ({LEAGUE_NAME_TRANSLATIONS[comp]}) \n{rolling_window} game rolling NPxG and NPxGa, {season} season",
        y=1.0,
        pad=-3,
        va="top",
    )
    ax.set_xlim(min(data["round"].values), max(data["round"].values))
    ax.set_xticks(data["round"].values[0::5])
    ax.set_xticklabels([pd.Timestamp(d).strftime("%Y-%m") for d in data["date"].values[0::5]])

    ax.text(0.01, 0.01, "@mclachbot", fontsize=10, transform=ax.transAxes, alpha=0.5)
    ax.grid(alpha=0.1)

    fig.tight_layout(pad=0.5)
    return fig
