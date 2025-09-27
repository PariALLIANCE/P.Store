import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone
import re
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
}

LEAGUES = {
    "Colombia - Primera A": {"code": "col.1", "json": "Colombia_Primera_A.json"},
    "France - Ligue 1": {"code": "fra.1", "json": "France_Ligue_1.json"},
    "Belgium - Jupiler Pro League": {"code": "bel.1", "json": "Belgium_Jupiler_Pro_League.json"},
    "England - National League": {"code": "eng.5", "json": "England_National_League.json"},
    "Netherlands - Eredivisie": {"code": "ned.1", "json": "Netherlands_Eredivisie.json"},
    "Portugal - Primeira Liga": {"code": "por.1", "json": "Portugal_Primeira_Liga.json"},
    "Italy - Serie A": {"code": "ita.1", "json": "Italy_Serie_A.json"},
    "Austria - Bundesliga": {"code": "aut.1", "json": "Austria_Bundesliga.json"},
    "Brazil - Serie A": {"code": "bra.1", "json": "Brazil_Serie_A.json"},
    "Brazil - Serie B": {"code": "bra.2", "json": "Brazil_Serie_B.json"},
    "Turkey - Süper Lig": {"code": "tur.1", "json": "Turkey_Super_Lig.json"},
    "Mexico - Liga MX": {"code": "mex.1", "json": "Mexico_Liga_MX.json"},
    "USA - Major League Soccer": {"code": "usa.1", "json": "USA_Major_League_Soccer.json"},
    "Japan - J1 League": {"code": "jpn.1", "json": "Japan_J1_League.json"},
    "Saudi-Arabia - Pro League": {"code": "ksa.1", "json": "Saudi_Arabia_Pro_League.json"},
    "Switzerland - Super League": {"code": "sui.1", "json": "Switzerland_Super_League.json"},
    "China - Super League": {"code": "chn.1", "json": "China_Super_League.json"},
    "Russia - Premier League": {"code": "rus.1", "json": "Russia_Premier_League.json"},
    "Greece - Super League 1": {"code": "gre.1", "json": "Greece_Super_League_1.json"},
    "Chile - Primera División": {"code": "chi.1", "json": "Chile_Primera_Division.json"},
    "Peru - Primera División": {"code": "per.1", "json": "Peru_Primera_Division.json"},
    "Sweden - Allsvenskan": {"code": "swe.1", "json": "Sweden_Allsvenskan.json"},
    "Argentina - Primera Nacional": {"code": "arg.2", "json": "Argentina_Primera_Nacional.json"},
    "Paraguay - Division Profesional": {"code": "par.1", "json": "Paraguay_Division_Profesional.json"},
    "Venezuela - Primera División": {"code": "ven.1", "json": "Venezuela_Primera_Division.json"},
    "Romania - Liga I": {"code": "rou.1", "json": "Romania_Liga_I.json"}
}

# Calcul de la date d'hier en UTC
yesterday = datetime.now(timezone.utc) - timedelta(days=1)
date_str = yesterday.strftime("%Y%m%d")

for league_name, league_info in LEAGUES.items():
    BASE_URL = f"https://www.espn.com/soccer/schedule/_/date/{{date}}/league/{league_info['code']}"
    JSON_FILE = league_info["json"]

    print(f"\n📅 Récupération des matchs du {date_str} pour {league_name}...")

    # Charger les anciens matchs
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            existing_matches = {match["gameId"]: match for match in json.load(f)}
    else:
        existing_matches = {}

    new_matches = {}

    try:
        res = requests.get(BASE_URL.format(date=date_str), headers=HEADERS)
        soup = BeautifulSoup(res.content, "html.parser")
    except Exception as e:
        print(f"⚠️ Erreur de requête pour {league_name}: {e}")
        continue

    tables = soup.select("div.ResponsiveTable")
    for table in tables:
        date_title_tag = table.select_one("div.Table__Title")
        date_text = date_title_tag.text.strip() if date_title_tag else date_str

        rows = table.select("tbody > tr.Table__TR")
        for row in rows:
            try:
                away_team_tag = row.select_one("td.events__col span.Table__Team.away a.AnchorLink:last-child")
                home_team_tag = row.select_one("td.colspan__col span.Table__Team a.AnchorLink:last-child")
                score_tag = row.select_one("td.colspan__col a.AnchorLink.at")

                if not away_team_tag or not home_team_tag or not score_tag:
                    continue

                team1 = away_team_tag.text.strip()
                team2 = home_team_tag.text.strip()
                score = score_tag.text.strip()

                # Ignorer certaines équipes
                if "USMNT" in team1 or "USWNT" in team1 or "USMNT" in team2 or "USWNT" in team2:
                    continue

                # Ignorer les matchs à venir
                if score.lower() == "v":
                    continue

                match_url = score_tag["href"]
                match_id_match = re.search(r"gameId/(\d+)", match_url)
                if not match_id_match:
                    continue

                game_id = match_id_match.group(1)

                if game_id not in existing_matches:
                    match_data = {
                        "gameId": game_id,
                        "date": date_text,
                        "team1": team1,
                        "score": score,
                        "team2": team2,
                        "title": f"{team1} VS {team2}",
                        "match_url": "https://www.espn.com" + match_url
                    }
                    new_matches[game_id] = match_data
                    existing_matches[game_id] = match_data

            except Exception as e:
                print(f"⚠️ Erreur lors du parsing pour {league_name} : {e}")
                continue

    # Sauvegarde mise à jour
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(list(existing_matches.values()), f, indent=2, ensure_ascii=False)

    print(f"✅ {league_name} mise à jour : {len(existing_matches)} matchs au total, +{len(new_matches)} ajoutés.")
