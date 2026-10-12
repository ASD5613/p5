"""PS5 Pro stok kontrolu - GitHub Actions icin TEK seferlik kontrol.
Stok varsa Telegram'a mesaj atar. Elle calistirilirsa (Run workflow) test mesaji da atar.
"""
import os
import sys

import requests
from playwright.sync_api import sync_playwright

URL = "https://direct.playstation.com/it-it/buy-consoles/playstation5-pro-console-2-tb"
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
MANUAL = os.environ.get("EVENT_NAME") == "workflow_dispatch"


def telegram(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=15,
    )
    print("telegram:", r.status_code, r.text[:200] if r.status_code != 200 else "ok")


def check():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(locale="it-IT", viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)

        title = page.title()
        print("sayfa basligi:", title)

        def visible(text):
            loc = page.get_by_text(text, exact=False)
            return any(loc.nth(i).is_visible() for i in range(min(loc.count(), 10)))

        unavailable = visible("Al momento non disponibile") or visible("Scorte attualmente esaurite")
        btn = page.get_by_role("button", name="Aggiungi al carrello")
        can_add = any(
            btn.nth(i).is_visible() and btn.nth(i).is_enabled() for i in range(min(btn.count(), 10))
        )
        browser.close()
        print(f"unavailable={unavailable} can_add={can_add}")
        return can_add and not unavailable, title


def main():
    try:
        in_stock, title = check()
    except Exception as e:
        print("HATA:", e)
        if MANUAL:
            telegram(f"GitHub Actions testi: kontrol HATA verdi: {e}")
        return 0

    if in_stock:
        telegram("PS5 Pro STOKTA! Hemen gir: " + URL)
    elif MANUAL:
        telegram(f"GitHub Actions testi calisiyor. Stok durumu: yok. Sayfa: {title}")
    else:
        print("stok yok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
