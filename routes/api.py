# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from core import q, run

bp = Blueprint("api", __name__)

@bp.route("/api/people/search")
def p():
    t = request.args.get("q", "").strip()
    if not t: return jsonify([])
    like = t + "%"; anyw = "%" + t + "%"
    rows = q("""SELECT id, name, birth_place FROM people
                WHERE name LIKE ? OR birth_place LIKE ? OR name LIKE ?
                ORDER BY name LIMIT 25""", (like, anyw, anyw))
    return jsonify([{"id": r[0], "name": r[1], "place": r[2] or ""} for r in rows])

@bp.route("/api/combinations/search")
def c():
    t = request.args.get("q", "").strip()
    if not t: return jsonify([])
    like = "%" + t + "%"
    rows = q("""SELECT DISTINCT c.id, c.title, c.result FROM combinations c
                LEFT JOIN combination_slots s ON s.combination_id = c.id
                WHERE c.title LIKE ? OR IFNULL(c.result,'') LIKE ?
                   OR IFNULL(s.value,'') LIKE ?
                ORDER BY c.id DESC LIMIT 25""", (like, like, like))
    return jsonify([{"id": r[0], "title": r[1] or "", "result": r[2] or ""} for r in rows])

@bp.route("/api/research/search")
def r():
    t = request.args.get("q", "").strip()
    if not t: return jsonify([])
    like = "%" + t + "%"
    rows = q("""SELECT DISTINCT r.id, r.main_event, r.result FROM research r
                LEFT JOIN research_slots s ON s.research_id = r.id
                WHERE r.main_event LIKE ? OR IFNULL(r.result,'') LIKE ?
                   OR IFNULL(s.value,'') LIKE ?
                ORDER BY r.id DESC LIMIT 25""", (like, like, like))
    return jsonify([{"id": r[0], "title": r[1] or "", "result": r[2] or ""} for r in rows])

@bp.route("/api/person/create", methods=["POST"])
def person_create():
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    run("""INSERT INTO people (name, birth_date, birth_time, birth_place)
           VALUES (?, ?, ?, ?)""",
        (name, request.form.get("dob", ""), request.form.get("tob", ""),
         request.form.get("loc", "")))
    rid = q("SELECT last_insert_rowid()")[0][0]
    return jsonify({"id": rid, "name": name})
