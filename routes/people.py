# -*- coding: utf-8 -*-
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
