import sys
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random

# YAML'dan gelen girdileri alıyoruz (Mühendis dokunuşu)
TARGET_CITY = sys.argv[1] if len(sys.argv) > 1 else "Istanbul"
TARGET_QUERY = sys.argv[2] if len(sys.argv) > 2 else "Eczane"

async def scrape_leads():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        search_url = f"https://www.google.com/maps/search/{TARGET_QUERY}+in+{TARGET_CITY}"
        print(f"🚀 {TARGET_CITY} - {TARGET_QUERY} avı başladı...")
        
        await page.goto(search_url)
        await page.wait_for_timeout(5000)

        # Listeyi yüklemek için kaydır
        for _ in range(5):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(2)

        leads = []
        items = await page.query_selector_all("a.hfpxzc") # Tıklanabilir kartlar
        
        print(f"📊 {len(items)} işletme bulundu. Detaylar çekiliyor...")

        for index, item in enumerate(items[:20]): # Test için ilk 20, işe göre artırılabilir
            try:
                await item.click()
                await asyncio.sleep(2) # Detay panelinin açılmasını bekle

                # Verileri yakala
                name = await page.locator("h1.DUwDvf").inner_text()
                
                # Adres ve Telefon bazen olmayabilir, hata almamak için try/except
                try:
                    address = await page.locator("button[data-item-id='address']").inner_text()
                except: address = "Yok"
                
                try:
                    phone = await page.locator("button[data-item-id*='phone:tel:']").inner_text()
                except: phone = "Yok"

                leads.append({
                    "İşletme Adı": name,
                    "Telefon": phone,
                    "Adres": address,
                    "Şehir": TARGET_CITY,
                    "Kategori": TARGET_QUERY
                })
                print(f"✅ Çekildi: {name}")
            except:
                continue

        await browser.close()
        
        # VERİYİ EXCEL YAP (Müşterinin istediği temiz format)
        df = pd.DataFrame(leads)
        df.to_excel("leads_output.xlsx", index=False) 
        print(f"🏁 BİTTİ! leads_output.xlsx oluşturuldu.")

if __name__ == "__main__":
    asyncio.run(scrape_leads())
