# -*- coding: utf-8 -*-
from flask import Blueprint, request, redirect
from core import q, run, insert_and_id, page

bp = Blueprint("combinations", __name__)


def get_slots(cid):
    return q("SELECT slot_num, label, value FROM combination_slots WHERE combination_id=? ORDER BY slot_num", (cid,))


def build_title(slots):
    parts = []
    for n, label, value in slots:
        v = (value or "").strip()
        if v:
            parts.append(v[:4].upper())
    return "+".join(parts)


def combo_card(r):
    cid, title, result, cref, obs, pcount, rcount = r
    h = "<div class='card'>"
    h += "<a class='edit' href='/combination/%d/edit'>&#9998;</a>" % cid
    h += "<p class='name'><a href='/combination/%d' style='color:inherit;text-decoration:none;'>%s</a></p>" % (cid, title or "(untitled)")
    if result:
        h += "<div class='result-box'><b>Result</b><p>%s</p></div>" % result
    if cref: h += "<div class='row'><b>Ref</b> %s</div>" % cref
    if obs:  h += "<div class='row'><b>Obs</b> %s</div>" % obs
    h += "<div class='row' style='color:#888; font-size:13px;'>"
    h += "&#128100; %d people &nbsp;&middot;&nbsp; &#128221; %d research</div>" % (pcount, rcount)
    h += "<div style='margin-top:10px;'>"
    h += "<a class='btn btn-secondary' href='/combination/%d'>View</a> " % cid
    h += "<a class='btn btn-secondary' href='/combination/%d/edit'>Edit</a> " % cid
    h += "<form method='post' action='/combination/%d/delete' style='display:inline;' onsubmit=\"return confirm('Delete?');\">" % cid
    h += "<button class='btn btn-danger' type='submit'>DLT</button></form>"
    h += "</div></div>"
    return h


@bp.route("/combinations")
def list_combinations():
    rows = q("""
        SELECT c.id, c.title, c.result, c.chart_ref, c.observation,
          (SELECT COUNT(*) FROM combination_people cp WHERE cp.combination_id = c.id),
          (SELECT COUNT(*) FROM research r WHERE r.combination_id = c.id)
        FROM combinations c ORDER BY c.id DESC
    """)
    h = """<div class="top-bar"><h2>Combinations</h2><div class="actions">
        <a class="btn btn-secondary" href="/">&#127968; Home</a>
        <a class="btn" href="/combination/new">+ NEW</a></div></div>"""
    if not rows:
        return page(h + "<div class='empty'>No combinations yet.<br>Tap + NEW.</div>")
    for r in rows:
        h += combo_card(r)
    return page(h)


@bp.route("/combination/new", methods=["GET", "POST"])
def combination_new():
    if request.method == "POST":
        cid = save_combination(None)
        return redirect("/combination/%d" % cid)
    return page(combination_form(None, [], []))


@bp.route("/combination/<int:cid>")
def combination_view(cid):
    rows = q("SELECT id, title, result, chart_ref, observation FROM combinations WHERE id=?", (cid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    cid, title, result, cref, obs = rows[0]
    slots = get_slots(cid)
    people = q("""SELECT p.id, p.name FROM people p
                  JOIN combination_people cp ON cp.person_id = p.id
                  WHERE cp.combination_id=?""", (cid,))
    research = q("SELECT id, main_event, result FROM research WHERE combination_id=?", (cid,))

    h = "<div class='top-bar'><h2>%s</h2>" % (title or "(untitled)")
    h += """<div class="actions">
      <a class="btn btn-secondary" href="/combinations">&larr; Back</a>
      <a class="btn btn-secondary" href="/">&#127968; Home</a></div></div>"""

    h += "<div class='card'><span class='section-label'>Slots</span>"
    if slots:
        for n, lbl, v in slots:
            h += "<div class='row'><b>%s</b> %s</div>" % (lbl or ("X%d" % n), v or "")
    else:
        h += "<p class='muted'>No slots.</p>"
    if cref: h += "<div class='row' style='margin-top:10px;'><b>Ref</b> %s</div>" % cref
    h += "</div>"

    if result:
        h += "<div class='card'><div class='result-box'><b>Result</b><p>%s</p></div></div>" % result
    if obs:
        h += "<div class='card'><span class='section-label'>Observation</span><p>%s</p></div>" % obs

    h += "<div class='card'><span class='section-label'>Linked People (%d)</span>" % len(people)
    if people:
        for pid, name in people:
            h += "<div class='row'>&bull; <a href='/person/%d'>%s</a></div>" % (pid, name)
    else:
        h += "<p class='muted'>None</p>"
    h += "</div>"

    h += "<div class='card'><span class='section-label'>Linked Research (%d)</span>" % len(research)
    if research:
        for rid, ev, res in research:
            h += "<div class='row'>&bull; <a href='/research/%d'>%s</a></div>" % (rid, ev or "(event)")
    else:
        h += "<p class='muted'>None</p>"
    h += "</div>"

    h += """<div style="margin-top:14px;">
      <a class="btn" href="/research/new?from_combo=%d">&#128300; Research this combo</a>
      <a class="btn btn-secondary" href="/combination/%d/edit">&#9998; Edit</a>
      <form method="post" action="/combination/%d/delete" style="display:inline;"
            onsubmit="return confirm('Delete this combination?');">
        <button class="btn btn-danger" type="submit">&#128465; DLT</button>
      </form>
    </div>""" % (cid, cid, cid)

    return page(h)


@bp.route("/combination/<int:cid>/edit", methods=["GET", "POST"])
def combination_edit(cid):
    rows = q("SELECT id, title, result, chart_ref, observation FROM combinations WHERE id=?", (cid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    if request.method == "POST":
        save_combination(cid)
        return redirect("/combination/%d" % cid)
    linked = set(r[0] for r in q("SELECT person_id FROM combination_people WHERE combination_id=?", (cid,)))
    slots = get_slots(cid)
    return page(combination_form(rows[0], slots, list(linked)))


@bp.route("/combination/<int:cid>/delete", methods=["POST"])
def combination_delete(cid):
    run("DELETE FROM combination_slots WHERE combination_id=?", (cid,))
    run("DELETE FROM combination_people WHERE combination_id=?", (cid,))
    run("UPDATE research SET combination_id=NULL WHERE combination_id=?", (cid,))
    run("DELETE FROM combinations WHERE id=?", (cid,))
    return redirect("/combinations")


def save_combination(cid):
    title = request.form.get("title", "").strip()
    result = request.form.get("result", "").strip()
    cref = request.form.get("chart_ref", "").strip()
    obs = request.form.get("observation", "").strip()
    ppl = request.form.getlist("people")

    if cid is None:
        cid = insert_and_id(
            "INSERT INTO combinations (title, result, chart_ref, observation) VALUES (?, ?, ?, ?)",
            (title, result, cref, obs))
    else:
        run("UPDATE combinations SET title=?, result=?, chart_ref=?, observation=? WHERE id=?",
            (title, result, cref, obs, cid))
        run("DELETE FROM combination_slots WHERE combination_id=?", (cid,))
        run("DELETE FROM combination_people WHERE combination_id=?", (cid,))

    for i in range(1, 31):
        lbl = request.form.get("slot_label_%d" % i, "").strip()
        val = request.form.get("slot_value_%d" % i, "").strip()
        if lbl or val:
            run("INSERT INTO combination_slots (combination_id, slot_num, label, value) VALUES (?, ?, ?, ?)",
                (cid, i, lbl, val))

    for pid in ppl:
        try:
            run("INSERT OR IGNORE INTO combination_people (combination_id, person_id) VALUES (?, ?)",
                (cid, int(pid)))
        except Exception:
            pass
    return cid


def combination_form(row, slots, linked):
    if row is None:
        cid, title, result, cref, obs = (None,) * 5
        heading = "NEW COMBINATION"
    else:
        cid, title, result, cref, obs = row
        heading = "EDIT COMBINATION"
    action = "/combination/%d/edit" % cid if cid else "/combination/new"

    slot_rows = ""
    sv = {}
    for n, lbl, v in slots:
        sv[n] = (lbl, v)
    max_slot = max([n for n, _, _ in slots] or [5])
    if max_slot < 5:
        max_slot = 5
    for i in range(1, max_slot + 1):
        lbl, v = sv.get(i, ("", ""))
        slot_rows += """<div class="slot-row">
          <input type="text" name="slot_label_%d" value="%s" placeholder="Jupiter, Sign, House...">
          <input type="text" name="slot_value_%d" value="%s" placeholder="Aries, 7th, Mercury...">
        </div>""" % (i, lbl or "", i, v or "")

    all_ppl = q("SELECT id, name FROM people ORDER BY name")
    ppl_html = ""
    if not all_ppl:
        ppl_html = "<p class='muted'>No people yet.</p>"
    else:
        for pid, name in all_ppl:
            ck = " checked" if pid in linked else ""
            ppl_html += ("<label style='display:flex; align-items:center; font-weight:400; margin-top:6px;'>"
                         "<input type='checkbox' name='people' value='%d'%s style='width:auto; margin-right:8px;'>"
                         "%s</label>") % (pid, ck, name)

    return """
      <div class="top-bar"><h2>%s</h2>
        <div class="actions">
          <a class="btn btn-secondary" href="/combinations">&larr; Back</a>
          <a class="btn btn-secondary" href="/">&#127968; Home</a>
        </div></div>

      <div class="card"><form method="post" action="%s">
        <label>Title (auto from slots if empty)</label>
        <input type="text" name="title" value="%s" placeholder="JU+SAT+ASHWINI...">

        <span class="section-label">Slots</span>
        %s

        <span class="section-label">Result</span>
        <input type="text" name="result" value="%s" placeholder="Gives bad marriage...">

        <label>Chart Ref (comma separated)</label>
        <input type="text" name="chart_ref" value="%s" placeholder="D1, D9">

        <label>Observation</label>
        <textarea name="observation" rows="3">%s</textarea>

        <span class="section-label">Linked People</span>
        %s

        <div style="margin-top:20px;">
          <button class="btn" type="submit">Save</button>
          <a class="btn btn-secondary" href="/combinations">Cancel</a>
        </div>
      </form></div>
    """ % (heading, action, title or "", slot_rows, result or "",
           cref or "", obs or "", ppl_html)
