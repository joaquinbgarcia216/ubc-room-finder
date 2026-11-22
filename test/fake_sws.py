"""Stand-in for the UBC timetable (SWS), shaped like the live pages observed on 2026-11-20."""
import datetime, html
from urllib.parse import parse_qs

ANGUS = ['037', '039', '098', '232', '234', '235', '237', '241', '243', '254', '291', '292', '293', '295',
         '296', '332', '334', '335', '339', '343', '345', '347', '350', '354', '432', '434', '435', '437']
ALLARD = ['105', '112', '113']

# Friday week 13 bookings in Angus (seen live), plus a duplicate row and a multi-room row
FRI_ROWS = [
    ('PSYC 217 Lab', '037', '9:00', '15:00'), ('PSYC 217 Lab', '434', '9:00', '15:00'),
    ('COMM 644', '232', '9:00', '12:00'), ('COMM 682', '232', '14:00', '17:30'),
    ('X', '237', '12:00', '16:30'), ('X', '254', '14:00', '17:00'), ('X', '292', '15:30', '17:00'),
    ('X', '332', '13:00', '17:00'), ('X', '332', '17:00', '19:00'),
    ('X', '339', '15:30', '16:30'), ('X', '339', '17:00', '19:00'), ('X', '339', '17:00', '19:00'),
    ('X', '435', '15:30', '17:00'), ('UBCTG Competition 1', '098', '16:30', '21:00'),
]


def page(body):
    return '<!DOCTYPE html><html><head><title>SWS Vancouver - 3.1.0.0</title></head><body>' + body + '</body></html>'


def root():
    return page('<a href="https://sws-van.as.it.ubc.ca/sws_2026">2026W_2027S</a>')


def home():
    return page('<form id="form1" method="post" action="./"><input type="hidden" name="__VIEWSTATE" value="vs-home">'
                '<input type="hidden" name="__EVENTTARGET" value=""><input type="hidden" name="__EVENTARGUMENT" value="">'
                '<a id="LinkBtn_locationByZone" href="javascript:__doPostBack(\'LinkBtn_locationByZone\',\'\')">General Teaching Spaces</a></form>')


def room_form():
    opts = ''.join(f'<option value="ALL-{r}">Allard Hall - Room {r}</option>' for r in ALLARD)
    opts += ''.join(f'<option value="ANG-{r}">Henry Angus - Room {r}</option>' for r in ANGUS)
    start = datetime.date(2026, 8, 24)
    weeks = '<option selected value="1-53">All Weeks</option><option value="t">This Week</option><option value="n">Next Week</option>'
    for i in range(53):
        d = start + datetime.timedelta(weeks=i)
        weeks += f'<option value=" {i + 1}">Week {i + 1} w/c {d.strftime("%d %b %Y")}</option>'
    days = ''.join(f'<option value="{v}">{t}</option>' for v, t in
                   [('1-7', 'All Days'), ('1-5', 'Week days'), ('1', 'Mon'), ('2', 'Tue'), ('3', 'Wed'), ('4', 'Thu'), ('5', 'Fri'), ('6', 'Sat'), ('7', 'Sun')])
    return page('<form id="form1" method="post" action="./">'
                '<input type="hidden" name="__VIEWSTATE" value="vs-rooms"><input type="hidden" name="__EVENTTARGET" value="">'
                '<input type="hidden" name="__EVENTARGUMENT" value=""><input type="text" name="tWildcard" value="">'
                '<input type="submit" name="bWildcard" value="Filter">'
                f'<select name="dlObject" multiple>{opts}</select><select name="lbWeeks" multiple>{weeks}</select>'
                f'<select name="lbDays">{days}</select>'
                '<select name="dlPeriod"><option selected value="0-10">Morning</option><option value="0-30">All Day</option></select>'
                '<select name="dlType"><option selected value="individual;swsurl;UBCSWSLocationIndividual">Single</option>'
                '<option value="textspreadsheet;swsurl;UBCSWSActivities_TS">List Timetable</option></select>'
                '<input type="submit" name="bGetTimetable" value="View Timetable"></form>')


HEAD = ['Name', 'Section ID', 'Type', 'Name of Department', 'Weeks', 'Location', 'Staff', 'Module', 'Day', 'Start Time', 'End Time']


def report(rows):
    if not rows:
        return page('<table><tr><td>Exported Weeks: 14, 11/23/26 To 11/29/2026</td></tr></table>')
    by_room = {}
    for r in rows:
        by_room.setdefault(r[1], []).append(r)
    out = ''
    for room, rs in by_room.items():
        trs = '<tr>' + ''.join(f'<td>{h}</td>' for h in HEAD) + '</tr>'
        for name, rm, s, e in rs:
            cells = [name, '', 'WRB-ACTIVE', 'WRB_UBC', '13', f'ANGU {rm}', '', '', 'Fri', s, e]
            trs += '<tr>' + ''.join(f'<td>{html.escape(c)}</td>' for c in cells) + '</tr>'
        out += ('<table><tr><td>Exported Weeks: 13, 11/16/26 To 11/22/2026</td></tr></table>'
                f'<table><tr><td>Fri</td></tr></table><table>{trs}</table>')
    return page('<table><tr><td>' + out + '</td></tr></table>')


class State:
    def __init__(self, signed_in=True):
        self.signed_in = signed_in
        self.last_query = None

    def handle(self, method, url, body):
        """Return (status, headers, text)."""
        path = url.split('sws-van.as.it.ubc.ca', 1)[1]
        if not self.signed_in and path.startswith('/sws_'):
            return 302, {'location': 'https://authentication.ubc.ca/idp/profile/SAML2/Redirect/SSO'}, ''
        if path == '/':
            return 200, {}, root()
        if path == '/sws_2026/' and method == 'GET':
            return 200, {}, home()
        if path == '/sws_2026/' and method == 'POST':
            q = parse_qs(body or '', keep_blank_values=True)
            if q.get('__EVENTTARGET') == ['LinkBtn_locationByZone']:
                return 200, {}, room_form()
            if 'bGetTimetable' in q:
                self.last_query = q
                return 200, {}, page('<form id="form1"></form><script>window.open(\'showtimetable.aspx\', \'\', \'\');</script>')
            return 400, {}, 'bad post'
        if path == '/sws_2026/showtimetable.aspx':
            q = self.last_query or {}
            if q.get('lbDays') == ['5'] and q.get('lbWeeks') == [' 13']:
                rooms = {v.split('-')[1] for v in q.get('dlObject', [])}
                return 200, {}, report([r for r in FRI_ROWS if r[1] in rooms])
            return 200, {}, report([])
        return 404, {}, 'not found'
