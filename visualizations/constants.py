import numpy as np

img_file_translates = {
    "man utd": "manchester_united",
    "man city": "manchester_city",
    "leicester": "leicester_city",
    "newcastle": "newcastle_united",
}

team_colors = {
    "arsenal": ("#EF0107", "#FFFFFF"),
    "aston villa": ("#670E36", "#95BFE5"),
    "brighton": ("#0057B8", "#FFCD00"),
    "brentford": ("#E30614", "#FBB800"),
    "burnley": ("#6C1D45", "#99D6EA"),
    "chelsea": ("#034694", "#FFFFFF"),
    "crystal palace": ("#1B458F", "#A7A5A6"),
    "everton": ("#003399", "#FFFFFF"),
    "leeds": ("#1D428A", "#FFCD00"),
    "leicester": ("#003090", "#FDBE11"),
    "liverpool": ("#C8102E", "#F6EB61"),
    "man city": ("#6CABDD", "#1C2C5B"),
    "man utd": ("#DA291C", "#FBE122"),
    "newcastle": ("#41B6E6", "#241F20"),
    "norwich": ("#00A650", "#FFF200"),
    "southampton": ("#D71920", "#130C0E"),
    "tottenham": ("#132257", "#FFFFFF"),
    "watford": ("#FBEE23", "#ED2127"),
    "west ham": ("#7A263A", "#1BB1E7"),
    "wolves": ("#FDB913", "#231F20"),
}

GOAL_LOCATION = (100, 50)
TOP_GOAL = (100, 56)
BOTTOM_GOAL = (100, 44)


def pitch_distance(x, y, end_x, end_y):
    return np.sqrt(((end_x - x) * 1.2) ** 2 + ((end_y - y) * 0.8) ** 2)
