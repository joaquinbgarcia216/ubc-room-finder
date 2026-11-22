# UBC Room Finder: Chrome Web Store listing

Copy each section into the matching field in the Chrome Web Store Developer Dashboard.

---

## Package tab
Upload: `ubc-room-finder-v1.0.1.zip`

---

## Store listing tab

**Name** (comes from the manifest)
UBC Room Finder

**Summary** (comes from the manifest, max 132 characters)
Find free UBC Vancouver teaching rooms for any date and time, straight from the UBC Online Timetable.

**Description**
```
Need a room for a meeting, study session or practice? UBC Room Finder shows you every free teaching room in a UBC Vancouver building for the date and time you pick.

HOW IT WORKS
1. Sign in to the UBC Online Timetable (sws-van.as.it.ubc.ca) with your CWL, like you normally would.
2. Click the Room Finder icon on any tab.
3. It opens straight to today's free rooms. Change the date, time or building and hit "Find free rooms".

WHAT YOU GET
• Rooms that are free for your whole time range
• Rooms that are partly free, with exactly when they open up and what's booked
• Rooms that are booked the whole time, tucked out of the way
• One-tap buttons for your recent times (like "Mon 4–7pm"), so repeat searches take a single click
• Remembers your usual time for each day of the week and your building (hit "Reset" to clear them)
• A "Copy room list" button to paste the results into any chat or email

PRIVACY
Room Finder only talks to the UBC Online Timetable, using your own signed-in session in your browser. It doesn't collect, store or send your data anywhere else, and it has no servers of its own.

GOOD TO KNOW
• Read-only: it doesn't book rooms. Request rooms through UBC's usual booking process.
• Tentative holds and very recent bookings may not show up.
• Unofficial tool, not affiliated with or endorsed by the University of British Columbia.
```

**Category**
Education (or Productivity → Tools)

**Language**
English

**Graphic assets**
- Store icon: `store-icon-128x128.png`
- Screenshot: `screenshot-1280x800.png`
- Small promo tile: `promo-440x280.png`
- Marquee promo tile: skip (optional)

**Official URL / Homepage URL / Support URL**
Leave blank, or add a support email you're happy to make public.

---

## Privacy tab

**Single purpose description**
```
UBC Room Finder has one purpose: showing which UBC Vancouver teaching rooms are free at a chosen date and time, by reading room bookings from the UBC Online Timetable.
```

**Permission justification: Host permission (https://sws-van.as.it.ubc.ca/*)**
```
The extension reads room bookings from the UBC Online Timetable at sws-van.as.it.ubc.ca, using the user's existing signed-in session, so it can work out which rooms are free. It needs access to this one site only and makes no requests to any other site.
```

**Are you using remote code?**
No, I am not using remote code. (All JavaScript ships in the package.)

**Data usage**
Leave every data type unchecked (personally identifiable info, health, financial, authentication, personal communications, location, web history, user activity, website content). The extension doesn't collect or transmit any user data. It reads timetable pages in the user's browser and shows the result. The only things it saves are the user's recent time ranges and building, kept locally in their browser.

Tick all three certifications:
- I do not sell or transfer user data to third parties, outside of the approved use cases
- I do not use or transfer user data for purposes that are unrelated to my item's single purpose
- I do not use or transfer user data to determine creditworthiness or for lending purposes

**Privacy policy URL**
Optional when no user data is collected. Leave blank.

---

## Distribution tab
- **Payments:** Free of charge
- **Visibility:** Unlisted
- **Regions:** All regions

---

## After approval
Share the store link (it looks like `https://chromewebstore.google.com/detail/ubc-room-finder/<id>`). To ship an update, bump `version` in `manifest.json`, zip the folder again, and upload it under **Package**. Each update goes through review again.
