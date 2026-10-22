import os
import requests

MOJ_CHAT_ID = "6610333161"
URL_RAW = os.environ.get('RSS_JSON_URL')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
BAZA_PLIK = "wyslane_oferty.txt"

def wczytaj_baze_wyslanych():
    if not os.path.exists(BAZA_PLIK):
        return set()
    with open(BAZA_PLIK, "r", encoding="utf-8") as f:
        return set(linia.strip() for linia in f if linia.strip())

def zapisz_do_bazy_wyslanych(identyfikator):
    with open(BAZA_PLIK, "a", encoding="utf-8") as f:
        f.write(f"{identyfikator}\n")

def wyslij_telegram(tekst_wiadomosci):
    if not TELEGRAM_TOKEN:
        print("   [TELEGRAM ERROR] Brak zmiennej TELEGRAM_TOKEN!")
        return
    telegram_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": MOJ_CHAT_ID, 
        "text": tekst_wiadomosci, 
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(telegram_url, json=payload, timeout=10)
        print(f"   [SUROWY WYNIK TELEGRAMA] -> {res.text}")
    except Exception as e:
        print(f"   [TELEGRAM CRASH] Błąd: {e}")

def main():
    print("=== START BOT.PY ===")
    if not URL_RAW:
        print("Błąd krytyczny: Zmienna RSS_JSON_URL w Secrets jest pusta!")
        return

    wyslane_ogloszenia = wczytaj_baze_wyslanych()
    print(f"Wczytano {len(wyslane_ogloszenia)} pozycji z bazy.")

    linki_rss = [l.strip() for l in URL_RAW.split(",") if l.strip().startswith("http")]
    licznik_wyslanych = 0

    # Podrobienie nagłówka prawdziwej przeglądarki (często rozwiązuje problem blokad)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for nr, url in enumerate(linki_rss, 1):
        print(f"Skanuję źródło {nr}/{len(linki_rss)}...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"   -> Kod odpowiedzi serwera: {response.status_code}")
            
            # Jeśli serwer nie zwrócił JSON-a, przechwytujemy surowy tekst do logów
            try:
                dane = response.json()
            except Exception as json_err:
                print(f"   -> [BŁĄD PARSOWANIA] Serwer nie zwrócił JSON-a. Pokazuję początek odpowiedzi:")
                print(f"--------------------------------------------------")
                print(response.text[:500])
                print(f"--------------------------------------------------")
                continue
                
        except Exception as e:
            print(f"   -> Błąd połączenia z serwerem: {e}")
            continue

        oferty = dane.get('items', [])
        print(f"   -> Odczytano ofert z JSON: {len(oferty)}")
        
        pierwsze_uruchomienie = len(wyslane_ogloszenia) == 0

        for oferta in ofertas:
            link = oferta.get('url') or oferta.get('link') or oferta.get('id')
            tytul = oferta.get('title', 'Brak tytułu').strip()
            
            if not link:
                continue

            if tytul.startswith(".") or "position:" in tytul or "border-radius" in tytul:
                continue

            oferta_id = str(link).split('?')[0]

            if oferta_id not in wyslane_ogloszenia:
                wyslane_ogloszenia.add(oferta_id)
                zapisz_do_bazy_wyslanych(oferta_id)

                if not pierwsze_uruchomienie:
                    print(f"   [WYSYŁKA] {tytul}")
                    czysty_tytul = tytul.replace("*", "").replace("_", "").replace("[", "").replace("]", "")
                    wiadomosc = f"🚨 *NOWE OGŁOSZENIE PRL!* 🚨\n\n📌 *{czysty_tytul}*\n🔗 [Otwórz ogłoszenie]({link})"
                    wyslij_telegram(wiadomosc)
                    licznik_wyslanych += 1

    print(f"=== KONIEC === Wysłano nowych powiadomień: {licznik_wyslanych}")

if __name__ == "__main__":
    main()
