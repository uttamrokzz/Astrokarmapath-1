# -*- coding: utf-8 -*-
import io
import csv
import json
import zipfile
import re
from datetime import datetime
from flask import Blueprint, request, redirect, Response, send_file
from core import q, run, insert_and_id, page, nav

bp = Blueprint("data", __name__)


# ============================================================
# PASTE PARSER
# ============================================================
BLOCK_RE = re.compile(r"^#?\[?(person|combination|research|observation)\]?$",
                      re.IGNORECASE)


def parse_paste(text):
    """Parse the flexible paste format into structured dict."""
    result = {"people": [], "combinations": [], "researches": []}
    cur_block = None          # current dict
    cur_kind = None           # 'person' | 'combination' | 'research' | 'observation'
    cur_list = None           # 'slots' | 'dasha' | 'body'
    last_research = None      # reference to last research for observations

    def new_block(kind):
        nonlocal cur_block, cur_kind, cur_list
        cur_kind = kind
        cur_list = None
        if kind == "person":
            cur_block = {"_kind": "person"}
            result["people"].append(cur_block)
        elif kind == "combination":
            cur_block = {"_kind": "combination", "slots": [], "dasha": [],
                         "persons": []}
            result["combinations"].append(cur_block)
        elif kind == "research":
            cur_block = {"_kind": "research", "observations": [], "persons": []}
            result["researches"].append(cur_block)
            last_research_ref[0] = cur_block
        elif kind == "observation":
            cur_block = {"_kind": "observation", "slots": [], "dasha": [],
                         "persons": []}
            if last_research_ref[0] is not None:
                last_research_ref[0]["observations"].append(cur_block)
            else:
                # Orphan observation -> treat as independent combination
                result["combinations"].append(cur_block)

    last_research_ref = [None]

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            cur_list = None
            continue

        # New block header
        m = BLOCK_RE.match(stripped.lower())
        if m:
            new_block(m.group(1).lower())
            continue

        if cur_block is None:
            continue

        # List-section header (slots: / dasha:)
        low = stripped.lower()
        if low in ("slots:", "slots", "slot:"):
            cur_list = "slots"
            continue
        if low in ("dasha:", "dasha"):
            cur_list = "dasha"
            continue
        if low in ("body:", "body") or low == "body":
            cur_list = "body"
            cur_block["body"] = cur_block.get("body", "")
            continue

        # Inside a list section — indented entries
        if cur_list in ("slots", "dasha") and (line.startswith(" ") or line.startswith("\t")):
            # split on " - " or " -" or "- "
            parts = re.split(r"\s*-\s*", stripped, maxsplit=2)
            if cur_list == "slots":
                if len(parts) >= 2:
                    cur_block["slots"].append((parts[0].strip(), parts[1].strip()))
            else:
                if len(parts) >= 3:
                    cur_block["dasha"].append((parts[0].strip(),
                                                parts[1].strip(),
                                                parts[2].strip()))
                elif len(parts) == 2:
                    cur_block["dasha"].append((parts[0].strip(),
                                                parts[1].strip(), ""))
            continue

        # Body continuation (indented under body:)
        if cur_list == "body" and (line.startswith(" ") or line.startswith("\t")):
            cur_block["body"] = cur_block.get("body", "") + "\n" + stripped
            continue

        # key: value line
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip().lower().replace(" ", "_")
            val = val.strip()
            cur_list = None
            cur_block[key] = val
            continue

    return result


# ============================================================
# SAVE PARSED DATA
# ============================================================
def ensure_person(name):
    """Find or create a person by name. Returns id."""
    if not name:
        return None
    name = name.strip()
    r = q("SELECT id FROM people WHERE name=?", (name,))
    if r:
        return r[0][0]
    return insert_and_id("INSERT INTO people (name) VALUES (?)", (name,))


def save_person_dict(p):
    """Save one person, overwriting by name+dob+location."""
    name = (p.get("name") or "").strip()
    if not name:
        return None
    dob = (p.get("dob") or "").strip()
    loc = (p.get("location") or "").strip()
    tob = (p.get("tob") or "").strip()
    tags = (p.get("tags") or "").strip()
    stags = (p.get("short_tags") or "").strip()
    notes = (p.get("notes") or "").strip()
    man = (p.get("manual_coords") or "").strip()

    existing = q("""SELECT id FROM people
                    WHERE name=? AND IFNULL(birth_date,'')=?
                      AND IFNULL(birth_place,'')=?""",
                 (name, dob, loc))
    if existing:
        pid = existing[0][0]
        run("""UPDATE people SET birth_time=?, manual_coords=?,
               broader_tags=?, multiple_tags=?, notes=?
               WHERE id=?""",
            (tob, man, tags, stags, notes, pid))
        return pid
    return insert_and_id("""INSERT INTO people
        (name, birth_date, birth_time, birth_place, manual_coords,
         broader_tags, multiple_tags, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, dob, tob, loc, man, tags, stags, notes))


def save_combination_dict(c, research_id=None, obs_num=None, is_main=0):
    title = (c.get("title") or "").strip()
    body = (c.get("body") or "").strip()
    refs = c.get("refs") or ""
    if isinstance(refs, list):
        refs = ", ".join(refs)
    edf = (c.get("event_date_from") or "").strip()
    edt = (c.get("event_date_to") or "").strip()
    etime = (c.get("event_time") or "").strip()
    ldate = (c.get("log_date") or "").strip()
    ltime = (c.get("log_time") or "").strip()

    # Parse "event date: X to Y" if present
    ed_all = c.get("event_date") or ""
    if ed_all and not edf:
        parts = re.split(r"\s+to\s+", ed_all, maxsplit=1)
        edf = parts[0].strip()
        if len(parts) > 1:
            edt = parts[1].strip()

    if not ldate:
        ldate = datetime.now().strftime("%Y-%m-%d")
    if not ltime:
        ltime = datetime.now().strftime("%H:%M")

    cid = insert_and_id("""INSERT INTO combinations
        (title, body, chart_ref, event_date_from, event_date_to,
         event_time, log_date, log_time, research_id, observation_num, is_main)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, body, refs, edf, edt, etime, ldate, ltime,
         research_id, obs_num, is_main))

    for i, (lbl, val) in enumerate(c.get("slots", []), 1):
        if lbl or val:
            run("""INSERT INTO combination_slots
                   (combination_id, slot_num, label, value)
                   VALUES (?, ?, ?, ?)""", (cid, i, lbl, val))

    for i, (lvl, lord, dd) in enumerate(c.get("dasha", []), 1):
        if lvl or lord or dd:
            run("""INSERT INTO combination_dasha
                   (combination_id, level, lord, dasha_date)
                   VALUES (?, ?, ?, ?)""", (cid, lvl, lord, dd))

    # Link persons (either "persons" list or by name)
    pnames = c.get("persons") or []
    if isinstance(pnames, str):
        pnames = [x.strip() for x in pnames.split(",") if x.strip()]
    for pn in pnames:
        pid = ensure_person(pn)
        if pid:
            run("""INSERT OR IGNORE INTO combination_people
                   (combination_id, person_id) VALUES (?, ?)""", (cid, pid))
    return cid


def save_research_dict(r):
    event = (r.get("event") or "").strip()
    edf = (r.get("event_date_from") or "").strip()
    edt = (r.get("event_date_to") or "").strip()
    etime = (r.get("event_time") or "").strip()

    ed_all = r.get("event_date") or ""
    if ed_all and not edf:
        parts = re.split(r"\s+to\s+", ed_all, maxsplit=1)
        edf = parts[0].strip()
        if len(parts) > 1:
            edt = parts[1].strip()

    rid = insert_and_id("""INSERT INTO research
        (event, event_date_from, event_date_to, event_time)
        VALUES (?, ?, ?, ?)""", (event, edf, edt, etime))

    pnames = r.get("persons") or []
    if isinstance(pnames, str):
        pnames = [x.strip() for x in pnames.split(",") if x.strip()]
    for pn in pnames:
        pid = ensure_person(pn)
        if pid:
            run("""INSERT OR IGNORE INTO research_people
                   (research_id, person_id) VALUES (?, ?)""", (rid, pid))

    for i, obs in enumerate(r.get("observations", []), 1):
        save_combination_dict(obs, research_id=rid, obs_num=i,
                               is_main=(1 if i == 1 else 0))
    return rid


# ============================================================
# ROUTES
# ============================================================
@bp.route("/data")
def data_home():
    h = '<div class="top-bar"><h2>Import / Export</h2>' + nav("/") + '</div>'

    # Paste importer
    h += '<div class="card">'
    h += '<p class="card-title">Paste Import</p>'
    h += '<p class="muted">Paste your data below. Format: person / combination / research / observation blocks. '
    h += 'Fields as <code>key: value</code>, slots and dasha as indented <code>label - value</code>.</p>'
    h += '<form method="post" action="/data/parse">'
    h += '<textarea name="paste" rows="16" placeholder="person&#10;name: Test Person&#10;dob: 1990-08-14&#10;..."></textarea>'
    h += '<div style="margin-top:14px;">'
    h += '<button class="btn" type="submit">PARSE &amp; PREVIEW</button>'
    h += '</div></form></div>'

    # Export buttons
    h += '<div class="card">'
    h += '<p class="card-title">Export</p>'
    h += '<p class="muted">Download all your data in the chosen format.</p>'
    h += '<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">'
    h += '<a class="btn" href="/data/export/json">&#128229; JSON</a>'
    h += '<a class="btn btn-secondary" href="/data/export/csv">&#128229; CSV (ZIP)</a>'
    h += '</div></div>'

    # Import JSON
    h += '<div class="card">'
    h += '<p class="card-title">Import JSON File</p>'
    h += '<p class="muted">Upload a previously exported JSON file. Data will be merged (duplicates skipped by name).</p>'
    h += '<form method="post" action="/data/import_json" enctype="multipart/form-data">'
    h += '<input type="file" name="file" accept=".json" style="margin-top:10px;">'
    h += '<div style="margin-top:14px;">'
    h += '<button class="btn" type="submit">UPLOAD &amp; IMPORT</button>'
    h += '</div></form></div>'

    return page(h)


@bp.route("/data/parse", methods=["POST"])
def data_parse():
    paste = request.form.get("paste", "")
    parsed = parse_paste(paste)

    # Store parsed data in a hidden field
    payload = json.dumps(parsed)

    # Preview
    counts = {
        "people": len(parsed["people"]),
        "combinations": len(parsed["combinations"]),
        "researches": len(parsed["researches"]),
        "observations": sum(len(r.get("observations", [])) for r in parsed["researches"]),
    }

    h = '<div class="top-bar"><h2>Preview</h2>' + nav("/data") + '</div>'

    h += '<div class="card">'
    h += '<p class="card-title">Parsed Summary</p>'
    h += '<div class="row"><b>People</b> %d</div>' % counts["people"]
    h += '<div class="row"><b>Independent combinations</b> %d</div>' % counts["combinations"]
    h += '<div class="row"><b>Research</b> %d</div>' % counts["researches"]
    h += '<div class="row"><b>Observations</b> %d</div>' % counts["observations"]
    h += '</div>'

    if counts["people"]:
        h += '<div class="card"><p class="card-title">People</p>'
        for p in parsed["people"]:
            h += '<div class="row">&#128100; <b>%s</b> &mdash; %s %s</div>' % (
                p.get("name", ""), p.get("dob", ""), p.get("location", ""))
        h += '</div>'

    if counts["combinations"]:
        h += '<div class="card"><p class="card-title">Combinations</p>'
        for c in parsed["combinations"]:
            h += '<div class="row">&#128279; <b>%s</b> &mdash; %d slots</div>' % (
                c.get("title", ""), len(c.get("slots", [])))
        h += '</div>'

    if counts["researches"]:
        h += '<div class="card"><p class="card-title">Research</p>'
        for r in parsed["researches"]:
            h += '<div class="row">&#128221; <b>%s</b> &mdash; %d observations</div>' % (
                r.get("event", ""), len(r.get("observations", [])))
        h += '</div>'

    h += '<form method="post" action="/data/save_parsed">'
    h += '<input type="hidden" name="payload" value="%s">' % _esc_attr(payload)
    h += '<button class="btn" type="submit">CONFIRM &amp; SAVE</button> '
    h += '<a class="btn btn-secondary" href="/data">&#8592; BACK TO EDIT</a>'
    h += '</form>'

    return page(h)


def _esc_attr(s):
    """Escape for HTML attribute."""
    return (s.replace("&", "&amp;")
             .replace('"', "&quot;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


@bp.route("/data/save_parsed", methods=["POST"])
def data_save_parsed():
    payload = request.form.get("payload", "{}")
    try:
        parsed = json.loads(payload)
    except Exception as e:
        return page("<div class='empty'>Bad payload: %s</div>" % e)

    # Save people first
    for p in parsed.get("people", []):
        try:
            save_person_dict(p)
        except Exception as e:
            print("person error:", e)

    # Save independent combinations
    for c in parsed.get("combinations", []):
        try:
            save_combination_dict(c)
        except Exception as e:
            print("combination error:", e)

    # Save researches with observations
    for r in parsed.get("researches", []):
        try:
            save_research_dict(r)
        except Exception as e:
            print("research error:", e)

    return redirect("/data/done")


@bp.route("/data/done")
def data_done():
    h = '<div class="top-bar"><h2>Import complete</h2>' + nav("/data") + '</div>'
    h += '<div class="card"><p>All data saved. Check People, Combos, and Research pages.</p></div>'
    h += '<a class="btn" href="/">&#127968; Home</a>'
    return page(h)


# ============================================================
# EXPORT
# ============================================================
def fetch_all():
    data = {}
    data["people"] = q("""SELECT id, name, birth_date, birth_time, birth_place,
                          manual_coords, broader_tags, multiple_tags, notes
                          FROM people ORDER BY id""")
    data["research"] = q("""SELECT id, event, event_date_from, event_date_to,
                            event_time, created_at FROM research ORDER BY id""")
    data["research_people"] = q("SELECT research_id, person_id FROM research_people")
    data["combinations"] = q("""SELECT id, title, body, chart_ref,
                                event_date_from, event_date_to, event_time,
                                log_date, log_time, research_id,
                                observation_num, is_main, created_at
                                FROM combinations ORDER BY id""")
    data["combination_slots"] = q("""SELECT combination_id, slot_num, label, value
                                     FROM combination_slots ORDER BY id""")
    data["combination_dasha"] = q("""SELECT combination_id, level, lord, dasha_date
                                     FROM combination_dasha ORDER BY id""")
    data["combination_people"] = q("SELECT combination_id, person_id FROM combination_people")
    return data


@bp.route("/data/export/json")
def export_json():
    data = fetch_all()
    # convert tuples to lists for JSON
    out = {}
    for k, rows in data.items():
        out[k] = [list(r) for r in rows]
    out["_exported_at"] = datetime.now().isoformat()
    out["_version"] = "1.0"
    s = json.dumps(out, indent=2, ensure_ascii=False, default=str)
    filename = "astrokarmapath_%s.json" % datetime.now().strftime("%Y%m%d_%H%M")
    return Response(s, mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=" + filename})


@bp.route("/data/export/csv")
def export_csv():
    data = fetch_all()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, rows in data.items():
            csv_buf = io.StringIO()
            w = csv.writer(csv_buf)
            if name == "people":
                w.writerow(["S.No", "Name", "DOB", "TOB", "Location",
                            "Manual Coords", "Tags", "Short Tags", "Notes"])
                for r in rows:
                    w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]])
            elif name == "research":
                w.writerow(["S.No", "Event", "Date From", "Date To", "Time", "Created"])
                for r in rows:
                    w.writerow(list(r))
            elif name == "combinations":
                w.writerow(["S.No", "Title", "Body", "Refs",
                            "Event Date From", "Event Date To", "Event Time",
                            "Log Date", "Log Time",
                            "Research S.No", "Obs Num", "Is Main", "Created"])
                for r in rows:
                    w.writerow(list(r))
            elif name == "combination_slots":
                w.writerow(["Combination S.No", "Slot Num", "Label", "Value"])
                for r in rows:
                    w.writerow(list(r))
            elif name == "combination_dasha":
                w.writerow(["Combination S.No", "Level", "Lord", "Date"])
                for r in rows:
                    w.writerow(list(r))
            elif name == "research_people":
                w.writerow(["Research S.No", "Person S.No"])
                for r in rows:
                    w.writerow(list(r))
            elif name == "combination_people":
                w.writerow(["Combination S.No", "Person S.No"])
                for r in rows:
                    w.writerow(list(r))
            z.writestr(name + ".csv", csv_buf.getvalue())
    buf.seek(0)
    filename = "astrokarmapath_%s.zip" % datetime.now().strftime("%Y%m%d_%H%M")
    return send_file(buf, mimetype="application/zip",
                     as_attachment=True, download_name=filename)


# ============================================================
# IMPORT JSON
# ============================================================
@bp.route("/data/import_json", methods=["POST"])
def import_json():
    f = request.files.get("file")
    if not f:
        return page("<div class='empty'>No file uploaded.</div>")
    try:
        raw = f.read().decode("utf-8")
        data = json.loads(raw)
    except Exception as e:
        return page("<div class='empty'>Cannot read file: %s</div>" % e)

    people_map = {}
    for row in data.get("people", []):
        # row: [id, name, dob, tob, loc, man, tags, stags, notes]
        try:
            pid = save_person_dict({
                "name": row[1], "dob": row[2] or "", "tob": row[3] or "",
                "location": row[4] or "", "manual_coords": row[5] or "",
                "tags": row[6] or "", "short_tags": row[7] or "",
                "notes": row[8] or "",
            })
            if pid:
                people_map[row[0]] = pid
        except Exception as e:
            print("import person error:", e)

    # Researches
    research_map = {}
    for row in data.get("research", []):
        try:
            rid = insert_and_id("""INSERT INTO research
                (event, event_date_from, event_date_to, event_time)
                VALUES (?, ?, ?, ?)""",
                (row[1], row[2], row[3], row[4]))
            research_map[row[0]] = rid
        except Exception as e:
            print("import research error:", e)

    for row in data.get("research_people", []):
        if row[0] in research_map and row[1] in people_map:
            try:
                run("INSERT OR IGNORE INTO research_people (research_id, person_id) VALUES (?, ?)",
                    (research_map[row[0]], people_map[row[1]]))
            except Exception:
                pass

    # Combinations
    combo_map = {}
    for row in data.get("combinations", []):
        try:
            rid_old = row[9]
            rid_new = research_map.get(rid_old) if rid_old else None
            cid = insert_and_id("""INSERT INTO combinations
                (title, body, chart_ref, event_date_from, event_date_to,
                 event_time, log_date, log_time, research_id, observation_num, is_main)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (row[1], row[2], row[3], row[4], row[5], row[6],
                 row[7], row[8], rid_new, row[10], row[11]))
            combo_map[row[0]] = cid
        except Exception as e:
            print("import combination error:", e)

    for row in data.get("combination_slots", []):
        if row[0] in combo_map:
            try:
                run("""INSERT INTO combination_slots
                       (combination_id, slot_num, label, value)
                       VALUES (?, ?, ?, ?)""",
                    (combo_map[row[0]], row[1], row[2], row[3]))
            except Exception:
                pass

    for row in data.get("combination_dasha", []):
        if row[0] in combo_map:
            try:
                run("""INSERT INTO combination_dasha
                       (combination_id, level, lord, dasha_date)
                       VALUES (?, ?, ?, ?)""",
                    (combo_map[row[0]], row[1], row[2], row[3]))
            except Exception:
                pass

    for row in data.get("combination_people", []):
        if row[0] in combo_map and row[1] in people_map:
            try:
                run("INSERT OR IGNORE INTO combination_people (combination_id, person_id) VALUES (?, ?)",
                    (combo_map[row[0]], people_map[row[1]]))
            except Exception:
                pass

    return redirect("/data/done")


# ============================================================
# GITHUB EXPORT / IMPORT
# ============================================================
import base64
import urllib.request
import urllib.error


def _github_env():
    user  = os.environ.get("GITHUB_USER", "").strip()
    repo  = os.environ.get("GITHUB_REPO", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    return user, repo, token


@bp.route("/data/export/github", methods=["GET", "POST"])
def export_github():
    user, repo, token = _github_env()
    if not (user and repo and token):
        return page("<div class='empty'>GitHub credentials not configured. "
                    "Set GITHUB_USER, GITHUB_REPO, GITHUB_TOKEN on the server.</div>")

    # Build payload
    data = fetch_all()
    out = {}
    for k, rows in data.items():
        out[k] = [list(r) for r in rows]
    out["_exported_at"] = datetime.now().isoformat()
    out["_version"] = "1.0"
    payload = json.dumps(out, indent=2, ensure_ascii=False, default=str)

    filename = "backups/%s.json" % datetime.now().strftime("%Y-%m-%d_%H-%M")
    api = "https://api.github.com/repos/%s/%s/contents/%s" % (user, repo, filename)

    # Check if file exists (to get SHA)
    sha = None
    try:
        req = urllib.request.Request(api, headers={
            "Authorization": "token " + token,
            "Accept": "application/vnd.github+json",
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            sha = json.loads(r.read()).get("sha")
    except Exception:
        pass

    body = {
        "message": "Backup " + datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": base64.b64encode(payload.encode("utf-8")).decode(),
    }
    if sha:
        body["sha"] = sha

    try:
        req = urllib.request.Request(api, method="PUT",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": "token " + token,
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
            })
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = r.status in (200, 201)
    except Exception as e:
        return page("<div class='empty'>GitHub export failed: %s</div>" % e)

    h = '<div class="top-bar"><h2>GitHub Export</h2>' + nav("/data") + '</div>'
    if ok:
        h += '<div class="card"><p class="card-title">&#10003; Exported</p>'
        h += '<p class="muted">File: %s</p>' % filename
        h += '<p class="muted">Check: https://github.com/%s/%s</p>' % (user, repo)
        h += '</div>'
    else:
        h += '<div class="card"><p>Export may have failed. Check the repo.</p></div>'
    h += '<a class="btn" href="/data">&#8592; Back to Data</a>'
    return page(h)


@bp.route("/data/import/github")
def import_github_list():
    user, repo, token = _github_env()
    if not (user and repo and token):
        return page("<div class='empty'>GitHub credentials not configured.</div>")

    api = "https://api.github.com/repos/%s/%s/contents/backups" % (user, repo)
    try:
        req = urllib.request.Request(api, headers={
            "Authorization": "token " + token,
            "Accept": "application/vnd.github+json",
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            items = json.loads(r.read())
    except Exception as e:
        return page("<div class='empty'>Cannot list backups: %s</div>" % e)

    files = [i for i in items if i.get("name", "").endswith(".json")]
    files.sort(key=lambda x: x["name"], reverse=True)

    h = '<div class="top-bar"><h2>Import from GitHub</h2>' + nav("/data") + '</div>'
    if not files:
        h += '<div class="empty">No backup files found.</div>'
    else:
        h += '<div class="card"><p class="card-title">Pick a backup</p>'
        for f in files[:20]:
            h += '<div class="picker-row"><div class="nm">%s</div>' % f["name"]
            h += '<div class="ac"><a class="btn btn-sm" href="/data/import/github/%s">IMPORT</a></div></div>' % f["name"]
        h += '</div>'
    return page(h)


@bp.route("/data/import/github/<path:name>")
def import_github_file(name):
    user, repo, token = _github_env()
    if not (user and repo and token):
        return page("<div class='empty'>GitHub credentials not configured.</div>")

    api = "https://api.github.com/repos/%s/%s/contents/backups/%s" % (user, repo, name)
    try:
        req = urllib.request.Request(api, headers={
            "Authorization": "token " + token,
            "Accept": "application/vnd.github+json",
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            item = json.loads(r.read())
        content = base64.b64decode(item["content"]).decode("utf-8")
        data = json.loads(content)
    except Exception as e:
        return page("<div class='empty'>Cannot read file: %s</div>" % e)

    # Reuse the same import logic from JSON import
    people_map = {}
    for row in data.get("people", []):
        try:
            pid = save_person_dict({
                "name": row[1], "dob": row[2] or "", "tob": row[3] or "",
                "location": row[4] or "", "manual_coords": row[5] or "",
                "tags": row[6] or "", "short_tags": row[7] or "",
                "notes": row[8] or "",
            })
            if pid:
                people_map[row[0]] = pid
        except Exception as e:
            print("person err:", e)

    research_map = {}
    for row in data.get("research", []):
        try:
            rid = insert_and_id("""INSERT INTO research
                (event, event_date_from, event_date_to, event_time)
                VALUES (?, ?, ?, ?)""",
                (row[1], row[2], row[3], row[4]))
            research_map[row[0]] = rid
        except Exception as e:
            print("res err:", e)

    for row in data.get("research_people", []):
        if row[0] in research_map and row[1] in people_map:
            try:
                run("INSERT OR IGNORE INTO research_people (research_id, person_id) VALUES (?, ?)",
                    (research_map[row[0]], people_map[row[1]]))
            except Exception:
                pass

    combo_map = {}
    for row in data.get("combinations", []):
        try:
            rid_old = row[9]
            rid_new = research_map.get(rid_old) if rid_old else None
            cid = insert_and_id("""INSERT INTO combinations
                (title, body, chart_ref, event_date_from, event_date_to,
                 event_time, log_date, log_time, research_id, observation_num, is_main)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (row[1], row[2], row[3], row[4], row[5], row[6],
                 row[7], row[8], rid_new, row[10], row[11]))
            combo_map[row[0]] = cid
        except Exception as e:
            print("combo err:", e)

    for row in data.get("combination_slots", []):
        if row[0] in combo_map:
            try:
                run("""INSERT INTO combination_slots
                       (combination_id, slot_num, label, value)
                       VALUES (?, ?, ?, ?)""",
                    (combo_map[row[0]], row[1], row[2], row[3]))
            except Exception:
                pass

    return redirect("/data/done")
