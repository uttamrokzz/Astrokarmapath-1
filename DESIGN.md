# AstroKarmaPath - Design Document

**Version:** 1.3
**Last updated:** 2026-09-26

---

## 1. Core Concept

Combination and Research are the same conceptual object.

- A **Combination** = an astrological pattern (Jupiter + Saturn + Ashwini + 4th house)
- A **Research** = a real-life event, studied through one or more combinations
- **Research is a container.** It holds an event, persons, and observations.
- Each **observation = one combination attempt** - a pattern tested against the event.
- One event may have many combinations. Astrology rarely has a single cause.
- Combinations are optional in a research - a research can have zero.
- One combination can be linked to unlimited researches, via user action.

---

## 2. The Unified Form

Both independent combinations and research observations use the SAME form.
The ONLY difference: title is pre-filled when entered through a research.

| Field | Rules |
|---|---|
| **Main title** * | Required. Short result. Free text. From research, pre-filled as 'Event name #N', editable. |
| **Ref chart** | Multi-select pills (D1, D9, D10...) with + button. Custom refs can be added. |
| **Combination slots** | Label + value rows. Add/remove with +/x buttons. Both label and value are free text. |
| **Dasha** | Rows with level (dropdown: MD / AD / PD / SD / Pratyantar) + lord + date. |
| **Date of event** | From -> To, plus optional time. Single date is allowed (leave To empty). |
| **Date of logging** | Auto-filled with current date + time. Editable. |
| **Persons** | Modal picker with search + add new. Inherited from research (cannot remove originals). |
| **Body** | Large text area. Multiple paragraphs. This is the LONG ANSWER / explanation. |

### Title rule
- Independent combination -> user types the title freely (this IS the result)
- From research observation -> pre-filled as Event name #N (e.g. 'Anemia happened #1')
- The #N is for user convenience only. **Ignored during search.**

### Field semantics
- **Title** = short result (e.g. 'Bad marriage', 'Anemia happened #1')
- **Body** = long answer (detailed explanation of what happened)
- These are two separate fields.

---

## 3. Data Model

### Tables

**people**
- id
- name
- dob
- tob
- location
- manual_coords
- tags              (Profession / Disease etc - comma separated)
- short_tags        (Family art / Dealer etc - comma separated)
- notes
- created_at
- Overwrite key: name + dob + location

**research**
- id
- event             (event name - becomes title of linked combinations)
- event_date_from
- event_date_to
- event_time
- created_at
- Overwrite key: event + person + date

**research_people**   (many-to-many)
- research_id
- person_id

**combinations**      (holds both independent combos AND observations from research)
- id
- research_id       (nullable - empty for independent combinations)
- observation_num   (nullable - 1, 2, 3... for observations within a research)
- is_main           (0/1 - one per research is main)
- title             (required - the short result)
- refs              (comma separated: 'D1, D9')
- event_date_from
- event_date_to
- event_time
- log_date          (auto-filled with now(), editable)
- log_time          (auto-filled with now(), editable)
- body              (large text - the long answer / explanation)
- created_at
- Overwrite key: title + observation_num

**combination_slots**
- id
- combination_id
- slot_num
- label
- value

**combination_dasha**
- id
- combination_id
- level             (MD / AD / PD / SD / Pratyantar)
- lord
- dasha_date

**combination_people** (many-to-many)
- combination_id
- person_id

---

## 4. Save Behaviour

### From research observation
When an observation is saved:
- Stored in combinations with research_id set and observation_num assigned
- Title prefilled with event name, but editable
- All research persons linked automatically
- Additional persons can be added; original research persons cannot be removed
- Body becomes the long answer

### From independent combination
- Stored in combinations with research_id empty
- Title = user-typed result
- Persons explicitly linked

### Overwrite rules
- Person: key = name + dob + location
- Combination: key = title + observation_num
- Research: key = event + person + date
- Independent combos with same title -> both saved, distinguished by slots

### Delete behaviour
- Deleting research or observation -> small popup: 'Delete linked combination too?'
- No page redirect. Modal popup only.

---

## 5. Observations Within Research

- Every research starts with **one main observation**
- Additional observations can be added (optional, unlimited)
- **Any observation can be promoted to main** at any time
- Main is just a display flag - no data difference
- Every observation has its own event date - may differ from the research's overall date
- Every observation has its own person list - inherited from research + additions
- Original research persons **cannot be removed** from the observation
- New persons added to an observation **can** be edited or deleted
- **Dasha lives only at observation level** (not at research level)

---

## 6. UI Principles

- Spacious display - fewer, larger elements (phone-first)
- Save button at both top and bottom
- Observations open on a **separate full-screen page** (same layout as the combination page)
- Every page has BACK + HOME buttons
- Purple theme (#5e35b1 primary)
- Built for hourly use - optimised for speed

### Research page layout

Event title, event date range, persons
   |
[Main observation card - collapsible]
[Observation 2 card - collapsible]
[Observation 3 card - collapsible]
   |
[+ ADD OBSERVATION]
   |
[SAVE]

### Combination card (list view)

Title (large, bold)
Slots (small, muted)
Body - long answer / explanation
Persons: Test Person, Abhishek
Refs: D1, D9
Event: 20/03/2024 -> 15/04/2024
Logged: 26/09/2026 10:51

### Combination detail page
Same layout as above, plus:
- Linked research (if observation)
- Dasha table
- All slots expanded
- Edit / Delete buttons

---

## 7. Search

- **Mixed results, ranked by relevance** (one list, not grouped)
- **Visual chip at right corner**:
  - Purple = Person
  - Orange = Combination
  - Green = Research
- **Tap to expand** - shows inline links + summary badge ('-> 3 combos, 2 persons')
- Searches across: title, body, slot values, person names
- The #N numbering is **ignored** during ranking

---

## 8. Paste / Import Format

Flexible, systematic, lenient. **Preview + edit before saving.**
**Overwrite, don't duplicate.**

person
name: Test Person
dob: 1990-08-14
tob: 06:42
location: Chennai, India
manual coords: 13.0827, 80.2707
tags: cinema, sports
short tags: psycho movies, baseball
notes: notes here

combination
title: Bad marriage
refs: D1, D9
slots:
  Jupiter - Aries
  Saturn - 7th house
dasha:
  MD - Jupiter - 2019
  AD - Saturn - 2021
event date: 20/03/2024 to 15/04/2024
log date: 2026-09-26
body: Long description here spanning
      multiple lines is fine.

research
event: Anemia happened
event date: 20/03/2024 to 15/04/2024
persons: Test Person, Abhishek

observation
title: Anemia happened #1
refs: D1
slots:
  Moon - 6th
  Ketu - 8th
dasha:
  MD - Jupiter - 2019
event date: 20/03/2024
log date: 2026-09-26
body: Severe anemia detected.

### Rules
- Header: #person or person (both work)
- Simple fields: key: value
- Slots: label - value (dash separator)
- Dasha: level - lord - date
- Dates: accept many formats (14/08/1990, Aug 14 1990, 1990-08-14)
- Partial paste allowed - save whatever fields are given
- **Overwrite, don't duplicate**

---

## 9. Excel Structure

Multi-sheet with auto serial numbers. Cross-linked.
Serial numbers can repeat in foreign keys (same person in multiple rows).

**Sheet 1 - Persons**
S.No | Name | DOB | TOB | Location | Manual Coords | Tags | Short Tags | Notes

**Sheet 2 - Research**
S.No | Event | Date From | Date To | Time | Person S.No(s)

**Sheet 3 - Observations**
S.No | Research S.No | Obs Num | Is Main | Title | Refs | Slots | Dasha | Event Date From | Event Date To | Log Date | Body | Person S.No(s)

**Sheet 4 - Combinations**
S.No | Title | Observation S.No | Research S.No | Refs | Slots | Dasha | Event Date | Log Date | Body | Person S.No(s)

Notes:
- Slots stored as Label-Value; Label-Value
- Dasha stored as Level-Lord-Date; Level-Lord-Date
- Dates in YYYY-MM-DD format for Excel compatibility
- Import reads all sheets, links by S.No, overwrites on re-import

---

## 10. Export / Import

- **Manual button** - user decides when
- **Formats**: JSON, CSV, or both - user picks each time
- **Destinations**: phone download, GitHub repo, email - user picks
- **Input = Output** - export -> edit -> re-import works
- **Overwrite, don't duplicate**

### Destinations
- **Phone**: downloads to /storage/emulated/0/astrokarmapath/exports/
- **GitHub**: commits to backups/YYYY-MM-DD.json in repo
- **Email**: sends to your email address

---

## 11. Folders

| Purpose | Path |
|---|---|
| Watch folder (phone) | /storage/emulated/0/astrokarmapath/import/ |
| After import | /storage/emulated/0/astrokarmapath/imported/ |
| Export (phone) | /storage/emulated/0/astrokarmapath/exports/ |
| GitHub import | import/ folder in repo |
| GitHub backup | backups/YYYY-MM-DD.json |

### Import triggers
- **Manual button**: 'Import file' -> file picker -> choose .csv / .json / .txt
- **Watch folder**: drop files into /import/ -> tap 'Sync now' -> files read and moved to /imported/
- **GitHub import**: drop file in import/ folder on GitHub -> tap 'Import from GitHub'

---

## 12. Offline

- **Paste importer** for offline writing -> paste when back online
- **Offline queue** - adds, edits, deletes queue locally; auto-sync when online
- **Cache last-viewed pages** when offline
- **Daily auto-export** to GitHub (runs on Render server)

---

## 13. Hosting Stack

- **Turso** - cloud SQLite database
- **Render** - Flask app host (free tier)
- **GitHub** - code + backups + import source
- **Pydroid 3** - local development on phone
- URL: https://astrokarmapath-1.onrender.com

---

## 14. Known Limitations

- Render free tier sleeps after 15 min - first visit takes 30-60 sec to wake
- No persistent file system on Render - file operations go through GitHub API or the user's phone
- Daily export runs on Render and commits to GitHub (not to phone directly)
- On Android, watch folder path requires storage permission for Pydroid 3

---

## 15. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-09-26 | Initial design - unified combination/research model |
| 1.1 | 2026-09-26 | Corrected: Body = answer. Main observation flag. Log date field. Excel cross-links. |
| 1.2 | 2026-09-26 | Added: Persons on unified form. Dasha section. Inherited-persons rule. Each observation has its own event date. Title vs Body semantics. |
| 1.3 | 2026-09-26 | Dasha lives only at observation level (removed research-level default). |

---

*End of Design Document*