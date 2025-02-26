import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment

# Use a custom User-Agent header to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

def get_regular_season_table(soup):
    """
    Locate the Regular Season table by first finding the container div with id
    "switcher_per_game_stats" and then retrieving the table with id "per_game_stats".
    If not found directly, check within any commented HTML inside the container.
    """
    container = soup.find("div", {"id": "switcher_per_game_stats"})
    if container:
        table = container.find("table", {"id": "per_game_stats"})
        if table:
            return table
        # Look in comments for the table
        comments = container.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment_soup = BeautifulSoup(comment, "html.parser")
            table = comment_soup.find("table", {"id": "per_game_stats"})
            if table:
                return table
    return None

def get_player_photo(relative_link):
    """
    Construct the Basketball-Reference headshot URL from the player's relative link.
    Example: for "/players/j/jokicni01.html", returns
    "https://www.basketball-reference.com/req/202106291/images/headshots/jokicni01.jpg"
    """
    parts = relative_link.strip("/").split("/")
    if len(parts) >= 2:
        # Extract the player_id from the second element of the list.
        player_id = parts[-1].replace(".html", "")
        return f"https://www.basketball-reference.com/req/202106291/images/headshots/{player_id}.jpg"
    return ""

def team_logo(team_abbr):
    """
    Given the team abbreviation (e.g., "GSW"), return the team logo URL from NBA.com.
    Uses a pre-defined mapping from Basketball-Reference team abbreviations to NBA.com team IDs.
    """
    team_mapping = {
        "ATL": "1610612737", "BOS": "1610612738", "BKN": "1610612751", "CHA": "1610612766",
        "CHI": "1610612741", "CLE": "1610612739", "DAL": "1610612742", "DEN": "1610612743",
        "DET": "1610612765", "GSW": "1610612744", "HOU": "1610612745", "IND": "1610612754",
        "LAC": "1610612746", "LAL": "1610612747", "MEM": "1610612763", "MIA": "1610612748",
        "MIL": "1610612749", "MIN": "1610612750", "NOP": "1610612740", "NYK": "1610612752",
        "OKC": "1610612760", "ORL": "1610612753", "PHI": "1610612755", "PHX": "1610612756",
        "POR": "1610612757", "SAC": "1610612758", "SAS": "1610612759", "TOR": "1610612761",
        "UTA": "1610612762", "WAS": "1610612764"
    }
    team_id = team_mapping.get(team_abbr, "")
    if team_id:
        return f"https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg"
    return ""

# URL for MVP winners on Basketball-Reference
mvp_url = "https://www.basketball-reference.com/awards/mvp.html"
response = requests.get(mvp_url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

# Locate the MVP winners table (id "mvp_NBA")
mvp_table = soup.find("table", {"id": "mvp_NBA"})
if not mvp_table:
    raise Exception("MVP winners table not found on the page.")

rows = mvp_table.find("tbody").find_all("tr")
data = []
unique_mvp = set()

# Process rows to get the last 20 unique MVP winners
for row in rows:
    player_cell = row.find("td", {"data-stat": "player"})
    if not player_cell:
        continue
    player_name = player_cell.get_text(strip=True)
    if player_name in unique_mvp:
        continue
    unique_mvp.add(player_name)
    mvp_award_year = row.find("th").get_text(strip=True)
    relative_link = player_cell.find("a")["href"]
    full_player_link = f"https://www.basketball-reference.com{relative_link}"
    print(f"Processing {player_name} - {full_player_link}")
    
    # Compute the player's photo URL directly from the relative link.
    player_photo_url = get_player_photo(relative_link)
    
    # Request the player's page to get the regular season table.
    player_resp = requests.get(full_player_link, headers=headers)
    player_soup = BeautifulSoup(player_resp.content, 'html.parser')
    reg_table = get_regular_season_table(player_soup)
    
    if reg_table:
        tbody = reg_table.find("tbody")
        if tbody:
            season_rows = tbody.find_all("tr")
            for season_row in season_rows:
                th = season_row.find("th", {"data-stat": 'year_id'})
                if not th or th.get_text(strip=True) == "":
                    continue
                season_data = {"Player": player_name, "MVP_Award_Year": mvp_award_year}
                for cell in season_row.find_all(["th", 'td']):
                    stat = cell.get('data-stat')
                    if stat:
                        season_data[stat] = cell.get_text(strip=True)
                    # If this cell is the team abbreviation, compute the team logo.
                    if stat == 'team_name_abbr':
                        a = cell.find('a')
                        if a:
                            team_abbr = a.get_text(strip=True)
                            season_data["TeamLogo"] = team_logo(team_abbr)
                if "TeamLogo" not in season_data:
                    season_data["TeamLogo"] = ""
                season_data["PlayerPhoto"] = player_photo_url
                data.append(season_data)
        else:
            print(f"<tbody> not found for {player_name}")
    else:
        print(f"Regular Season table not found for {player_name}")
    
    time.sleep(1)  # Polite delay between requests
    if len(unique_mvp) == 20:
        break

# Convert collected data to a DataFrame
df = pd.DataFrame(data)

# Rename columns to the desired headers
rename_map = {
    "year_id": "Season", "age": "Age", "team_name_abbr": "Team", "comp_name_abbr": "Lg", "pos": "Pos",
    "games": "G", "games_started": "GS", "mp_per_g": "MP", "fg_per_g": "FG", "fga_per_g": "FGA",
    "fg_pct": "FG%", "fg3_per_g": "3P", "fg3a_per_g": "3PA", "fg3_pct": "3P%", "fg2_per_g": "2P",
    "fg2a_per_g": "2PA", "fg2_pct": "2P%", "efg_pct": "eFG%", "ft_per_g": "FT", "fta_per_g": "FTA",
    "ft_pct": "FT%", "orb_per_g": "ORB", "drb_per_g": "DRB", "trb_per_g": "TRB", "ast_per_g": "AST",
    "stl_per_g": "STL", "blk_per_g": "BLK", "tov_per_g": "TOV", "pf_per_g": "PF", "pts_per_g": "PTS"
}
df.rename(columns=rename_map, inplace=True)

# Convert Games to numeric and filter out rows with no games played
df["G"] = pd.to_numeric(df["G"], errors="coerce")
df = df[df["G"] > 0]

# Define final desired column order (with PlayerPhoto and TeamLogo as the last two columns)
desired_columns = [
    "Player", "Season", "Age", "Team", "Lg", "Pos", "G", "GS", "MP", "FG", "FGA", "FG%", 
    "3P", "3PA", "3P%", "2P", "2PA", "2P%", "eFG%", "FT", "FTA", "FT%", "ORB", "DRB", "TRB", 
    "AST", "STL", "BLK", "TOV", "PF", "PTS", "MVP_Award_Year", "PlayerPhoto", "TeamLogo"
]
existing_columns = [col for col in desired_columns if col in df.columns]
df = df[existing_columns]

# Save the DataFrame to CSV with UTF-8-sig encoding
target_dir = r"C:\Users\z003yh0e\OneDrive - Siemens Energy\Desktop\Reliability Data Engineer\Training\ETL to Power BI End-to-End Training\NBA MVP Data\datasets"
if not os.path.exists(target_dir):
    os.makedirs(target_dir)
csv_filename = os.path.join(target_dir, "mvp_data.csv")
df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
print(f"Data scraped and saved to {csv_filename}")