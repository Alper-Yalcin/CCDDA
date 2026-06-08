"""Yeni web arayüzünden poster için ekran görüntüsü yakalar (Playwright)."""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
BASE = "http://127.0.0.1:3001"


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1680, "height": 1120}, device_scale_factor=2)
        page = ctx.new_page()

        print("goto", BASE)
        page.goto(BASE, wait_until="networkidle")
        time.sleep(0.6)

        # Analiz sayfasına geç
        page.get_by_text("Analiz", exact=True).first.click()
        page.get_by_text("Örnek Çizimler").first.wait_for(timeout=10000)
        time.sleep(0.5)

        # Örnek çizim seç
        samples = page.locator("button:has(img)")
        samples.nth(4).click()
        time.sleep(1.2)

        # Analizi başlat
        page.get_by_role("button", name="Analizi Başlat").click()
        print("analiz başladı, sonuç bekleniyor...")

        page.get_by_text("Tahmin Edilen Duygu").first.wait_for(timeout=120000)
        time.sleep(2.5)

        out = OUT / "new_analysis_result.png"
        page.screenshot(path=str(out))
        print("kaydedildi:", out)

        browser.close()
        print("done")


if __name__ == "__main__":
    run()
