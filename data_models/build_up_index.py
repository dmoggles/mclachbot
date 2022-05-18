import pandas as pd
from dbconnect import FbRefQuery
from footmav import FbRefData, Filter, filter, filters, rank, per_90, fb, aggregate_by
from footmav.operations.normalize import z_score

from footmav.data_definitions.derived import function_attribute
from footmav.data_definitions import attribute_functions as F
from footmav.operations.possession_adjust import possession_adjust
import numpy as np


@function_attribute
def TURNOVER_AVOIDANCE():
    return F.Lit(0) - (
        F.Col(fb.MISCONTROLS)
        + F.Col(fb.DISPOSSESSED)
        + (F.Col(fb.PASSES) - F.Col(fb.PASSES_COMPLETED))
    )


@function_attribute
def BUILD_UP_SCORE():
    return (
        F.Col(TURNOVER_AVOIDANCE)
        + F.Col(fb.PROGRESSIVE_CARRIES)
        + F.Col(fb.PROGRESSIVE_PASSES)
        + F.Col(fb.PASSES_INTO_FINAL_THIRD)
        + F.Col(fb.CARRIES_INTO_FINAL_THIRD)
        + F.Col(fb.TOUCHES_MID_3RD)
        + F.Col(fb.PASSES_SWITCHES)
    ) / F.Lit(np.sqrt(7))


@function_attribute
def TURNOVERS():
    return (
        F.Col(fb.MISCONTROLS)
        + F.Col(fb.DISPOSSESSED)
        + (F.Col(fb.PASSES) - F.Col(fb.PASSES_COMPLETED))
    )


def get_build_up_index_table(league: str, season: int) -> pd.DataFrame:

    columns = [
        fb.MISCONTROLS,
        fb.DISPOSSESSED,
        fb.PASSES,
        fb.PASSES_COMPLETED,
        fb.COMPETITION,
        fb.PROGRESSIVE_CARRIES,
        fb.PROGRESSIVE_PASSES,
        fb.PASSES_INTO_FINAL_THIRD,
        fb.CARRIES_INTO_FINAL_THIRD,
        fb.TOUCHES_MID_3RD,
        fb.PASSES_SWITCHES,
        fb.MINUTES,
        fb.PLAYER,
        fb.TEAM,
        fb.POSITION,
        fb.DATE,
        fb.PLAYER_ID,
        fb.TOUCHES,
        fb.OPPONENT,
    ]

    cols = [c.N for c in columns]
    if league == "Top 5 Mens League":
        data = FbRefData(
            FbRefQuery(password="M0neyMa$e").query(columns=cols, season=season).get()
        )
        data = data.pipe(
            filter,
            [
                Filter(fb.COMPETITION, "Champions League", filters.NEQ),
                Filter(fb.COMPETITION, "Europa League", filters.NEQ),
                Filter(fb.COMPETITION, "MLS", filters.NEQ),
                Filter(fb.COMPETITION, "WSL", filters.NEQ),
            ],
        )
    else:
        data = FbRefData(
            FbRefQuery(password="M0neyMa$e")
            .query(columns=cols, league=league, season=season)
            .get()
        )

    build_up_index = (
        data.with_attributes([TURNOVER_AVOIDANCE, BUILD_UP_SCORE])
        .pipe(filter, [Filter(fb.POSITION, ["CM", "DM"], filters.StrContainsOneOf)])
        .pipe(aggregate_by, [fb.PLAYER])
        .pipe(filter, [Filter(fb.MINUTES, 750, filters.GTE)])
        .pipe(per_90)
        .pipe(possession_adjust)
        .pipe(z_score)
        .pipe(rank)
        .df[[fb.PLAYER.N, fb.TEAM.N, BUILD_UP_SCORE.N]]
        .sort_values(BUILD_UP_SCORE.N)
        .set_index(fb.PLAYER.N)
    )
    build_up_index[BUILD_UP_SCORE.N] *= 100
    actual_metrics = (
        data.with_attributes([TURNOVERS])
        .pipe(filter, [Filter(fb.POSITION, ["CM", "DM"], filters.StrContainsOneOf)])
        .pipe(aggregate_by, [fb.PLAYER])
        .pipe(filter, [Filter(fb.MINUTES, 750, filters.GTE)])
        .pipe(per_90)
        .pipe(possession_adjust)
        .df[
            [
                fb.PLAYER.N,
                fb.MINUTES.N,
                TURNOVERS.N,
                fb.PROGRESSIVE_CARRIES.N,
                fb.PROGRESSIVE_PASSES.N,
                fb.PASSES_INTO_FINAL_THIRD.N,
                fb.CARRIES_INTO_FINAL_THIRD.N,
                fb.TOUCHES_MID_3RD.N,
                fb.PASSES_SWITCHES.N,
            ]
        ]
        .set_index(fb.PLAYER.N)
    )

    build_up_index = pd.merge(
        build_up_index,
        actual_metrics,
        left_index=True,
        right_index=True,
        how="left",
        suffixes=("", "_dup"),
    )
    build_up_index["player_display"] = (
        build_up_index.reset_index()["player"].apply(lambda x: x.title()).values
    )
    build_up_index["squad"] = build_up_index["squad"].apply(
        lambda x: x.replace("_", " ").title()
    )
    return build_up_index


def get_build_up_index_pizza(league: str, season: int) -> pd.DataFrame:

    columns = [
        fb.MISCONTROLS,
        fb.DISPOSSESSED,
        fb.PASSES,
        fb.PASSES_COMPLETED,
        fb.COMPETITION,
        fb.PROGRESSIVE_CARRIES,
        fb.PROGRESSIVE_PASSES,
        fb.PASSES_INTO_FINAL_THIRD,
        fb.CARRIES_INTO_FINAL_THIRD,
        fb.TOUCHES_MID_3RD,
        fb.PASSES_SWITCHES,
        fb.MINUTES,
        fb.PLAYER,
        fb.TEAM,
        fb.POSITION,
        fb.DATE,
        fb.PLAYER_ID,
        fb.TOUCHES,
        fb.OPPONENT,
    ]

    cols = [c.N for c in columns]
    if league == "Top 5 Mens League":
        data = FbRefData(
            FbRefQuery(password="M0neyMa$e").query(columns=cols, season=season).get()
        )
        data = data.pipe(
            filter,
            [
                Filter(fb.COMPETITION, "Champions League", filters.NEQ),
                Filter(fb.COMPETITION, "Europa League", filters.NEQ),
                Filter(fb.COMPETITION, "MLS", filters.NEQ),
                Filter(fb.COMPETITION, "WSL", filters.NEQ),
            ],
        )
    else:
        data = FbRefData(
            FbRefQuery(password="M0neyMa$e")
            .query(columns=cols, league=league, season=season)
            .get()
        )
    minutes = (
        (
            data.pipe(
                filter, [Filter(fb.POSITION, ["CM", "DM"], filters.StrContainsOneOf)]
            )
            .pipe(aggregate_by, [fb.PLAYER])
            .pipe(filter, [Filter(fb.MINUTES, 750, filters.GTE)])
        )
        .df[[fb.PLAYER.N, fb.MINUTES.N]]
        .set_index(fb.PLAYER.N)
    )

    build_up_index = (
        data.with_attributes([TURNOVER_AVOIDANCE, BUILD_UP_SCORE])
        .pipe(filter, [Filter(fb.POSITION, ["CM", "DM"], filters.StrContainsOneOf)])
        .pipe(aggregate_by, [fb.PLAYER])
        .pipe(filter, [Filter(fb.MINUTES, 750, filters.GTE)])
        .pipe(per_90)
        .pipe(possession_adjust)
        .pipe(z_score)
        .pipe(rank)
        .df[
            [
                fb.PLAYER.N,
                fb.TEAM.N,
                BUILD_UP_SCORE.N,
                TURNOVER_AVOIDANCE.N,
                fb.PROGRESSIVE_CARRIES.N,
                fb.PROGRESSIVE_PASSES.N,
                fb.PASSES_INTO_FINAL_THIRD.N,
                fb.CARRIES_INTO_FINAL_THIRD.N,
                fb.TOUCHES_MID_3RD.N,
                fb.PASSES_SWITCHES.N,
            ]
        ]
        .set_index(fb.PLAYER.N)
    )
    build_up_index = pd.merge(
        build_up_index, minutes, left_index=True, right_index=True, how="left"
    )
    return build_up_index
