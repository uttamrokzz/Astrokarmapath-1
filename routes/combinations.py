# -*- coding: utf-8 -*-
from flask import Blueprint, request, redirect
from core import q, run, insert_and_id, page, nav

bp = Blueprint("combinations", __name__)

def slots_of(cid):
    return q("SELECT slot_num, label, value FROM combination_slots WHERE combination_id=? ORDER BY slot_num", (cid,))

def refs_of(cid):
    r = q("SELECT chart_ref FROM combinations WHERE id=?", (cid,))
    return r[0][0] if r and r[0][0] else ""

def card(r):
    cid, title, result, cref, ppl = r
    h = "<div class='card'>"
    h += "<a class='edit' href='/combination/%d/edit'>&#9998;</a>" % cid
    h += "<p class='name'><a href='/combination/%d'>%s</a></p>" % (cid, title or "(untitled)")
    sl = slots_of(cid)
    if sl:
        cats = ", ".join([(s[2] or "") for s in sl if s[2]])
        if cats: h += "<div class='row' style='color:#888;'><b>Categories</b> %s</div>" % cats
    if cref:
        h += "<div class='row'><b>Refs</b>"
        for rr in [x.strip() for x in cref.split(",") if x.strip()]:
            h += " <span class='pill ref'>%s</span>" % rr
        h += "</div>"
    if result: h += "<div class='result-box'><b>Result</b><p>%s</p></div>" % result
    if ppl: h += "<div class='row'><b>Persons</b> %s</div>" % ppl
    linked = q("SELECT id, main_event FROM research WHERE combination_id=? ORDER BY id DESC", (cid,))
    if linked:
        h += "<div class='row'><b>Research</b>"
        for rid, ev in linked: h += " <span class='pill small'>%s</span>" % (ev or "")
        h += "</div>"
    else:
        h += "<div class='row' style='color:#c62828;'><b>Research</b> not linked</div>"
    h += "<div style='margin-top:10px;'>"
    h += "<a class='btn btn-secondary btn-sm' href='/combination/%d'>VIEW</a> " % cid
    h += "<a class='btn btn-secondary btn-sm' href='/combination/%d/edit'>EDIT</a> " % cid
    h += "<a class='btn btn-secondary btn-sm' href='/combination/%d/link_research'>LINK RESEARCH</a> " % cid
    h += "<form method='post' action='/combination/%d/delete' style='display:inline;' onsubmit=\"return confirm('Delete?');\"><button class='btn btn-danger btn-sm' type='submit'>DLT</button></form>" % cid
    h += "</div></div>"
    return h

@bp.route("/combinations")
def list_combinations():
    rows = q("""SELECT c.id, c.title, c.result, c.chart_ref,
                (SELECT GROUP_CONCAT(p.name, ', ') FROM combination_people cp
                 JOIN people p ON p.id = cp.person_id WHERE cp.combination_id = c.id)
                FROM combinations c ORDER BY c.id DESC""")
    h = '<div class="top-bar"><h2>Combinations</h2><div class="actions">'
    h += '<a class="btn btn-secondary btn-sm" href="/combinations/search">SEARCH</a>'
    h += '<a class="btn btn-sm" href="/combination/new">+ NEW</a></div></div>'
    if not rows: return page(h + "<div class='empty'>No combinations yet.</div>")
    for r in rows: h += card(r)
    return page(h)

@bp.route("/combinations/search")
def search_combinations():
    h = '<div class="top-bar"><h2>Search Combinations</h2>' + nav("/combinations") + "</div>"
    h += '<div class="search-bar"><input type="text" id="q" autocomplete="off" autofocus placeholder="Title, result, slot..."></div>'
    h += '<div class="letters" id="letters"></div><div id="results"></div>'
    h += """<script>(function(){var i=document.getElementById('q'),r=document.getElementById('results'),l=document.getElementById('letters'),t=null;
    function c(x){var h="<div class='card'><p class='name'><a href='/combination/"+x.id+"'>"+(x.title||'(untitled)')+"</a></p>";if(x.result)h+="<div class='result-box'><b>Result</b><p>"+x.result+"</p></div>";return h+"</div>";}
    function s(term){if(!term){r.innerHTML="";return;}fetch('/api/combinations/search?q='+encodeURIComponent(term)).then(function(x){return x.json();}).then(function(it){if(!it.length){r.innerHTML="<div class='empty'>No matches.</div>";return;}var h="<p class='muted'>"+it.length+" match(es)</p>";for(var j=0;j<it.length;j++)h+=c(it[j]);r.innerHTML=h;});}
    i.addEventListener('input',function(){clearTimeout(t);t=setTimeout(function(){s(i.value.trim());},200);});
    var A='ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split(''),hh='';for(var j=0;j<A.length;j++)hh+="<button class='letter' data-l='"+A[j]+"'>"+A[j]+"</button>";l.innerHTML=hh;
    l.addEventListener('click',function(e){var L=e.target.getAttribute('data-l');if(!L)return;i.value=L;s(L);});})();</script>"""
    return page(h)

@bp.route("/combination/new", methods=["GET", "POST"])
def combination_new():
    if request.method == "POST":
        cid = save_combination(None)
        return redirect("/combination/%d/saved" % cid)
    return page(combination_form(None, [], "", []))

@bp.route("/combination/<int:cid>")
def combination_view(cid):
    rows = q("SELECT id, title, result, chart_ref, observation FROM combinations WHERE id=?", (cid,))
    if not rows: return page("<div class='empty'>Not found.</div>")
    cid, title, result, cref, obs = rows[0]
    sl = slots_of(cid)
    ppl = q("""SELECT p.id, p.name FROM people p
               JOIN combination_people cp ON cp.person_id = p.id
               WHERE cp.combination_id=?""", (cid,))
    rsh = q("SELECT id, main_event FROM research WHERE combination_id=?", (cid,))
    h = '<div class="top-bar"><h2>%s</h2>' % (title or "(untitled)") + nav("/combinations") + "</div>"
    h += "<div class='card'><span class='section-label'>Slots (Combination)</span>"
    if sl:
        for n, lbl, v in sl: h += "<div class='row'><b>%s</b> %s</div>" % (lbl or ("X%d" % n), v or "")
    else: h += "<p class='muted'>No slots.</p>"
    h += "</div>"
    if result: h += "<div class='card'><div class='result-box'><b>Result</b><p>%s</p></div></div>" % result
    if cref:
        h += "<div class='card'><span class='section-label'>Refs</span>"
        for rr in [x.strip() for x in cref.split(",") if x.strip()]:
            h += "<span class='pill ref'>%s</span>" % rr
        h += "</div>"
    if obs: h += "<div class='card'><span class='section-label'>Observation</span><p>%s</p></div>" % obs
    h += "<div class='card'><span class='section-label'>Linked People (%d)</span>" % len(ppl)
    if ppl:
        for pid, name in ppl: h += "<div class='row'>&bull; <a href='/person/%d'>%s</a></div>" % (pid, name)
    else: h += "<p class='muted'>None</p>"
    h += "</div>"
    h += "<div class='card'><span class='section-label'>Linked Research (%d)</span>" % len(rsh)
    if rsh:
        for rid, ev in rsh: h += "<div class='row'>&bull; <a href='/research/%d'>%s</a></div>" % (rid, ev or "")
    else: h += "<p class='muted'>None</p>"
    h += '<div style="margin-top:10px;"><a class="btn btn-secondary btn-sm" href="/combination/%d/link_research">+ LINK RESEARCH</a></div></div>' % cid
    h += '<div style="margin-top:14px;"><a class="btn" href="/research/new?from_combo=%d">&#128300; Research this combo</a> ' % cid
    h += '<a class="btn btn-secondary" href="/combination/%d/edit">&#9998; EDIT</a> ' % cid
    h += '<form method="post" action="/combination/%d/delete" style="display:inline;" onsubmit="return confirm(\'Delete?\');"><button class="btn btn-danger" type="submit">&#128465; DLT</button></form></div>' % cid
    return page(h)

@bp.route("/combination/<int:cid>/edit", methods=["GET", "POST"])
def combination_edit(cid):
    rows = q("SELECT id, title, result, chart_ref, observation FROM combinations WHERE id=?", (cid,))
    if not rows: return page("<div class='empty'>Not found.</div>")
    if request.method == "POST":
        save_combination(cid)
        return redirect("/combination/%d" % cid)
    linked = [r[0] for r in q("SELECT person_id FROM combination_people WHERE combination_id=?", (cid,))]
    return page(combination_form(rows[0], slots_of(cid), rows[0][3] or "", linked))

@bp.route("/combination/<int:cid>/delete", methods=["POST"])
def combination_delete(cid):
    run("DELETE FROM combination_slots WHERE combination_id=?", (cid,))
    run("DELETE FROM combination_people WHERE combination_id=?", (cid,))
    run("UPDATE research SET combination_id=NULL WHERE combination_id=?", (cid,))
    run("DELETE FROM combinations WHERE id=?", (cid,))
    return redirect("/combinations")

@bp.route("/combination/<int:cid>/saved")
def combination_saved(cid):
    rows = q("SELECT title, result FROM combinations WHERE id=?", (cid,))
    if not rows: return redirect("/combinations")
    title, result = rows[0]
    people = q("SELECT id, name FROM people ORDER BY name")
    research = q("SELECT id, main_event FROM research ORDER BY id DESC LIMIT 30")
    h = '<div class="top-bar"><h2>Saved</h2>' + nav("/combinations") + "</div>"
    h += '<div class="sheet"><h3>&#10003; Combination saved</h3><p class="muted">%s</p>' % (title or "")
    if result: h += "<p class='muted'>Result: %s</p>" % result
    h += "</div>"
    h += '<form method="post" action="/combination/%d/saved">' % cid
    h += '<div class="sheet"><h3>Link it to other places?</h3>'
    h += '<div class="section-label">Save to Research DB</div>'
    h += '<input type="text" name="research_event" placeholder="Main event title (leave empty to skip)">'
    h += '<div class="section-label">Link to People</div>'
    for pid, name in people:
        h += '<label class="chk"><input type="checkbox" name="people" value="%d">%s</label>' % (pid, name)
    h += '<div class="section-label">Link to Existing Research</div>'
    for rid, ev in research:
        h += '<label class="chk"><input type="checkbox" name="research_link" value="%d">%s</label>' % (rid, ev or "")
    h += '<div style="margin-top:18px;"><button class="btn" type="submit">Save links</button> '
    h += '<a class="btn btn-secondary" href="/combinations">Skip</a></div></div></form>'
    return page(h)

@bp.route("/combination/<int:cid>/saved", methods=["POST"])
def combination_saved_post(cid):
    rows = q("SELECT title, result, chart_ref, observation FROM combinations WHERE id=?", (cid,))
    if not rows: return redirect("/combinations")
    title, result, cref, obs = rows[0]
    for pid in request.form.getlist("people"):
        try: run("INSERT OR IGNORE INTO combination_people (combination_id, person_id) VALUES (?, ?)", (cid, int(pid)))
        except Exception: pass
    for rid in request.form.getlist("research_link"):
        try: run("UPDATE research SET combination_id=? WHERE id=?", (cid, int(rid)))
        except Exception: pass
    ev = request.form.get("research_event", "").strip()
    if ev:
        rid = insert_and_id("INSERT INTO research (main_event, result, combination_id) VALUES (?, ?, ?)", (ev, result, cid))
        for n, lbl, v in slots_of(cid):
            run("INSERT INTO research_slots (research_id, slot_num, label, value) VALUES (?, ?, ?, ?)", (rid, n, lbl, v))
    return redirect("/combinations")

@bp.route("/combination/<int:cid>/link_research")
def combo_link_research(cid):
    rows = q("""SELECT id, main_event, result FROM research
                WHERE combination_id IS NULL OR combination_id != ?
                ORDER BY id DESC LIMIT 50""", (cid,))
    h = '<div class="top-bar"><h2>Link Research</h2>' + nav("/combination/%d" % cid) + "</div>"
    h += '<div class="search-bar"><input type="text" id="q" placeholder="Search research..." autocomplete="off"></div>'
    for rid, ev, result in rows:
        h += "<div class='picker-row'><div class='nm'>%s</div><div class='ac'>" % (ev or "")
        h += '<a class="btn btn-secondary btn-sm" href="/research/%d/edit">EDIT</a> ' % rid
        h += '<a class="btn btn-sm" href="/combination/%d/link_research/%d">LINK</a></div></div>' % (cid, rid)
    if not rows: h += "<div class='empty'>No unlinked research.</div>"
    h += '<div style="margin-top:12px;"><a class="btn" href="/research/new?from_combo=%d">+ NEW RESEARCH</a></div>' % cid
    return page(h)

@bp.route("/combination/<int:cid>/link_research/<int:rid>")
def combo_do_link_research(cid, rid):
    run("UPDATE research SET combination_id=? WHERE id=?", (cid, rid))
    return redirect("/combination/%d" % cid)

def save_combination(cid):
    title = request.form.get("title", "").strip()
    result = request.form.get("result", "").strip()
    refs_raw = request.form.getlist("chart_ref")
    cref = ", ".join([x.strip() for x in refs_raw if x.strip()])
    obs = request.form.get("observation", "").strip()
    if cid is None:
        cid = insert_and_id("INSERT INTO combinations (title, result, chart_ref, observation) VALUES (?, ?, ?, ?)", (title, result, cref, obs))
    else:
        run("UPDATE combinations SET title=?, result=?, chart_ref=?, observation=? WHERE id=?", (title, result, cref, obs, cid))
        run("DELETE FROM combination_slots WHERE combination_id=?", (cid,))
    for i in range(1, 51):
        lbl = request.form.get("slot_label_%d" % i, "").strip()
        val = request.form.get("slot_value_%d" % i, "").strip()
        if lbl or val:
            run("INSERT INTO combination_slots (combination_id, slot_num, label, value) VALUES (?, ?, ?, ?)", (cid, i, lbl, val))
    for pid in request.form.getlist("people"):
        try: run("INSERT OR IGNORE INTO combination_people (combination_id, person_id) VALUES (?, ?)", (cid, int(pid)))
        except Exception: pass
    return cid

def combination_form(row, slots, cref, linked):
    if row is None:
        cid = None; title = result = obs = ""; heading = "NEW COMBINATION"; cref = ""
    else:
        cid, title, result, cref2, obs = row
        cref = cref2 or cref
        heading = "EDIT COMBINATION"
    action = "/combination/%d/edit" % cid if cid else "/combination/new"
    back = "/combination/%d" % cid if cid else "/combinations"

    sv = {n: (lbl, v) for n, lbl, v in slots}
    max_slot = max([n for n, _, _ in slots] or [3])
    if max_slot < 3: max_slot = 3
    slot_html = ""
    for i in range(1, max_slot + 1):
        lbl, v = sv.get(i, ("", ""))
        slot_html += '<div class="slot-row"><input type="text" name="slot_label_%d" value="%s" placeholder="FIELD %d"><input type="text" name="slot_value_%d" value="%s" placeholder="Jupiter / Aries / 7th"><button type="button" class="rm-btn" onclick="this.parentNode.remove()">&#10005;</button></div>' % (i, lbl or "", i, i, v or "")

    ref_list = [x.strip() for x in (cref or "").split(",") if x.strip()]
    if not ref_list: ref_list = [""]
    ref_html = ""
    for i, rr in enumerate(ref_list, 1):
        ref_html += '<div class="ref-row"><input type="text" name="chart_ref" value="%s" placeholder="D1, D9"><button type="button" class="rm-btn" onclick="this.parentNode.remove()">&#10005;</button></div>' % (rr or "")

    all_ppl = q("SELECT id, name FROM people ORDER BY name")
    ppl_html = ""
    if not all_ppl: ppl_html = "<p class='muted'>No people yet.</p>"
    else:
        for pid, name in all_ppl:
            ck = " checked" if pid in linked else ""
            ppl_html += '<label class="chk"><input type="checkbox" name="people" value="%d"%s>%s</label>' % (pid, ck, name)

    res_html = ""
    if cid:
        rl = q("SELECT id, main_event FROM research WHERE combination_id=?", (cid,))
        if rl:
            for rid, ev in rl: res_html += "<div class='row'>&bull; <a href='/research/%d'>%s</a></div>" % (rid, ev or "")
        else: res_html = "<p class='muted'>No linked research.</p>"

    h = '<div class="top-bar"><h2>%s</h2>' % heading + nav(back) + "</div>"
    h += '<div class="card"><form method="post" action="%s">' % action
    h += '<label>Title (auto from slots if empty)</label><input type="text" name="title" value="%s" placeholder="JU+SAT+ASHWINI...">' % (title or "")
    h += '<div class="section-label">Fields / Slots <button type="button" class="add" onclick="addSlot()">+ ADD FIELD</button></div>'
    h += '<div id="slots">%s</div>' % slot_html
    h += '<div class="section-label">Result <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0;">— main title on card</span></div>'
    h += '<input type="text" name="result" value="%s" placeholder="Gives bad marriage...">' % (result or "")
    h += '<div class="section-label">Chart Refs <button type="button" class="add" onclick="addRef()">+ REF / CHART</button></div>'
    h += '<div id="refs">%s</div>' % ref_html
    h += '<div class="section-label">Observation</div><textarea name="observation" rows="3">%s</textarea>' % (obs or "")
    h += '<div class="section-label">Linked People</div>%s' % ppl_html
    if cid:
        h += '<div class="section-label">Linked Research <a class="add" href="/combination/%d/link_research">+ LINK</a></div>%s' % (cid, res_html)
    h += '<div style="margin-top:20px;"><button class="btn" type="submit">SAVE</button> '
    h += '<a class="btn btn-secondary" href="%s">CANCEL</a></div></form></div>' % back

    h += """<script>
    var slotN = %d, refN = 0;
    function addSlot() {
      slotN++;
      var d = document.createElement('div');
      d.className = 'slot-row';
      d.innerHTML = '<input type="text" name="slot_label_'+slotN+'" placeholder="FIELD '+slotN+'"><input type="text" name="slot_value_'+slotN+'" placeholder="Jupiter / Aries"><button type="button" class="rm-btn" onclick="this.parentNode.remove()">&#10005;</button>';
      document.getElementById('slots').appendChild(d);
    }
    function addRef() {
      refN++;
      var d = document.createElement('div');
      d.className = 'ref-row';
      d.innerHTML = '<input type="text" name="chart_ref" placeholder="D1, D9"><button type="button" class="rm-btn" onclick="this.parentNode.remove()">&#10005;</button>';
      document.getElementById('refs').appendChild(d);
    }
    </script>""" % max_slot
    return page(h)
