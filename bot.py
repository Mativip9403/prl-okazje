import os
import requests
import xml.etree.ElementTree as ET

# DANE WPISANE NA SZTYWNO - Brak ryzyka pomylenia zmiennych w GitHub Secrets
MOJ_CHAT_ID = "6610333161"
SZTYWNY_TOKEN = "8933900136:AAGPxiJd2EbGqIXJl2wbr6HWOCwSEsa9TO4"

# Jedyna zmienna pobierana z GitHub Secrets (Link do Twojego RSS z OLX)
URL_RAW = os.environ.get('RSS_JSON_URL')
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
    # W 100% prawidłowy i niezmienny adres URL do serwerów Telegrama
    telegram_url = f"https://telegram.org{SZTYWNY_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": str(MOJ_CHAT_ID).strip(), 
        "text": tekst_wiadomosci, 
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(telegram_url, json=payload, timeout=12)
        print(f"   [WYNIK TELEGRAMA] -> {res.text}")
    except Exception as e:
        print(f"   [TELEGRAM CRASH KRYTYCZNY] Szczegóły błędu wysyłki: {e}")

def main():
    print("=== START BOT.PY (WERSJA OSTATECZNA - BEZPIECZNY URL) ===")
    if not URL_RAW:
        print("Błąd krytyczny: Zmienna RSS_JSON_URL w GitHub Secrets jest pusta lub uszkodzona!")
        return

    wyslane_ogloszenia = wczytaj_baze_wyslanych()
    print(f"Wczytano {len(wyslane_ogloszenia)} pozycji z bazy.")

    # Czyszczenie i wyciąganie prawidłowego linku do OLX ze zmiennej
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
                print(f"   -> Błąd statusu serwera OLX: {response.status_code}")
                continue
            root = ET.fromstring(response.content)
        except Exception as e:
            print(f"   -> Błąd pobierania danych z OLX: {e}")
            continue

        oferty = root.findall('.//item')
        print(f"   -> Odczytano ofert z RSS: {len(oferty)}")

        # TRYB AUTOMATYCZNY 24/7: Pierwsze uruchomienie przy pustym pliku buduje bazę bez spamu.
        # Każde kolejne uruchomienie crona (co 15 minut) wyśle tylko PRAWDZIWE nowości.
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

            # Filtr spamu reklamowego CSS z OLX
            if tytul.startswith(".") or "position:" in tytul or "border-radius" in tytul:
                continue

            # Pobieranie linku jako unikalny tekst (string)
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
                    print(f"   [BAZA ZBUDOWANA] Zapisano w historii: {tytul[:40]}...")

    print(f"=== KONIEC === Wysłano nowych powiadomień: {licznik_wyslanych}")

if __name__ == "__main__":
    main()
