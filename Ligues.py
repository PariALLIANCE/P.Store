import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone
import re
import os
import subprocess
import sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
}

LEAGUES = {
    "Colombia - Primera A": {
        "code": "col.1", 
        "json": "Colombia_Primera_A.json",
        "date_debut": "19 janvier 2024"
    },
    "France - Ligue 1": {
        "code": "fra.1", 
        "json": "France_Ligue_1.json",
        "date_debut": "16 aout 2024"
    },
    "Belgium - Jupiler Pro League": {
        "code": "bel.1", 
        "json": "Belgium_Jupiler_Pro_League.json",
        "date_debut": "26 juillet 2024"
    },
    "England - National League": {
        "code": "eng.5", 
        "json": "England_National_League.json",
        "date_debut": "10 aout 2024"
    },
    "Netherlands - Eredivisie": {
        "code": "ned.1", 
        "json": "Netherlands_Eredivisie.json",
        "date_debut": "9 aout 2024"
    },
    "Portugal - Primeira Liga": {
        "code": "por.1", 
        "json": "Portugal_Primeira_Liga.json",
        "date_debut": "9 aout 2024"
    },
    "Italy - Serie A": {
        "code": "ita.1", 
        "json": "Italy_Serie_A.json",
        "date_debut": "17 aout 2024"
    },
    "Austria - Bundesliga": {
        "code": "aut.1", 
        "json": "Austria_Bundesliga.json",
        "date_debut": "2 aout 2024"
    },
    "Brazil - Serie A": {
        "code": "bra.1", 
        "json": "Brazil_Serie_A.json",
        "date_debut": "13 avril 2024"
    },
    "Brazil - Serie B": {
        "code": "bra.2", 
        "json": "Brazil_Serie_B.json",
        "date_debut": "19 avril 2024"
    },
    "Turkey - Super Lig": {
        "code": "tur.1", 
        "json": "Turkey_Super_Lig.json",
        "date_debut": "9 aout 2024"
    },
    "Mexico - Liga MX": {
        "code": "mex.1", 
        "json": "Mexico_Liga_MX.json",
        "date_debut": "5 juillet 2024"
    },
    "USA - Major League Soccer": {
        "code": "usa.1", 
        "json": "USA_Major_League_Soccer.json",
        "date_debut": "21 fevrier 2024"
    },
    "Japan - J1 League": {
        "code": "jpn.1", 
        "json": "Japan_J1_League.json",
        "date_debut": "23 fevrier 2024"
    },
    "Saudi-Arabia - Pro League": {
        "code": "ksa.1", 
        "json": "Saudi_Arabia_Pro_League.json",
        "date_debut": "22 aout 2024"
    },
    "Switzerland - Super League": {
        "code": "sui.1", 
        "json": "Switzerland_Super_League.json",
        "date_debut": "20 juillet 2024"
    },
    "China - Super League": {
        "code": "chn.1", 
        "json": "China_Super_League.json",
        "date_debut": "1 mars 2024"
    },
    "Russia - Premier League": {
        "code": "rus.1", 
        "json": "Russia_Premier_League.json",
        "date_debut": "21 juillet 2024"
    },
    "Greece - Super League 1": {
        "code": "gre.1", 
        "json": "Greece_Super_League_1.json",
        "date_debut": "17 aout 2024"
    },
    "Chile - Primera Division": {
        "code": "chi.1", 
        "json": "Chile_Primera_Division.json",
        "date_debut": "17 fevrier 2024"
    },
    "Peru - Primera Division": {
        "code": "per.1", 
        "json": "Peru_Primera_Division.json",
        "date_debut": "15 fevrier 2024"
    },
    "Sweden - Allsvenskan": {
        "code": "swe.1", 
        "json": "Sweden_Allsvenskan.json",
        "date_debut": "30 mars 2024"
    },
    "Argentina - Primera Nacional": {
        "code": "arg.2", 
        "json": "Argentina_Primera_Nacional.json",
        "date_debut": "16 fevrier 2024"
    },
    "Paraguay - Division Profesional": {
        "code": "par.1", 
        "json": "Paraguay_Division_Profesional.json",
        "date_debut": "16 fevrier 2024"
    },
    "Venezuela - Primera Division": {
        "code": "ven.1", 
        "json": "Venezuela_Primera_Division.json",
        "date_debut": "16 fevrier 2024"
    },
    "Romania - Liga I": {
        "code": "rou.1", 
        "json": "Romania_Liga_I.json",
        "date_debut": "12 juillet 2024"
    }
}

def run_git_command(command, description):
    """Execute une commande git et gere les erreurs"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ {description} - succes")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - erreur: {e.stderr}")
        return False, e.stderr
    except Exception as e:
        print(f"❌ {description} - erreur inattendue: {e}")
        return False, str(e)

def check_git_repo():
    """Verifie si on est dans un depot git"""
    success, output = run_git_command(["git", "rev-parse", "--git-dir"], "Verification du depot git")
    return success

def check_git_status():
    """Verifie le statut git et retourne s'il y a des changements"""
    success, output = run_git_command(["git", "status", "--porcelain"], "Verification du statut git")
    if success:
        return len(output.strip()) > 0, output
    return False, ""

def convert_french_date_to_datetime(date_str):
    """Convertit une date en francais vers un objet datetime"""
    months_fr = {
        'janvier': 1, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'decembre': 12
    }
    
    parts = date_str.split()
    day = int(parts[0])
    month = months_fr[parts[1]]
    year = int(parts[2])
    
    return datetime(year, month, day)

def generate_date_range(start_date, end_date):
    """Genere une liste de dates entre start_date et end_date"""
    current_date = start_date
    dates = []
    
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y%m%d"))
        current_date += timedelta(days=1)
    
    return dates

# Date d'aujourd'hui en UTC
today = datetime.now(timezone.utc).replace(tzinfo=None)

# Verification du depot git avant de commencer
if not check_git_repo():
    print("❌ Ce repertoire n'est pas un depot git. Arrêt du script.")
    sys.exit(1)

total_new_matches = 0
modified_files = []

for league_name, league_info in LEAGUES.items():
    BASE_URL = f"https://www.espn.com/soccer/schedule/_/date/{{date}}/league/{league_info['code']}"
    JSON_FILE = league_info["json"]
    
    # Convertir la date de debut
    start_date = convert_french_date_to_datetime(league_info["date_debut"])
    
    # Generer la liste des dates a recuperer
    dates_to_fetch = generate_date_range(start_date, today)
    
    print(f"\n📅 Recuperation des matchs pour {league_name} du {league_info['date_debut']} a aujourd'hui ({len(dates_to_fetch)} jours)...")
    
    # Charger les anciens matchs
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            existing_matches = {match["gameId"]: match for match in json.load(f)}
    else:
        existing_matches = {}
    
    new_matches = {}
    
    for date_str in dates_to_fetch:
        try:
            res = requests.get(BASE_URL.format(date=date_str), headers=HEADERS)
            soup = BeautifulSoup(res.content, "html.parser")
        except Exception as e:
            print(f"⚠️ Erreur de requete pour {league_name} le {date_str}: {e}")
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
                    
                    # Ignorer certaines equipes
                    if "USMNT" in team1 or "USWNT" in team1 or "USMNT" in team2 or "USWNT" in team2:
                        continue
                    
                    # Ignorer les matchs a venir
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
                    print(f"⚠️ Erreur lors du parsing pour {league_name} le {date_str} : {e}")
                    continue
    
    # Sauvegarde mise a jour
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(list(existing_matches.values()), f, indent=2, ensure_ascii=False)
    
    if len(new_matches) > 0:
        modified_files.append(JSON_FILE)
        total_new_matches += len(new_matches)
    
    print(f"✅ {league_name} mise a jour : {len(existing_matches)} matchs au total, +{len(new_matches)} ajoutes.")

# Gestion Git uniquement s'il y a des changements
print(f"\n🔄 Verification des changements git...")

has_changes, status_output = check_git_status()

if not has_changes:
    print("✅ Aucun changement detecte. Pas besoin de commit.")
    sys.exit(0)

print(f"📝 Changements detectes:\n{status_output}")

if modified_files:
    print(f"\n🚀 Debut de la synchronisation git...")
    
    # Ajouter tous les fichiers JSON modifies
    json_files = [league_info["json"] for league_info in LEAGUES.values()]
    success, output = run_git_command(["git", "add"] + json_files, "Ajout des fichiers JSON")
    
    if not success:
        print("❌ Echec de l'ajout des fichiers. Arrêt du script.")
        sys.exit(1)
    
    # Verifier qu'il y a quelque chose a commiter
    success, output = run_git_command(["git", "diff", "--cached", "--name-only"], "Verification des fichiers stages")
    
    if success and output.strip():
        # Commit automatique avec message detaille
        commit_message = f"Mise a jour des JSON des matchs - {total_new_matches} nouveaux matchs ajoutes"
        success, output = run_git_command(["git", "commit", "-m", commit_message], "Commit des changements")
        
        if not success:
            print("❌ Echec du commit. Arrêt du script.")
            sys.exit(1)
        
        # Push vers le depot distant
        success, output = run_git_command(["git", "push"], "Push vers le depot distant")
        
        if success:
            print(f"🎉 Synchronisation terminee avec succes!")
            print(f"📊 Resume: {total_new_matches} nouveaux matchs ajoutes dans {len(modified_files)} ligues")
        else:
            print("❌ Echec du push. Les changements sont commites localement mais pas sur le depot distant.")
            sys.exit(1)
    else:
        print("⚠️ Aucun changement a commiter apres staging.")
else:
    print("⚠️ Aucun fichier modifie detecte.")
