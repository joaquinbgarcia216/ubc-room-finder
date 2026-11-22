"""Captures a sharp popup screenshot (against the fake timetable) for the store screenshot."""
import asyncio, os, sys, tempfile
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'test'))
from fake_sws import State
from run_tests import ext_id, EXT
async def main():
    state = State()
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(tempfile.mkdtemp(), headless=False, executable_path=os.environ.get('CHROME_PATH'),
            args=['--headless=new','--no-sandbox',f'--disable-extensions-except={EXT}',f'--load-extension={EXT}'],
            viewport={'width':360,'height':600}, device_scale_factor=2)
        async def h(route):
            r=route.request; s,hd,b=state.handle(r.method,r.url,r.post_data)
            await route.fulfill(status=s,headers=dict(hd,**{'content-type':'text/html'}),body=b)
        await ctx.route('https://sws-van.as.it.ubc.ca/**', h)
        import datetime as _dt
        await ctx.clock.set_fixed_time(_dt.datetime(2026, 11, 20, 15, 0))
        await ctx.add_init_script("""if (location.protocol === 'chrome-extension:' && !localStorage.getItem('seeded')) {
          localStorage.setItem('seeded','1');
          localStorage.setItem('recent', JSON.stringify([{day:5,from:'16:00',to:'19:00'},{day:4,from:'19:00',to:'22:00'},{day:1,from:'16:00',to:'19:00'}]));
        }""")
        pg = await ctx.new_page(); await pg.goto(f'chrome-extension://{ext_id(EXT)}/popup.html')
        await pg.wait_for_selector('.chip')
        await pg.screenshot(path=os.path.join(HERE, 'popup@2x.png'), clip={'x':0,'y':0,'width':360,'height':600})
        await ctx.close()
asyncio.run(main())
