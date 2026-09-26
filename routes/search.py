# -*- coding: utf-8 -*-
from flask import Blueprint, request
from core import q, page, nav

bp = Blueprint("search", __name__)


def find_people(term):
    starts = term + "%"
    anywhere = "%" + term + "%"
    rows = q("""SELECT id, name, birth_place, birth_date,
                       broader_tags, multiple_tags
                FROM people
                WHERE name LIKE ? OR IFNULL(birth_place,'') LIKE ?
                   OR IFNULL(broader_tags,'') LIKE ?
                   OR IFNULL(multiple_tags,'') LIKE ?
                   OR name LIKE ?
                ORDER BY
                  CASE WHEN name LIKE ? THEN 0 ELSE 1 END,
                  name
                LIMIT 20""",
             (starts, anywhere, anywhere, anywhere, anywhere, starts))
    out = []
    for r in rows:
        pid, name, place, dob, tags, stags = r
        # count linked items
        cc = q("SELECT COUNT(*) FROM combination_people WHERE person_id=?", (pid,))[0][0]
        rc = q("SELECT COUNT(*) FROM research_people WHERE person_id=?", (pid,))[0][0]
        out.append({
            "id": pid, "name": name or "",
            "place": place or "", "dob": dob or "",
            "tags": tags or "", "stags": stags or "",
            "cc": cc, "rc": rc,
        })
    return out


def find_combinations(term):
    starts = term + "%"
    anywhere = "%" + term + "%"
    rows = q("""SELECT DISTINCT c.id, c.title, c.body, c.chart_ref,
                                c.research_id, c.observation_num, c.is_main
                FROM combinations c
                LEFT JOIN combination_slots s ON s.combination_id = c.id
                LEFT JOIN combination_people cp ON cp.combination_id = c.id
                LEFT JOIN people p ON p.id = cp.person_id
                WHERE c.title LIKE ? OR c.title LIKE ?
                   OR IFNULL(c.body,'') LIKE ?
                   OR IFNULL(s.value,'') LIKE ?
                   OR IFNULL(s.label,'') LIKE ?
                   OR IFNULL(p.name,'') LIKE ?
                ORDER BY
                  CASE WHEN c.title LIKE ? THEN 0 ELSE 1 END,
                  c.id DESC
                LIMIT 20""",
             (starts, anywhere, anywhere, anywhere, anywhere,
              anywhere, starts))
    out = []
    for r in rows:
        cid = r[0]
        ppl = q("""SELECT p.name FROM people p
                   JOIN combination_people cp ON cp.person_id = p.id
                   WHERE cp.combination_id=?""", (cid,))
        rtitle = ""
        if r[4]:
            rr = q("SELECT event FROM research WHERE id=?", (r[4],))
            if rr:
                rtitle = rr[0][0] or ""
        out.append({
            "id": cid, "title": r[1] or "",
            "body": (r[2] or "")[:200], "cref": r[3] or "",
            "persons": ", ".join([p[0] for p in ppl if p[0]]),
            "research": rtitle, "obs_num": r[5] or "",
            "is_main": r[6] or 0,
        })
    return out


def find_research(term):
    starts = term + "%"
    anywhere = "%" + term + "%"
    rows = q("""SELECT DISTINCT r.id, r.event, r.event_date_from,
                                r.event_date_to, r.event_time
                FROM research r
                LEFT JOIN research_people rp ON rp.research_id = r.id
                LEFT JOIN people p ON p.id = rp.person_id
                WHERE r.event LIKE ? OR r.event LIKE ?
                   OR IFNULL(p.name,'') LIKE ?
                ORDER BY
                  CASE WHEN r.event LIKE ? THEN 0 ELSE 1 END,
                  r.id DESC
                LIMIT 20""",
             (starts, anywhere, anywhere, starts))
    out = []
    for r in rows:
        rid = r[0]
        ppl = q("""SELECT p.name FROM people p
                   JOIN research_people rp ON rp.person_id = p.id
                   WHERE rp.research_id=?""", (rid,))
        obs = q("SELECT COUNT(*) FROM combinations WHERE research_id=?", (rid,))[0][0]
        d = ""
        if r[2] or r[3]:
            d = "%s -> %s" % (r[2] or "?", r[3] or "?")
        out.append({
            "id": rid, "event": r[1] or "",
            "date": d, "persons": ", ".join([p[0] for p in ppl if p[0]]),
            "obs": obs,
        })
    return out


def relevance_score(item, term):
    """Simple scoring: exact match > starts with > contains."""
    t = term.lower()
    title = (item.get("name") or item.get("title")
             or item.get("event") or "").lower()
    if title == t:
        return 0
    if title.startswith(t):
        return 1
    if t in title:
        return 2
    return 3


@bp.route("/search")
def search():
    term = request.args.get("q", "").strip()
    body = ""

    if term:
        people = find_people(term)
        combos = find_combinations(term)
        research = find_research(term)

        # Mixed list, ranked by relevance
        mixed = []
        for p in people:
            mixed.append(("person", relevance_score(p, term), p))
        for c in combos:
            mixed.append(("combination", relevance_score(c, term), c))
        for r in research:
            mixed.append(("research", relevance_score(r, term), r))

        # Sort: first by score, then by type priority (research > comb > person)
        type_order = {"research": 0, "combination": 1, "person": 2}
        mixed.sort(key=lambda x: (x[1], type_order.get(x[0], 9)))

        if not mixed:
            body = "<div class='empty'>No matches for &ldquo;%s&rdquo;.</div>" % term
        else:
            body += "<p class='muted'>%d match(es) for &ldquo;%s&rdquo;</p>" % (
                len(mixed), term)
            for kind, score, item in mixed:
                if kind == "person":
                    body += render_person(item, term)
                elif kind == "combination":
                    body += render_combination(item, term)
                else:
                    body += render_research(item, term)

    h = '<div class="top-bar"><h2>Global Search</h2>' + nav("/") + '</div>'
    h += '<form method="get" class="search-bar">'
    h += '<input type="text" name="q" value="%s" placeholder="Search people, combinations, research..." autofocus>' % term
    h += '<button class="btn" type="submit">SEARCH</button></form>'
    h += body
    return page(h)


def render_person(item, term):
    h = "<div class='card'>"
    h += "<span class='chip p' style='float:right;margin-left:8px;'>P</span>"
    h += "<p class='card-title'><a href='/person/%d'>%s</a></p>" % (item["id"], item["name"])
    if item["dob"]:
        h += "<div class='row'><b>DOB</b> %s</div>" % item["dob"]
    if item["place"]:
        h += "<div class='row'><b>Loc</b> %s</div>" % item["place"]
    if item["tags"]:
        h += "<div style='margin-top:6px;'>"
        for t in [x.strip() for x in item["tags"].split(",") if x.strip()][:4]:
            h += "<span class='pill'>%s</span>" % t
        h += "</div>"
    if item["cc"] or item["rc"]:
        h += "<div class='row' style='color:#888;font-size:11px;margin-top:6px;'>"
        h += "&rarr; %d combos, %d research</div>" % (item["cc"], item["rc"])
    h += "</div>"
    return h


def render_combination(item, term):
    h = "<div class='card'>"
    h += "<span class='chip c' style='float:right;margin-left:8px;'>C</span>"
    h += "<p class='card-title'><a href='/combination/%d'>%s</a></p>" % (item["id"], item["title"])
    if item["is_main"]:
        h += "<span class='badge-main'>Main</span>"
    if item["body"]:
        show = item["body"]
        if len(show) > 160:
            show = show[:160] + "..."
        h += "<div class='body-display'>%s</div>" % show
    if item["cref"]:
        h += "<div class='row'><b>Refs</b>"
        for rr in [x.strip() for x in item["cref"].split(",") if x.strip()]:
            h += " <span class='pill ref'>%s</span>" % rr
        h += "</div>"
    if item["persons"]:
        h += "<div class='row'><b>Persons</b> %s</div>" % item["persons"]
    if item["research"]:
        h += "<div class='row' style='color:#888;font-size:11px;'>&rarr; research: %s" % item["research"]
        if item["obs_num"]:
            h += " (obs #%d)" % item["obs_num"]
        h += "</div>"
    h += "</div>"
    return h


def render_research(item, term):
    h = "<div class='card'>"
    h += "<span class='chip r' style='float:right;margin-left:8px;'>R</span>"
    h += "<p class='card-title'><a href='/research/%d'>%s</a></p>" % (item["id"], item["event"])
    if item["date"]:
        h += "<div class='row'><b>Date</b> %s</div>" % item["date"]
    if item["persons"]:
        h += "<div class='row'><b>Persons</b> %s</div>" % item["persons"]
    if item["obs"]:
        h += "<div class='row' style='color:#888;font-size:11px;'>&rarr; %d observations</div>" % item["obs"]
    h += "</div>"
    return h
