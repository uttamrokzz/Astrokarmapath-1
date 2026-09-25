# -*- coding: utf-8 -*-
"""
AstroKarmaPath - Round 1
Updates People page with live autocomplete search + A-Z letters + BACK/HOME nav.
Run once. Overwrites existing files.
"""
import os

BASE = None
for c in ["/storage/emulated/0/astrokarmapath",
          "/sdcard/astrokarmapath",
          os.path.join(os.path.expanduser("~"), "astrokarmapath")]:
    if os.path.isdir(c):
        BASE = c
        break
if BASE is None:
    print("ERROR: project folder not found. Run the full setup first.")
    raise SystemExit(1)

print("Project folder:", BASE)
print()

FILES = {}

# ============================================================
# core.py  (updated layout: nav + letters CSS)
# ============================================================
FILES["core.py"] = r'''# -*- coding: utf-8 -*-
import turso_serverless as turso
from config import URL, TOKEN


def conn():
    return turso.connect(URL, auth_token=TOKEN)


def q(sql, args=()):
    c = conn(); cur = c.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()
    c.close()
    return rows


def run(sql, args=()):
    c = conn(); cur = c.cursor()
    cur.execute(sql, args)
    c.commit()
    c.close()


def insert_and_id(sql, args=()):
    c = conn(); cur = c.cursor()
    cur.execute(sql, args)
    c.commit()
    cur.execute("SELECT last_insert_rowid()")
    rid = cur.fetchone()[0]
    c.close()
    return rid


LAYOUT = """<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AstroKarmaPath</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, Roboto, sans-serif; margin: 0;
         background: #f4f5f7; color: #222; padding-bottom: 30px; }
  header { background: #5e35b1; color: #fff; padding: 14px 16px;
           position: sticky; top: 0; z-index: 10;
           display: flex; align-items: center; justify-content: space-between; }
  header .brand { font-weight: 600; font-size: 16px; color: #fff;
                  text-decoration: none; }
  header .brand .inf { font-size: 22px; margin-left: 4px; }
  header nav a { color: #fff; text-decoration: none; margin-left: 10px;
                 font-size: 12px; opacity: 0.9; }
  main { padding: 14px; max-width: 780px; margin: 0 auto; }
  .title { text-align: center; margin: 30px 0; }
  .title h1 { font-size: 28px; color: #5e35b1; margin: 0; letter-spacing: -0.5px; }
  .title p  { color: #888; font-size: 13px; margin: 8px 0 0;
              letter-spacing: 2px; text-transform: uppercase; }
  .menu a { display: block; background: #fff; color: #333;
            text-decoration: none; padding: 18px 20px; border-radius: 12px;
            margin-bottom: 12px; font-size: 16px; font-weight: 500;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            border-left: 4px solid #5e35b1; }
  .menu a .arrow { float: right; color: #b0b0b0; }
  .btn { background: #5e35b1; color: #fff; border: none; padding: 11px 16px;
         border-radius: 8px; font-size: 14px; cursor: pointer;
         text-decoration: none; display: inline-block; }
  .btn-secondary { background: #e8eaf6; color: #4527a0; }
  .btn-danger { background: #c62828; color: #fff; }
  .top-bar { display: flex; justify-content: space-between;
             align-items: center; margin-bottom: 14px;
             gap: 8px; flex-wrap: wrap; }
  .top-bar h2 { margin: 0; font-size: 20px; }
  .top-bar .actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .card { background: #fff; border-radius: 12px; padding: 14px;
          margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);
          position: relative; }
  .card .name { font-size: 17px; font-weight: 600; margin: 0 0 8px; }
  .card .row { font-size: 14px; color: #555; margin: 3px 0; }
  .card .row b { color: #333; font-weight: 500;
                 display: inline-block; min-width: 50px; }
  .card .edit { position: absolute; top: 12px; right: 12px;
                color: #5e35b1; text-decoration: none; font-size: 18px; }
  .tags { margin-top: 10px; }
  .tags .pill { display: inline-block; background: #ede7f6; color: #4527a0;
                padding: 4px 10px; border-radius: 12px; font-size: 12px;
                margin: 3px 4px 0 0; }
  .tags .pill.multi { background: #e0f2f1; color: #00695c; }
  .tags .label { display: block; font-size: 11px; color: #999;
                 text-transform: uppercase; letter-spacing: 1px;
                 margin-top: 8px; }
  form label { font-size: 13px; color: #555; display: block;
               margin-top: 12px; font-weight: 500; }
  form input[type=text], form input[type=date], form input[type=time],
  form textarea, form select {
    width: 100%; padding: 11px; font-size: 15px;
    border: 1px solid #ccc; border-radius: 8px; margin-top: 4px;
    background: #fff; color: #222; }
  form .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .muted { color: #999; font-size: 13px; }
  .empty { text-align: center; color: #999; padding: 40px 10px; }
  .search-bar { display: flex; gap: 8px; margin-bottom: 12px; }
  .search-bar input { flex: 1; padding: 12px; font-size: 15px;
                      border: 1px solid #ccc; border-radius: 8px; }
  .letters { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 14px; }
  .letter { background: #fff; border: 1px solid #ddd; border-radius: 6px;
            padding: 6px 10px; font-size: 14px; cursor: pointer;
            color: #4527a0; font-weight: 600; min-width: 32px;
            text-align: center; }
  .letter:active { background: #ede7f6; }
  .section-label { font-size: 12px; color: #5e35b1; font-weight: 600;
                   text-transform: uppercase; letter-spacing: 1px;
                   margin: 18px 0 6px; }
  .result-box { background: #fff8e1; border-left: 4px solid #ffb300;
                padding: 12px; border-radius: 8px; margin: 10px 0; }
  .result-box b { color: #ef6c00; font-size: 12px;
                  text-transform: uppercase; letter-spacing: 1px; }
  .result-box p { margin: 6px 0 0; font-size: 15px; }
  .slot-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
              margin-top: 6px; }
  .slot-row input { padding: 10px; font-size: 14px; border: 1px solid #ccc;
                    border-radius: 8px; }
  .dasha-row { display: grid; grid-template-columns: 60px 1fr 1fr;
               gap: 6px; margin-top: 6px; }
  .dasha-row input { padding: 9px; font-size: 13px; border: 1px solid #ccc;
                     border-radius: 8px; }
</style>
</head><body>
<header>
  <a class="brand" href="/">AstroKarmaPath <span class="inf">&infin;</span></a>
  <nav>
    <a href="/people">People</a>
    <a href="/combinations">Combos</a>
    <a href="/research">Research</a>
    <a href="/search">Search</a>
  </nav>
</header>
<main>__BODY__</main>
</body></html>"""


def page(body):
    return LAYOUT.replace("__BODY__", body)
'''

# ============================================================
# routes/api.py  (autocomplete endpoint)
# ============================================================
FILES["routes/api.py"] = r'''# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from core import q

bp = Blueprint("api", __name__)


@bp.route("/api/people/search")
def api_people_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    like = term + "%"
    like_any = "%" + term + "%"
    rows = q("""SELECT id, name, birth_place, birth_date FROM people
                WHERE name LIKE ? OR birth_place LIKE ?
                   OR name LIKE ?
                ORDER BY name LIMIT 25""", (like, like_any, like_any))
    return jsonify([
        {"id": r[0], "name": r[1], "place": r[2] or "", "dob": r[3] or ""}
        for r in rows
    ])
'''

# ============================================================
# routes/people.py  (rewritten)
# ============================================================
FILES["routes/people.py"] = r'''# -*- coding: utf-8 -*-
from flask import Blueprint, request, redirect
from core import q, run, insert_and_id, page

bp = Blueprint("people", __name__)


def person_card(r):
    pid, name, dob, tob, loc, tags, short_tags, cc, rc = r
    h = "<div class='card'>"
    h += "<a class='edit' href='/person/%d/edit'>&#9998;</a>" % pid
    h += ("<p class='name'><a href='/person/%d' "
          "style='color:inherit;text-decoration:none;'>%s</a></p>") % (pid, name)
    if dob: h += "<div class='row'><b>DOB</b> %s</div>" % dob
    if tob: h += "<div class='row'><b>TOB</b> %s</div>" % tob
    if loc: h += "<div class='row'><b>Loc</b> %s</div>" % loc
    if tags or short_tags:
        h += "<div class='tags'>"
        if tags:
            h += "<span class='label'>Tags</span>"
            for t in [x.strip() for x in tags.split(",") if x.strip()]:
                h += "<span class='pill'>%s</span>" % t
        if short_tags:
            h += "<span class='label'>Short tags</span>"
            for t in [x.strip() for x in short_tags.split(",") if x.strip()]:
                h += "<span class='pill multi'>%s</span>" % t
        h += "</div>"
    h += "<div class='row' style='margin-top:10px; color:#888; font-size:13px;'>"
    h += "&#128279; %d combos &nbsp;&middot;&nbsp; &#128221; %d research" % (cc, rc)
    h += "</div></div>"
    return h


# ---------------------------------------------------------------
# LIST
# ---------------------------------------------------------------
@bp.route("/people")
def list_people():
    rows = q("""
        SELECT p.id, p.name, p.birth_date, p.birth_time, p.birth_place,
               p.broader_tags, p.multiple_tags,
               (SELECT COUNT(*) FROM combination_people cp WHERE cp.person_id = p.id),
               (SELECT COUNT(*) FROM research r WHERE r.person_id = p.id)
        FROM people p ORDER BY p.name
    """)
    h = """<div class="top-bar"><h2>People</h2><div class="actions">
        <a class="btn btn-secondary" href="/people/search">Search Name / Location</a>
        <a class="btn" href="/person/new">+ NEW</a></div></div>"""
    if not rows:
        return page(h + "<div class='empty'>No people yet.<br>Tap + NEW.</div>")
    for r in rows:
        h += person_card(r)
    return page(h)


# ---------------------------------------------------------------
# SEARCH  (Google-style live autocomplete + A-Z letters)
# ---------------------------------------------------------------
@bp.route("/people/search")
def search_people():
    return page("""
      <div class="top-bar">
        <h2>Search People</h2>
        <div class="actions">
          <a class="btn btn-secondary" href="/people">&larr; Back</a>
          <a class="btn btn-secondary" href="/">&#127968; Home</a>
        </div>
      </div>

      <div class="search-bar">
        <input type="text" id="q"
               placeholder="Type a name or location..."
               autocomplete="off" autofocus>
      </div>

      <div class="letters" id="letters"></div>

      <div id="results"></div>

      <script>
      (function(){
        var input   = document.getElementById('q');
        var results = document.getElementById('results');
        var letters = document.getElementById('letters');
        var timer   = null;

        function card(p) {
          var h = "<div class='card'>";
          h += "<a class='edit' href='/person/" + p.id + "/edit'>&#9998;</a>";
          h += "<p class='name'><a href='/person/" + p.id +
               "' style='color:inherit;text-decoration:none;'>" + p.name + "</a></p>";
          if (p.dob)   h += "<div class='row'><b>DOB</b> " + p.dob + "</div>";
          if (p.place) h += "<div class='row'><b>Loc</b> " + p.place + "</div>";
          h += "</div>";
          return h;
        }

        function render(items) {
          if (!items || !items.length) {
            results.innerHTML = "<div class='empty'>No matches.</div>";
            return;
          }
          var h = "<p class='muted'>" + items.length + " match(es)</p>";
          for (var i = 0; i < items.length; i++) h += card(items[i]);
          results.innerHTML = h;
        }

        function search(term) {
          if (!term) { results.innerHTML = ""; return; }
          fetch('/api/people/search?q=' + encodeURIComponent(term))
            .then(function(r){ return r.json(); })
            .then(render)
            .catch(function(){
              results.innerHTML = "<div class='empty'>Search error.</div>";
            });
        }

        input.addEventListener('input', function(){
          clearTimeout(timer);
          var v = input.value.trim();
          timer = setTimeout(function(){ search(v); }, 200);
        });

        // A-Z buttons
        var alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
        var html = '';
        for (var i = 0; i < alphabet.length; i++) {
          html += "<button class='letter' data-l='" + alphabet[i] + "'>" +
                  alphabet[i] + "</button>";
        }
        letters.innerHTML = html;

        letters.addEventListener('click', function(e){
          var L = e.target.getAttribute('data-l');
          if (!L) return;
          input.value = L;
          search(L);
        });
      })();
      </script>
    """)


# ---------------------------------------------------------------
# DETAIL
# ---------------------------------------------------------------
@bp.route("/person/<int:pid>")
def person_detail(pid):
    rows = q("""SELECT id, name, birth_date, birth_time, birth_place,
                       broader_tags, multiple_tags, notes
                FROM people WHERE id=?""", (pid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    pid, name, dob, tob, loc, tags, short_tags, notes = rows[0]

    combos = q("""SELECT c.id, c.title, c.result
                  FROM combinations c
                  JOIN combination_people cp ON cp.combination_id = c.id
                  WHERE cp.person_id = ?
                  ORDER BY c.id DESC""", (pid,))
    research = q("""SELECT id, main_event, result
                    FROM research WHERE person_id = ? ORDER BY id DESC""", (pid,))

    h = "<div class='top-bar'><h2>%s</h2>" % name
    h += """<div class="actions">
      <a class="btn btn-secondary" href="/people">&larr; Back</a>
      <a class="btn btn-secondary" href="/">&#127968; Home</a>
    </div></div>"""

    h += "<div class='card'>"
    if dob: h += "<div class='row'><b>DOB</b> %s</div>" % dob
    if tob: h += "<div class='row'><b>TOB</b> %s</div>" % tob
    if loc: h += "<div class='row'><b>Loc</b> %s</div>" % loc
    if tags:
        h += "<span class='label' style='font-size:11px; color:#999; text-transform:uppercase;'>Tags</span>"
        for t in [x.strip() for x in tags.split(",") if x.strip()]:
            h += "<span class='tags'><span class='pill'>%s</span></span>" % t
    if short_tags:
        h += "<span class='label' style='font-size:11px; color:#999; text-transform:uppercase; display:block; margin-top:8px;'>Short tags</span>"
        for t in [x.strip() for x in short_tags.split(",") if x.strip()]:
            h += "<span class='tags'><span class='pill multi'>%s</span></span>" % t
    if notes:
        h += "<div class='row' style='margin-top:10px;'><b>Notes</b> %s</div>" % notes
    h += "</div>"

    h += "<div class='card'><span class='section-label'>Linked Combinations (%d)</span>" % len(combos)
    if combos:
        for cid, title, result in combos:
            h += "<div class='row'>&bull; <a href='/combination/%d'>%s</a>" % (cid, title or "(untitled)")
            if result: h += " &mdash; <span class='muted'>%s</span>" % result
            h += "</div>"
    else:
        h += "<p class='muted'>None</p>"
    h += "<div style='margin-top:10px;'><a class='btn btn-secondary' href='/person/%d/link_combinations'>+ Link Combination</a></div>" % pid
    h += "</div>"

    h += "<div class='card'><span class='section-label'>Linked Research (%d)</span>" % len(research)
    if research:
        for rid, ev, result in research:
            h += "<div class='row'>&bull; <a href='/research/%d'>%s</a>" % (rid, ev or "(event)")
            if result: h += " &mdash; <span class='muted'>%s</span>" % result
            h += "</div>"
    else:
        h += "<p class='muted'>None</p>"
    h += "<div style='margin-top:10px;'><a class='btn btn-secondary' href='/person/%d/link_research'>+ Link Research</a></div>" % pid
    h += "</div>"

    h += """<div style="margin-top:14px;">
      <a class="btn" href="/person/%d/edit">&#9998; Edit</a>
      <form method="post" action="/person/%d/delete" style="display:inline;"
            onsubmit="return confirm('Delete this person?');">
        <button class="btn btn-danger" type="submit">&#128465; Delete</button>
      </form>
    </div>""" % (pid, pid)

    return page(h)


@bp.route("/person/<int:pid>/link_combinations")
def link_combinations(pid):
    return page("""<div class="top-bar"><h2>Link Combination</h2>
      <a class="btn btn-secondary" href="/person/%d">&larr; Back</a></div>
      <div class="empty">Picker coming in Round 3.</div>""" % pid)


@bp.route("/person/<int:pid>/link_research")
def link_research(pid):
    return page("""<div class="top-bar"><h2>Link Research</h2>
      <a class="btn btn-secondary" href="/person/%d">&larr; Back</a></div>
      <div class="empty">Picker coming in Round 3.</div>""" % pid)


# ---------------------------------------------------------------
# ADD / EDIT
# ---------------------------------------------------------------
@bp.route("/person/new", methods=["GET", "POST"])
def person_new():
    if request.method == "POST":
        pid = save_person(None)
        return redirect("/person/%d" % pid)
    return page(person_form(None))


@bp.route("/person/<int:pid>/edit", methods=["GET", "POST"])
def person_edit(pid):
    rows = q("""SELECT id, name, birth_date, birth_time, birth_place,
                       broader_tags, multiple_tags, notes
                FROM people WHERE id=?""", (pid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    if request.method == "POST":
        save_person(pid)
        return redirect("/person/%d" % pid)
    return page(person_form(rows[0]))


@bp.route("/person/<int:pid>/delete", methods=["POST"])
def person_delete(pid):
    run("DELETE FROM person_tags WHERE person_id=?", (pid,))
    run("DELETE FROM combination_people WHERE person_id=?", (pid,))
    run("UPDATE research SET person_id=NULL WHERE person_id=?", (pid,))
    run("DELETE FROM people WHERE id=?", (pid,))
    return redirect("/people")


def save_person(pid):
    name   = request.form.get("name", "").strip()
    dob    = request.form.get("dob", "").strip()
    tob    = request.form.get("tob", "").strip()
    loc    = request.form.get("location", "").strip()
    manual = request.form.get("manual", "").strip()
    tags   = request.form.get("broader_tags", "").strip()
    stags  = request.form.get("multiple_tags", "").strip()
    notes  = request.form.get("notes", "").strip()
    place = loc
    if manual:
        place = (place + "  (" + manual + ")").strip() if place else manual

    if pid is None:
        return insert_and_id("""INSERT INTO people
            (name, birth_date, birth_time, birth_place,
             broader_tags, multiple_tags, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, dob, tob, place, tags, stags, notes))
    else:
        run("""UPDATE people SET name=?, birth_date=?, birth_time=?,
                 birth_place=?, broader_tags=?, multiple_tags=?, notes=?
               WHERE id=?""",
            (name, dob, tob, place, tags, stags, notes, pid))
        return pid


def person_form(row):
    if row is None:
        pid, name, dob, tob, place, tags, stags, notes = (None,) * 8
        heading = "NEW PERSON"
    else:
        pid, name, dob, tob, place, tags, stags, notes = row
        heading = "EDIT PERSON"

    action = "/person/%d/edit" % pid if pid else "/person/new"

    delete_block = ""
    if pid:
        delete_block = """
        <form method="post" action="/person/%d/delete"
              onsubmit="return confirm('Delete this person?');"
              style="margin-top:22px; text-align:right;">
          <button class="btn btn-danger" type="submit">Delete person</button>
        </form>""" % pid

    return """
      <div class="top-bar"><h2>%s</h2>
        <div class="actions">
          <a class="btn btn-secondary" href="%s">&larr; Back</a>
          <a class="btn btn-secondary" href="/">&#127968; Home</a>
        </div>
      </div>

      <div class="card"><form method="post" action="%s">
        <label>Name *</label>
        <input type="text" name="name" value="%s" required autofocus>

        <div class="row2">
          <div><label>DOB *</label>
            <input type="date" name="dob" value="%s" required></div>
          <div><label>TOB</label>
            <input type="time" name="tob" value="%s"></div>
        </div>

        <label>Location (City, Country)</label>
        <input type="text" name="location" value="%s"
               placeholder="Chennai, India">

        <label>Manual Coordinates (optional)</label>
        <input type="text" name="manual" placeholder="13.0827, 80.2707">

        <label>Tags <span class="muted">(Profession / Disease &mdash; comma separated)</span></label>
        <input type="text" name="broader_tags" value="%s"
               placeholder="cinema, sports">

        <label>Short tags <span class="muted">(Family art, Dealer, Family Catholic &mdash; comma separated)</span></label>
        <input type="text" name="multiple_tags" value="%s"
               placeholder="psycho movies, baseball">

        <label>Notes</label>
        <textarea name="notes" rows="2">%s</textarea>

        <div style="margin-top:20px;">
          <button class="btn" type="submit">Save</button>
          <a class="btn btn-secondary" href="%s">Cancel</a>
        </div>
      </form>%s</div>
    """ % (heading,
           "/person/%d" % pid if pid else "/people",
           action,
           name or "", dob or "", tob or "", place or "",
           tags or "", stags or "", notes or "",
           "/person/%d" % pid if pid else "/people",
           delete_block)
'''

# ============================================================
# app.py  (register api blueprint)
# ============================================================
FILES["app.py"] = r'''# -*- coding: utf-8 -*-
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from flask import Flask
from core import page
from routes import people, combinations, research, search, learning, api

app = Flask(__name__)


@app.route("/")
def home():
    return page("""
      <div class="title">
        <h1>AstroKarmaPath &infin;</h1>
        <p>Turso</p>
      </div>
      <div class="menu">
        <a href="/people">&#128100; View / Add People <span class="arrow">&rsaquo;</span></a>
        <a href="/combinations">&#128279; View / Add Combination <span class="arrow">&rsaquo;</span></a>
        <a href="/research">&#128221; Research Notes <span class="arrow">&rsaquo;</span></a>
        <a href="/search">&#128269; Search <span class="arrow">&rsaquo;</span></a>
        <a href="/learning">&#128218; Learning Database <span class="arrow">&rsaquo;</span></a>
      </div>
    """)


app.register_blueprint(people.bp)
app.register_blueprint(combinations.bp)
app.register_blueprint(research.bp)
app.register_blueprint(search.bp)
app.register_blueprint(learning.bp)
app.register_blueprint(api.bp)


if __name__ == "__main__":
    print("=" * 55)
    print("AstroKarmaPath is running.")
    print("Open in browser:  http://127.0.0.1:5000")
    print("=" * 55)
    app.run(host="127.0.0.1", port=5000, debug=False)
'''

# ============================================================
# Write files
# ============================================================
print("Writing files...")
print()
for rel, content in FILES.items():
    full = os.path.join(BASE, rel)
    parent = os.path.dirname(full)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("  wrote", rel)

print()
print("=" * 55)
print("ROUND 1 FILES UPDATED")
print("=" * 55)
print()
print("Next steps:")
print("1. Open and run:")
print("   " + os.path.join(BASE, "app.py"))
print("2. In browser open:  http://127.0.0.1:5000")
print("3. Go to People -> Search Name / Location")
print()
print("Files changed:")
for rel in FILES:
    print("  -", rel)