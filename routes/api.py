# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from core import q, run

bp = Blueprint("api", __name__)


@bp.route("/api/people/search")
def people_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    like = "%" + term + "%"
    starts = term + "%"
    rows = q("""SELECT id, name, birth_place FROM people
                WHERE name LIKE ? OR name LIKE ?
                   OR IFNULL(birth_place,'') LIKE ?
                ORDER BY
                    CASE WHEN name LIKE ? THEN 0 ELSE 1 END,
                    name
                LIMIT 25""", (starts, like, like, starts))
    return jsonify([{"id": r[0], "name": r[1] or "",
                     "sub": r[2] or ""} for r in rows])


@bp.route("/api/combinations/search")
def combinations_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    like = "%" + term + "%"
    starts = term + "%"
    rows = q("""SELECT DISTINCT c.id, c.title, c.result
                FROM combinations c
                LEFT JOIN combination_slots s ON s.combination_id = c.id
                WHERE c.title LIKE ? OR c.title LIKE ?
                   OR IFNULL(c.result,'') LIKE ?
                   OR IFNULL(s.value,'') LIKE ?
                ORDER BY
                    CASE WHEN c.title LIKE ? THEN 0 ELSE 1 END,
                    c.id DESC
                LIMIT 25""", (starts, like, like, like, starts))
    return jsonify([{"id": r[0], "title": r[1] or "",
                     "sub": (r[2] or "")[:60]} for r in rows])


@bp.route("/api/research/search")
def research_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    like = "%" + term + "%"
    starts = term + "%"
    rows = q("""SELECT id, event FROM research
                WHERE event LIKE ? OR event LIKE ?
                ORDER BY
                    CASE WHEN event LIKE ? THEN 0 ELSE 1 END,
                    id DESC
                LIMIT 25""", (starts, like, starts))
    return jsonify([{"id": r[0], "event": r[1] or "",
                     "sub": ""} for r in rows])


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
