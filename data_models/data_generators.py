from lib2to3.pgen2.pgen import DFAState
from data_models.constants import LEAGUE_NAME_TRANSLATIONS
from data_models.fbref_data_manager import get_fbref_data, ConnectionManager
from footmav import fb, aggregate_by, filter, Filter, filters, FbRefData
import pandas as pd
import logging
from pypika import Table, MySQLQuery, Order


def npxg_for_against(team: str, season: int, comp: str, rolling_window: int = 5):
    """
    Joins team and opponent nxpg data and computes rolling averages on each
    """

    log = logging.getLogger(__name__)
    fbref_data = Table("fbref2")
    query_columns = [
        fb.DATE.N,
        fb.TEAM.N,
        fb.OPPONENT.N,
        fb.NPXG.N,
        fb.PLAYER_ID.N,
    ]

    query = (
        MySQLQuery.from_(fbref_data)
        .select(*query_columns)
        .where(fbref_data.season == season)
        .where(fbref_data.comp == LEAGUE_NAME_TRANSLATIONS[comp])
        .where((fbref_data.squad == team) | (fbref_data.opponent == team))
    )

    log.info(f'Running query: "{query}"')
    df = pd.read_sql(query.get_sql(), ConnectionManager().engine)
    data = FbRefData(df)
    team_data = data.pipe(filter, [Filter(fb.TEAM, team, filters.EQ)]).pipe(
        aggregate_by, [fb.DATE]
    )
    opp_data = data.pipe(filter, [Filter(fb.OPPONENT, team, filters.EQ)]).pipe(
        aggregate_by, [fb.DATE]
    )
    df = pd.merge(
        left=team_data.df, right=opp_data.df, on=[fb.DATE.N], suffixes=("", "_opp")
    )[[fb.DATE.N, fb.OPPONENT.N, fb.NPXG.N, fb.NPXG.N + "_opp"]]
    npxg_for_against_rolling = (
        df.set_index([fb.DATE.N, fb.OPPONENT.N])
        .rolling(window=rolling_window)
        .mean()
        .reset_index()
        .dropna()
    )
    npxg_for_against_rolling["round"] = range(0, len(npxg_for_against_rolling))
    return npxg_for_against_rolling


def get_teams_from_fbref():
    log = logging.getLogger(__name__)
    teams = Table("fbref_teams")
    query = (
        MySQLQuery.from_(teams)
        .select(teams.star)
        .where(teams.comp != "Champions Lg")
        .orderby("comp", order=Order.asc)
        .orderby("squad", order=Order.asc)
        .orderby("season", order=Order.desc)
    )
    log.info(f'Running query: "{query}"')
    df = pd.read_sql(query.get_sql(), ConnectionManager().engine)
    dict_teams = dict()
    for _, r in df.iterrows():
        if r["comp"] not in dict_teams:
            dict_teams[r["comp"]] = dict()
        if r["squad"] not in dict_teams[r["comp"]]:
            dict_teams[r["comp"]][r["squad"]] = []
        dict_teams[r["comp"]][r["squad"]].append(r["season"])

    d_names = {t: t.replace("_", " ").title() for t in df["squad"]}
    return dict_teams, d_names


def get_latest_match_for_team_from_whoscored(team: str):
    log = logging.getLogger(__name__)
    engine = ConnectionManager().engine
    first_query = f"""
    SELECT matchId FROM whoscored_meta WHERE match_date IN (
        SELECT MAX(match_date) FROM whoscored_meta WHERE home='{team}' or away='{team}'
        )
        AND (home='{team}' or away='{team}')
    """

    match_id = pd.read_sql_query(first_query, engine)["matchId"].tolist()[0]

    query = f"""
SELECT main.x, main.y, main.endX, main.endY, main.player_name, main.event_type, main.outcomeType, main.team, main.competition, main.opponent, main.match_date, main.is_home_team, main.satisfied_events,
legacy.shirt_number, legacy.pass_receiver_shirt_number, legacy.pass_receiver, legacy.position, legacy.team_score, legacy.opponent_score, legacy.formation
FROM whoscored AS main LEFT JOIN derived.whoscored_mclachbot_legacy_data AS legacy ON
 main.id = legacy.id 
 
WHERE main.matchId = {match_id} and team = '{team}'
"""
    log.info(f'Running query: "{query}"')
    df = pd.read_sql_query(query, engine)
    return df


def get_match_for_team_from_whoscored_for_date(team: str, date: str):
    log = logging.getLogger(__name__)

    engine = ConnectionManager().engine
    first_query = f"""
    SELECT matchId FROM whoscored_meta WHERE match_date = '{date}'
        AND (home='{team}' or away='{team}')
    """

    match_id = pd.read_sql_query(first_query, engine)["matchId"].tolist()[0]

    query = f"""
SELECT main.x, main.y, main.endX, main.endY, main.player_name, main.event_type, main.outcomeType, main.team, main.competition, main.opponent, main.match_date, main.is_home_team, main.satisfied_events,
legacy.shirt_number, legacy.pass_receiver_shirt_number, legacy.pass_receiver, legacy.position, legacy.team_score, legacy.opponent_score, legacy.formation
FROM whoscored AS main LEFT JOIN derived.whoscored_mclachbot_legacy_data AS legacy ON
 main.id = legacy.id
 
WHERE main.matchId = {match_id} and team = '{team}'
"""
    log.info(f'Running query: "{query}"')
    df = pd.read_sql_query(query, ConnectionManager().engine)
    return df


def get_whoscored_position_df():
    log = logging.getLogger(__name__)
    query = "SELECT * FROM whoscored_positions"
    log.info(f'Running query: "{query}"')
    df = pd.read_sql_query(query, ConnectionManager().engine)
    return df


def get_whoscored_all_teams(league, season):
    log = logging.getLogger(__name__)
    query = f"SELECT DISTINCT home FROM whoscored_meta WHERE season={season} and comp = '{league}'"
    log.info(f'Running query: "{query}"')
    df = pd.read_sql_query(query, ConnectionManager().engine)
    return df["home"].tolist()


def get_whoscored_matches_for_team(team: str):
    log = logging.getLogger(__name__)
    query = f"""
SELECT match_date, home, away, home_score, away_score FROM whoscored_meta WHERE match_date > '2021-08-01' AND (home='{team}' or away='{team}')
"""
    log.info(f'Running query: "{query}"')
    df = pd.read_sql_query(query, ConnectionManager().engine)
    return df
