"""
Custom override rules mapping common/informal country names to the OFFICIAL
ISO 3166-1 names used in the real reference dataset (data/raw/iso_3166_full_reference.csv).

Why this file exists: the ISO standard uses formal names
("Korea, Republic of", "United States of America", "Viet Nam") that real-world
data almost never uses ("South Korea", "USA", "Vietnam"). This is the actual
gap the original resume bullet is about - reconciling messy real names against
a rigid formal standard.
"""

ALIAS_OVERRIDES = {
    "usa": "United States of America",
    "u.s.a.": "United States of America",
    "us": "United States of America",
    "united states": "United States of America",
    "uk": "United Kingdom of Great Britain and Northern Ireland",
    "u.k.": "United Kingdom of Great Britain and Northern Ireland",
    "united kingdom": "United Kingdom of Great Britain and Northern Ireland",
    "great britain": "United Kingdom of Great Britain and Northern Ireland",
    "england": "United Kingdom of Great Britain and Northern Ireland",
    "south korea": "Korea, Republic of",
    "korea, republic of": "Korea, Republic of",
    "republic of korea": "Korea, Republic of",
    "north korea": "Korea, Democratic People's Republic of",
    "korea, dem. people's rep.": "Korea, Democratic People's Republic of",
    "russia": "Russian Federation",
    "russian federation": "Russian Federation",
    "uae": "United Arab Emirates",
    "u.a.e.": "United Arab Emirates",
    "deutschland": "Germany",
    "burma": "Myanmar",
    "swaziland": "Eswatini",
    "macedonia": "North Macedonia",
    "vatican": "Holy See",
    "peoples republic of china": "China",
    "mainland china": "China",
    "dr congo": "Congo, Democratic Republic of the",
    "drc": "Congo, Democratic Republic of the",
    "democratic republic of the congo": "Congo, Democratic Republic of the",
    "viet nam": "Viet Nam",
    "vietnam": "Viet Nam",
    "laos": "Lao People's Democratic Republic",
    "lao pdr": "Lao People's Democratic Republic",
    "ivory coast": "Côte d'Ivoire",
    "cote d'ivoire": "Côte d'Ivoire",
    "czechia": "Czechia",
    "czech republic": "Czechia",
}

HISTORICAL_SUCCESSOR_OVERRIDES = {
    "ussr": "Russian Federation",
    "soviet union": "Russian Federation",
    "west germany": "Germany",
    "east germany": "Germany",
}

NON_STANDARDIZABLE = {
    "eu",
    "european union",
}