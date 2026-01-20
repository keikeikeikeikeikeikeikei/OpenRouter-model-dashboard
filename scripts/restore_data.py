from playwright.sync_api import sync_playwright
import json
import time
import re

def run():
    with sync_playwright() as p:
        try:
            print("🚀 Re-fetching Ultimate Data...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 20000}, # Force render
                device_scale_factor=1,
            )
            page = context.new_page()
            url = "https://www.openrouterstats.com/"
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5)

            unique_rows = {}
            
            def scrape_visible():
                return page.evaluate("""() => {
                    const rows = Array.from(document.querySelectorAll('table tbody tr'));
                    return rows.map(r => r.innerText);
                }""")
            
            def parse_row(text):
                parts = [p.strip() for p in re.split(r'[\t\n]', text) if p.strip()]
                if len(parts) >= 5:
                    return {
                        "model_name": parts[0],
                        "provider": parts[1],
                        "p50_throughput": parts[2],
                        "p50_latency": parts[3],
                        "p90_latency": parts[4]
                    }
                return None

            container = page.locator("div.overflow-auto").first
            if container.count() > 0:
                for i in range(50): # Deep scroll
                    container.evaluate("el => el.scrollBy(0, 2000)")
                    time.sleep(0.3)
                    lines = scrape_visible()
                    for line in lines:
                        p = parse_row(line)
                        if p: unique_rows[f"{p['model_name']}|{p['provider']}"] = p
            
            print(f"✅ Recovered {len(unique_rows)} rows.")
            with open("openrouter-pricing/data/openrouterstats_full_scraped.json", "w") as f:
                json.dump(list(unique_rows.values()), f, indent=2)
            
            browser.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run()
