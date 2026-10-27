#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def wczytaj_json(sciezka):
    with open(sciezka, "r", encoding="utf-8") as plik:
        return json.load(plik)


def pobierz_odpowiedz(pytanie, odpowiedzi):
    print(f"\n{pytanie}")
    for i, opcja in enumerate(odpowiedzi, start=1):
        etykieta = opcja.replace("_", " ")
        print(f"  {i}. {etykieta}")

    while True:
        wybor = input("Wybierz numer odpowiedzi: ").strip()
        if wybor.isdigit():
            nr = int(wybor)
            if 1 <= nr <= len(odpowiedzi):
                return odpowiedzi[nr - 1]
        print("Niepoprawny wybór. Wpisz numer z listy.")


def main():
    if len(sys.argv) > 1:
        sciezka_json = Path(sys.argv[1])
    else:
        sciezka_json = Path(__file__).with_name("zadanie.json")

    try:
        dane = wczytaj_json(sciezka_json)
    except FileNotFoundError:
        print(f"Nie znaleziono pliku JSON: {sciezka_json}")
        return
    except json.JSONDecodeError:
        print(f"Plik JSON jest niepoprawny: {sciezka_json}")
        return

    pytania = dane.get("questions", {})
    odpowiedzi_uzytkownika = {}

    print("Diagnostyka problemu z komputerem")
    for klucz, pytanie in pytania.items():
        odpowiedzi_uzytkownika[klucz] = pobierz_odpowiedz(
            pytanie["text"],
            pytanie["answers"],
        )

    pasujace_reguly = []
    for regula in dane.get("rules", []):
        warunki = regula.get("if", {})
        if all(warunki.get(klucz) == odpowiedzi_uzytkownika.get(klucz) for klucz in warunki):
            pasujace_reguly.append(regula["then"])

    print("\nWynik diagnostyki:")
    if not pasujace_reguly:
        print("Brak reguł pasujących do udzielonych odpowiedzi.")
        return

    for i, wynik in enumerate(pasujace_reguly, start=1):
        print(f"\nReguła {i}:")
        print(f"Diagnoza: {wynik.get('diagnosis', 'brak danych')}")
        print(f"Działanie: {wynik.get('action', 'brak danych')}")


if __name__ == "__main__":
    main()
