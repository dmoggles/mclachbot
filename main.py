from io import BytesIO
from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
from visualizations.passmap import player_passing_maps, plot_pass_map

import logging
from data_models.constants import LEAGUE_NAME_TRANSLATIONS

from data_models.data_generators import (
    get_teams_from_fbref,
    get_latest_match_for_team_from_whoscored,
    get_whoscored_position_df,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()],
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
@repeat_every(seconds=60 * 10)
def reload_data():
    app.fbref_data.load_data()


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/rolling_npxg/{comp}/{team}/{season}")
def rolling_npxg(comp: str, team: str, season: int):
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
def rolling_npxg_team_list(request: Request):
    team_dictionary, team_name_dictionary = get_teams_from_fbref()
    return team_dictionary


@app.get("/passmap/{team}/{date}")
def team_passmap(request: Request, team, date):
    if date != "latest":
        return "past dates not implemented yet"
    team = team.replace("_", " ")
    df = get_latest_match_for_team_from_whoscored(team)
    if df.shape[0] == 0:
        return "no data for this team"

    fig = plot_pass_map(df)
    output = BytesIO()
    fig.savefig(output, format="png", pad_inches=0.1)
    return Response(output.getvalue(), media_type="image/png")


@app.get("/playerpassmap/{team}/{date}")
def player_passmap(request: Request, team, date):
    log = logging.getLogger(__name__)
    team = team.replace("_", " ")
    if date != "latest":
        return "past dates not implemented yet"
    log.info(f"getting data for {team}")
    df = get_latest_match_for_team_from_whoscored(team)
    log.info(f"got data for {team}")
    log.info("getting position dataframe")
    position_df = get_whoscored_position_df()
    log.info("got position dataframe")
    if df.shape[0] == 0:
        return "no data for this team"

    log.info("plotting")
    fig = player_passing_maps(df, position_df)
    output = BytesIO()
    log.info("saving")
    fig.savefig(output, format="png", pad_inches=0.1)
    return Response(output.getvalue(), media_type="image/png")


@app.get("/passmap")
def passmaps_idx(request: Request):
    return templates.TemplateResponse("passmap.html", {"request": request})
