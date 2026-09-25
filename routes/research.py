# -*- coding: utf-8 -*-
from flask import Blueprint, request, redirect
from core import q, run, insert_and_id, page, nav

bp = Blueprint("research", __name__)

def slots_of(rid):
    return q("SELECT slot_num, label, value FROM research_slots WHERE research_id=? ORDER BY slot_num", (rid,))

def card(r):
    rid, ev, result, evd, rf, rt, pname, combo = r
    sl = slots_of(rid)
    slot_summary = ""
    if sl:
        slot_summary = " + ".join([(s[2] or "")[:8] for s in sl if s[2]])
    h = "<div class='card'>"
    h += "<a class='edit' href='/research/%d/edit'>&#9998;</a>" % rid
    h += "<p class='name'><a href='/research/%d'>%s</a></p>" % (rid, ev or "(event)")
    h += "<div class='row'><b>Combination</b> %s</div>" % (combo or "<span class='muted'>not linked</span>")
    if slot_summary:
        h += "<div class='row'><b>Slots</b> <span class='muted'>%s</span></div>" % slot_summary
    if rf or rt:
        h += "<div class='row'><b>Date</b> %s &mdash; %s</div>" % (rf or "?", rt or "?")
    elif evd:
        h += "<div class='row'><b>Date</b> %s</div>" % evd
    if pname: h += "<div class='row'><b>Person</b> %s</div>" % pname
    if result: h += "<div class='result-box'><b>Result</b><p>%s</p></div>" % result
    h += "<div style='margin-top:10px;'>"
    h += "<a class='btn btn-secondary btn-sm' href='/research/%d'>VIEW</a> " % rid
    h += "<a class='btn btn-secondary btn-sm' href='/research/%d/edit'>EDIT</a> " % rid
    h += "<form method='post' action='/research/%d/delete' style='display:inline;' onsubmit=\"return confirm('Delete?');\"><button class='btn btn-danger btn-sm' type='submit'>DLT</button></form>" % rid
    h += "</div></div>"
    return h

@bp.route("/research")
def list_research():
    rows = q("""SELECT r.id, r.main_event, r.result, r.main_event_date,
                r.research_from, r.research_to,
                (SELECT name FROM people WHERE id=r.person_id),
                (SELECT title FROM combinations WHERE id=r.combination_id)
                FROM research r ORDER BY r.id DESC""")
    h = '<div class="top-bar"><h2>Research Notes</h2><div class="actions">'
    h += '<a class="btn btn-secondary btn-sm" href="/research/search">SEARCH</a>'
    h += '<a class="btn btn-sm" href="/research/new">+ NEW</a></div></div>'
    if not rows: return page(h + "<div class='empty'>No research notes yet.</div>")
    for r in rows: h += card(r)
    return page(h)

@bp.route("/research/search")
def search_research():
    h = '<div class="top-bar"><h2>Search Research</h2>' + nav("/research") + "</div>"
    h += '<div class="search-bar"><input type="text" id="q" autocomplete="off" autofocus placeholder="Event, result, slot..."></div>'
    h += '<div class="letters" id="letters"></div><div id="results"></div>'
    h += """<script>(function(){var i=document.getElementById('q'),r=document.getElementById('results'),l=document.getElementById('letters'),t=null;
    function c(x){var h="<div class='card'><p class='name'><a href='/research/"+x.id+"'>"+(x.title||'(event)')+"</a></p>";if(x.result)h+="<div class='result-box'><b>Result</b><p>"+x.result+"</p></div>";return h+"</div>";}
    function s(term){if(!term){r.innerHTML="";return;}fetch('/api/research/search?q='+encodeURIComponent(term)).then(function(x){return x.json();}).then(function(it){if(!it.length){r.innerHTML="<div class='empty'>No matches.</div>";return;}var h="<p class='muted'>"+it.length+" match(es)</p>";for(var j=0;j<it.length;j++)h+=c(it[j]);r.innerHTML=h;});}
    i.addEventListener('input',function(){clearTimeout(t);t=setTimeout(function(){s(i.value.trim());},200);});
    var A='ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split(''),hh='';for(var j=0;j<A.length;j++)hh+="<button class='letter' data-l='"+A[j]+"'>"+A[j]+"</button>";l.innerHTML=hh;
    l.addEventListener('click',function(e){var L=e.target.getAttribute('data-l');if(!L)return;i.value=L;s(L);});})();</script>"""
    return page(h)

@bp.route("/research/new", methods=["GET", "POST"])
def research_new():
    if request.method == "POST":
        rid = save_research(None)
        return redirect("/research/%d/saved" % rid)
    fc = request.args.get("from_combo", "").strip()
    pre = None; pre_slots = []
    if fc:
        try:
            cid = int(fc)
            cr = q("SELECT title, result, chart_ref, observation FROM combinations WHERE id=?", (cid,))
            if cr:
                pre = {"combination_id": cid, "title": cr[0][0], "result": cr[0][1],
                       "chart_ref": cr[0][2], "observation": cr[0][3]}
                pre_slots = slots_of(cid)
        except Exception: pass
    # last viewed research result for placeholder
    last = q("SELECT result FROM research WHERE result != '' ORDER BY id DESC LIMIT 1")
    last_result = last[0][0] if last else ""
    return page(research_form(None, pre, pre_slots, last_result))

@bp.route("/research/<int:rid>")
def research_view(rid):
    rows = q("""SELECT id, main_event, main_event_date, research_from, research_to,
                result, observation, person_id, combination_id FROM research WHERE id=?""", (rid,))
    if not rows: return page("<div class='empty'>Not found.</div>")
    rid, ev, evd, rf, rt, result, obs, pid, cid = rows[0]
    sl = slots_of(rid)
    dasha = q("SELECT level, lord, dasha_date FROM research_dasha WHERE research_id=? ORDER BY id", (rid,))
    pname = ""
    if pid:
        pr = q("SELECT name FROM people WHERE id=?", (pid,))
        if pr: pname = pr[0][0]
    combo = ""
    if cid:
        cr = q("SELECT title FROM combinations WHERE id=?", (cid,))
        if cr: combo = cr[0][0]
    h = '<div class="top-bar"><h2>%s</h2>' % (ev or "(event)") + nav("/research") + "</div>"
    h += "<div class='card'><div class='row'><b>Event</b> %s</div>" % (ev or "")
    if evd: h += "<div class='row'><b>Date</b> %s</div>" % evd
    if pname: h += "<div class='row'><b>Person</b> %s</div>" % pname
    if rf or rt: h += "<div class='row'><b>Range</b> %s &rarr; %s</div>" % (rf or "?", rt or "?")
    h += "</div>"
    if result: h += "<div class='card'><div class='result-box'><b>Result</b><p>%s</p></div></div>" % result
    if sl:
        h += "<div class='card'><span class='section-label'>Combination (Slots)</span>"
        for n, lbl, v in sl: h += "<div class='row'><b>%s</b> %s</div>" % (lbl or ("X%d" % n), v or "")
        h += "</div>"
    if dasha:
        h += "<div class='card'><span class='section-label'>Dasha</span>"
        for lvl, lord, dt in dasha: h += "<div class='row'><b>%s</b> %s &mdash; %s</div>" % (lvl or "", lord or "", dt or "")
        h += "</div>"
    if obs: h += "<div class='card'><span class='section-label'>Observation</span><p>%s</p></div>" % obs
    h += "<div class='card'>"
    if cid:
        h += "<span class='section-label'>Saved in Combinations DB</span><div class='row'>&#10003; <a href='/combination/%d'>%s</a></div>" % (cid, combo)
    else:
        h += "<p class='muted'>Not yet saved as a combination.</p>"
    h += "</div>"
    h += '<div style="margin-top:14px;"><a class="btn btn-secondary" href="/research/%d/edit">&#9998; EDIT</a> ' % rid
    h += '<form method="post" action="/research/%d/delete" style="display:inline;" onsubmit="return confirm(\'Delete?\');"><button class="btn btn-danger" type="submit">&#128465; DLT</button></form></div>' % rid
    return page(h)

@bp.route("/research/<int:rid>/edit", methods=["GET", "POST"])
def research_edit(rid):
    rows = q("""SELECT id, main_event, main_event_date, research_from, research_to,
                result, observation, person_id, combination_id FROM research WHERE id=?""", (rid,))
    if not rows: return page("<div class='empty'>Not found.</div>")
    if request.method == "POST":
        save_research(rid)
        return redirect("/research/%d" % rid)
    return page(research_form(rows[0], None, slots_of(rid), ""))

@bp.route("/research/<int:rid>/delete", methods=["POST"])
def research_delete(rid):
    run("DELETE FROM research_slots WHERE research_id=?", (rid,))
    run("DELETE FROM research_dasha WHERE research_id=?", (rid,))
    run("DELETE FROM research WHERE id=?", (rid,))
    return redirect("/research")

@bp.route("/research/<int:rid>/saved")
def research_saved(rid):
    rows = q("SELECT main_event, result, combination_id, person_id FROM research WHERE id=?", (rid,))
    if not rows: return redirect("/research")
    ev, result, cid, pid = rows[0]
    people = q("SELECT id, name FROM people ORDER BY name")
    h = '<div class="top-bar"><h2>Saved</h2>' + nav("/research") + "</div>"
    h += '<div class="sheet"><h3>&#10003; Research saved</h3><p class="muted">%s</p>' % (ev or "")
    if result: h += "<p class='muted'>Result: %s</p>" % result
    h += "</div>"
    h += '<form method="post" action="/research/%d/saved">' % rid
    h += '<div class="sheet"><h3>Link it to other places?</h3>'
    if not cid:
        h += '<div class="section-label">Save slots as a Combination?</div>'
        h += '<label class="chk"><input type="checkbox" name="save_as_combo" value="1" checked>Save to Combinations DB</label>'
    else:
        h += "<p class='muted'>Already linked to combination #%d.</p>" % cid
    h += '<div class="section-label">Link to People</div>'
    for p_id, name in people:
        ck = " checked" if pid and p_id == pid else ""
        h += '<label class="chk"><input type="checkbox" name="people" value="%d"%s>%s</label>' % (p_id, ck, name)
    h += '<div style="margin-top:18px;"><button class="btn" type="submit">Save links</button> '
    h += '<a class="btn btn-secondary" href="/research">Skip</a></div></div></form>'
    return page(h)

@bp.route("/research/<int:rid>/saved", methods=["POST"])
def research_saved_post(rid):
    rows = q("SELECT main_event, result, chart_ref, observation, combination_id FROM research WHERE id=?", (rid,))
    if not rows: return redirect("/research")
    ev, result, cref, obs, cid = rows[0]
    for pid in request.form.getlist("people"):
        try:
            run("UPDATE research SET person_id=? WHERE id=?", (int(pid), rid))
            run("INSERT OR IGNORE INTO research_people (research_id, person_id) VALUES (?, ?)", (rid, int(pid)))
        except Exception: pass
    if request.form.get("save_as_combo") and not cid:
        sl = slots_of(rid)
        title = "+".join([(v or "")[:4].upper() for n, lbl, v in sl if v])
        new_cid = insert_and_id("INSERT INTO combinations (title, result, chart_ref, observation) VALUES (?, ?, ?, ?)",
            (title, result, cref, obs))
        for n, lbl, v in sl:
            run("INSERT INTO combination_slots (combination_id, slot_num, label, value) VALUES (?, ?, ?, ?)", (new_cid, n, lbl, v))
        run("UPDATE research SET combination_id=? WHERE id=?", (new_cid, rid))
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
             result, observation, combination_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (int(pid) if pid else None, ev, evd, rf, rt, result, obs, int(cid) if cid else None))
    else:
        run("""UPDATE research SET person_id=?, main_event=?, main_event_date=?,
               research_from=?, research_to=?, result=?, observation=?, combination_id=?
               WHERE id=?""",
            (int(pid) if pid else None, ev, evd, rf, rt, result, obs, int(cid) if cid else None, rid))
        run("DELETE FROM research_slots WHERE research_id=?", (rid,))
        run("DELETE FROM research_dasha WHERE research_id=?", (rid,))
    for i in range(1, 51):
        lbl = request.form.get("slot_label_%d" % i, "").strip()
        val = request.form.get("slot_value_%d" % i, "").strip()
        if lbl or val:
            run("INSERT INTO research_slots (research_id, slot_num, label, value) VALUES (?, ?, ?, ?)", (rid, i, lbl, val))
    for i in range(1, 21):
        lvl = request.form.get("dasha_level_%d" % i, "").strip()
        lord = request.form.get("dasha_lord_%d" % i, "").strip()
        dt = request.form.get("dasha_date_%d" % i, "").strip()
        if lvl or lord or dt:
            run("INSERT INTO research_dasha (research_id, level, lord, dasha_date) VALUES (?, ?, ?, ?)", (rid, lvl, lord, dt))
    return rid

def research_form(row, pre, slots, last_result):
    if row is None:
        rid = None; ev = evd = rf = rt = obs = ""; result = ""; pid = None
        cid = pre.get("combination_id") if pre else None
        if pre:
            result = pre.get("result", "") or ""
            obs = pre.get("observation", "") or ""
    else:
        rid, ev, evd, rf, rt, result, obs, pid, cid = row
    heading = "Add Research" if rid is None else "Edit Research"
    action = "/research/%d/edit" % rid if rid else "/research/new"
    back = "/research/%d" % rid if rid else "/research"
    people = q("SELECT id, name FROM people ORDER BY name")
    opts = "<option value=''>-- none --</option>"
    for p_id, name in people:
        sel = " selected" if pid and p_id == pid else ""
        opts += "<option value='%d'%s>%s</option>" % (p_id, sel, name)
    sv = {n: (lbl, v) for n, lbl, v in slots}
    max_slot = max([n for n, _, _ in slots] or [3])
    if max_slot < 3: max_slot = 3
    slot_html = ""
    for i in range(1, max_slot + 1):
        lbl, v = sv.get(i, ("", ""))
        slot_html += '<div class="slot-row"><input type="text" name="slot_label_%d" value="%s" placeholder="FIELD %d"><input type="text" name="slot_value_%d" value="%s" placeholder="Jupiter / Aries / 7th"><button type="button" class="rm-btn" onclick="this.parentNode.remove()">&#10005;</button></div>' % (i, lbl or "", i, i, v or "")
    dasha = q("SELECT level, lord, dasha_date FROM research_dasha WHERE research_id=? ORDER BY id", (rid,)) if rid else []
    dasha_html = ""
    for i in range(1, 5):
        lvl = dasha[i-1][0] if i <= len(dasha) else ""
        lord = dasha[i-1][1] if i <= len(dasha) else ""
        dt = dasha[i-1][2] if i <= len(dasha) else ""
        dasha_html += '<div class="dasha-row"><input type="text" name="dasha_level_%d" value="%s" placeholder="MD/AD/PD"><input type="text" name="dasha_lord_%d" value="%s" placeholder="Lord"><input type="text" name="dasha_date_%d" value="%s" placeholder="Date"><button type="button" class="rm-btn" onclick="this.parentNode.remove()">&#10005;</button></div>' % (i, lvl or "", i, lord or "", i, dt or "")
    banner = ""
    if pre and rid is None:
        banner = '<div class="result-box"><b>From combination</b><p>%s</p></div>' % pre.get("title", "")
    combo_hidden = ""
    if cid:
        combo_hidden = '<input type="hidden" name="combination_id" value="%d">' % cid
    placeholder_result = last_result or "What does this produce?"
    h = '<div class="top-bar"><h2>%s</h2>' % heading + nav(back) + "</div>"
    h += banner
    h += '<div class="card"><form method="post" action="%s">' % action + combo_hidden
    h += '<div class="section-label">Event / Title</div>'
    h += '<input type="text" name="main_event" value="%s" placeholder="Anemia happened">' % (ev or "")
    h += '<div class="section-label">Date</div>'
    h += '<div class="row2"><div><label>Event Date</label><input type="date" name="main_event_date" value="%s"></div>' % (evd or "")
    h += '<div><label>Person</label><select name="person_id">%s</select>' % opts
    h += '<a href="#" onclick="document.getElementById(\'pmodal\').classList.add(\'on\'); return false;" style="font-size:11px; color:#5e35b1; margin-top:4px; display:inline-block;">+ ADD NEW PERSON</a>'
    h += '</div></div>'
    h += '<div class="row2"><div><label>Research From</label><input type="date" name="research_from" value="%s"></div>' % (rf or "")
    h += '<div><label>Research To</label><input type="date" name="research_to" value="%s"></div></div>' % (rt or "")
    h += '<div class="section-label">Combination (Slots) <button type="button" class="add" onclick="addSlot()">+ ADD SLOT</button></div>'
    h += '<div id="slots">%s</div>' % slot_html
    h += '<div class="section-label">Result</div>'
    h += '<input type="text" name="result" value="%s" placeholder="%s">' % (result or "", placeholder_result)
    h += '<div class="section-label">Dasha <button type="button" class="add" onclick="addDasha()">+ ADD DASHA</button></div>'
    h += '<div id="dasha">%s</div>' % dasha_html
    h += '<div class="section-label">Observation</div><textarea name="observation" rows="3">%s</textarea>' % (obs or "")
    h += '<div style="margin-top:20px;"><button class="btn" type="submit">SAVE RESEARCH</button> '
    h += '<a class="btn btn-secondary" href="%s">CANCEL</a></div></form></div>' % back
    h += """<div class="modal" id="pmodal"><div class="modal-inner">
      <h3>Add New Person</h3>
      <label>Name *</label><input type="text" id="np_name">
      <div class="row2"><div><label>DOB</label><input type="date" id="np_dob"></div>
      <div><label>TOB</label><input type="time" id="np_tob"></div></div>
      <label>Location</label><input type="text" id="np_loc" placeholder="Chennai, India">
      <div style="margin-top:14px;">
        <button class="btn" type="button" onclick="saveNP()">SAVE</button>
        <button class="btn btn-secondary" type="button" onclick="document.getElementById('pmodal').classList.remove('on')">CANCEL</button>
      </div>
    </div></div>
    <script>
    var slotN = %d, dashaN = 4;
    function addSlot(){slotN++;var d=document.createElement('div');d.className='slot-row';d.innerHTML='<input type="text" name="slot_label_'+slotN+'" placeholder="FIELD '+slotN+'"><input type="text" name="slot_value_'+slotN+'" placeholder="Jupiter / Aries"><button type="button" class="rm-btn" onclick="this.parentNode.remove()">&#10005;</button>';document.getElementById('slots').appendChild(d);}
    function addDasha(){dashaN++;var d=document.createElement('div');d.className='dasha-row';d.innerHTML='<input type="text" name="dasha_level_'+dashaN+'" placeholder="MD"><input type="text" name="dasha_lord_'+dashaN+'" placeholder="Lord"><input type="text" name="dasha_date_'+dashaN+'" placeholder="Date"><button type="button" class="rm-btn" onclick="this.parentNode.remove()">&#10005;</button>';document.getElementById('dasha').appendChild(d);}
    function saveNP(){
      var n=document.getElementById('np_name').value.trim();
      if(!n){alert('Name required');return;}
      var fd=new FormData();
      fd.append('name',n);
      fd.append('dob',document.getElementById('np_dob').value);
      fd.append('tob',document.getElementById('np_tob').value);
      fd.append('loc',document.getElementById('np_loc').value);
      fetch('/api/person/create',{method:'POST',body:fd}).then(function(r){return r.json();}).then(function(d){
        if(d.error){alert(d.error);return;}
        var sel=document.querySelector('select[name=person_id]');
        var opt=document.createElement('option');
        opt.value=d.id; opt.textContent=d.name; opt.selected=true;
        sel.appendChild(opt);
        document.getElementById('pmodal').classList.remove('on');
        document.getElementById('np_name').value='';
        document.getElementById('np_dob').value='';
        document.getElementById('np_tob').value='';
        document.getElementById('np_loc').value='';
      });
    }
    </script>""" % max_slot
    return page(h)
