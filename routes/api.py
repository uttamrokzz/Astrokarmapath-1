# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from core import q, run

bp = Blueprint("api", __name__)


@bp.route("/api/people/search")
def people_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    starts = term + "%"
    anywhere = "%" + term + "%"
    rows = q("""SELECT id, name, birth_place, birth_date FROM people
                WHERE name LIKE ? OR IFNULL(birth_place,'') LIKE ?
                   OR name LIKE ?
                ORDER BY name LIMIT 25""", (starts, anywhere, anywhere))
    return jsonify([{"id": r[0], "name": r[1] or "",
                     "place": r[2] or "", "dob": r[3] or ""}
                    for r in rows])


@bp.route("/api/person/create", methods=["POST"])
def person_create():
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    run("""INSERT INTO people (name, birth_date, birth_time, birth_place)
           VALUES (?, ?, ?, ?)""",
        (name, request.form.get("dob", ""), request.form.get("tob", ""),
         request.form.get("loc", "")))
    rid = q("SELECT last_insert_rowid()")[0][0]
    return jsonify({"id": rid, "name": name})


@bp.route("/api/combinations/search")
def combinations_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    starts = term + "%"
    anywhere = "%" + term + "%"
    rows = q("""SELECT DISTINCT c.id, c.title, c.body FROM combinations c
                LEFT JOIN combination_slots s ON s.combination_id = c.id
                WHERE c.title LIKE ? OR IFNULL(c.body,'') LIKE ?
                   OR IFNULL(s.value,'') LIKE ? OR IFNULL(s.label,'') LIKE ?
                   OR c.title LIKE ?
                ORDER BY c.id DESC LIMIT 25""",
             (starts, anywhere, anywhere, anywhere, anywhere))
    out = []
    for r in rows:
        body = (r[2] or "").replace("\n", " ")
        if len(body) > 100:
            body = body[:100] + "..."
        out.append({"id": r[0], "title": r[1] or "", "body": body})
    return jsonify(out)


@bp.route("/api/research/search")
def research_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    starts = term + "%"
    anywhere = "%" + term + "%"
    rows = q("""SELECT id, event, event_date_from, event_date_to FROM research
                WHERE event LIKE ? OR event LIKE ?
                ORDER BY id DESC LIMIT 25""", (starts, anywhere))
    out = []
    for r in rows:
        d = ""
        if r[2] or r[3]:
            d = "%s -> %s" % (r[2] or "?", r[3] or "?")
        out.append({"id": r[0], "event": r[1] or "", "date": d})
    return jsonify(out)
