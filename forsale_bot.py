import os
import time
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()  # يحمل .env لو موجود (للتشغيل محلياً)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BASE_URL = "https://www.q84sale.com"

if not TOKEN or not CHAT_ID:
    raise SystemExit("Please set TOKEN and CHAT_ID in environment variables or in a .env file")

CHAT_ID = str(CHAT_ID)
SENT_FILE = "sent_ads.json"

def load_sent():
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_sent(sent):
    try:
        with open(SENT_FILE, "w", encoding="utf-8") as f:
            json.dump(list(sent), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to save sent file:", e)

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        r = requests.post(url, data=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Failed to send message:", e)

def get_ads():
    url = f"{BASE_URL}/ar/property"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ForsaleBot/1.0)"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    items = []
    # محاولات للعثور على عناصر الإعلان — عدّل الـ selectors لو الموقع مختلف
    ad_nodes = soup.select(".real-estate-item") or soup.select(".property-item") or soup.select(".property") or soup.select("article")
    for ad in ad_nodes:
        title_tag = ad.select_one(".title") or ad.select_one("h2") or ad.select_one("a")
        title = title_tag.get_text(strip=True) if title_tag else "إعلان جديد"
        a = ad.find("a", href=True)
        if a:
            href = a["href"]
            if href.startswith("http"):
                link = href
            else:
                link = BASE_URL.rstrip("/") + "/" + href.lstrip("/")
            items.append((title, link))
    return items

def main():
    sent = load_sent()
    while True:
        try:
            ads = get_ads()
            for title, link in ads:
                if link not in sent:
                    text = f"📢 إعلان جديد:\n{title}\n{link}"
                    send_message(text)
                    sent.add(link)
            save_sent(sent)
        except Exception as e:
            print("Error:", e)
            try:
                send_message(f"⚠️ حدث خطأ في البوت: {e}")
            except:
                pass
        time.sleep(60)  # يفحص كل دقيقة

if __name__ == "__main__":
    main()
