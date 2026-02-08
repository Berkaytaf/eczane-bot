import asyncio
from playwright.async_api import async_playwright
import pandas as pd # Veriyi Excel/CSV yapmak için
import random

async def scrape_leads(target_city, target_query):
    async with async_playwright() as p:
        # İnsansı tarayıcı
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # Google Maps veya bir rehber sitesi üzerinden arama
        search_url = f"https://www.google.com/maps/search/{target_query}+in+{target_city}"
        print(f"🚀 {target_city} için {target_query} avı başladı...")
        
        await page.goto(search_url)
        await page.wait_for_timeout(5000) # Sayfanın oturması için

        leads = []
        
        # Sayfayı kaydırarak ilanları yükle (Lead Generation'ın kalbi burası)
        for _ in range(5): # 5 kere aşağı kaydır (Daha fazla veri için artırabilirsin)
            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(2000)

        # Kartları bul ve veriyi çek
        items = await page.query_selector_all("div[role='article']")
        
        for item in items:
            try:
                # İsim, adres ve telefon seçicileri (Siteye göre güncellenir)
                name = await item.get_attribute("aria-label")
                # Detaylı veri için her karta tıklayıp sağ panelden çekmek en temizidir
                # Ama hızlıca isim ve temel bilgileri alalım:
                leads.append({
                    "İşletme Adı": name,
                    "Şehir": target_city,
                    "Kategori": target_query,
                    "Durum": "Aktif"
                })
            except:
                continue

        await browser.close()
        
        # VERİYİ TEMİZLE VE EXCEL'E DÖK
        df = pd.DataFrame(leads)
        df.to_csv("istanbul_eczaneler.csv", index=False, encoding="utf-8-sig")
        print(f"✅ İşlem Tamam! {len(leads)} adet veri 'istanbul_eczaneler.csv' olarak kaydedildi.")

if __name__ == "__main__":
    asyncio.run(scrape_leads("Istanbul", "Eczane"))
