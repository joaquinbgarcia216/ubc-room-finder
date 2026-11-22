/* Reads room bookings from the UBC Online Timetable (SWS) using the user's own signed-in session. */
(function () {
  'use strict';

  const ORIGIN = 'https://sws-van.as.it.ubc.ca';
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const REPORT_TYPE = 'textspreadsheet;swsurl;UBCSWSActivities_TS';

  class SignInRequired extends Error {
    constructor(url) { super('Sign-in required'); this.name = 'SignInRequired'; this.url = url; }
  }

  const parse = html => new DOMParser().parseFromString(html, 'text/html');

  const toMinutes = t => {
    const m = String(t).match(/(\d{1,2}):(\d{2})/);
    return m ? Number(m[1]) * 60 + Number(m[2]) : NaN;
  };

  async function getText(url, opts) {
    const res = await fetch(url, Object.assign({ credentials: 'include', redirect: 'manual', cache: 'no-store' }, opts || {}));
    if (res.type === 'opaqueredirect' || (res.status >= 300 && res.status < 400)) throw new SignInRequired(url);
    if (!res.ok) throw new Error('The timetable returned an error (HTTP ' + res.status + '). Try again in a minute.');
    return res.text();
  }

  function formFields(form) {
    const data = new URLSearchParams();
    for (const el of form.elements) {
      if (!el.name || el.disabled || /submit|button|image|reset/.test(el.type)) continue;
      if (el.tagName === 'SELECT') {
        for (const o of el.options) if (o.selected) data.append(el.name, o.value);
      } else if (/checkbox|radio/.test(el.type) && !el.checked) {
        continue;
      } else {
        data.append(el.name, el.value);
      }
    }
    return data;
  }

  let basesPromise = null;
  function sessionBases() {
    if (!basesPromise) {
      basesPromise = (async () => {
        const doc = parse(await getText(ORIGIN + '/'));
        const list = [];
        for (const a of doc.querySelectorAll('a[href*="sws_"]')) {
          let u = new URL(a.getAttribute('href'), ORIGIN + '/').href.replace(/[?#].*$/, '');
          if (!u.startsWith(ORIGIN + '/')) continue;
          if (!u.endsWith('/')) u += '/';
          if (!list.includes(u)) list.push(u);
        }
        if (!list.length) throw new Error('Couldn’t find the current timetable session.');
        return list;
      })().catch(e => { basesPromise = null; throw e; });
    }
    return basesPromise;
  }

  async function loadRoomForm(base) {
    let doc = parse(await getText(base));
    let form = doc.getElementById('form1');
    if (!form) throw new Error('The timetable page looked different than expected.');
    if (!doc.querySelector('[name=dlObject]')) {
      const data = formFields(form);
      data.set('__EVENTTARGET', 'LinkBtn_locationByZone');
      data.set('__EVENTARGUMENT', '');
      doc = parse(await getText(base, { method: 'POST', body: data }));
      form = doc.getElementById('form1');
    }
    if (!form || !doc.querySelector('[name=dlObject]')) throw new Error('Couldn’t open General Teaching Spaces on the timetable.');
    return doc;
  }

  function weekValueFor(doc, date) {
    for (const o of doc.querySelector('[name=lbWeeks]').options) {
      const m = o.text.match(/w\/c\s+(\d{1,2})\s+(\w{3})\w*\s+(\d{4})/);
      if (!m) continue;
      const start = new Date(Number(m[3]), MONTHS.indexOf(m[2]), Number(m[1]));
      const end = new Date(start); end.setDate(end.getDate() + 7);
      if (date >= start && date < end) return o.value;
    }
    return null;
  }

  function buildings(doc) {
    const set = new Set();
    for (const o of doc.querySelector('[name=dlObject]').options) {
      const m = o.text.match(/^(.*?)\s+-\s+Room\s+/);
      if (m) set.add(m[1]);
    }
    return [...set].sort((a, b) => a.localeCompare(b));
  }

  const roomNumber = s => {
    const m = String(s).match(/Room\s+(\S+)/i);
    return (m ? m[1] : String(s).trim().split(/\s+/).pop()).toUpperCase();
  };

  async function getRoomForm(date) {
    for (const base of await sessionBases()) {
      const doc = await loadRoomForm(base);
      if (!date) return { base, doc };
      const week = weekValueFor(doc, date);
      if (week) return { base, doc, week };
    }
    throw new Error('That date isn’t in the timetable yet. It only covers the current session.');
  }

  async function listBuildings() {
    const { doc } = await getRoomForm(null);
    return buildings(doc);
  }

  /* date: local Date at midnight; from/to: minutes after midnight; building: e.g. "Henry Angus" */
  async function findRooms(date, from, to, building) {
    const { base, doc, week } = await getRoomForm(date);
    const rooms = [...doc.querySelector('[name=dlObject]').options].filter(o => o.text.startsWith(building + ' - '));
    if (!rooms.length) throw new Error('No rooms found for ' + building + '.');

    const data = formFields(doc.getElementById('form1'));
    ['dlObject', 'lbWeeks', 'lbDays', 'dlPeriod', 'dlType', '__EVENTTARGET', '__EVENTARGUMENT'].forEach(n => data.delete(n));
    data.append('__EVENTTARGET', '');
    data.append('__EVENTARGUMENT', '');
    rooms.forEach(o => data.append('dlObject', o.value));
    data.append('lbWeeks', week);
    data.append('lbDays', String(date.getDay() || 7));
    data.append('dlPeriod', '0-30');
    data.append('dlType', REPORT_TYPE);
    data.append('bGetTimetable', 'View Timetable');

    const reply = await getText(base, { method: 'POST', body: data });
    if (!/showtimetable\.aspx/i.test(reply)) throw new Error('The timetable didn’t return a report. Try again.');
    const report = parse(await getText(base + 'showtimetable.aspx'));

    const bookings = {};
    let sawHeader = false;
    for (const table of report.querySelectorAll('table')) {
      let idx = null;
      for (const tr of table.querySelectorAll(':scope > tbody > tr, :scope > tr')) {
        const cells = [...tr.children].map(td => td.textContent.trim());
        if (cells.includes('Location') && cells.includes('Start Time') && cells.includes('End Time')) {
          idx = { loc: cells.indexOf('Location'), s: cells.indexOf('Start Time'), e: cells.indexOf('End Time'), n: cells.length };
          sawHeader = true;
          continue;
        }
        if (!idx || cells.length !== idx.n) continue;
        const s = toMinutes(cells[idx.s]), e = toMinutes(cells[idx.e]);
        if (isNaN(s) || isNaN(e)) continue;
        for (const loc of cells[idx.loc].split(/\s*,\s*/)) {
          const k = roomNumber(loc);
          (bookings[k] = bookings[k] || []).push([s, e]);
        }
      }
    }
    /* No header usually means no bookings at all; if there are times on the page we just couldn't read it. */
    if (!sawHeader && /\b\d{1,2}:\d{2}\b/.test(report.body.textContent)) {
      throw new Error('Couldn’t read the timetable report.');
    }

    const free = [], partial = [], booked = [];
    for (const o of rooms) {
      const room = roomNumber(o.text);
      const seen = new Set();
      const hits = (bookings[room] || [])
        .filter(([s, e]) => s < to && e > from && !seen.has(s + '-' + e) && seen.add(s + '-' + e))
        .sort((a, b) => a[0] - b[0]);
      if (!hits.length) { free.push(room); continue; }
      const gaps = [];
      let cur = from;
      for (const [s, e] of hits) {
        if (s > cur) gaps.push([cur, Math.min(s, to)]);
        cur = Math.max(cur, e);
      }
      if (cur < to) gaps.push([cur, to]);
      const item = { room, busy: hits, gaps, freeMinutes: gaps.reduce((t, [a, b]) => t + b - a, 0) };
      (gaps.length ? partial : booked).push(item);
    }
    partial.sort((a, b) => b.freeMinutes - a.freeMinutes);
    return { free, partial, booked };
  }

  async function signInUrl() {
    try { return (await sessionBases())[0]; } catch (e) { return ORIGIN + '/'; }
  }

  window.SWS = { ORIGIN, SignInRequired, listBuildings, findRooms, signInUrl, toMinutes };
})();
