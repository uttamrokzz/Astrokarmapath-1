# -*- coding: utf-8 -*-
import os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from flask import Flask
from core import page

app = Flask(__name__)


@app.route("/")
def home():
    return page("""
      <div class="home-title">
        <h1>AstroKarmaPath &infin;</h1>
        <p>Turso</p>
      </div>
      <div class="home-menu" style="max-width:420px;margin:0 auto;">
        <a href="/people">&#128100; View / Add People</a>
        <a href="/combinations">&#128279; View / Add Combination</a>
        <a href="/research">&#128221; Research Notes</a>
        <a href="/search">&#128269; Search</a>
        <a href="/data">&#128190; Import / Export</a>
        <a href="/learning">&#128218; Learning Database</a>
      </div>
    """)


@app.route("/learning")
def learning():
    return page('<div class="top-bar"><h2>Learning Database</h2>'
                '<div class="actions"><a class="btn btn-secondary btn-sm" href="/">&#127968; Home</a></div></div>'
                '<div class="card"><p>Coming soon.</p></div>')


# Auto-register blueprints if their files exist
for modname in ["people", "combinations", "research", "search", "api", "data"]:
    try:
        mod = __import__("routes." + modname, fromlist=["bp"])
        app.register_blueprint(mod.bp)
        print("Registered:", modname)
    except Exception as e:
        print("Skipped:", modname, "-", e)


if __name__ == "__main__":
    print("=" * 60)
    print("AstroKarmaPath running.")
    print("Open: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
