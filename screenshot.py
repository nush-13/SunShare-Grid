
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://localhost:8501")
        await asyncio.sleep(10)  # Wait for the map to load
        await page.screenshot(path="screenshot.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
