import asyncio, hashlib, os, sys, tempfile, json
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(__file__))
from fake_sws import State

EXT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'extension'))
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)


def ext_id(path):
    h = hashlib.sha256(path.encode()).hexdigest()[:32]
    return ''.join(chr(ord('a') + int(c, 16)) for c in h)


results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond)))
    print(('PASS ' if cond else 'FAIL ') + name + ((' :: ' + str(detail)) if detail and not cond else ''))


async def main():
    state = State(signed_in=True)
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            tempfile.mkdtemp(), headless=False, executable_path=os.environ.get('CHROME_PATH'),
            args=['--headless=new', '--no-sandbox', f'--disable-extensions-except={EXT}', f'--load-extension={EXT}'],
            viewport={'width': 360, 'height': 640})

        async def handler(route):
            req = route.request
            status, headers, body = state.handle(req.method, req.url, req.post_data)
            await route.fulfill(status=status, headers=dict(headers, **{'content-type': 'text/html; charset=utf-8'}), body=body)
        await ctx.route('https://sws-van.as.it.ubc.ca/**', handler)
        import datetime as _dt
        await ctx.clock.set_fixed_time(_dt.datetime(2026, 11, 20, 15, 0))  # pretend it's Friday Nov 20, 3pm

        url = f'chrome-extension://{ext_id(EXT)}/popup.html'
        pg = await ctx.new_page()
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))

        async def wait_done():
            await pg.wait_for_function("() => { const g=document.getElementById('go'); const o=document.getElementById('out').textContent; return !g.disabled && !/Checking|Connecting/.test(o); }", timeout=15000)

        # A: signed in, opens and auto-searches today (Fri Nov 20, 4-7pm default)
        await pg.goto(url)
        await wait_done()
        chips = await pg.locator('.chip').all_text_contents()
        expected_free = ['HA ' + r for r in ['037', '039', '234', '235', '241', '243', '291', '293', '295', '296', '334', '335', '343', '345', '347', '350', '354', '432', '434', '437']]
        check('auto-search on open finds the 20 free rooms', chips == expected_free, chips)
        partial = await pg.locator('.section .item b').all_text_contents()
        check('partly free sorted by most free time', partial[:3] == ['HA 237', 'HA 254', 'HA 292'] and set(partial) == {'HA 098', 'HA 232', 'HA 237', 'HA 254', 'HA 292', 'HA 339', 'HA 435'}, partial)
        items = await pg.locator('.section .item').all_text_contents()
        check('duplicate bookings collapsed', any('HA 339' in t and t.count('5:00pm–7:00pm') == 1 for t in items), items)
        check('HA 332 counted as booked the whole time', 'HA 332' in (await pg.locator('details').text_content()))
        q = state.last_query
        check('query: all 28 Angus rooms, week 13, Friday, all day, list report',
              len(q['dlObject']) == 28 and all(v.startswith('ANG-') for v in q['dlObject']) and q['lbWeeks'] == [' 13'] and q['lbDays'] == ['5']
              and q['dlPeriod'] == ['0-30'] and q['dlType'] == ['textspreadsheet;swsurl;UBCSWSActivities_TS'] and q['__VIEWSTATE'] == ['vs-rooms'], q)
        bopts = await pg.locator('#building option').all_text_contents()
        check('building list loaded, Henry Angus selected', bopts == ['Allard Hall', 'Henry Angus'] and await pg.input_value('#building') == 'Henry Angus', bopts)
        await pg.screenshot(path=f'{OUT}/a-results.png', full_page=True)

        # B: change time; it is remembered for Fridays when the popup reopens
        await pg.fill('#from', '17:00'); await pg.fill('#to', '20:00')
        await pg.click('#go'); await wait_done()
        h2 = await pg.locator('h2').first.text_content()
        check('custom time range searched', '5:00pm–8:00pm' in h2, h2)
        await pg.goto(url); await wait_done()
        check('Friday times remembered on reopen', await pg.input_value('#from') == '17:00' and await pg.input_value('#to') == '20:00')

        # C: a different weekday uses its own times (default 4-7pm) and a day with no bookings shows every room free
        await pg.fill('#date', '2026-11-23')
        await pg.dispatch_event('#date', 'change')
        check('Monday falls back to default 4-7pm', await pg.input_value('#from') == '16:00')
        await pg.click('#go'); await wait_done()
        check('day with no bookings: all 28 rooms free', len(await pg.locator('.chip').all_text_contents()) == 28)
        check('Monday query used week 14, Monday', state.last_query['lbWeeks'] == [' 14'] and state.last_query['lbDays'] == ['1'])

        # D: bad inputs
        await pg.fill('#from', '19:00'); await pg.fill('#to', '16:00'); await pg.click('#go')
        check('end before start is rejected', 'end time has to be after' in (await pg.text_content('#out')))
        await pg.fill('#date', '2027-09-10'); await pg.fill('#from', '16:00'); await pg.fill('#to', '19:00')
        await pg.click('#go'); await wait_done()
        check('date outside the session explains why', 'isn’t in the timetable' in (await pg.text_content('#out')))

        # E: other building
        await pg.fill('#date', '2026-11-20'); await pg.select_option('#building', 'Allard Hall'); await pg.click('#go'); await wait_done()
        chips = await pg.locator('.chip').all_text_contents()
        check('other building lists its rooms', chips == ['105', '112', '113'], chips)
        await pg.select_option('#building', 'Henry Angus'); await pg.click('#go'); await wait_done()

        # G: recent buttons
        pills = await pg.locator('.pill').all_text_contents()
        check('recent buttons show the last 3 distinct searches', pills[:1] == ['Fri 4\u20137pm'] and len(pills) == 3, pills)
        await pg.fill('#date', '2026-11-20'); await pg.fill('#from', '17:00'); await pg.fill('#to', '20:00')
        await pg.click('#go'); await wait_done()
        await pg.fill('#date', '2026-11-23'); await pg.dispatch_event('#date', 'change')
        await pg.locator('.pill', has_text='Fri 5\u20138pm').click(); await wait_done()
        check('tapping a recent button sets day + time and searches', await pg.input_value('#date') == '2026-11-20' and await pg.input_value('#from') == '17:00'
              and '5:00pm\u20138:00pm' in (await pg.locator('h2').first.text_content()))
        pills = await pg.locator('.pill').all_text_contents()
        check('no duplicate recent buttons', len(pills) == len(set(pills)), pills)
        check('copy button says Copy room list', await pg.locator('button.secondary', has_text='Copy room list').count() == 1)
        await pg.click('.reset')
        check('Reset clears saved times and recent buttons', await pg.locator('.pill').count() == 0 and await pg.input_value('#from') == '16:00')
        await pg.goto(url); await wait_done()
        check('after reset, Friday opens at 4-7pm again', await pg.input_value('#from') == '16:00' and await pg.input_value('#to') == '19:00')

        # F: signed out
        state.signed_in = False
        pg2 = await ctx.new_page()
        pg2.on('pageerror', lambda e: errors.append(str(e)))
        await pg2.goto(url)
        await pg2.wait_for_selector('.err', timeout=15000)
        txt = await pg2.text_content('#out')
        check('signed out: asks to sign in with CWL', 'sign in' in txt.lower() and await pg2.locator('button.secondary').count() == 1, txt)
        await pg2.screenshot(path=f'{OUT}/f-signin.png', full_page=True)

        check('no JavaScript errors', not errors, errors)
        await ctx.close()

    print(f"\n{sum(ok for _, ok in results)}/{len(results)} passed")

if __name__ == "__main__":
    asyncio.run(main())
