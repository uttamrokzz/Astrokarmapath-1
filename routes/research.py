# -*- coding: utf-8 -*-
from flask import Blueprint, request, redirect
from core import q, run, insert_and_id, page

bp = Blueprint("research", __name__)


def get_slots(rid):
    return q("SELECT slot_num, label, value FROM research_slots WHERE research_id=? ORDER BY slot_num", (rid,))


def research_card(r):
    rid, ev, result, evd, pname, combo_title = r
    h = "<div class='card'>"
    h += "<a class='edit' href='/research/%d/edit'>&#9998;</a>" % rid
    h += "<p class='name'><a href='/research/%d' style='color:inherit;text-decoration:none;'>%s</a></p>" % (rid, ev or "(event)")
    if result:
        h += "<div class='result-box'><b>Result</b><p>%s</p></div>" % result
    if evd: h += "<div class='row'><b>Date</b> %s</div>" % evd
    if pname: h += "<div class='row'><b>Person</b> %s</div>" % pname
    if combo_title:
        h += "<div class='row'><b>Combo</b> %s</div>" % combo_title
    h += "<div style='margin-top:10px;'>"
    h += "<a class='btn btn-secondary' href='/research/%d'>View</a> " % rid
    h += "<a class='btn btn-secondary' href='/research/%d/edit'>Edit</a> " % rid
    h += "<form method='post' action='/research/%d/delete' style='display:inline;' onsubmit=\"return confirm('Delete?');\">" % rid
    h += "<button class='btn btn-danger' type='submit'>DLT</button></form>"
    h += "</div></div>"
    return h


@bp.route("/research")
def list_research():
    rows = q("""
        SELECT r.id, r.main_event, r.result, r.main_event_date,
               (SELECT name FROM people WHERE id = r.person_id),
               (SELECT title FROM combinations WHERE id = r.combination_id)
        FROM research r ORDER BY r.id DESC
    """)
    h = """<div class="top-bar"><h2>Research Notes</h2><div class="actions">
        <a class="btn btn-secondary" href="/">&#127968; Home</a>
        <a class="btn" href="/research/new">+ NEW</a></div></div>"""
    if not rows:
        return page(h + "<div class='empty'>No research notes yet.<br>Tap + NEW.</div>")
    for r in rows:
        h += research_card(r)
    return page(h)


@bp.route("/research/new", methods=["GET", "POST"])
def research_new():
    if request.method == "POST":
        rid = save_research(None)
        return redirect("/research/%d" % rid)
    from_combo = request.args.get("from_combo", "").strip()
    pre = None
    pre_slots = []
    if from_combo:
        try:
            cid = int(from_combo)
            cr = q("SELECT title, result, chart_ref, observation FROM combinations WHERE id=?", (cid,))
            if cr:
                pre = {"combination_id": cid, "title": cr[0][0], "result": cr[0][1],
                       "chart_ref": cr[0][2], "observation": cr[0][3]}
                pre_slots = get_slots(cid)
        except Exception:
            pass
    return page(research_form(None, pre, pre_slots))


@bp.route("/research/<int:rid>")
def research_view(rid):
    rows = q("""SELECT id, main_event, main_event_date, research_from, research_to,
                       result, observation, person_id, combination_id
                FROM research WHERE id=?""", (rid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    rid, ev, evd, rf, rt, result, obs, pid, cid = rows[0]
    slots = get_slots(rid)
    dasha = q("SELECT level, lord, dasha_date FROM research_dasha WHERE research_id=? ORDER BY id", (rid,))
    pname = ""
    if pid:
        pr = q("SELECT name FROM people WHERE id=?", (pid,))
        if pr: pname = pr[0][0]
    combo_title = ""
    if cid:
        cr = q("SELECT title FROM combinations WHERE id=?", (cid,))
        if cr: combo_title = cr[0][0]

    h = "<div class='top-bar'><h2>%s</h2>" % (ev or "(event)")
    h += """<div class="actions">
      <a class="btn btn-secondary" href="/research">&larr; Back</a>
      <a class="btn btn-secondary" href="/">&#127968; Home</a></div></div>"""

    h += "<div class='card'>"
    if evd: h += "<div class='row'><b>Date</b> %s</div>" % evd
    if pname: h += "<div class='row'><b>Person</b> %s</div>" % pname
    if rf or rt: h += "<div class='row'><b>Range</b> %s &rarr; %s</div>" % (rf or "?", rt or "?")
    h += "</div>"

    if result:
        h += "<div class='card'><div class='result-box'><b>Result</b><p>%s</p></div></div>" % result

    if slots:
        h += "<div class='card'><span class='section-label'>Slots</span>"
        for n, lbl, v in slots:
            h += "<div class='row'><b>%s</b> %s</div>" % (lbl or ("X%d" % n), v or "")
        h += "</div>"

    if dasha:
        h += "<div class='card'><span class='section-label'>Dasha</span>"
        for lvl, lord, dt in dasha:
            h += "<div class='row'><b>%s</b> %s &mdash; %s</div>" % (lvl or "", lord or "", dt or "")
        h += "</div>"

    if obs:
        h += "<div class='card'><span class='section-label'>Observation</span><p>%s</p></div>" % obs

    h += "<div class='card'>"
    if cid:
        h += "<span class='section-label'>Saved in Combinations DB</span>"
        h += "<div class='row'>&#10003; <a href='/combination/%d'>%s</a></div>" % (cid, combo_title)
    else:
        h += "<p class='muted'>Not yet saved as a combination.</p>"
    h += "</div>"

    h += """<div style="margin-top:14px;">
      <a class="btn btn-secondary" href="/research/%d/edit">&#9998; Edit</a>
      <form method="post" action="/research/%d/delete" style="display:inline;"
            onsubmit="return confirm('Delete this research?');">
        <button class="btn btn-danger" type="submit">&#128465; DLT</button>
      </form>
    </div>""" % (rid, rid)

    return page(h)


@bp.route("/research/<int:rid>/edit", methods=["GET", "POST"])
def research_edit(rid):
    rows = q("""SELECT id, main_event, main_event_date, research_from, research_to,
                       result, observation, person_id, combination_id
                FROM research WHERE id=?""", (rid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    if request.method == "POST":
        save_research(rid)
        return redirect("/research/%d" % rid)
    slots = get_slots(rid)
    return page(research_form(rows[0], None, slots))


@bp.route("/research/<int:rid>/delete", methods=["POST"])
def research_delete(rid):
    run("DELETE FROM research_slots WHERE research_id=?", (rid,))
    run("DELETE FROM research_dasha WHERE research_id=?", (rid,))
    run("DELETE FROM research WHERE id=?", (rid,))
    return redirect("/research")


def save_research(rid):
    pid = request.form.get("person_id", "").strip() or None
    ev = request.form.get("main_event", "").strip()
    evd = request.form.get("main_event_date", "").strip()
    rf = request.form.get("research_from", "").strip()
    rt = request.form.get("research_to", "").strip()
    result = request.form.get("result", "").strip()
    obs = request.form.get("observation", "").strip()
    cid = request.form.get("combination_id", "").strip() or None

    if rid is None:
        rid = insert_and_id("""INSERT INTO research
            (person_id, main_event, main_event_date, research_from, research_to,
             result, observation, combination_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (int(pid) if pid else None, ev, evd, rf, rt, result, obs,
             int(cid) if cid else None))
    else:
        run("""UPDATE research SET person_id=?, main_event=?, main_event_date=?,
               research_from=?, research_to=?, result=?, observation=?, combination_id=?
               WHERE id=?""",
            (int(pid) if pid else None, ev, evd, rf, rt, result, obs,
             int(cid) if cid else None, rid))
        run("DELETE FROM research_slots WHERE research_id=?", (rid,))
        run("DELETE FROM research_dasha WHERE research_id=?", (rid,))

    for i in range(1, 31):
        lbl = request.form.get("slot_label_%d" % i, "").strip()
        val = request.form.get("slot_value_%d" % i, "").strip()
        if lbl or val:
            run("INSERT INTO research_slots (research_id, slot_num, label, value) VALUES (?, ?, ?, ?)",
                (rid, i, lbl, val))

    for i in range(1, 11):
        lvl = request.form.get("dasha_level_%d" % i, "").strip()
        lord = request.form.get("dasha_lord_%d" % i, "").strip()
        dt = request.form.get("dasha_date_%d" % i, "").strip()
        if lvl or lord or dt:
            run("INSERT INTO research_dasha (research_id, level, lord, dasha_date) VALUES (?, ?, ?, ?)",
                (rid, lvl, lord, dt))
    return rid


def research_form(row, pre, slots):
    if row is None:
        rid = None
        ev = evd = rf = rt = obs = ""
        result = ""
        pid = None
        cid = pre.get("combination_id") if pre else None
        if pre:
            result = pre.get("result", "") or ""
            obs = pre.get("observation", "") or ""
    else:
        rid, ev, evd, rf, rt, result, obs, pid, cid = row

    heading = "Add Research" if rid is None else "Edit Research"
    action = "/research/%d/edit" % rid if rid else "/research/new"

    people = q("SELECT id, name FROM people ORDER BY name")
    opts = "<option value=''>-- none --</option>"
    for p_id, name in people:
        sel = " selected" if pid and p_id == pid else ""
        opts += "<option value='%d'%s>%s</option>" % (p_id, sel, name)

    sv = {}
    for n, lbl, v in slots:
        sv[n] = (lbl, v)
    max_slot = max([n for n, _, _ in slots] or [5])
    if max_slot < 5:
        max_slot = 5
    slot_rows = ""
    for i in range(1, max_slot + 1):
        lbl, v = sv.get(i, ("", ""))
        slot_rows += """<div class="slot-row">
          <input type="text" name="slot_label_%d" value="%s" placeholder="Jupiter, Sign...">
          <input type="text" name="slot_value_%d" value="%s" placeholder="Aries, 7th...">
        </div>""" % (i, lbl or "", i, v or "")

    dasha = q("SELECT level, lord, dasha_date FROM research_dasha WHERE research_id=? ORDER BY id", (rid,)) if rid else []
    dasha_rows = ""
    for i in range(1, 6):
        lvl = dasha[i-1][0] if i <= len(dasha) else ""
        lord = dasha[i-1][1] if i <= len(dasha) else ""
        dt = dasha[i-1][2] if i <= len(dasha) else ""
        dasha_rows += """<div class="dasha-row">
          <input type="text" name="dasha_level_%d" value="%s" placeholder="MD">
          <input type="text" name="dasha_lord_%d" value="%s" placeholder="Lord">
          <input type="text" name="dasha_date_%d" value="%s" placeholder="Date">
        </div>""" % (i, lvl or "", i, lord or "", i, dt or "")

    banner = ""
    if pre and rid is None:
        banner = "<div class='result-box'><b>From combination</b><p>%s</p></div>" % pre.get("title", "")

    combo_hidden = ""
    if cid:
        combo_hidden = "<input type='hidden' name='combination_id' value='%d'>" % cid

    return """
      <div class="top-bar"><h2>%s</h2>
        <div class="actions">
          <a class="btn btn-secondary" href="/research">&larr; Back</a>
          <a class="btn btn-secondary" href="/">&#127968; Home</a>
        </div></div>
      %s
      <div class="card"><form method="post" action="%s">
        %s

        <span class="section-label">Main Event</span>
        <label>Event</label>
        <input type="text" name="main_event" value="%s" placeholder="Anemia happened">
        <div class="row2">
          <div><label>Event Date</label>
            <input type="date" name="main_event_date" value="%s"></div>
          <div><label>Person</label>
            <select name="person_id">%s</select></div>
        </div>
        <div class="row2">
          <div><label>Research From</label>
            <input type="date" name="research_from" value="%s"></div>
          <div><label>Research To</label>
            <input type="date" name="research_to" value="%s"></div>
        </div>

        <span class="section-label">Slots (Combination)</span>
        %s

        <span class="section-label">Result</span>
        <input type="text" name="result" value="%s" placeholder="What does this produce?">

        <span class="section-label">Dasha</span>
        %s

        <span class="section-label">Observation</span>
        <textarea name="observation" rows="3">%s</textarea>

        <div style="margin-top:20px;">
          <button class="btn" type="submit">Save Research</button>
          <a class="btn btn-secondary" href="/research">Cancel</a>
        </div>
      </form></div>
    """ % (heading, banner, action, combo_hidden,
           ev or "", evd or "", opts, rf or "", rt or "",
           slot_rows, result or "", dasha_rows, obs or "")
