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
    "atlanta united": ("#80000A", "#A19060"),
    "austin fc": ("#00B140", "#000000"),
    "chicago": ("#7CCDEF", "#FF0000"),
    "fc cincinnati": ("#F05323", "#263B80"),
    "colorado": ("#960A2C", "#9CC2EA"),
    "columbus": ("#FEDD00", "#000000"),
    "dc united": ("#EF3E42", "#231F20"),
    "fc dallas": ("#E81F3E", "#2A4076"),
    "houston": ("#FF6B00", "#101820"),
    "inter miami cf": ("#F7B5CD", "#231F20"),
    "l.a. galaxy": ("#00245D", "#FFD200"),
    "los angeles fc": ("#C39E6D", "#000000"),
    "minnesota united": ("#8CD2F4", "#231F20"),
    "montreal": ("#0033A1", "#000000"),
    "new england": ("#CE0E2D", "#0A2240"),
    "new york city fc": ("#6CACE4", "#F15524"),
    "new york": ("#ED1E36", "#23326A"),
    "orlando city": ("#633492", "#FDE192"),
    "philadelphia": ("#B19B69", "#071B2C"),
    "portland": ("#00482B", "#D69A00"),
    "salt lake": ("#B30838", "#013A81"),
    "san jose": ("#0067B1", "#000000"),
    "seattle": ("#5D9741", "#005595"),
    "kansas city": ("#91B0D5", "#002F65"),
    "toronto": ("#B81137", "#455560"),
    "vancouver": ("#00245E", "#9DC2EA"),
    "charlotte fc": ("#1A85C8", "#000000"),
    "nashville sc": ("#ECE83A", "#1F1646"),
}

GOAL_LOCATION = (100, 50)
TOP_GOAL = (100, 56)
BOTTOM_GOAL = (100, 44)


def pitch_distance(x, y, end_x, end_y):
    return np.sqrt(((end_x - x) * 1.2) ** 2 + ((end_y - y) * 0.8) ** 2)
