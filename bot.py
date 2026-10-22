import os
import requests
import xml.etree.ElementTree as ET

MOJ_CHAT_ID = "6610333161"
URL_RAW = os.environ.get('RSS_JSON_URL')
BAZA_PLIK = "wyslane_oferty.txt"

# Token wpisany bezpośrednio w adres - zero ryzyka błędu hosta
TELEGRAM_URL = "https://telegram.org"

def wczytaj_baze_wyslanych():
    if not os.path.exists(BAZA_PLIK):
        return set()
    with open(BAZA_PLIK, "r", encoding="utf-8") as f:
        return set(linia.strip() for linia in f if linia.strip())

def zapisz_do_bazy_wyslanych(identyfikator):
    with open(BAZA_PLIK, "a", encoding="utf-8") as f:
        f.write(f"{identyfikator}\n")

def wyslij_telegram(tekst_wiadomosci):
    payload = {
        "chat_id": str(MOJ_CHAT_ID).strip(), 
        "text": tekst_wiadomosci, 
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(TELEGRAM_URL, json=payload, timeout=12)
        print(f"   [SUROWY WYNIK TELEGRAMA] -> {res.text}")
    except Exception as e:
        print(f"   [TELEGRAM CRASH KRYTYCZNY] Szczegóły: {e}")

def main():
    print("=== START BOT.PY (FINALNA WERSJA PROD) ===")
    if not URL_RAW:
        print("Błąd krytyczny: Zmienna RSS_JSON_URL w Secrets jest pusta!")
        return

    wyslane_ogloszenia = wczytaj_baze_wyslanych()
    print(f"Wczytano {len(wyslane_ogloszenia)} pozycji z bazy.")

    linki_rss = [l.strip() for l in URL_RAW.split(",") if l.strip().startswith("http")]
    licznik_wyslanych = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for nr, url in enumerate(linki_rss, 1):
        print(f"Skanuję źródło {nr}/{len(linki_rss)}...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue
            root = ET.fromstring(response.content)
        except:
            continue

        oferty = root.findall('.//item')
        print(f"   -> Odczytano ofert z RSS: {len(oferty)}")

        # UNIKANIE SPAMU: Jeśli plik bazy jest pusty, bot zapisze obecne 25 ofert bez wysyłania.
        # Jeśli chcesz przetestować wysyłkę na żywo, zmień poniższe True na False!
        pierwsze_uruchomienie = False
        if pierwsze_uruchomienie:
            print("   [INFO] Pierwsze uruchomienie bota. Buduję bazę danych bez spamu...")

        for oferta in oferty:
            link_node = oferta.find('link')
            tytul_node = oferta.find('title')
            
            link = link_node.text.strip() if link_node is not None and link_node.text else None
            tytul = tytul_node.text.strip() if tytul_node is not None and tytul_node.text else 'Brak tytułu'
            
            if not link:
                continue

            # Filtr śmieci CSS z OLX
            if tytul.startswith(".") or "position:" in tytul or "border-radius" in tytul:
                continue

            # Pobieranie linku jako unikalny tekst bez parametrów trackingowych
            oferta_id = str(link).split('?')[0]

            if oferta_id not in wyslane_ogloszenia:
                wyslane_ogloszenia.add(oferta_id)
                zapisz_do_bazy_wyslanych(oferta_id)

                if not pierwsze_uruchomienie:
                    print(f"   [NOWA OFERTA -> WYSYŁKA] {tytul[:50]}...")
                    czysty_tytul = tytul.replace("*", "").replace("_", "").replace("[", "").replace("]", "")
                    wiadomosc = f"🚨 *NOWE OGŁOSZENIE PRL!* 🚨\n\n📌 *{czysty_tytul}*\n🔗 [Otwórz ogłoszenie]({link})"
                    wyslij_telegram(wiadomosc)
                    licznik_wyslanych += 1
                else:
                    print(f"   [BAZA ZBUDOWANA] Zapisano: {tytul[:40]}...")

    print(f"=== KONIEC === Wysłano nowych powiadomień: {licznik_wyslanych}")

if __name__ == "__main__":
    main()

