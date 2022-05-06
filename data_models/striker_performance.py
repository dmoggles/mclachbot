import logging
from pypika import Table,MySQLQuery, Order
import pandas as pd
from data_models.fbref_data_manager import ConnectionManager
from scipy.stats import norm
import numpy as np
def get_striker_overperformance_summary(league_tag:str):
    log = logging.getLogger(__name__)
    summary = Table("current_npxg_plus_summary")
    query = (
        MySQLQuery.from_(summary)
        .select(summary.star)
        .where(summary.tag == league_tag)
        
    )
    log.info(f'Running query: "{query}"')
    df = pd.read_sql(query.get_sql(), ConnectionManager('derived').engine)
    df['player_display']=df['player'].apply(lambda x:x.title())
    df['squad']=df['squad'].apply(lambda x:x.replace('_',' ').replace(',',', ').title())
    df['comp']=df['comp'].apply(lambda x:x.replace(',',', '))
    df['confidence']=df['std_diff'].apply(lambda x:1-(2*(1-norm.cdf(np.abs(x),0,1))))
    cutoff = 0.5 if league_tag == 'WSL' else 1
    over_df = df.loc[df['std_diff'] > cutoff]
    over_df = over_df.sort_values(by=['std_diff'], ascending=False)

    under_df = df.loc[df['std_diff'] < -cutoff]
    under_df = under_df.sort_values(by=['std_diff'], ascending=True)
    return over_df, under_df


def get_striker_performance_player_data(player: str, league_tag:str):
    if league_tag == "WSL":
        full_filter = 30
        season_filter = 20
    else:
        full_filter = 50
        season_filter = 30

    engine = ConnectionManager('derived').engine
    striker_data = pd.read_sql_query(f"SELECT * FROM current_npxg_plus_full_game_log WHERE player='{player}'", engine).sort_values('date')
    striker_data=striker_data[striker_data['shots_total_cumulative']>full_filter]
    striker_data_2021 = pd.read_sql_query(f"SELECT * FROM current_npxg_plus_this_season_game_log WHERE player='{player}'", engine).sort_values('date')
    striker_data_2021=striker_data_2021[striker_data_2021['shots_total_cumulative']>season_filter]
    return striker_data,striker_data_2021