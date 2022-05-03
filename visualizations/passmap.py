import pandas as pd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import math
from matplotlib.lines import Line2D
import cmasher as cmr
from mplsoccer import Pitch, FontManager, add_image
from PIL import Image
from urllib.request import urlopen
from io import StringIO
from visualizations.constants import (
    img_file_translates,
    GOAL_LOCATION,
    TOP_GOAL,
    BOTTOM_GOAL,
    pitch_distance,
    team_colors,
)


URL = "https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Regular.ttf?raw=true"
robotto_regular = FontManager(URL)


def generate_pass_network(pass_df, point_df, subbed_on, min_passes_to_show):
    pass_network = (
        pass_df.groupby(["player_name", "pass_receiver"])
        .count()[["x"]]
        .rename(columns={"x": "passes"})
        .reset_index()
    )
    pass_network["player1"] = pass_network.apply(
        lambda r: sorted([r["player_name"], r["pass_receiver"]])[0], axis=1
    )
    pass_network["player2"] = pass_network.apply(
        lambda r: sorted([r["player_name"], r["pass_receiver"]])[1], axis=1
    )
    pass_network = pass_network.groupby(["player1", "player2"]).sum().reset_index()
    pass_network = pass_network.loc[
        (~pass_network["player1"].isin(subbed_on))
        & (~pass_network["player2"].isin(subbed_on))
    ]
    pass_network = pd.merge(
        pass_network,
        point_df[["player", "x", "y"]].rename(columns={"x": "s_x", "y": "s_y"}),
        left_on="player1",
        right_on="player",
        how="left",
    )
    pass_network = pd.merge(
        pass_network,
        point_df[["player", "x", "y"]].rename(columns={"x": "e_x", "y": "e_y"}),
        left_on="player2",
        right_on="player",
        how="left",
    )
    pass_network = pass_network.loc[pass_network["passes"] >= min_passes_to_show]
    return pass_network


def plot_pass_map(game):
    min_size = 15
    max_size = 40
    min_width = 1
    max_width = 20
    MIN_TRANSPARENCY = 0.3
    team = game["team"].unique().tolist()[0]
    opponent = game["opponent"].unique().tolist()[0]
    game["home_away"] = game["is_home_team"].apply(lambda x: "home" if x else "away")
    home_away = game["home_away"].unique().tolist()[0]
    min_passes_to_show = 1 if team == "burnley" else 3
    team_img = Image.open(
        urlopen(
            f'https://s10.gifyu.com/images/{img_file_translates.get(team, team).lower().replace(" ","_")}.png'
        )
    )
    opp_img = Image.open(
        urlopen(
            f'https://s10.gifyu.com/images/{img_file_translates.get(opponent, opponent).lower().replace(" ","_")}.png'
        )
    )

    game["start_distance_to_goal0"] = game.apply(
        lambda r: pitch_distance(r["x"], r["y"], GOAL_LOCATION[0], GOAL_LOCATION[1]),
        axis=1,
    )
    game["start_distance_to_goal1"] = game.apply(
        lambda r: pitch_distance(r["x"], r["y"], TOP_GOAL[0], TOP_GOAL[1]), axis=1
    )
    game["start_distance_to_goal2"] = game.apply(
        lambda r: pitch_distance(r["x"], r["y"], BOTTOM_GOAL[0], BOTTOM_GOAL[1]), axis=1
    )
    game["start_distance_to_goal"] = game.apply(
        lambda r: min(r[f"start_distance_to_goal{c}"] for c in range(0, 3)), axis=1
    )
    game["end_distance_to_goal0"] = game.apply(
        lambda r: pitch_distance(
            r["endX"], r["endY"], GOAL_LOCATION[0], GOAL_LOCATION[1]
        ),
        axis=1,
    )
    game["end_distance_to_goal1"] = game.apply(
        lambda r: pitch_distance(r["endX"], r["endY"], TOP_GOAL[0], TOP_GOAL[1]), axis=1
    )
    game["end_distance_to_goal2"] = game.apply(
        lambda r: pitch_distance(r["endX"], r["endY"], BOTTOM_GOAL[0], BOTTOM_GOAL[1]),
        axis=1,
    )
    game["end_distance_to_goal"] = game.apply(
        lambda r: min(r[f"end_distance_to_goal{c}"] for c in range(0, 3)), axis=1
    )
    game["progressive_pass"] = game.apply(
        lambda r: (r["end_distance_to_goal"] < r["start_distance_to_goal"] * 0.75)
        and ("passCorner" not in r["satisfied_events"]),
        axis=1,
    )

    subbed_on = game.loc[game["event_type"] == 19, "player_name"]

    passes_attempted_series = game.loc[(game["event_type"] == 1)][
        ["player_name"]
    ].value_counts()
    passes_attempted_series.name = "passes_attempted"
    passes_completed_series = game.loc[
        (game["event_type"] == 1) & (game["outcomeType"] == 1)
    ][["player_name"]].value_counts()
    passes_completed_series.name = "passes_completed"
    pd_passes_by_player = pd.merge(
        passes_attempted_series.to_frame(),
        passes_completed_series.to_frame(),
        left_on="player_name",
        right_on="player_name",
    ).reset_index()
    pd_passes_by_player["pct"] = (
        pd_passes_by_player["passes_completed"]
        / pd_passes_by_player["passes_attempted"]
    )
    pd_passes_by_player = pd_passes_by_player.loc[
        ~pd_passes_by_player["player_name"].isin(subbed_on)
    ]
    pd_passes_by_player = pd_passes_by_player.sort_values("pct", ascending=False)[
        ["player_name", "pct"]
    ][0:3].values

    most_passes_attempted = passes_attempted_series[0:3].reset_index().values
    most_passes_completed = passes_completed_series[0:3].reset_index().values
    most_prog_passes_attempted = (
        game.loc[(game["progressive_pass"] == True)][["player_name"]]
        .value_counts()[0:3]
        .reset_index()
        .values
    )
    most_prog_passes_completed = (
        game.loc[(game["progressive_pass"] == True) & (game["outcomeType"] == 1)][
            ["player_name"]
        ]
        .value_counts()[0:3]
        .reset_index()
        .values
    )
    most_prog_passes_received = (
        game.loc[(game["progressive_pass"] == True) & (game["outcomeType"] == 1)][
            ["pass_receiver"]
        ]
        .value_counts()[0:3]
        .reset_index()
        .values
    )
    attacking_actions = [1, 15, 3, 50, 61, 74]
    formation = game["formation"].iloc[0]
    team_score = game["team_score"].iloc[0]
    opponent_score = game["opponent_score"].iloc[0]

    attacking_actions_df = game.loc[
        (game["event_type"].isin(attacking_actions))
        & (~game["player_name"].isin(subbed_on))
    ]
    attacking_actions_df = attacking_actions_df.loc[
        attacking_actions_df["formation"] == formation
    ]
    passes = attacking_actions_df.loc[
        (attacking_actions_df["event_type"] == 1)
        & (attacking_actions_df["outcomeType"] == 1)
    ]
    pass_network = passes.groupby(["player_name", "pass_receiver"]).count()[
        "event_type"
    ]
    touch_counts = (
        attacking_actions_df.groupby(["player_name", "shirt_number"])
        .count()[["event_type"]]
        .reset_index()
        .set_index("player_name")
    )
    touch_locations = attacking_actions_df.groupby("player_name").mean()[["x", "y"]]
    df_to_plot_points = pd.DataFrame(
        [
            {
                "player": player,
                "player_label": touch_counts.loc[player, "shirt_number"],
                "count": touch_counts.loc[player, "event_type"],
                "x": touch_locations.loc[player, "x"],
                "y": touch_locations.loc[player, "y"],
            }
            for player in touch_counts.index
        ]
    )
    df_to_plot_points["s"] = min_size + df_to_plot_points["count"] / df_to_plot_points[
        "count"
    ].max() * (max_size - min_size)
    passes = game.loc[(game["event_type"] == 1) & (game["outcomeType"] == 1)]
    pass_network = generate_pass_network(
        passes, df_to_plot_points, subbed_on, min_passes_to_show
    )

    pass_network["width"] = min_width + (
        pass_network["passes"] - min_passes_to_show
    ) / pass_network["passes"].max() * (max_width - min_width)

    progressive_passes = game.loc[
        (game["event_type"] == 1)
        & (game["outcomeType"] == 1)
        & (game["progressive_pass"] == True)
    ]
    progressive_pass_network = generate_pass_network(
        progressive_passes, df_to_plot_points, subbed_on, 1
    )
    progressive_pass_network["width"] = min_width + (
        progressive_pass_network["passes"] - 1
    ) / pass_network["passes"].max() * (max_width - min_width)

    pitch = Pitch(pitch_type="opta", pitch_color="#000000", line_color="#c7d5cc")
    fig, axs = pitch.grid(
        left=0.2,
        grid_width=0.8,
        figheight=10,
        title_height=0.08,
        endnote_space=0,
        axis=False,
        title_space=0,
        grid_height=0.82,
        endnote_height=0.05,
    )
    ax_panel = fig.add_axes([0.0, 0.05, 0.2, 0.82])
    ax_panel.set_facecolor("#000000")

    name_to_number_dict = {
        r["player_name"]: r["shirt_number"]
        for _, r in game.groupby("player_name")
        .agg({"player_name": "first", "shirt_number": "first"})
        .iterrows()
    }

    def _display_name(name):
        t = name.title().split(" ")
        if len(t) == 1:
            return t[0]
        else:
            return " ".join([f"{t[0][0]}."] + t[1:])

    panel_text = ""
    panel_text += "\nPasses Attempted\n"
    panel_text += "--------------------------\n"
    for i, v in enumerate(most_passes_attempted):
        panel_text += f'{name_to_number_dict[v[0]]:{" "}{"<"}{3}}{_display_name(v[0]):{" "}{"<"}{20}}{v[1]:{"<"}{3}}\n'

    panel_text += "\nPasses Completed\n"
    panel_text += "--------------------------\n"
    for i, v in enumerate(most_passes_completed):
        panel_text += f'{name_to_number_dict[v[0]]:{" "}{"<"}{3}}{_display_name(v[0]):{" "}{"<"}{20}}{v[1]:{"<"}{3}}\n'

    panel_text += "\nPct Passes Completed\n"
    panel_text += "--------------------------\n"
    for i, v in enumerate(pd_passes_by_player):
        panel_text += f'{name_to_number_dict[v[0]]:{" "}{"<"}{3}}{_display_name(v[0]):{" "}{"<"}{20}}{int(v[1]*100):{"<"}{2}}%\n'

    panel_text += "\nProg. Passes Attempted\n"
    panel_text += "--------------------------\n"
    for i, v in enumerate(most_prog_passes_attempted):
        panel_text += f'{name_to_number_dict[v[0]]:{" "}{"<"}{3}}{_display_name(v[0]):{" "}{"<"}{20}}{v[1]:{"<"}{3}}\n'

    panel_text += "\nProg. Passes Completed\n"
    panel_text += "--------------------------\n"
    for i, v in enumerate(most_prog_passes_completed):
        panel_text += f'{name_to_number_dict[v[0]]:{" "}{"<"}{3}}{_display_name(v[0]):{" "}{"<"}{20}}{v[1]:{"<"}{3}}\n'

    panel_text += "\nProg. Passes Received\n"
    panel_text += "--------------------------\n"
    for i, v in enumerate(most_prog_passes_received):
        panel_text += f'{name_to_number_dict[v[0]]:{" "}{"<"}{3}}{_display_name(v[0]):{" "}{"<"}{20}}{v[1]:{"<"}{3}}\n'

    ax_panel.text(
        x=0.1,
        y=1,
        s=panel_text,
        color="lightgrey",
        size=12,
        va="top",
        ha="left",
        family="monospace",
    )
    for spine in ax_panel.spines.values():
        spine.set_visible(False)
    ax_panel.get_xaxis().set_ticks([])
    fig.set_facecolor("#000000")
    color = np.array(to_rgba("white"))
    color = np.tile(color, (len(pass_network), 1))
    c_transparency = pass_network["passes"] / pass_network["passes"].max()
    c_transparency = (c_transparency * (1 - MIN_TRANSPARENCY)) + MIN_TRANSPARENCY
    color[:, 3] = c_transparency

    pitch.lines(
        pass_network["s_x"],
        pass_network["s_y"],
        pass_network["e_x"],
        pass_network["e_y"],
        lw=pass_network["width"],
        color=color,
        zorder=2,
        ax=axs["pitch"],
    )

    pitch.lines(
        progressive_pass_network["s_x"],
        progressive_pass_network["s_y"],
        progressive_pass_network["e_x"],
        progressive_pass_network["e_y"],
        lw=progressive_pass_network["width"],
        color="red",
        zorder=3,
        ax=axs["pitch"],
    )

    pitch.scatter(
        df_to_plot_points["x"],
        df_to_plot_points["y"],
        s=df_to_plot_points["s"] ** 2,
        zorder=4,
        ax=axs["pitch"],
        c=team_colors[team][0],
    )
    for index, row in df_to_plot_points.iterrows():
        pitch.annotate(
            row["player_label"],
            xy=(row.x, row.y),
            c=team_colors[team][1],
            va="center",
            ha="center",
            size=12,
            weight="bold",
            ax=axs["pitch"],
            zorder=5,
        )

    # endnote /title
    axs["endnote"].text(
        0.07,
        0.5,
        f"@McLachBot\nhttps://www.mclachbot/passmap/{team}/latest",
        color="#c7d5cc",
        va="center",
        ha="left",
        fontsize=12,
        fontproperties=robotto_regular.prop,
    )
    axs["endnote"].text(
        0.95,
        0.5,
        f"Red lines are progressive passes made between\nthat pair of players (minimum of {min_passes_to_show})",
        color="#c7d5cc",
        va="center",
        ha="right",
        fontsize=12,
        fontproperties=robotto_regular.prop,
    )
    date = pd.Timestamp(game["match_date"].iloc[0]).strftime("%Y-%m-%d")
    TITLE_TEXT = f"{team.title()} vs {opponent.title()} ({home_away.title()})"
    axs["title"].text(
        0.5,
        0.7,
        TITLE_TEXT,
        color="#c7d5cc",
        va="center",
        ha="center",
        fontproperties=robotto_regular.prop,
        fontsize=30,
    )
    axs["title"].text(
        0.5,
        0.25,
        f"Formation: {formation}.  Date: {date}. Result: {team_score}:{opponent_score} ",
        color="#c7d5cc",
        va="center",
        ha="center",
        fontproperties=robotto_regular.prop,
        fontsize=18,
    )
    image = Image.open(
        urlopen(
            "https://pbs.twimg.com/profile_images/1490059544734703620/7avjgS-D_400x400.jpg"
        )
    )
    add_image(image, fig, left=0.21, bottom=0.01, width=0.07, height=0.07)
    add_image(team_img, fig, left=0.25, bottom=0.88, width=0.05)
    add_image(opp_img, fig, left=0.90, bottom=0.88, width=0.05)
    return fig


def player_pass_map(game_data, player_name, ax, pitch: Pitch):
    passes = game_data.loc[
        (game_data["player_name"] == player_name) & (game_data["event_type"] == 1)
    ]
    n_tot = len(passes)
    if n_tot < 1:
        return
    position_array = game_data.loc[
        (game_data["player_name"] == player_name)
        & (~game_data["position"].isin(["Substitute", "Error"])),
        "position",
    ]
    if position_array.shape[0]>0:
        position = position_array.iloc[0]
    else:
        position = ""
    number_array = game_data.loc[
        (game_data["player_name"] == player_name)
        & (~game_data["position"].isin(["Substitute", "Error"])),
        "shirt_number",
    ]
    if number_array.shape[0]>0:
        number = number_array.iloc[0]
    else:
        number = ""

    # print(passes['position'])
    # position = passes['position'].iloc[0]
    progressive_pass_mask = passes["progressive_pass"] == True
    completed_mask = passes["outcomeType"] == 1
    n_comp = len(passes[completed_mask])
    pitch.lines(
        passes.loc[(~progressive_pass_mask) & (~completed_mask)]["x"],
        passes.loc[(~progressive_pass_mask) & (~completed_mask)]["y"],
        passes.loc[(~progressive_pass_mask) & (~completed_mask)]["endX"],
        passes.loc[(~progressive_pass_mask) & (~completed_mask)]["endY"],
        ax=ax,
        color="darkred",
        linewidth=3,
        comet=True,
        capstyle="round",
        alpha=0.8,
    )
    pitch.lines(
        passes.loc[(~progressive_pass_mask) & (completed_mask)]["x"],
        passes.loc[(~progressive_pass_mask) & (completed_mask)]["y"],
        passes.loc[(~progressive_pass_mask) & (completed_mask)]["endX"],
        passes.loc[(~progressive_pass_mask) & (completed_mask)]["endY"],
        ax=ax,
        color="orange",
        linewidth=3,
        comet=True,
        capstyle="round",
        alpha=1,
    )

    pitch.lines(
        passes.loc[(progressive_pass_mask) & (~completed_mask)]["x"],
        passes.loc[(progressive_pass_mask) & (~completed_mask)]["y"],
        passes.loc[(progressive_pass_mask) & (~completed_mask)]["endX"],
        passes.loc[(progressive_pass_mask) & (~completed_mask)]["endY"],
        ax=ax,
        color="blue",
        linewidth=3,
        comet=True,
        capstyle="round",
        alpha=0.8,
    )
    pitch.lines(
        passes.loc[(progressive_pass_mask) & (completed_mask)]["x"],
        passes.loc[(progressive_pass_mask) & (completed_mask)]["y"],
        passes.loc[(progressive_pass_mask) & (completed_mask)]["endX"],
        passes.loc[(progressive_pass_mask) & (completed_mask)]["endY"],
        ax=ax,
        color="lightblue",
        linewidth=3,
        comet=True,
        capstyle="round",
        alpha=1,
    )
    player_name_display = (
        " ".join(
            [f"{p[0]}." if i == 0 else p for i, p in enumerate(player_name.split(" "))]
        )
        if " " in player_name
        else player_name
    )

    ax.text(
        0,
        107,
        f"{position} | {number} | {player_name_display.title()} | {n_comp}/{n_tot} ({n_comp/n_tot * 100 if n_tot > 0 else 0:.0f}%)",
        ha="left",
        va="center",
        fontsize=12,
        color="#c7d5cc",
        fontproperties=robotto_regular.prop,
    )


def player_passing_maps(game, position_df):
    position_df["formation_name"] = position_df["formation_name"].apply(
        lambda x: x.replace("-", "")
    )
    team = game["team"].unique().tolist()[0]
    opponent = game["opponent"].unique().tolist()[0]
    game["home_away"] = game["is_home_team"].apply(lambda x: "home" if x else "away")
    home_away = game["home_away"].unique().tolist()[0]

    game["start_distance_to_goal0"] = game.apply(
        lambda r: pitch_distance(r["x"], r["y"], GOAL_LOCATION[0], GOAL_LOCATION[1]),
        axis=1,
    )
    game["start_distance_to_goal1"] = game.apply(
        lambda r: pitch_distance(r["x"], r["y"], TOP_GOAL[0], TOP_GOAL[1]), axis=1
    )
    game["start_distance_to_goal2"] = game.apply(
        lambda r: pitch_distance(r["x"], r["y"], BOTTOM_GOAL[0], BOTTOM_GOAL[1]), axis=1
    )
    game["start_distance_to_goal"] = game.apply(
        lambda r: min(r[f"start_distance_to_goal{c}"] for c in range(0, 3)), axis=1
    )
    game["end_distance_to_goal0"] = game.apply(
        lambda r: pitch_distance(
            r["endX"], r["endY"], GOAL_LOCATION[0], GOAL_LOCATION[1]
        ),
        axis=1,
    )
    game["end_distance_to_goal1"] = game.apply(
        lambda r: pitch_distance(r["endX"], r["endY"], TOP_GOAL[0], TOP_GOAL[1]), axis=1
    )
    game["end_distance_to_goal2"] = game.apply(
        lambda r: pitch_distance(r["endX"], r["endY"], BOTTOM_GOAL[0], BOTTOM_GOAL[1]),
        axis=1,
    )
    game["end_distance_to_goal"] = game.apply(
        lambda r: min(r[f"end_distance_to_goal{c}"] for c in range(0, 3)), axis=1
    )
    game["progressive_pass"] = game.apply(
        lambda r: (r["end_distance_to_goal"] < r["start_distance_to_goal"] * 0.75)
        and ("passCorner" not in r["satisfied_events"]),
        axis=1,
    )
    pitch = Pitch(
        pitch_type="opta", pitch_color="#000000", line_color="#c7d5cc", linewidth=1
    )
    fig, axs = pitch.grid(
        nrows=5,
        ncols=3,
        figheight=14,
        title_space=0.025,
        title_height=0.06,
        endnote_height=0.03,
        grid_height=0.875,
        axis=False,
    )
    axs["title"].set_facecolor("#000000")
    fig.set_facecolor("#000000")

    subs = game.loc[game["event_type"] == 19, "player_name"]
    names_position_list = (
        game.loc[(~game["player_name"].isna()) & (~game["player_name"].isin(subs))]
        .groupby("player_name")
        .first()
        .reset_index()
    )
    names = (
        pd.merge(
            names_position_list,
            position_df,
            left_on=["formation", "position"],
            right_on=["formation_name", "position"],
            suffixes=("", "_"),
        )
        .sort_values("team_player_formation")["player_name"]
        .tolist()
        + subs.tolist()
    )

    for i, name in enumerate(names):
        r_i = int(math.floor(i / 3))
        r_j = i % 3

        if name:

            player_pass_map(game, name, axs["pitch"][r_i][r_j], pitch)

    successful_pass_mask = (game["event_type"] == 1) & (game["outcomeType"] == 1)
    # print(game.loc[successful_pass_mask])
    # pitch.kdeplot(x=game.loc[successful_pass_mask]['endX'], y=game.loc[successful_pass_mask]['endX'], ax=axs['pitch'][4][2],
    #            #cmap=cmr.lavender,
    #            levels=100,
    #            thresh=0, shade=True)
    # pcm = pitch.heatmap(bin_statistic, ax=axs['pitch'][4][2], cmap='hot', edgecolors='#c7d5cc', linewidths=1)
    kde = pitch.kdeplot(
        game.loc[successful_pass_mask]["endX"],
        game.loc[successful_pass_mask]["endY"],
        ax=axs["pitch"][4][2],
        levels=50,
        shade=True,
        cmap=cmr.amber,
        thresh=0.1,
        alpha=0.8,
    )
    axs["pitch"][4][2].text(
        0,
        107,
        f"Passes Received Locations",
        ha="left",
        va="center",
        fontsize=12,
        color="#c7d5cc",
        fontproperties=robotto_regular.prop,
    )

    formation = game["formation"].iloc[0]
    team_score = game["team_score"].iloc[0]
    opponent_score = game["opponent_score"].iloc[0]
    date = pd.Timestamp(game["match_date"].iloc[0]).strftime("%Y-%m-%d")
    TITLE_TEXT = f"{team.title()} vs {opponent.title()} ({home_away.title()})"
    axs["title"].text(
        0.5,
        0.7,
        TITLE_TEXT,
        color="#c7d5cc",
        va="center",
        ha="center",
        fontproperties=robotto_regular.prop,
        fontsize=30,
    )
    axs["title"].text(
        0.5,
        0.25,
        f"Formation: {formation}.  Date: {date}. Result: {team_score}:{opponent_score} ",
        color="#c7d5cc",
        va="center",
        ha="center",
        fontproperties=robotto_regular.prop,
        fontsize=18,
    )
    team_img = Image.open(
        urlopen(
            f'https://s10.gifyu.com/images/{img_file_translates.get(team, team).lower().replace(" ","_")}.png'
        )
    )
    opp_img = Image.open(
        urlopen(
            f'https://s10.gifyu.com/images/{img_file_translates.get(opponent, opponent).lower().replace(" ","_")}.png'
        )
    )
    add_image(team_img, fig, left=0.05, bottom=0.95, width=0.05)
    add_image(opp_img, fig, left=0.90, bottom=0.95, width=0.05)
    legend_elements = [
        Line2D(
            [0],
            [0],
            color="orange",
            marker="o",
            label="Complete Pass",
            markersize=5,
            linewidth=0,
        ),
        Line2D(
            [0],
            [0],
            color="darkred",
            marker="o",
            label="Incomplete Pass",
            markersize=5,
            linewidth=0,
        ),
        Line2D(
            [0],
            [0],
            color="lightblue",
            marker="o",
            label="Complete Progressive Pass",
            markersize=5,
            linewidth=0,
        ),
        Line2D(
            [0],
            [0],
            color="blue",
            marker="o",
            label="Incomplete Progressive Pass",
            markersize=5,
            linewidth=0,
        ),
    ]
    leg = axs["endnote"].legend(
        ncol=2,
        handles=legend_elements,
        loc="lower right",
        # bbox_to_anchor=(0.0, 0.0),
        facecolor="black",
        edgecolor="#c7d5cc",
        # labelcolor ='#c7d5cc',
        framealpha=1,
        labelspacing=0.5,
        fancybox=True,
        borderpad=0.25,
        handletextpad=0.1,
        prop=dict(family="monospace"),
    )
    for text in leg.get_texts():
        text.set_color("#c7d5cc")
    axs["endnote"].set_facecolor("#000000")
    axs["endnote"].text(
        0.08,
        0.5,
        f"@McLachBot\nhttps://www.mclachbot.com/playerpassmap/{team}/latest",
        color="#c7d5cc",
        va="center",
        ha="left",
        fontsize=12,
        fontproperties=robotto_regular.prop,
    )
    image = Image.open(
        urlopen(
            "https://pbs.twimg.com/profile_images/1490059544734703620/7avjgS-D_400x400.jpg"
        )
    )
    add_image(image, fig, left=0.02, bottom=-0.03, width=0.07, height=0.07)
    return fig
