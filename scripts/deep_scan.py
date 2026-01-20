from playwright.sync_api import sync_playwright
import json
import time
import re

def run():
    with sync_playwright() as p:
        try:
            print("🕵️ Launching Deep Scan Browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            url = "https://www.openrouterstats.com/"
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="networkidle", timeout=90000)
            
            # Wait for the row counter at the bottom to stabilize
            print("⏳ Waiting for data to fully load (watching counter)...")
            row_count_text = ""
            for _ in range(30):
                # Look for the "X rows" text at the bottom
                text = page.inner_text("body")
                match = re.search(r"(\d+)\s+rows", text)
                if match:
                    row_count_text = match.group(1)
                    print(f"  Current site counter: {row_count_text} rows")
                    if int(row_count_text) >= 700:
                        break
                time.sleep(2)

            unique_rows = {}
            
            def scrape_current():
                return page.evaluate("() => { return Array.from(document.querySelectorAll('table tbody tr')).map(r => r.innerText); }")

            def parse_raw(text):
                # Clean and split
                parts = [p.strip() for p in re.split(r'[\t\n]', text) if p.strip()]
                if len(parts) >= 3: # Loosen requirement to catch more
                    return {
                        "model_name": parts[0],
                        "provider": parts[1] if len(parts) > 1 else "Unknown",
                        "p50_throughput": parts[2] if len(parts) > 2 else "N/A",
                        "p50_latency": parts[3] if len(parts) > 3 else "N/A",
                        "raw": text
                    }
                return None

            print("🖱️ Starting Deep Iterative Scroll...")
            container = page.locator("div.overflow-auto").first
            
            # Scroll step by step, not jumping
            total_scroll_steps = 150
            for i in range(total_scroll_steps):
                if container.count() > 0:
                    container.evaluate("el => el.scrollBy(0, 400)") # Smaller steps
                else:
                    page.mouse.wheel(0, 400)
                
                # Scrape every few steps
                if i % 2 == 0:
                    lines = scrape_current()
                    for line in lines:
                        p = parse_raw(line)
                        if p:
                            key = f"{p['model_name']}|{p['provider']}"
                            unique_rows[key] = p
                
                if i % 20 == 0:
                    print(f"  Step {i}/{total_scroll_steps}: Collected {len(unique_rows)} unique rows...")

            print(f"🏆 Deep Scan Finished. Total collected: {len(unique_rows)} rows.")
            
            # Save results
            with open("openrouter-pricing/data/openrouterstats_deep_scan.json", "w") as f:
                json.dump(list(unique_rows.values()), f, indent=2)
            
            browser.close()
        except Exception as e:
            print(f"Error during deep scan: {e}")

if __name__ == "__main__":
    run()
