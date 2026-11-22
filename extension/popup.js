(function () {
  'use strict';

  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const DEFAULT_BUILDING = 'Henry Angus';
  const DEFAULT_TIMES = ['16:00', '19:00'];

  const $ = id => document.getElementById(id);
  const out = $('out');
  const pad = n => String(n).padStart(2, '0');
  const fmt = m => {
    const h = Math.floor(m / 60), mm = m % 60;
    return (h % 12 || 12) + ':' + pad(mm) + (h < 12 || h === 24 ? 'am' : 'pm');
  };
  const fmtRange = ([a, b]) => fmt(a) + '–' + fmt(b);

  function el(tag, props, ...children) {
    const node = document.createElement(tag);
    if (props) for (const [k, v] of Object.entries(props)) {
      if (k === 'class') node.className = v; else if (k === 'on') Object.entries(v).forEach(([e, f]) => node.addEventListener(e, f)); else node.setAttribute(k, v);
    }
    for (const c of children.flat()) if (c != null && c !== false) node.append(c);
    return node;
  }
  const show = (...nodes) => out.replaceChildren(...nodes);

  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage unavailable */ } }
  };

  function selectedDate() {
    const [y, m, d] = $('date').value.split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  function applyRememberedTimes() {
    const times = store.get('times-' + selectedDate().getDay()) || DEFAULT_TIMES;
    $('from').value = times[0];
    $('to').value = times[1];
  }

  /* Recent searches: up to 3 day + time ranges, newest first, shown as one-tap buttons */
  const MAX_RECENT = 3;
  const shortTime = (m, withSuffix) => {
    const h = Math.floor(m / 60), mm = m % 60;
    return (h % 12 || 12) + (mm ? ':' + pad(mm) : '') + (withSuffix ? (h < 12 || h === 24 ? 'am' : 'pm') : '');
  };
  const recentLabel = r => {
    const a = SWS.toMinutes(r.from), b = SWS.toMinutes(r.to);
    const sameHalf = (a < 720) === (b < 720);
    return DAYS[r.day] + ' ' + shortTime(a, !sameHalf) + '–' + shortTime(b, true);
  };
  function remember(day, from, to) {
    const list = (store.get('recent') || []).filter(r => !(r.day === day && r.from === from && r.to === to));
    list.unshift({ day, from, to });
    store.set('recent', list.slice(0, MAX_RECENT));
  }
  function nextDate(day) {
    const d = new Date(); d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() + ((day - d.getDay() + 7) % 7));
    return d;
  }
  function renderRecent() {
    const list = store.get('recent') || [];
    const box = $('recent');
    if (!list.length) { box.replaceChildren(); return; }
    box.replaceChildren(
      ...list.map(r => el('button', { type: 'button', class: 'pill', title: 'Search the next ' + DAYS[r.day] + ' at this time', on: { click: () => {
        const d = nextDate(r.day);
        $('date').value = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
        $('from').value = r.from; $('to').value = r.to;
        search();
      } } }, recentLabel(r))),
      el('button', { type: 'button', class: 'reset', title: 'Forget saved times', on: { click: resetTimes } }, 'Reset'));
  }
  function resetTimes() {
    try {
      Object.keys(localStorage).filter(k => k.startsWith('times-') || k === 'recent').forEach(k => localStorage.removeItem(k));
    } catch (e) { /* storage unavailable */ }
    $('from').value = DEFAULT_TIMES[0]; $('to').value = DEFAULT_TIMES[1];
    renderRecent();
  }

  const label = (building, room) => building === DEFAULT_BUILDING ? 'HA ' + room : room;
  const fullLabel = (building, room) => building === DEFAULT_BUILDING ? 'HA ' + room : building + ' ' + room;

  async function showSignIn() {
    const url = await SWS.signInUrl();
    show(el('div', { class: 'err' },
      'You need to sign in to the UBC Online Timetable first.',
      el('button', { class: 'secondary', on: { click: () => { chrome.tabs.create({ url }); window.close(); } } }, 'Sign in with CWL'),
      el('p', { class: 'muted' }, 'Once you’re signed in, click the Room Finder icon again.')));
  }

  function showError(e) {
    if (e instanceof SWS.SignInRequired) return showSignIn();
    if (e instanceof TypeError) {
      return show(el('div', { class: 'err' }, 'Couldn’t reach the UBC timetable. Check your internet connection, or sign in again.',
        el('button', { class: 'secondary', on: { click: showSignIn } }, 'Sign in again')));
    }
    show(el('div', { class: 'err' }, e && e.message ? e.message : String(e)));
  }

  function render(res, building, date, from, to) {
    const when = DAYS[date.getDay()] + ', ' + MONTHS[date.getMonth()] + ' ' + date.getDate() + ', ' + fmtRange([from, to]);
    const nodes = [];

    nodes.push(el('h2', null, 'Free the whole time ', el('span', { class: 'when' }, '· ' + when)));
    nodes.push(res.free.length
      ? el('div', { class: 'chips' }, res.free.map(r => el('span', { class: 'chip' }, label(building, r))))
      : el('div', { class: 'muted' }, 'No rooms in ' + building + ' are free for that whole time.'));

    if (res.partial.length) {
      nodes.push(el('div', { class: 'section' }, el('h2', null, 'Partly free'),
        res.partial.map(p => el('div', { class: 'item' },
          el('b', null, label(building, p.room)), ' free ' + p.gaps.map(fmtRange).join(', '),
          el('div', { class: 'muted' }, 'booked ' + p.busy.map(fmtRange).join(', '))))));
    }
    if (res.booked.length) {
      nodes.push(el('details', null, el('summary', null, 'Booked the whole time (' + res.booked.length + ')'),
        res.booked.map(p => el('div', { class: 'item' }, el('b', null, label(building, p.room)), ' ',
          el('span', { class: 'muted' }, p.busy.map(fmtRange).join(', '))))));
    }

    const copy = el('button', { class: 'secondary' }, 'Copy room list');
    copy.addEventListener('click', async () => {
      let text = 'Free rooms in ' + building + ' (' + when + '): ' + (res.free.length ? res.free.map(r => fullLabel(building, r)).join(', ') : 'none');
      if (res.partial.length) text += '\nPartly free: ' + res.partial.map(p => fullLabel(building, p.room) + ' (free ' + p.gaps.map(fmtRange).join(', ') + ')').join('; ');
      try { await navigator.clipboard.writeText(text); copy.textContent = 'Copied!'; }
      catch (e) { copy.textContent = 'Couldn’t copy'; }
      setTimeout(() => { copy.textContent = 'Copy room list'; }, 1500);
    });
    nodes.push(copy);
    show(...nodes);
  }

  let busy = false;
  async function search() {
    if (busy) return;
    const date = selectedDate();
    const from = SWS.toMinutes($('from').value), to = SWS.toMinutes($('to').value);
    const building = $('building').value;
    if (isNaN(date) || isNaN(from) || isNaN(to)) return show(el('div', { class: 'err' }, 'Pick a date and a time range.'));
    if (to <= from) return show(el('div', { class: 'err' }, 'The end time has to be after the start time.'));

    store.set('times-' + date.getDay(), [$('from').value, $('to').value]);
    store.set('building', building);
    remember(date.getDay(), $('from').value, $('to').value);
    renderRecent();

    busy = true;
    $('go').disabled = true; $('go').textContent = 'Checking…';
    show(el('div', { class: 'msg' }, 'Checking the timetable…'));
    try {
      render(await SWS.findRooms(date, from, to, building), building, date, from, to);
    } catch (e) {
      showError(e);
    } finally {
      busy = false;
      $('go').disabled = false; $('go').textContent = 'Find free rooms';
    }
  }

  async function init() {
    const now = new Date();
    $('date').value = now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate());
    applyRememberedTimes();
    renderRecent();
    $('date').addEventListener('change', () => { if ($('date').value) applyRememberedTimes(); });
    $('form').addEventListener('submit', e => { e.preventDefault(); search(); });

    const saved = store.get('building') || DEFAULT_BUILDING;
    $('building').replaceChildren(el('option', null, saved));
    $('go').disabled = true;
    show(el('div', { class: 'msg' }, 'Connecting to the UBC timetable…'));
    try {
      const list = await SWS.listBuildings();
      $('building').replaceChildren(...list.map(b => el('option', null, b)));
      $('building').value = list.includes(saved) ? saved : (list.includes(DEFAULT_BUILDING) ? DEFAULT_BUILDING : list[0]);
      $('go').disabled = false;
      search();
    } catch (e) {
      $('go').disabled = false;
      showError(e);
    }
  }

  init();
})();
