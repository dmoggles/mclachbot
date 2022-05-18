from mplsoccer import PyPizza, FontManager
from footmav import fb
from matplotlib.figure import Figure
import numpy as np


def bake_build_up_pizza(player, build_up_index, season, league):
    font_normal = FontManager(
        (
            "https://github.com/google/fonts/blob/main/apache/roboto/static/"
            "Roboto-Regular.ttf?raw=true"
        )
    )
    font_italic = FontManager(
        (
            "https://github.com/google/fonts/blob/main/apache/roboto/static/"
            "Roboto-Italic.ttf?raw=true"
        )
    )
    font_bold = FontManager(
        (
            "https://github.com/google/fonts/blob/main/apache/roboto/static/"
            "Roboto-Medium.ttf?raw=true"
        )
    )
    data_only = build_up_index[[c for c in build_up_index.columns if c != fb.TEAM.N]]

    bg_color = "#EBEBE9"
    baker = PyPizza(
        params=[
            s.replace("_", " ").title()
            for s in data_only.rename(
                columns={
                    "carries_into_final_3rd": "carries_into_final_third",
                    "passes_switches": "switches",
                }
            ).columns
        ],  # list of parameters
        background_color="#EBEBE9",  # background color
        straight_line_color="#EBEBE9",  # color for straight lines
        straight_line_lw=1,  # linewidth for straight lines
        last_circle_lw=0,  # linewidth of last circle
        other_circle_lw=0,  # linewidth for other circles
        inner_circle_size=0,  # size of inner circle
    )

    slice_colors = ["#FF9300"] + ["#1A78CF"] * 7
    text_colors = ["#000000"] * 8
    fig = Figure(figsize=(8, 8.5), facecolor=bg_color)
    ax = fig.add_axes(rect=(0.1, 0.1, 0.8, 0.8), projection="polar", facecolor=bg_color)

    baker.make_pizza(
        [int(v) for v in np.round(data_only.loc[player] * 100, decimals=0)],
        ax=ax,
        # figsize=(8, 8.5),                # adjust figsize according to your need
        color_blank_space="same",  # use same color to fill blank space
        slice_colors=slice_colors,  # color for individual slices
        value_colors=text_colors,  # color for the value-text
        value_bck_colors=slice_colors,  # color for the blank spaces
        blank_alpha=0.4,  # alpha for blank-space colors
        kwargs_slices=dict(
            edgecolor="#F2F2F2", zorder=2, linewidth=1
        ),  # values to be used when plotting slices
        kwargs_params=dict(
            color="#000000", fontsize=11, fontproperties=font_normal.prop, va="center"
        ),  # values to be used when adding parameter
        kwargs_values=dict(
            color="#000000",
            fontsize=11,
            fontproperties=font_normal.prop,
            zorder=3,
            bbox=dict(
                edgecolor="#000000",
                facecolor="cornflowerblue",
                boxstyle="round,pad=0.2",
                lw=1,
            ),
        ),  # values to be used when adding parameter-values
    )

    team = build_up_index.loc[player][fb.TEAM.N].replace("_", " ")

    # add title
    fig.text(
        0.515,
        0.975,
        f"{player.title()} - {team.title()}",
        size=16,
        ha="center",
        fontproperties=font_bold.prop,
        color="#000000",
    )

    # add subtitle
    fig.text(
        0.515,
        0.953,
        f"Build Up Participation Compared to {league} Midfielders, {season}-{season+1}",
        size=13,
        ha="center",
        fontproperties=font_bold.prop,
        color="#000000",
    )
    fig.text(
        0.515,
        0.05,
        "All stats are possession-adjusted",
        ha="center",
        fontproperties=font_bold.prop,
        color="#000000",
        size=10,
    )

    # add credits
    CREDIT_1 = "data: fbref"
    CREDIT_2 = "@ChicagoDmitry and @mclachbot"

    fig.text(
        0.99,
        0.02,
        f"{CREDIT_1}\n{CREDIT_2}",
        size=9,
        fontproperties=font_italic.prop,
        color="#000000",
        ha="right",
    )
    return fig
