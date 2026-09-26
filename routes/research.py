# -*- coding: utf-8 -*-
from flask import Blueprint, request, redirect
from core import q, run, insert_and_id, page, nav

bp = Blueprint("research", __name__)


def observations_of(rid):
    """All combinations linked to this research."""
    return q("""SELECT id, title, body, observation_num, is_main,
                       chart_ref, event_date_from, event_date_to, log_date, log_time
                FROM combinations
                WHERE research_id = ?
                ORDER BY is_main DESC, observation_num ASC, id ASC""", (rid,))


def persons_of(rid):
    return q("""SELECT p.id, p.name FROM people p
                JOIN research_people rp ON rp.person_id = p.id
                WHERE rp.research_id = ? ORDER BY p.name""", (rid,))


def obs_slot_summary(cid):
    rows = q("SELECT value FROM combination_slots WHERE combination_id=? ORDER BY slot_num", (cid,))
    return " + ".join([(r[0] or "") for r in rows if r[0]])


def observation_card(o):
    (cid, title, body, obs_num, is_main, cref,
     edf, edt, logd, logt) = o
    h = "<div class='obs-card%s'>" % (" main" if is_main else "")
    h += "<p class='obs-title'><a href='/combination/%d' style='color:inherit;text-decoration:none;'>%s</a>" % (cid, title or "(untitled)")
    if is_main:
        h += " <span class='badge-main'>Main</span>"
    h += "</p>"
    ss = obs_slot_summary(cid)
    if ss:
        h += "<p class='obs-slots'>%s</p>" % ss
    if body:
        show = body if len(body) <= 180 else body[:180] + "..."
        h += "<div class='body-display'>%s</div>" % show
    if cref:
        h += "<div class='row'><b>Refs</b>"
        for rr in [x.strip() for x in cref.split(",") if x.strip()]:
            h += " <span class='pill ref'>%s</span>" % rr
        h += "</div>"
    if edf or edt:
        h += "<div class='row'><b>Event</b> %s &rarr; %s</div>" % (edf or "?", edt or "?")
    if logd:
        h += "<div class='row' style='color:#aaa;font-size:11px;'>Logged: %s %s</div>" % (logd, logt or "")
    h += "<div class='obs-actions'>"
    h += "<a class='btn btn-secondary btn-sm' href='/combination/%d'>VIEW</a> " % cid
    h += "<a class='btn btn-secondary btn-sm' href='/combination/%d/edit'>EDIT</a> " % cid
    if not is_main:
        h += "<a class='btn btn-secondary btn-sm' href='/research/%d/set_main/%d'>SET AS MAIN</a> " % (cid, cid)
        h += "<a class='btn btn-secondary btn-sm' href='/research/%d/set_main/%d'>Set Main</a> " if False else ""
    h += "<form method='post' action='/combination/%d/delete' style='display:inline;' onsubmit=\"return confirm('Delete this observation?');\">" % cid
    h += "<button class='btn btn-danger btn-sm' type='submit'>DLT</button></form>"
    h += "</div></div>"
    return h


# ---------- LIST ----------
@bp.route("/research")
def list_research():
    rows = q("""
        SELECT r.id, r.event, r.event_date_from, r.event_date_to,
               (SELECT GROUP_CONCAT(p.name, ', ')
                  FROM research_people rp
                  JOIN people p ON p.id = rp.person_id
                 WHERE rp.research_id = r.id),
               (SELECT COUNT(*) FROM combinations WHERE research_id = r.id)
        FROM research r ORDER BY r.id DESC
    """)
    h = '<div class="top-bar"><h2>Research Notes</h2><div class="actions">'
    h += '<a class="btn btn-secondary btn-sm" href="/research/search">SEARCH</a>'
    h += '<a class="btn btn-sm" href="/research/new">+ NEW</a></div></div>'
    if not rows:
        return page(h + '<div class="empty">No research yet. Tap + NEW.</div>')
    for rid, event, edf, edt, pnames, obs_count in rows:
        h += "<div class='card'>"
        h += "<a class='edit' href='/research/%d/edit'>&#9998;</a>" % rid
        h += "<p class='card-title'><a href='/research/%d'>%s</a></p>" % (rid, event or "(event)")
        if edf or edt:
            h += "<div class='row'><b>Date</b> %s &rarr; %s</div>" % (edf or "?", edt or "?")
        if pnames:
            h += "<div class='row'><b>Persons</b> %s</div>" % pnames
        h += "<div class='row' style='color:#888;'>&#128279; %d observations</div>" % obs_count
        h += "<div style='margin-top:10px;'>"
        h += "<a class='btn btn-secondary btn-sm' href='/research/%d'>VIEW</a> " % rid
        h += "<a class='btn btn-secondary btn-sm' href='/research/%d/edit'>EDIT</a> " % rid
        h += "<form method='post' action='/research/%d/delete' style='display:inline;' " % rid
        h += "onsubmit=\"return confirm('Delete this research and its observations?');\">"
        h += "<button class='btn btn-danger btn-sm' type='submit'>DLT</button></form>"
        h += "</div></div>"
    return page(h)


# ---------- SEARCH ----------
@bp.route("/research/search")
def search_research():
    h = '<div class="top-bar"><h2>Search Research</h2>' + nav("/research") + '</div>'
    h += '<div class="search-bar"><input type="text" id="q" autocomplete="off" autofocus placeholder="Event name..."></div>'
    h += '<div class="letters" id="letters"></div>'
    h += '<div id="results"></div>'
    h += """<script>
(function(){
  var inp = document.getElementById('q'),
      res = document.getElementById('results'),
      let_ = document.getElementById('letters'),
      tmr = null;
  function render(items){
    if (!items || !items.length){
      res.innerHTML = "<div class='empty'>No matches.</div>";
      return;
    }
    var h = "<p class='muted'>" + items.length + " match(es)</p>";
    for (var i = 0; i < items.length; i++){
      var x = items[i];
      h += "<div class='card'><p class='card-title'><a href='/research/" + x.id + "'>" + (x.event || '(event)') + "</a></p>";
      if (x.date) h += "<div class='row'><b>Date</b> " + x.date + "</div>";
      h += "</div>";
    }
    res.innerHTML = h;
  }
  function search(term){
    if (!term){ res.innerHTML = ""; return; }
    fetch('/api/research/search?q=' + encodeURIComponent(term))
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


# ---------- NEW ----------
@bp.route("/research/new", methods=["GET", "POST"])
def research_new():
    if request.method == "POST":
        rid = save_research(None)
        return redirect("/research/%d" % rid)
    return page(research_form(None, []))


# ---------- VIEW ----------
@bp.route("/research/<int:rid>")
def research_view(rid):
    rows = q("""SELECT id, event, event_date_from, event_date_to, event_time
                FROM research WHERE id=?""", (rid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    rid, event, edf, edt, etime = rows[0]

    obs = observations_of(rid)
    ppl = persons_of(rid)

    h = '<div class="top-bar"><h2>%s</h2>' % (event or "(event)") + nav("/research") + '</div>'

    h += "<div class='card'>"
    if edf or edt:
        h += "<div class='row'><b>Date</b> %s &rarr; %s" % (edf or "?", edt or "?")
        if etime:
            h += " at %s" % etime
        h += "</div>"
    if ppl:
        names = ", ".join([p[1] for p in ppl])
        h += "<div class='row'><b>Persons</b> %s</div>" % names
    h += "<div class='row'><b>Observations</b> %d</div>" % len(obs)
    h += "</div>"

    h += "<div class='section-label'>Observations</div>"
    if obs:
        for o in obs:
            h += observation_card(o)
    else:
        h += "<div class='empty'>No observations yet. Tap + ADD OBSERVATION.</div>"

    h += '<div style="margin-top:14px;">'
    h += '<a class="btn" href="/combination/new?research_id=%d&prefill_title=%s">+ ADD OBSERVATION</a> ' % (
        rid, ("%s+%d" % (event.replace(" ", "+"), len(obs) + 1)) if event else "Observation")
    h += '<a class="btn btn-secondary" href="/research/%d/edit">&#9998; EDIT</a> ' % rid
    h += '<form method="post" action="/research/%d/delete" style="display:inline;" ' % rid
    h += 'onsubmit="return confirm(\'Delete this research and all observations?\');">'
    h += '<button class="btn btn-danger" type="submit">&#128465; DLT</button></form></div>'

    return page(h)


# ---------- EDIT ----------
@bp.route("/research/<int:rid>/edit", methods=["GET", "POST"])
def research_edit(rid):
    rows = q("SELECT id, event, event_date_from, event_date_to, event_time FROM research WHERE id=?", (rid,))
    if not rows:
        return page("<div class='empty'>Not found.</div>")
    if request.method == "POST":
        save_research(rid)
        return redirect("/research/%d" % rid)
    linked = [p[0] for p in persons_of(rid)]
    return page(research_form(rows[0], linked))


# ---------- DELETE ----------
@bp.route("/research/<int:rid>/delete", methods=["POST"])
def research_delete(rid):
    run("DELETE FROM research_people WHERE research_id=?", (rid,))
    # observations become standalone combinations
    run("UPDATE combinations SET research_id=NULL, observation_num=NULL, is_main=0 WHERE research_id=?", (rid,))
    run("DELETE FROM research WHERE id=?", (rid,))
    return redirect("/research")


# ---------- SET MAIN ----------
@bp.route("/research/<int:rid>/set_main/<int:cid>")
def set_main(rid, cid):
    run("UPDATE combinations SET is_main=0 WHERE research_id=?", (rid,))
    run("UPDATE combinations SET is_main=1 WHERE id=? AND research_id=?", (cid, rid))
    return redirect("/research/%d" % rid)


# ---------- SAVE ----------
def save_research(rid):
    event = request.form.get("event", "").strip()
    edf = request.form.get("event_date_from", "").strip()
    edt = request.form.get("event_date_to", "").strip()
    etime = request.form.get("event_time", "").strip()
    ppl = request.form.getlist("people")

    if rid is None:
        rid = insert_and_id("""INSERT INTO research
            (event, event_date_from, event_date_to, event_time)
            VALUES (?, ?, ?, ?)""", (event, edf, edt, etime))
    else:
        run("""UPDATE research SET event=?, event_date_from=?,
               event_date_to=?, event_time=? WHERE id=?""",
            (event, edf, edt, etime, rid))
        run("DELETE FROM research_people WHERE research_id=?", (rid,))

    for pid in ppl:
        try:
            run("INSERT OR IGNORE INTO research_people (research_id, person_id) VALUES (?, ?)",
                (rid, int(pid)))
        except Exception:
            pass
    return rid


def research_form(row, linked_ids):
    if row is None:
        rid = None
        event = edf = edt = etime = ""
        heading = "NEW RESEARCH"
    else:
        rid, event, edf, edt, etime = row
        heading = "EDIT RESEARCH"

    action = "/research/%d/edit" % rid if rid else "/research/new"
    back = "/research/%d" % rid if rid else "/research"

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

    h += '<label>Event *</label>'
    h += '<input type="text" name="event" value="%s" required placeholder="Anemia happened">' % (event or "")

    h += '<div class="section-label">Event date</div>'
    h += '<div class="row2">'
    h += '<div><label>From</label><input type="date" name="event_date_from" value="%s"></div>' % (edf or "")
    h += '<div><label>To</label><input type="date" name="event_date_to" value="%s"></div>' % (edt or "")
    h += '</div>'
    h += '<label>Time (optional)</label><input type="time" name="event_time" value="%s">' % (etime or "")

    h += '<div class="section-label">Persons</div>'
    h += ppl_html

    h += '<div style="margin-top:22px;">'
    h += '<button class="btn" type="submit">SAVE</button> '
    h += '<a class="btn btn-secondary" href="%s">CANCEL</a>' % back
    h += '</div></form></div>'
    return page(h)
