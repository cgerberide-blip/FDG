import os
import json
import requests
from datetime import datetime, timezone

API_KEY = os.environ["MAGAYO_API_KEY"]

GAMES = {
    "loto": "fr_loto",
    "euromillions": "euromillions"
}

def get_jackpot(game_code):
    url = "https://www.magayo.com/api/jackpot.php"
    params = {
        "api_key": API_KEY,
        "game": game_code
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()

    if int(data.get("error", 999)) != 0:
        raise Exception(f"Erreur Magayo pour {game_code}: {data}")

    return data

def euros_to_millions(value):
    """
    Convertit un jackpot en euros vers un montant en millions d'euros.
    Exemple : 2000000 -> 2
    """
    amount = float(str(value).replace(",", "").replace(" ", ""))
    return round(amount / 1_000_000, 2)

def main():
    loto = get_jackpot(GAMES["loto"])
    euromillions = get_jackpot(GAMES["euromillions"])

    result = {
        "loto": {
            "date": loto["next_draw"],
            "jackpotMillions": euros_to_millions(loto["jackpot"])
        },
        "euromillions": {
            "date": euromillions["next_draw"],
            "jackpotMillions": euros_to_millions(euromillions["jackpot"])
        },
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    with open("jackpots.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
