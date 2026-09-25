# -*- coding: utf-8 -*-
from flask import Blueprint
from core import page, nav

bp = Blueprint("learning", __name__)

@bp.route("/learning")
def learning():
    h = '<div class="top-bar"><h2>Learning Database</h2>' + nav("/") + "</div>"
    h += "<div class='card'><p class='name'>Coming soon</p>"
    h += "<p class='muted'>Collect rules, principles, textbook knowledge here.</p></div>"
    return page(h)
