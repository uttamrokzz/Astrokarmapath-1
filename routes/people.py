# -*- coding: utf-8 -*-
from flask import Blueprint, request, redirect
from core import q, run, insert_and_id, page, nav

bp = Blueprint("people", __name__)


def person_card(r):
    pid, name, dob, tob, loc, tags, stags, cc, rc = r
    h = "<div class='card'>"
    h += "<a class='edit' href='/person/%d/edit'>&#9998;</a>" % pid
    h += "<p class='card-title'><a href='/person/%d'>%s</a></p>" % (pid, name)
    if dob: h += "<div class='row'><b>DOB</b> %s</div>" % dob
    if tob: h += "<div class='row'><b>TOB</b> %s</div>" % tob
    if loc: h += "<div class='row'><b>Loc</b> %s</div>" % loc
    if tags:
        h += "<span class='label'>Tags</span>"
        for t in [x.strip() for x in tags.split(",") if x.strip()]:
            h += "<span class='pill'>%s</span>" % t
    if stags:
        h += "<span class='label'>Short tags</span>"
        for t in [x.strip() for x in stags.split(",") if x.strip()]:
            h += "<span class='pill multi'>%s</span>" % t
    h += "<div class='row' style='margin-top:10px;color:#888;'>"
    h += "&#128279; %d combos &middot; &#128221; %d research</div>" % (cc, rc)
    h += "</div>"
    return h


@bp.route("/people")
def list_people():
    rows = q("""SELECT p.id, p.name, p.birth_date, p.birth_time, p.birth_place,
                p.broader_tags, p.multiple_tags,
                (SELECT COUNT(*) FROM combination_people cp WHERE cp.person_id=p.id),
                (SELECT COUNT(*) FROM research_people rp WHERE rp.person_id=p.id)
                FROM people p ORDER BY p.name""")
    h = '<div class="top-bar"><h2>People</h2><div class="actions">'
    h += '<a class="btn btn-secondary btn-sm" href="/people/search">Search</a>'
    h += '<a class="btn btn-sm" href="/person/new">+ NEW</a></div></div>'
    if not rows:
        return page(h + '<div class="empty">No people yet.</div>')
    for r in rows:
        h += person_card(r)
    return page(h)


@bp.route("/people/search")
def search_people():
    h = '<div class="top-bar"><h2>Search People</h2>' + nav("/people") + '</div>'
    h += '<div class="search-bar">'
    h += '<input type="text" class="ac-search" data-src="people" '
    h += 'placeholder="Type a name or location..." autocomplete="off" autofocus>'
    h += '</div>'
    h += '<div id="results"></div>'
    h += """<script>
    document.addEventListener('change', function(e){
      var inp = e.target;
      if (!inp.classList || !inp.classList.contains('ac-search')) return;
      var id = inp.getAttribute('data-picked-id');
      if (id) { window.location.href = '/person/' + id; }
    });
    </script>"""
    return page(h)


@bp.route("/person/new", methods=["GET", "POST"])
def person_new():
    if request.method == "POST":
        pid = save_person(None)
        return redirect("/person/%d" % pid)
    return page(person_form(None))


@bp.route("/person/<int:pid>")
def person_detail(pid):
    rows = q("""SELECT id, name, birth_date, birth_time, birth_place,
                broader_tags, multiple_tags, notes
                FROM people WHERE id=?""", (pid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    pid, name, dob, tob, loc, tags, stags, notes = rows[0]

    combos = q("""SELECT c.id, c.title FROM combinations c
                  JOIN combination_people cp ON cp.combination_id = c.id
                  WHERE cp.person_id = ? ORDER BY c.id DESC""", (pid,))
    research = q("""SELECT r.id, r.event FROM research r
                    JOIN research_people rp ON rp.research_id = r.id
                    WHERE rp.person_id = ? ORDER BY r.id DESC""", (pid,))

    h = '<div class="top-bar"><h2>%s</h2>' % name + nav("/people") + '</div>'

    h += "<div class='card'>"
    if dob: h += "<div class='row'><b>DOB</b> %s</div>" % dob
    if tob: h += "<div class='row'><b>TOB</b> %s</div>" % tob
    if loc: h += "<div class='row'><b>Loc</b> %s</div>" % loc
    if tags:
        h += "<span class='label'>Tags</span>"
        for t in [x.strip() for x in tags.split(",") if x.strip()]:
            h += "<span class='pill'>%s</span>" % t
    if stags:
        h += "<span class='label'>Short tags</span>"
        for t in [x.strip() for x in stags.split(",") if x.strip()]:
            h += "<span class='pill multi'>%s</span>" % t
    if notes:
        h += "<div class='row' style='margin-top:10px;'><b>Notes</b> %s</div>" % notes
    h += "</div>"

    h += "<div class='card'><span class='section-label'>Linked Combinations (%d)</span>" % len(combos)
    if combos:
        for cid, title in combos:
            h += "<div class='row'>&bull; <a href='/combination/%d'>%s</a></div>" % (cid, title or "")
    else:
        h += "<p class='muted'>None</p>"
    h += '<div style="margin-top:10px;"><a class="btn btn-secondary btn-sm" href="/person/%d/link_combo">+ LINK COMBINATION</a></div>' % pid
    h += "</div>"

    h += "<div class='card'><span class='section-label'>Linked Research (%d)</span>" % len(research)
    if research:
        for rid, ev in research:
            h += "<div class='row'>&bull; <a href='/research/%d'>%s</a></div>" % (rid, ev or "")
    else:
        h += "<p class='muted'>None</p>"
    h += '<div style="margin-top:10px;"><a class="btn btn-secondary btn-sm" href="/person/%d/link_research">+ LINK RESEARCH</a></div>' % pid
    h += "</div>"

    h += '<div style="margin-top:14px;">'
    h += '<a class="btn" href="/person/%d/edit">&#9998; EDIT</a> ' % pid
    h += '<form method="post" action="/person/%d/delete" style="display:inline;" onsubmit="return confirm(\'Delete?\');">' % pid
    h += '<button class="btn btn-danger" type="submit">&#128465; DLT</button></form></div>'
    return page(h)


@bp.route("/person/<int:pid>/edit", methods=["GET", "POST"])
def person_edit(pid):
    rows = q("""SELECT id, name, birth_date, birth_time, birth_place, manual_coords,
                broader_tags, multiple_tags, notes FROM people WHERE id=?""", (pid,))
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
    run("DELETE FROM research_people WHERE person_id=?", (pid,))
    run("DELETE FROM people WHERE id=?", (pid,))
    return redirect("/people")


def save_person(pid):
    name = request.form.get("name", "").strip()
    dob = request.form.get("dob", "").strip()
    tob = request.form.get("tob", "").strip()
    loc = request.form.get("location", "").strip()
    man = request.form.get("manual", "").strip()
    tags = request.form.get("broader_tags", "").strip()
    stags = request.form.get("multiple_tags", "").strip()
    notes = request.form.get("notes", "").strip()
    if pid is None:
        return insert_and_id("""INSERT INTO people
            (name, birth_date, birth_time, birth_place, manual_coords,
             broader_tags, multiple_tags, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, dob, tob, loc, man, tags, stags, notes))
    else:
        run("""UPDATE people SET name=?, birth_date=?, birth_time=?, birth_place=?,
               manual_coords=?, broader_tags=?, multiple_tags=?, notes=?
               WHERE id=?""",
            (name, dob, tob, loc, man, tags, stags, notes, pid))
        return pid


def person_form(row):
    if row is None:
        pid = None
        name = dob = tob = loc = man = tags = stags = notes = ""
        heading = "NEW PERSON"
    else:
        pid, name, dob, tob, loc, man, tags, stags, notes = row
        heading = "EDIT PERSON"
    action = "/person/%d/edit" % pid if pid else "/person/new"
    back = "/person/%d" % pid if pid else "/people"
    del_btn = ""
    if pid:
        del_btn = ('<form method="post" action="/person/%d/delete" style="display:inline;margin-left:6px;" '
                   'onsubmit="return confirm(\'Delete?\');">'
                   '<button class="btn btn-danger" type="submit">DLT</button></form>') % pid

    h = '<div class="top-bar"><h2>%s</h2>' % heading + nav(back) + '</div>'
    h += '<div class="card"><form method="post" action="%s">' % action
    h += '<label>Name *</label><input type="text" name="name" value="%s" required autofocus>' % (name or "")
    h += '<div class="row2">'
    h += '<div><label>DOB</label><input type="date" name="dob" value="%s"></div>' % (dob or "")
    h += '<div><label>TOB</label><input type="time" name="tob" value="%s"></div>' % (tob or "")
    h += '</div>'
    h += '<label>Location (City, Country)</label><input type="text" name="location" value="%s" placeholder="Chennai, India">' % (loc or "")
    h += '<label>Manual Coordinates</label><input type="text" name="manual" value="%s" placeholder="13.0827, 80.2707">' % (man or "")
    h += '<label>Tags</label><input type="text" name="broader_tags" value="%s" placeholder="cinema, sports">' % (tags or "")
    h += '<label>Short tags</label><input type="text" name="multiple_tags" value="%s" placeholder="psycho movies">' % (stags or "")
    h += '<label>Notes</label><textarea name="notes" rows="3">%s</textarea>' % (notes or "")
    h += '<div style="margin-top:20px;"><button class="btn" type="submit">SAVE</button> '
    h += '<a class="btn btn-secondary" href="%s">CANCEL</a>%s</div></form></div>' % (back, del_btn)
    return page(h)


@bp.route("/person/<int:pid>/link_combo")
def link_combo(pid):
    rows = q("""SELECT c.id, c.title FROM combinations c
                WHERE c.id NOT IN
                    (SELECT combination_id FROM combination_people WHERE person_id=?)
                ORDER BY c.id DESC LIMIT 100""", (pid,))
    h = '<div class="top-bar"><h2>Link Combination</h2>' + nav("/person/%d" % pid) + '</div>'
    h += '<div class="search-bar"><input type="text" class="ac-search" data-src="combinations" placeholder="Search combinations..." autocomplete="off"></div>'
    h += '<div id="list">'
    for cid, title in rows:
        h += "<div class='picker-row'><div class='nm'>%s</div>" % (title or "")
        h += "<div class='ac'><a class='btn btn-sm' href='/person/%d/link_combo/%d'>LINK</a></div></div>" % (pid, cid)
    if not rows:
        h += "<div class='empty'>No combinations to link.</div>"
    h += "</div>"
    h += """<script>
    document.addEventListener('change', function(e){
      var inp = e.target;
      if (!inp.classList || !inp.classList.contains('ac-search')) return;
      var id = inp.getAttribute('data-picked-id');
      if (id) { window.location.href = '/person/%d/link_combo/' + id; }
    });
    </script>""" % pid
    return page(h)


@bp.route("/person/<int:pid>/link_combo/<int:cid>")
def do_link_combo(pid, cid):
    run("INSERT OR IGNORE INTO combination_people (combination_id, person_id) VALUES (?, ?)",
        (cid, pid))
    return redirect("/person/%d" % pid)


@bp.route("/person/<int:pid>/link_research")
def link_research(pid):
    rows = q("""SELECT r.id, r.event FROM research r
                WHERE r.id NOT IN
                    (SELECT research_id FROM research_people WHERE person_id=?)
                ORDER BY r.id DESC LIMIT 100""", (pid,))
    h = '<div class="top-bar"><h2>Link Research</h2>' + nav("/person/%d" % pid) + '</div>'
    h += '<div class="search-bar"><input type="text" class="ac-search" data-src="research" placeholder="Search research..." autocomplete="off"></div>'
    h += '<div id="list">'
    for rid, ev in rows:
        h += "<div class='picker-row'><div class='nm'>%s</div>" % (ev or "")
        h += "<div class='ac'><a class='btn btn-sm' href='/person/%d/link_research/%d'>LINK</a></div></div>" % (pid, rid)
    if not rows:
        h += "<div class='empty'>No research to link.</div>"
    h += "</div>"
    h += """<script>
    document.addEventListener('change', function(e){
      var inp = e.target;
      if (!inp.classList || !inp.classList.contains('ac-search')) return;
      var id = inp.getAttribute('data-picked-id');
      if (id) { window.location.href = '/person/%d/link_research/' + id; }
    });
    </script>""" % pid
    return page(h)


@bp.route("/person/<int:pid>/link_research/<int:rid>")
def do_link_research(pid, rid):
    run("INSERT OR IGNORE INTO research_people (research_id, person_id) VALUES (?, ?)",
        (rid, pid))
    return redirect("/person/%d" % pid)
