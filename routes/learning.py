# -*- coding: utf-8 -*-
from flask import Blueprint
from core import page

bp = Blueprint("learning", __name__)


@bp.route("/learning")
def learning():
    return page("""
      <div class="top-bar"><h2>Learning Database</h2>
        <a class="btn btn-secondary" href="/">&larr; Home</a></div>
      <div class="card">
        <p class="name">Coming soon</p>
        <p class="muted">This is where you'll collect rules, principles,
        and textbook knowledge &mdash; separate from your personal research.</p>
      </div>
    """)
