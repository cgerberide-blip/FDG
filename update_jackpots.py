import json
import requests
from datetime import datetime, timezone

OUTPUT_FILE = "jackpots.json"

FDJ_ENDPOINTS = {
    "loto": "https://www.sto.api.fdj.fr/anonymous/service-draw-info/v3/draws?game_name=loto&current=true",
    "euromillions": "https://www.sto.api.fdj.fr/anonymous/service-draw-info/v3/draws?game_name=euromillions&current=true",
}


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


def fetch_fdj_draw(game_key):
    url = FDJ_ENDPOINTS[game_key]

    response = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0 jackpot-checker"
        }
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list) or len(data) == 0:
        raise Exception(f"Réponse FDJ vide ou inattendue pour {game_key}: {data}")

    draw = data[0]

    print(f"Réponse FDJ pour {game_key}:")
    print(json.dumps(draw, ensure_ascii=False, indent=2))

    return draw


def amount_to_millions(amount_entry):
    """
    FDJ fournit par exemple :
    {
      "value": 200000000,
      "currency": "EUR",
      "scale": 2
    }

    Cela signifie 200000000 / 10^2 = 2 000 000 EUR,
    soit 2 millions d'euros.
    """
    value = float(amount_entry["value"])
    scale = int(amount_entry.get("scale", 0))

    euros = value / (10 ** scale)
    millions = euros / 1_000_000

    return round(millions, 2)


def extract_eur_amount(draw, possible_fields):
    for field in possible_fields:
        amounts = draw.get(field)

        if not amounts:
            continue

        for amount in amounts:
            if amount.get("currency") == "EUR":
                return amount_to_millions(amount)

    raise Exception(f"Aucun montant EUR trouvé dans les champs {possible_fields}")


def extract_date(draw):
    planned_at = draw.get("planned_at")

    if not planned_at:
        raise Exception(f"Champ planned_at absent : {draw}")

    parsed = datetime.fromisoformat(planned_at)
    return parsed.date().isoformat()


def update_game(existing_data, game_key):
    try:
        draw = fetch_fdj_draw(game_key)

        jackpot_millions = extract_eur_amount(
            draw,
            possible_fields=["estimated_jackpot", "guaranteed_amounts"]
        )

        new_value = {
            "date": extract_date(draw),
            "jackpotMillions": jackpot_millions
        }

        old_value = existing_data.get(game_key)

        existing_data[game_key] = new_value

        print(f"{game_key}: ancienne valeur -> {old_value}")
        print(f"{game_key}: nouvelle valeur -> {new_value}")

        return True

    except Exception as e:
        print(f"{game_key}: mise à jour impossible, conservation de l'ancienne valeur.")
        print(f"Détail: {e}")
        return False


def main():
    data = load_existing_data()

    loto_updated = update_game(data, "loto")
    euromillions_updated = update_game(data, "euromillions")

    retrieval_successful = loto_updated or euromillions_updated

    if retrieval_successful:
        data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        data["source"] = "fdj"
        print(f"Récupération réussie. updatedAt mis à jour : {data['updatedAt']}")
    else:
        print("Aucune récupération réussie. Conservation complète de l'ancien fichier, updatedAt inchangé.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("jackpots.json écrit.")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
