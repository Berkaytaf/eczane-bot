import sys
import asyncio
import json
import os
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

# Ayarlar
CITY = sys.argv[1] if len(sys.argv) > 1 else "Istanbul"
QUERY = sys.argv[2] if len(sys.argv) > 2 else "Eczane"
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def generate_dashboard(data):
    """Verileri şık bir HTML tabloya dönüştürür."""
    df = pd.DataFrame(data)
    # En yeni eklenen en üstte görünsün
    if not df.empty and 'Tarih' in df.columns:
        df = df.sort_values(by='Tarih', ascending=False)
    
    html_content = f"""
    <html>
    <head>
        <title>Lead Gen Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body class="container mt-5">
        <h2 class="mb-4">🚀 Canlı Veri İndeksi ({len(data)} Kayıt)</h2>
        <p>Son Güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <table class="table table-striped table-hover">
            <thead class="table-dark">
                <tr><th>İşletme Adı</th><th>Telefon</th><th>Adres</th><th>Tarih</th></tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td>{row['İşletme Adı']}</td><td>{row['Telefon']}</td><td>{row['Adres']}</td><td>{row['Tarih']}</td></tr>" for _, row in df.iterrows()])}
            </tbody>
        </table>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

async def scrape_google_maps(page, existing_names):
    # (Mevcut Google Maps kodun buraya gelecek - Optimize edilmiş hali aşağıda)
    results = []
    search_url = f"https://www.google.com/maps/search/{QUERY}+in+{CITY}"
    await page.goto(search_url)
    await page.wait_for_timeout(5000)
    
    # Derin kaydırma ve veri toplama (Önceki mesajdaki Buldozer mantığı)
    # ...
    return results

async def main():
    old_data = load_db()
    existing_names = {item["İşletme Adı"] for item in old_data}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # KAYNAK 1: Google Maps
        new_leads = await scrape_google_maps(page, existing_names)
        
        # (İstersen buraya KAYNAK 2: Sarı Sayfalar vb. modüllerini ekleyebilirsin)
        
        for item in new_leads:
            item['Tarih'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            old_data.append(item)
            
        await browser.close()
        
    # Veritabanını ve Dashboard'u güncelle
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(old_data, f, ensure_ascii=False, indent=4)
    
    generate_dashboard(old_data)
    pd.DataFrame(old_data).to_excel("leads_output.xlsx", index=False)

if __name__ == "__main__":
    asyncio.run(main())
