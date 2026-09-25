# -*- coding: utf-8 -*-
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from flask import Flask
from core import page
from routes import people, combinations, research, search, learning, api

app = Flask(__name__)


@app.route("/")
def home():
    return page("""
      <div class="title">
        <h1>AstroKarmaPath &infin;</h1>
        <p>Turso</p>
      </div>
      <div class="menu">
        <a href="/people">&#128100; View / Add People <span class="arrow">&rsaquo;</span></a>
        <a href="/combinations">&#128279; View / Add Combination <span class="arrow">&rsaquo;</span></a>
        <a href="/research">&#128221; Research Notes <span class="arrow">&rsaquo;</span></a>
        <a href="/search">&#128269; Search <span class="arrow">&rsaquo;</span></a>
        <a href="/learning">&#128218; Learning Database <span class="arrow">&rsaquo;</span></a>
      </div>
    """)


app.register_blueprint(people.bp)
app.register_blueprint(combinations.bp)
app.register_blueprint(research.bp)
app.register_blueprint(search.bp)
app.register_blueprint(learning.bp)
app.register_blueprint(api.bp)


if __name__ == "__main__":
    print("=" * 55)
    print("AstroKarmaPath is running.")
    print("Open in browser:  http://127.0.0.1:5000")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=False)
