import sys
import asyncio
import json
import os
from playwright.async_api import async_playwright
import pandas as pd
import random

# --- AYARLAR ---
TARGET_CITY = sys.argv[1] if len(sys.argv) > 1 else "Istanbul"
TARGET_QUERY = sys.argv[2] if len(sys.argv) > 2 else "Eczane"
DB_FILE = "database.json" # Hafıza dosyası

def load_database():
    """Eski verileri yükler."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_database(data):
    """Verileri JSON ve Excel olarak kaydeder."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    # Müşteriye verilecek Excel çıktısı
    df = pd.DataFrame(data)
    df.to_excel("leads_output.xlsx", index=False)

async def scrape_leads():
    # 1. ESKİ VERİLERİ HATIRLA
    old_data = load_database()
    # Sadece isimleri bir "set" içine alıyoruz ki kontrol hızı mermi gibi olsun
    existing_names = {item["İşletme Adı"] for item in old_data}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        search_url = f"https://www.google.com/maps/search/{TARGET_QUERY}+in+{TARGET_CITY}"
        print(f"🚀 {TARGET_CITY} - {TARGET_QUERY} için yeni veri avı başladı...")
        
        await page.goto(search_url)
        await page.wait_for_timeout(5000)

        # 2. DAHA FAZLA VERİ İÇİN DERİN KAYDIRMA
        # 5 yerine 15 yapıyoruz ki Google daha çok sonuç yüklesin
        for _ in range(15):
            await page.mouse.wheel(0, 5000)
            await asyncio.sleep(1.5)

        items = await page.query_selector_all("a.hfpxzc")
        print(f"📊 Ekranda {len(items)} işletme görüldü. Benzersiz olanlar ayıklanıyor...")

        new_entries = []
        # Limitini 100 yapıyoruz, freelance işlerde 100 idealdir
        for index, item in enumerate(items[:100]):
            try:
                # KRİTİK NOKTA: Tıklamadan önce ismi kontrol et
                name = await item.get_attribute("aria-label")
                
                if name in existing_names:
                    # print(f"⏭️ Atlanıyor (Zaten kayıtlı): {name}")
                    continue

                # Eğer yeni biriyse içeri gir ve detayları al
                await item.click()
                await asyncio.sleep(random.uniform(2, 3))

                try:
                    address = await page.locator("button[data-item-id='address']").inner_text()
                except: address = "Yok"
                
                try:
                    phone = await page.locator("button[data-item-id*='phone:tel:']").inner_text()
                except: phone = "Yok"

                new_data = {
                    "İşletme Adı": name,
                    "Telefon": phone,
                    "Adres": address,
                    "Şehir": TARGET_CITY,
                    "Kategori": TARGET_QUERY
                }
                
                new_entries.append(new_data)
                existing_names.add(name) # Aynı çalışmada tekrar gelirse diye ekle
                print(f"✨ YENİ BULUNDU: {name}")

            except Exception as e:
                continue

        await browser.close()
        
        # 3. VERİLERİ BİRLEŞTİR VE KAYDET
        combined_data = old_data + new_entries
        save_database(combined_data)
        
        print(f"🏁 BİTTİ! Toplam Veri: {len(combined_data)} (Bu sefer {len(new_entries)} yeni eklendi).")

if __name__ == "__main__":
    asyncio.run(scrape_leads())
