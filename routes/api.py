# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from core import q

bp = Blueprint("api", __name__)


@bp.route("/api/people/search")
def api_people_search():
    term = request.args.get("q", "").strip()
    if not term:
        return jsonify([])
    like = term + "%"
    like_any = "%" + term + "%"
    rows = q("""SELECT id, name, birth_place, birth_date FROM people
                WHERE name LIKE ? OR birth_place LIKE ?
                   OR name LIKE ?
                ORDER BY name LIMIT 25""", (like, like_any, like_any))
    return jsonify([
        {"id": r[0], "name": r[1], "place": r[2] or "", "dob": r[3] or ""}
        for r in rows
    ])
