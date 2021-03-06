from io import BytesIO
from fastapi import FastAPI, Request, Response, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
from data_models.build_up_index import (
    get_build_up_index_pizza,
    get_build_up_index_table,
)
from data_models.striker_performance import (
    get_striker_overperformance_summary,
    get_striker_performance_player_data,
)
from visualizations.build_up_pizza import bake_build_up_pizza
from visualizations.passmap import player_passing_maps, plot_pass_map
from matplotlib import pyplot as plt
import logging
from data_models.constants import LEAGUE_NAME_TRANSLATIONS
from functools import wraps
import os

from data_models.data_generators import (
    get_match_for_team_from_whoscored_for_date,
    get_teams_from_fbref,
    get_latest_match_for_team_from_whoscored,
    get_whoscored_all_teams,
    get_whoscored_matches_for_team,
    get_whoscored_position_df,
)
from visualizations.striker_overperformance import plot_finishing_performance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

BLACKLISTED_IPs = ["54.36.149.5"]


def check_blacklist(func):
    @wraps(func)
    def _inner(request: Request, *args, **kwargs):
        ip = str(request.client.host)
        print("IP:", ip)
        if ip in BLACKLISTED_IPs:
            logger.warn(f"{ip} is blacklisted")
            data = f"IP {ip} is not allowed to access this resource."
            return Response(content=data, status_code=status.HTTP_403_FORBIDDEN)
        else:
            return func(request, *args, **kwargs)

    return _inner


@app.get("/")
@check_blacklist
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/rolling_npxg/{comp}/{team}/{season}")
@check_blacklist
def rolling_npxg(request: Request, comp: str, team: str, season: int):
    if comp == "champions_league":
        rolling_window = 3
    else:
        rolling_window = 5
    from data_models.data_generators import npxg_for_against
    from visualizations.data_visualizations import npxg_rolling_plot

    team = team.lower()
    npxg_for_against_rolling = npxg_for_against(
        team, season, comp, rolling_window=rolling_window
    )
    fig = npxg_rolling_plot(
        npxg_for_against_rolling, team, season, comp, rolling_window
    )
    output = BytesIO()
    fig.savefig(output, format="png", pad_inches=0.1)
    return Response(output.getvalue(), media_type="image/png")


@app.get("/rolling_npxg")
@check_blacklist
def rolling_npxg_idx(request: Request):

    team_dictionary, team_name_dictionary = get_teams_from_fbref()
    reverse_dict = {v: k for k, v in LEAGUE_NAME_TRANSLATIONS.items()}
    return templates.TemplateResponse(
        "rolling_npxg.html",
        {
            "request": request,
            "leagues": team_dictionary,
            "team_name_dict": team_name_dictionary,
            "league_link_lookup": reverse_dict,
        },
    )


@app.get("/rolling_npxg/teamlist")
@check_blacklist
def rolling_npxg_team_list(request: Request):
    team_dictionary, team_name_dictionary = get_teams_from_fbref()
    return team_dictionary


@app.get("/passmap/{team}/{date}")
@check_blacklist
def team_passmap(request: Request, team, date):
    log = logging.getLogger(__name__)

    team = team.replace("_", " ").lower()
    log.info(f"Getting pass map for {team} on {date}")

    if date != "latest":

        date_to_use = date

    else:
        df = get_latest_match_for_team_from_whoscored(team)
        date_to_use = df["match_date"].tolist()[0].strftime("%Y-%m-%d")
        log.info(f"Using latest match for {team} on {date_to_use}")

    if not os.path.exists("static/img/visualisations/passmaps"):
        os.makedirs("static/img/visualisations/passmaps")
    output_file = (
        f"static/img/visualisations/passmaps/{team}_{date_to_use.replace('-','_')}.png"
    )
    if not os.path.exists(output_file):
        if date != "latest":
            df = get_match_for_team_from_whoscored_for_date(team, date)
        if df.shape[0] == 0:
            return "no data for this team"

        fig = plot_pass_map(df)

        fig.savefig(output_file, format="png", pad_inches=0.1)
        fig.clear()
        plt.clf()
        plt.close("all")
        # output = BytesIO()
        # fig.savefig(output, format="png", pad_inches=0.1)
        # return Response(output.getvalue(), media_type="image/png")
    with open(output_file, "rb") as f:
        return Response(f.read(), media_type="image/png")


@app.get("/playerpassmap/{team}/{date}")
@check_blacklist
def player_passmap(request: Request, team, date):
    log = logging.getLogger(__name__)
    team = team.replace("_", " ").lower()
    log.info(f"Getting pass map for {team} on {date}")
    log.info(f"getting data for {team}")
    if date != "latest":

        date_to_use = date

    else:
        df = get_latest_match_for_team_from_whoscored(team)
        date_to_use = df["match_date"].tolist()[0].strftime("%Y-%m-%d")
        log.info(f"Using latest match for {team} on {date_to_use}")

    if not os.path.exists("static/img/visualisations/playerpassmaps"):
        os.makedirs("static/img/visualisations/playerpassmaps")
    output_file = f"static/img/visualisations/playerpassmaps/{team}_{date_to_use.replace('-','_')}.png"

    if not os.path.exists(output_file):
        if date != "latest":
            df = get_match_for_team_from_whoscored_for_date(team, date)

        log.info(f"got data for {team}")
        log.info("getting position dataframe")
        position_df = get_whoscored_position_df()
        log.info("got position dataframe")
        if df.shape[0] == 0:
            return "no data for this team"

        log.info("plotting")
        fig = player_passing_maps(df, position_df)
        log.info("saving")
        fig.savefig(output_file, format="png", pad_inches=0.1)
        fig.clear()
        plt.clf()
        plt.close("all")
        # output = BytesIO()
        # fig.savefig(output, format="png", pad_inches=0.1)
        # return Response(output.getvalue(), media_type="image/png")
    with open(output_file, "rb") as f:
        return Response(f.read(), media_type="image/png")


@app.get("/passmap_for_league/{league}/{season}")
@check_blacklist
def passmaps_idx(request: Request, league: str, season: int):
    team_list = sorted([t.replace(" ", "_") for t in get_whoscored_all_teams(league, season)])
    team_name_dictionary = {t: t.replace("_", " ").title() for t in team_list}

    return templates.TemplateResponse(
        "passmap.html",
        {
            "request": request,
            "teams": team_list,
            "team_name_dict": team_name_dictionary,
        },
    )


@app.get("/passmap/{team}")
@check_blacklist
def passmap_team_page(request: Request, team: str):
    team = team.replace("_", " ")
    df = get_whoscored_matches_for_team(team).sort_values("match_date")
    df["home"] = df["home"].apply(lambda x: x.replace("_", " ").title())
    df["away"] = df["away"].apply(lambda x: x.replace("_", " ").title())
    df["match_date"] = df["match_date"].apply(lambda x: x.strftime("%Y-%m-%d"))

    if df.shape[0] == 0:
        return "no data for this team"
    records = df.to_records(index=False)
    return templates.TemplateResponse(
        "passmap_team_index.html",
        {"request": request, "team": team.title(), "records": records},
    )


@app.get("/striker_performance/{league}")
@check_blacklist
def striker_performance(request: Request, league: str):

    over_df, under_df = get_striker_overperformance_summary(league_tag=league)
    over_records = over_df.to_records(index=False)
    under_records = under_df.to_records(index=False)
    return templates.TemplateResponse(
        "striker_performance.html",
        {
            "request": request,
            "records_overperform": over_records,
            "records_underperform": under_records,
            "league": league,
            "league_name": "European Men's Top 5 Leagues"
            if league == "EUROTOP5"
            else league,
        },
    )


@app.get("/striker_performance/{league}/{player}")
@check_blacklist
def striker_performance_player(request: Request, league: str, player: str):
    full, this_season = get_striker_performance_player_data(
        league_tag=league, player=player
    )
    fig = plot_finishing_performance(full, this_season, league)

    output = BytesIO()
    fig.savefig(output, format="png", pad_inches=0.1)
    return Response(output.getvalue(), media_type="image/png")


@app.get("/theoven")
@check_blacklist
def theoven(request: Request):
    year_dict = {
        "Top 5 Mens League": [2017, 2018, 2019, 2020, 2021],
        "WSL": [2018, 2019, 2020, 2021],
        "MLS": [2018, 2019, 2020, 2021, 2022],
    }
    return templates.TemplateResponse(
        "theoven.html", {"request": request, "years": year_dict}
    )


@app.get("/buildup_pizza/{league}/{year}")
@check_blacklist
def buildup_pizza(request: Request, league: str, year: int):
    build_up_index = get_build_up_index_table(league, year).to_records(index=True)
    return templates.TemplateResponse(
        "build_up_index.html",
        {"request": request, "league": league, "year": year, "records": build_up_index},
    )


@app.get("/buildup_pizza/{league}/{year}/{player}")
@check_blacklist
def build_up_pizza_player(request: Request, league: str, year: int, player: str):
    print(str(request.client.host))
    build_up_index = get_build_up_index_pizza(league, year)
    fig = bake_build_up_pizza(player, build_up_index, year, league)
    output = BytesIO()
    fig.savefig(output, format="png", pad_inches=0.0, facecolor="#EBEBE9")
    return Response(output.getvalue(), media_type="image/png")
