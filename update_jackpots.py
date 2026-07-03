import os
import json
import requests
from datetime import datetime, timezone

API_KEY = os.environ["MAGAYO_API_KEY"]

GAMES = {
    "loto": "fr_loto",
    "euromillions": "euromillions"
}

OUTPUT_FILE = "jackpots.json"


def load_existing_data():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "loto": {
                "date": "",
                "jackpotMillions": 0
            },
            "euromillions": {
                "date": "",
                "jackpotMillions": 0
            },
            "updatedAt": ""
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

    error_code = int(data.get("error", 999))

    if error_code != 0:
        raise Exception(f"Erreur Magayo pour {game_code}: {data}")

    return data


def euros_to_millions(value):
    amount = float(str(value).replace(",", "").replace(" ", ""))
    return round(amount / 1_000_000, 2)


def update_game(existing_data, key, game_code):
    try:
        data = get_jackpot(game_code)

        existing_data[key] = {
            "date": data["next_draw"],
            "jackpotMillions": euros_to_millions(data["jackpot"])
        }

        print(f"{key}: mise à jour OK -> {existing_data[key]}")
        return True

    except Exception as e:
        print(f"{key}: mise à jour impossible, conservation de l'ancienne valeur.")
        print(f"Détail: {e}")
        return False


def main():
    data = load_existing_data()

    loto_updated = update_game(data, "loto", GAMES["loto"])
    euro_updated = update_game(data, "euromillions", GAMES["euromillions"])

    if loto_updated or euro_updated:
        data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        print("Au moins un jeu a été mis à jour.")
    else:
        print("Aucun jeu n'a pu être mis à jour. Le fichier existant est conservé.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Fin du script sans erreur bloquante.")


if __name__ == "__main__":
    main()
