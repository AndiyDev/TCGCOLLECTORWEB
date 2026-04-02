import requests
from bs4 import BeautifulSoup

def scrape_and_store_card(set_id, card_num):
    url = f"https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/series/{set_id}/{card_num}/"
    # Pokémon.com kräver en User-Agent för att inte blockera oss
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extrahera data från sidans struktur
    try:
        name = soup.find("div", class_="card-description").find("h1").text.strip()
        hp = soup.find("span", class_="hp").text.replace("HP", "").strip()
        
        # Hämta Set-info längst ner till höger (där din bild visar 36/132)
        stats_footer = soup.find("div", class_="stats-footer")
        set_name = stats_footer.find("h3").text.strip()
        number_info = stats_footer.find("span").text.strip() # "36/132 Double Rare"
        
        # Hämta symbol-förkortningen (MEG)
        symbol_id = stats_footer.find("i", class_="pkmn-card-set-symbol").get("class")[-1].replace("symbol-", "").upper()
        
        # Spara till din databas
        # [Här lägger vi in INSERT-logiken till SQL]
        print(f"✅ Skrapade: {name} ({symbol_id} {number_info})")
        return True
    except Exception as e:
        print(f"❌ Fel vid skrapning: {e}")
        return False