# -*- coding: utf-8 -*-
import datetime
from flask import Blueprint, request, redirect
from core import q, run, insert_and_id, page, nav

bp = Blueprint("combinations", __name__)


def slots_of(cid):
    return q("SELECT slot_num, label, value FROM combination_slots "
             "WHERE combination_id=? ORDER BY slot_num", (cid,))


def dasha_of(cid):
    return q("SELECT level, lord, dasha_date FROM combination_dasha "
             "WHERE combination_id=? ORDER BY id", (cid,))


def people_of(cid):
    return q("""SELECT p.id, p.name FROM people p
                JOIN combination_people cp ON cp.person_id = p.id
                WHERE cp.combination_id=? ORDER BY p.name""", (cid,))


def refs_list(cref):
    if not cref:
        return []
    return [x.strip() for x in cref.split(",") if x.strip()]


def slot_summary(cid):
    s = slots_of(cid)
    return " + ".join([(x[2] or "") for x in s if x[2]])


def card(r):
    cid, title, result, cref, body, obs_num, is_main, research_id, r_title = r
    h = "<div class='card'>"
    h += "<a class='edit' href='/combination/%d/edit'>&#9998;</a>" % cid
    h += "<p class='card-title'><a href='/combination/%d'>%s</a></p>" % (cid, title or "(untitled)")
    if is_main:
        h += "<span class='badge-main'>Main</span>"
    ss = slot_summary(cid)
    if ss:
        h += "<div class='row' style='color:#888;font-size:12px;'>%s</div>" % ss
    if body:
        show = body if len(body) <= 200 else body[:200] + "..."
        h += "<div class='body-display'>%s</div>" % show
    ppl = people_of(cid)
    if ppl:
        names = ", ".join([p[1] for p in ppl])
        h += "<div class='row'><b>Persons</b> %s</div>" % names
    refs = refs_list(cref)
    if refs:
        h += "<div class='row'><b>Refs</b>"
        for rr in refs:
            h += " <span class='pill ref'>%s</span>" % rr
        h += "</div>"
    if r_title:
        h += "<div class='row'><b>Research</b> %s</div>" % r_title
    h += "<div class='row' style='color:#aaa;font-size:11px;margin-top:8px;'>"
    h += "Logged: %s %s</div>" % (r[5] if len(r) > 5 else "", "")
    h += "<div style='margin-top:10px;'>"
    h += "<a class='btn btn-secondary btn-sm' href='/combination/%d'>VIEW</a> " % cid
    h += "<a class='btn btn-secondary btn-sm' href='/combination/%d/edit'>EDIT</a> " % cid
    h += "<form method='post' action='/combination/%d/delete' style='display:inline;' " % cid
    h += "onsubmit=\"return confirm('Delete this combination?');\">"
    h += "<button class='btn btn-danger btn-sm' type='submit'>DLT</button></form>"
    h += "</div></div>"
    return h


@bp.route("/combinations")
def list_combinations():
    rows = q("""
        SELECT c.id, c.title, c.result, c.chart_ref, c.body,
               c.observation_num, c.is_main, c.research_id,
               (SELECT event FROM research WHERE id = c.research_id)
        FROM combinations c
        ORDER BY c.id DESC
    """)
    h = '<div class="top-bar"><h2>Combinations</h2><div class="actions">'
    h += '<a class="btn btn-secondary btn-sm" href="/combinations/search">SEARCH</a>'
    h += '<a class="btn btn-sm" href="/combination/new">+ NEW</a></div></div>'
    if not rows:
        return page(h + '<div class="empty">No combinations yet. Tap + NEW.</div>')
    for r in rows:
        h += card(r)
    return page(h)


@bp.route("/combinations/search")
def search_combinations():
    h = '<div class="top-bar"><h2>Search Combinations</h2>' + nav("/combinations") + '</div>'
    h += '<div class="search-bar"><input type="text" id="q" autocomplete="off" autofocus placeholder="Title, body, slots..."></div>'
    h += '<div class="letters" id="letters"></div>'
    h += '<div id="results"></div>'
    h += """<script>
(function(){
  var inp = document.getElementById('q'),
      res = document.getElementById('results'),
      let_ = document.getElementById('letters'),
      tmr = null;
  function card(x){
    var h = "<div class='card'>";
    h += "<p class='card-title'><a href='/combination/" + x.id + "'>" + (x.title || '(untitled)') + "</a></p>";
    if (x.body) h += "<div class='body-display'>" + x.body + "</div>";
    h += "</div>";
    return h;
  }
  function render(items){
    if (!items || !items.length){
      res.innerHTML = "<div class='empty'>No matches.</div>";
      return;
    }
    var h = "<p class='muted'>" + items.length + " match(es)</p>";
    for (var i = 0; i < items.length; i++) h += card(items[i]);
    res.innerHTML = h;
  }
  function search(term){
    if (!term){ res.innerHTML = ""; return; }
    fetch('/api/combinations/search?q=' + encodeURIComponent(term))
      .then(function(r){ return r.json(); })
      .then(render)
      .catch(function(){ res.innerHTML = "<div class='empty'>Search error.</div>"; });
  }
  inp.addEventListener('input', function(){
    clearTimeout(tmr);
    tmr = setTimeout(function(){ search(inp.value.trim()); }, 200);
  });
  var A = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split(''), hh = '';
  for (var j = 0; j < A.length; j++)
    hh += "<button class='letter' data-l='" + A[j] + "'>" + A[j] + "</button>";
  let_.innerHTML = hh;
  let_.addEventListener('click', function(e){
    var L = e.target.getAttribute('data-l');
    if (!L) return;
    inp.value = L;
    search(L);
  });
})();
</script>"""
    return page(h)


@bp.route("/combination/new", methods=["GET", "POST"])
def combination_new():
    if request.method == "POST":
        cid = save_combination(None)
        return redirect("/combination/%d/saved" % cid)
    now = datetime.datetime.now()
    defaults = {
        "log_date": now.strftime("%Y-%m-%d"),
        "log_time": now.strftime("%H:%M"),
    }

    # Prefill from research
    rid = request.args.get("research_id", "").strip()
    prefill_title = request.args.get("prefill_title", "").strip()
    from_research = False
    if rid:
        try:
            rid_i = int(rid)
            defaults["research_id"] = rid_i
            from_research = True
        except Exception:
            pass
    if prefill_title:
        defaults["prefill_title"] = prefill_title
    defaults["from_research"] = from_research

    return page(combination_form(None, [], [], [], [], defaults))


@bp.route("/combination/<int:cid>")
def combination_view(cid):
    rows = q("""SELECT id, title, result, chart_ref, body, observation_num,
                is_main, research_id, event_date_from, event_date_to,
                event_time, log_date, log_time
                FROM combinations WHERE id=?""", (cid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    (cid, title, result, cref, body, obs_num, is_main, research_id,
     edf, edt, etime, ldate, ltime) = rows[0]

    sl = slots_of(cid)
    ppl = people_of(cid)
    dasha = dasha_of(cid)
    refs = refs_list(cref)

    r_title = ""
    if research_id:
        rr = q("SELECT event FROM research WHERE id=?", (research_id,))
        if rr:
            r_title = rr[0][0]

    h = '<div class="top-bar"><h2>%s</h2>' % (title or "(untitled)") + nav("/combinations") + '</div>'

    h += "<div class='card'>"
    h += "<p class='card-title'>%s</p>" % (title or "")
    if is_main:
        h += "<span class='badge-main'>Main observation</span>"
    ss = " + ".join([(x[2] or "") for x in sl if x[2]])
    if ss:
        h += "<div class='row' style='color:#888;'>%s</div>" % ss
    h += "</div>"

    if sl:
        h += "<div class='card'><span class='section-label'>Slots</span>"
        for n, lbl, v in sl:
            h += "<div class='row'><b>%s</b> %s</div>" % (lbl or ("X%d" % n), v or "")
        h += "</div>"

    if body:
        h += "<div class='card'><span class='section-label'>Body</span>"
        h += "<div class='body-display'>%s</div></div>" % body

    if dasha:
        h += "<div class='card'><span class='section-label'>Dasha</span>"
        for lvl, lord, dd in dasha:
            h += "<div class='row'><b>%s</b> %s &mdash; %s</div>" % (lvl or "", lord or "", dd or "")
        h += "</div>"

    if refs:
        h += "<div class='card'><span class='section-label'>Ref Charts</span>"
        for rr in refs:
            h += "<span class='pill ref'>%s</span>" % rr
        h += "</div>"

    if ppl:
        h += "<div class='card'><span class='section-label'>Linked People (%d)</span>" % len(ppl)
        for pid, name in ppl:
            h += "<div class='row'>&bull; <a href='/person/%d'>%s</a></div>" % (pid, name)
        h += "</div>"

    info = ""
    if edf or edt:
        info += "<div class='row'><b>Event date</b> %s &rarr; %s" % (edf or "?", edt or "?")
        if etime:
            info += " at %s" % etime
        info += "</div>"
    if ldate:
        info += "<div class='row'><b>Logged</b> %s %s</div>" % (ldate, ltime or "")
    if r_title:
        info += "<div class='row'><b>Research</b> <a href='/research/%d'>%s</a></div>" % (research_id, r_title)
    if info:
        h += "<div class='card'>%s</div>" % info

    h += '<div style="margin-top:14px;">'
    h += '<a class="btn btn-secondary" href="/combination/%d/edit">&#9998; EDIT</a> ' % cid
    h += '<form method="post" action="/combination/%d/delete" style="display:inline;" ' % cid
    h += 'onsubmit="return confirm(\'Delete this combination?\');">'
    h += '<button class="btn btn-danger" type="submit">&#128465; DLT</button></form></div>'
    return page(h)


@bp.route("/combination/<int:cid>/edit", methods=["GET", "POST"])
def combination_edit(cid):
    rows = q("""SELECT id, title, result, chart_ref, body,
                event_date_from, event_date_to, event_time,
                log_date, log_time, research_id, observation_num
                FROM combinations WHERE id=?""", (cid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    if request.method == "POST":
        save_combination(cid)
        return redirect("/combination/%d" % cid)

    sl = slots_of(cid)
    dasha = dasha_of(cid)
    ppl = people_of(cid)
    linked_ids = [p[0] for p in ppl]
    refs = refs_list(rows[0][3] or "")
    return page(combination_form(rows[0], sl, dasha, linked_ids, refs, {}))


@bp.route("/combination/<int:cid>/delete", methods=["POST"])
def combination_delete(cid):
    run("DELETE FROM combination_slots WHERE combination_id=?", (cid,))
    run("DELETE FROM combination_dasha WHERE combination_id=?", (cid,))
    run("DELETE FROM combination_people WHERE combination_id=?", (cid,))
    run("DELETE FROM combinations WHERE id=?", (cid,))
    return redirect("/combinations")


@bp.route("/combination/<int:cid>/saved")
def combination_saved(cid):
    rows = q("SELECT title, body, research_id FROM combinations WHERE id=?", (cid,))
    if not rows:
        return redirect("/combinations")
    title, body, research_id = rows[0]

    all_research = q("SELECT id, event FROM research ORDER BY id DESC LIMIT 50")
    all_people = q("SELECT id, name FROM people ORDER BY name")

    h = '<div class="top-bar"><h2>Saved</h2>' + nav("/combinations") + '</div>'

    h += '<div class="save-sheet"><h3>&#10003; Combination saved</h3>'
    h += '<p class="muted">%s</p>' % (title or "")
    h += '</div>'

    h += '<form method="post" action="/combination/%d/saved">' % cid
    h += '<div class="save-sheet"><h3>Link it to other places?</h3>'

    h += '<div class="section-label">Link to Research</div>'
    if research_id:
        rr = q("SELECT event FROM research WHERE id=?", (research_id,))
        h += '<p class="muted">Already linked to: %s</p>' % (rr[0][0] if rr else "")
    else:
        h += '<select name="research_id">'
        h += '<option value="">-- none --</option>'
        for rid, ev in all_research:
            h += '<option value="%d">%s</option>' % (rid, ev or "(event)")
        h += '</select>'

    h += '<div class="section-label">Link to People</div>'
    for pid, name in all_people:
        h += '<label class="chk"><input type="checkbox" name="people" value="%d">%s</label>' % (pid, name)

    h += '<div style="margin-top:18px;">'
    h += '<button class="btn" type="submit">Save links</button> '
    h += '<a class="btn btn-secondary" href="/combinations">Skip</a>'
    h += '</div></div></form>'
    return page(h)


@bp.route("/combination/<int:cid>/saved", methods=["POST"])
def combination_saved_post(cid):
    rid = request.form.get("research_id", "").strip()
    if rid:
        try:
            rid_i = int(rid)
            # Get next observation_num for that research
            r = q("SELECT IFNULL(MAX(observation_num),0) FROM combinations WHERE research_id=?", (rid_i,))
            next_num = (r[0][0] or 0) + 1
            run("UPDATE combinations SET research_id=?, observation_num=? WHERE id=?",
                (rid_i, next_num, cid))
        except Exception:
            pass

    for pid in request.form.getlist("people"):
        try:
            run("INSERT OR IGNORE INTO combination_people (combination_id, person_id) VALUES (?, ?)",
                (cid, int(pid)))
        except Exception:
            pass

    # If this combo belongs to a research, go back there
    rr = q("SELECT research_id FROM combinations WHERE id=?", (cid,))
    if rr and rr[0][0]:
        return redirect("/research/%d" % rr[0][0])
    return redirect("/combinations")


@bp.route("/combination/<int:cid>/link_research")
def combo_link_research(cid):
    rows = q("""SELECT id, event FROM research
                WHERE id != IFNULL((SELECT research_id FROM combinations WHERE id=?), 0)
                ORDER BY id DESC LIMIT 50""", (cid,))
    h = '<div class="top-bar"><h2>Link Research</h2>' + nav("/combination/%d" % cid) + '</div>'
    for rid, ev in rows:
        h += "<div class='picker-row'><div class='nm'>%s</div><div class='ac'>" % (ev or "(event)")
        h += '<a class="btn btn-secondary btn-sm" href="/research/%d/edit">EDIT</a> ' % rid
        h += '<a class="btn btn-sm" href="/combination/%d/link_research/%d">LINK</a>' % (cid, rid)
        h += "</div></div>"
    if not rows:
        h += "<div class='empty'>No research notes yet.</div>"
    return page(h)


@bp.route("/combination/<int:cid>/link_research/<int:rid>")
def combo_do_link_research(cid, rid):
    r = q("SELECT IFNULL(MAX(observation_num),0) FROM combinations WHERE research_id=?", (rid,))
    next_num = (r[0][0] or 0) + 1
    run("UPDATE combinations SET research_id=?, observation_num=? WHERE id=?",
        (rid, next_num, cid))
    return redirect("/combination/%d" % cid)


def save_combination(cid):
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    edf = request.form.get("event_date_from", "").strip()
    edt = request.form.get("event_date_to", "").strip()
    etime = request.form.get("event_time", "").strip()
    ldate = request.form.get("log_date", "").strip()
    ltime = request.form.get("log_time", "").strip()
    rid = request.form.get("research_id", "").strip()
    rid_i = int(rid) if rid else None

    refs = [x.strip() for x in request.form.getlist("ref") if x.strip()]
    cref = ", ".join(refs)

    if cid is None:
        obs_num = None
        is_main = 0
        if rid_i:
            r = q("SELECT IFNULL(MAX(observation_num),0) FROM combinations WHERE research_id=?",
                  (rid_i,))
            obs_num = (r[0][0] or 0) + 1
            if obs_num == 1:
                is_main = 1
        cid = insert_and_id("""INSERT INTO combinations
            (title, body, chart_ref, event_date_from, event_date_to,
             event_time, log_date, log_time, research_id, observation_num, is_main)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, body, cref, edf, edt, etime, ldate, ltime,
             rid_i, obs_num, is_main))
    else:
        run("""UPDATE combinations SET title=?, body=?, chart_ref=?,
               event_date_from=?, event_date_to=?, event_time=?,
               log_date=?, log_time=? WHERE id=?""",
            (title, body, cref, edf, edt, etime, ldate, ltime, cid))
        run("DELETE FROM combination_slots WHERE combination_id=?", (cid,))
        run("DELETE FROM combination_dasha WHERE combination_id=?", (cid,))
        run("DELETE FROM combination_people WHERE combination_id=?", (cid,))

    # slots: slot_label_N, slot_value_N
    for i in range(1, 51):
        lbl = request.form.get("slot_label_%d" % i, "").strip()
        val = request.form.get("slot_value_%d" % i, "").strip()
        if lbl or val:
            run("INSERT INTO combination_slots (combination_id, slot_num, label, value) VALUES (?, ?, ?, ?)",
                (cid, i, lbl, val))

    # dasha: dasha_level_N, dasha_lord_N, dasha_date_N
    for i in range(1, 21):
        lvl = request.form.get("dasha_level_%d" % i, "").strip()
        lord = request.form.get("dasha_lord_%d" % i, "").strip()
        dd = request.form.get("dasha_date_%d" % i, "").strip()
        if lvl or lord or dd:
            run("INSERT INTO combination_dasha (combination_id, level, lord, dasha_date) VALUES (?, ?, ?, ?)",
                (cid, lvl, lord, dd))

    for pid in request.form.getlist("people"):
        try:
            run("INSERT OR IGNORE INTO combination_people (combination_id, person_id) VALUES (?, ?)",
                (cid, int(pid)))
        except Exception:
            pass

    return cid


def combination_form(row, slots, dasha, linked_ids, refs, defaults):
    hidden_rid = ""
    if row is None:
        cid = None
        title = body = cref = edf = edt = etime = ldate = ltime = ""
        heading = "NEW COMBINATION"
        # Prefill from research
        if defaults.get("prefill_title"):
            title = defaults["prefill_title"]
        if defaults.get("research_id"):
            hidden_rid = '<input type="hidden" name="research_id" value="%d">' % defaults["research_id"]
            heading = "NEW OBSERVATION"
    else:
        (cid, title, result, cref, body, edf, edt, etime, ldate, ltime,
         research_id, obs_num) = row
        heading = "EDIT OBSERVATION" if research_id else "EDIT COMBINATION"
        if research_id:
            hidden_rid = '<input type="hidden" name="research_id" value="%d">' % research_id

    if not ldate and defaults.get("log_date"):
        ldate = defaults["log_date"]
    if not ltime and defaults.get("log_time"):
        ltime = defaults["log_time"]

    action = "/combination/%d/edit" % cid if cid else "/combination/new"
    back = "/combination/%d" % cid if cid else "/combinations"

    # Slot rows
    sv = {n: (lbl, v) for n, lbl, v in slots}
    max_slot = max([n for n, _, _ in slots] or [0])
    if max_slot < 3:
        max_slot = 3
    slot_html = ""
    for i in range(1, max_slot + 1):
        lbl, v = sv.get(i, ("", ""))
        slot_html += ('<div class="slot-row">'
                      '<input type="text" name="slot_label_%d" value="%s" placeholder="Label (Jupiter)">'
                      '<input type="text" name="slot_value_%d" value="%s" placeholder="Value (Aries)">'
                      '<button type="button" class="rm-btn" onclick="this.parentNode.remove()">&times;</button>'
                      '</div>') % (i, lbl or "", i, v or "")

    # Dasha rows
    dasha_html = ""
    for i in range(1, 5):
        if i <= len(dasha):
            lvl, lord, dd = dasha[i-1]
        else:
            lvl, lord, dd = "", "", ""
        opts = ["MD", "AD", "PD", "SD", "Pratyantar"]
        opt_html = '<option value="">--</option>'
        for o in opts:
            sel = " selected" if lvl == o else ""
            opt_html += '<option value="%s"%s>%s</option>' % (o, sel, o)
        dasha_html += ('<div class="dasha-row">'
                       '<select name="dasha_level_%d">%s</select>'
                       '<input type="text" name="dasha_lord_%d" value="%s" placeholder="Lord">'
                       '<input type="text" name="dasha_date_%d" value="%s" placeholder="Date">'
                       '<button type="button" class="rm-btn" onclick="this.parentNode.remove()">&times;</button>'
                       '</div>') % (i, opt_html, i, lord or "", i, dd or "")

    # Ref rows
    if not refs:
        refs = [""]
    ref_html = ""
    for i, rr in enumerate(refs, 1):
        ref_html += ('<div class="ref-row">'
                     '<input type="text" name="ref" value="%s" placeholder="D1, D9">'
                     '<button type="button" class="rm-btn" onclick="this.parentNode.remove()">&times;</button>'
                     '</div>') % (rr or "")

    # People checkboxes
    all_ppl = q("SELECT id, name FROM people ORDER BY name")
    ppl_html = ""
    if not all_ppl:
        ppl_html = "<p class='muted'>No people yet.</p>"
    else:
        for pid, name in all_ppl:
            ck = " checked" if pid in linked_ids else ""
            ppl_html += ('<label class="chk">'
                         '<input type="checkbox" name="people" value="%d"%s>%s</label>'
                         ) % (pid, ck, name)

    h = '<div class="top-bar"><h2>%s</h2>' % heading + nav(back) + '</div>'
    h += '<div class="card"><form method="post" action="%s">' % action
    h += hidden_rid

    h += '<label>Main title *</label>'
    h += '<input type="text" name="title" value="%s" required placeholder="Bad marriage">' % (title or "")

    h += '<div class="section-label">Ref chart <button type="button" class="add" onclick="addRef()">+ ADD REF</button></div>'
    h += '<div id="refs">%s</div>' % ref_html

    h += '<div class="section-label">Combination slots <button type="button" class="add" onclick="addSlot()">+ ADD FIELD</button></div>'
    h += '<div id="slots">%s</div>' % slot_html

    h += '<div class="section-label">Dasha <button type="button" class="add" onclick="addDasha()">+ ADD DASHA</button></div>'
    h += '<div id="dasha">%s</div>' % dasha_html

    h += '<div class="section-label">Date of event</div>'
    h += '<div class="row2">'
    h += '<div><label>From</label><input type="date" name="event_date_from" value="%s"></div>' % (edf or "")
    h += '<div><label>To</label><input type="date" name="event_date_to" value="%s"></div>' % (edt or "")
    h += '</div>'
    h += '<label>Time (optional)</label><input type="time" name="event_time" value="%s">' % (etime or "")

    h += '<div class="section-label">Date of logging (auto)</div>'
    h += '<div class="row2">'
    h += '<div><input type="date" name="log_date" value="%s"></div>' % (ldate or "")
    h += '<div><input type="time" name="log_time" value="%s"></div>' % (ltime or "")
    h += '</div>'

    h += '<div class="section-label">Body</div>'
    h += '<textarea name="body" rows="8" placeholder="Long explanation of what happened...">%s</textarea>' % (body or "")

    h += '<div class="section-label">Persons</div>'
    h += ppl_html

    h += '<div style="margin-top:22px;">'
    h += '<button class="btn" type="submit">SAVE</button> '
    h += '<a class="btn btn-secondary" href="%s">CANCEL</a>' % back
    h += '</div></form></div>'

    # JS for dynamic add
    js = """<script>
var slotN = %d, dashaN = 5, refN = 0;
function addSlot(){
  slotN++;
  var d = document.createElement('div');
  d.className = 'slot-row';
  d.innerHTML = '<input type="text" name="slot_label_' + slotN + '" placeholder="Label">'
              + '<input type="text" name="slot_value_' + slotN + '" placeholder="Value">'
              + '<button type="button" class="rm-btn" onclick="this.parentNode.remove()">&times;</button>';
  document.getElementById('slots').appendChild(d);
}
function addDasha(){
  dashaN++;
  var opts = '<option value="">--</option><option>MD</option><option>AD</option><option>PD</option><option>SD</option><option>Pratyantar</option>';
  var d = document.createElement('div');
  d.className = 'dasha-row';
  d.innerHTML = '<select name="dasha_level_' + dashaN + '">' + opts + '</select>'
              + '<input type="text" name="dasha_lord_' + dashaN + '" placeholder="Lord">'
              + '<input type="text" name="dasha_date_' + dashaN + '" placeholder="Date">'
              + '<button type="button" class="rm-btn" onclick="this.parentNode.remove()">&times;</button>';
  document.getElementById('dasha').appendChild(d);
}
function addRef(){
  refN++;
  var d = document.createElement('div');
  d.className = 'ref-row';
  d.innerHTML = '<input type="text" name="ref" placeholder="D1, D9">'
              + '<button type="button" class="rm-btn" onclick="this.parentNode.remove()">&times;</button>';
  document.getElementById('refs').appendChild(d);
}
</script>""" % max_slot
    h += js
    return page(h)
