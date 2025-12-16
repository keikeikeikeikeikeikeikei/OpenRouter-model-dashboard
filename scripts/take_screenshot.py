import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        # Determine paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        html_path = os.path.join(project_root, "docs", "index.html")
        output_path = os.path.join(project_root, "images", "dashboard.png")
        
        print(f"Opening: file://{html_path}")
        await page.goto(f"file://{html_path}")
        
        # Wait for any content to load if needed (e.g. table)
        await page.wait_for_load_state("networkidle")
        
        print(f"Saving screenshot to: {output_path}")
        await page.screenshot(path=output_path, full_page=False)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
