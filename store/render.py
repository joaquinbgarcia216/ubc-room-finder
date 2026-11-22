"""Renders screenshot.html and promo.html into the PNGs the Chrome Web Store needs."""
import asyncio, os
HERE = os.path.dirname(os.path.abspath(__file__))
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get('CHROME_PATH'), args=['--no-sandbox','--allow-file-access-from-files'])
        for name,w,h in [('screenshot',1280,800),('promo',440,280)]:
            pg = await b.new_page(viewport={'width':w,'height':h})
            await pg.goto('file://' + os.path.join(HERE, name + '.html'))
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=os.path.join(HERE, f'{name}-{w}x{h}.png'))
        await b.close()
asyncio.run(main())
