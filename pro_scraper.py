import sys
import asyncio
import json
import os
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

# --- 3 GİRDİLİ SİSTEM ---
# main.yml'den gelen: CITY, DISTRICT, QUERY
CITY = sys.argv[1] if len(sys.argv) > 1 else "Istanbul"
DISTRICT = sys.argv[2] if len(sys.argv) > 2 else ""
QUERY = sys.argv[3] if len(sys.argv) > 3 else "Eczane"
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def generate_dashboard(data):
    """Verileri şık bir HTML tabloya (GitHub Pages için) dönüştürür."""
    if not data: return
    df = pd.DataFrame(data)
    if 'Tarih' in df.columns:
        df = df.sort_values(by='Tarih', ascending=False)
    
    html_content = f"""
    <html>
    <head>
        <title>Lead Gen Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>body {{ background: #f4f7f6; }} .card {{ border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}</style>
    </head>
    <body class="container py-5">
        <div class="card p-4">
            <h2 class="text-primary mb-0">🚀 Canlı Veri İndeksi</h2>
            <p class="text-muted">Toplam Kayıt: {len(data)} | Son Güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <div class="table-responsive">
                <table class="table table-hover mt-3">
                    <thead class="table-dark">
                        <tr><th>İşletme Adı</th><th>Telefon</th><th>Adres</th><th>Bölge</th><th>Tarih</th></tr>
                    </thead>
                    <tbody>
                        {''.join([f"<tr><td>{row.get('İşletme Adı','-')}</td><td>{row.get('Telefon','-')}</td><td>{row.get('Adres','-')}</td><td>{row.get('Bölge','-')}</td><td>{row.get('Tarih','-')}</td></tr>" for _, row in df.iterrows()])}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

async def scrape_google_maps(page, existing_names):
    """Google Maps'ten derinlemesine veri çeker."""
    results = []
    # Nokta atışı arama: "Eczane in Kadikoy Istanbul"
    search_query = f"{QUERY} in {DISTRICT} {CITY}"
    search_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
    
    print(f"🌐 Hedef: {search_query} aratılıyor...")
    await page.goto(search_url)
    await page.wait_for_timeout(5000)

    # 9 VERİ ENGELİNİ KIRAN BULDOZER SCROLL
    try:
        await page.click("div[role='feed']", timeout=5000)
    except: pass

    print("⏬ Liste derinlemesine kaydırılıyor...")
    for _ in range(15): # Daha fazla sonuç için 15 kez kaydır
        await page.mouse.wheel(0, 10000)
        await asyncio.sleep(2)

    listings = await page.query_selector_all('a.hfpxzc')
    print(f"📊 {len(listings)} potansiyel işletme bulundu. Yeni olanlar taranıyor...")

    for item in listings[:100]: # Tek seferde en fazla 100 yeni veri
        try:
            name = await item.get_attribute("aria-label")
            if not name or name in existing_names: continue

            await item.click()
            await page.wait_for_timeout(2500) # Detayların yüklenmesi

            address = "Yok"
            phone = "Yok"
            try: address = await page.locator("button[data-item-id='address']").inner_text()
            except: pass
            try: phone = await page.locator("button[data-item-id*='phone:tel:']").inner_text()
            except: pass

            results.append({
                "İşletme Adı": name,
                "Telefon": phone,
                "Adres": address,
                "Bölge": f"{DISTRICT}/{CITY}",
                "Tarih": datetime.now().strftime('%Y-%m-%d %H:%M')
            })
            existing_names.add(name)
            print(f"✅ Yeni: {name}")
        except: continue
    return results

async def main():
    old_data = load_db()
    existing_names = {item["İşletme Adı"] for item in old_data if "İşletme Adı" in item}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Türkçe sonuçlar için locale ayarı
        context = await browser.new_context(locale="tr-TR", user_agent="Mozilla/5.0...")
        page = await context.new_page()
        
        # Google Maps Taraması
        new_leads = await scrape_google_maps(page, existing_names)
        
        # Verileri Birleştir
        final_data = old_data + new_leads
        
        await browser.close()
        
    # Dosyaları Güncelle
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    
    generate_dashboard(final_data)
    pd.DataFrame(final_data).to_excel("leads_output.xlsx", index=False)
    print(f"🏁 Bitti! Toplam veritabanı: {len(final_data)} kayıt.")

if __name__ == "__main__":
    asyncio.run(main())
