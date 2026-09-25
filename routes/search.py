# -*- coding: utf-8 -*-
from flask import Blueprint, request
from core import q, page

bp = Blueprint("search", __name__)


@bp.route("/search")
def search():
    term = request.args.get("q", "").strip()
    body = ""
    if term:
        like = "%" + term + "%"

        ppl = q("""SELECT id, name, birth_place FROM people
                   WHERE name LIKE ? OR IFNULL(birth_place,'') LIKE ?
                      OR IFNULL(broader_tags,'') LIKE ?
                      OR IFNULL(multiple_tags,'') LIKE ?
                   LIMIT 30""", (like, like, like, like))

        combos = q("""SELECT DISTINCT c.id, c.title, c.result
                      FROM combinations c
                      LEFT JOIN combination_slots s ON s.combination_id = c.id
                      WHERE c.title LIKE ? OR IFNULL(c.result,'') LIKE ?
                         OR IFNULL(s.value,'') LIKE ?
                         OR IFNULL(s.label,'') LIKE ?
                      LIMIT 30""", (like, like, like, like))

        res = q("""SELECT DISTINCT r.id, r.main_event, r.result
                   FROM research r
                   LEFT JOIN research_slots s ON s.research_id = r.id
                   WHERE r.main_event LIKE ? OR IFNULL(r.result,'') LIKE ?
                      OR IFNULL(s.value,'') LIKE ?
                      OR IFNULL(s.label,'') LIKE ?
                   LIMIT 30""", (like, like, like, like))

        if ppl:
            body += "<div class='card'><p class='name'>People (%d)</p>" % len(ppl)
            for pid, name, loc in ppl:
                body += "<div class='row'><a href='/person/%d'>%s</a> &mdash; %s</div>" % (pid, name, loc or "")
            body += "</div>"

        if combos:
            body += "<div class='card'><p class='name'>Combinations (%d)</p>" % len(combos)
            for cid, title, result in combos:
                body += "<div class='row'><a href='/combination/%d'>%s</a>" % (cid, title or "(untitled)")
                if result:
                    body += " &mdash; <span class='muted'>%s</span>" % result
                body += "</div>"
            body += "</div>"

        if res:
            body += "<div class='card'><p class='name'>Research (%d)</p>" % len(res)
            for rid, ev, result in res:
                body += "<div class='row'><a href='/research/%d'>%s</a>" % (rid, ev or "(event)")
                if result:
                    body += " &mdash; <span class='muted'>%s</span>" % result
                body += "</div>"
            body += "</div>"

        if not (ppl or combos or res):
            body = "<div class='empty'>No matches for &ldquo;%s&rdquo;.</div>" % term

    return page("""
      <div class="top-bar"><h2>Global Search</h2>
        <a class="btn btn-secondary" href="/">&larr; Home</a></div>
      <form method="get" class="search-bar">
        <input type="text" name="q" value="%s"
               placeholder="Search people, combos, research..." autofocus>
        <button class="btn" type="submit">Search</button>
      </form>%s
    """ % (term, body))
