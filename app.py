# -*- coding: utf-8 -*-
import os, sys
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
      <div style="text-align:center; margin:30px 0;">
        <h1 style="font-size:28px; color:#5e35b1; margin:0;">AstroKarmaPath &infin;</h1>
        <p style="color:#888; font-size:13px; margin:8px 0 0; letter-spacing:2px; text-transform:uppercase;">Turso</p>
      </div>
      <div style="max-width:400px; margin:0 auto;">
        <a href="/people" style="display:block; background:#fff; color:#333; text-decoration:none; padding:18px 20px; border-radius:12px; margin-bottom:12px; font-size:16px; font-weight:500; box-shadow:0 2px 6px rgba(0,0,0,0.08); border-left:4px solid #5e35b1;">&#128100; View / Add People</a>
        <a href="/combinations" style="display:block; background:#fff; color:#333; text-decoration:none; padding:18px 20px; border-radius:12px; margin-bottom:12px; font-size:16px; font-weight:500; box-shadow:0 2px 6px rgba(0,0,0,0.08); border-left:4px solid #5e35b1;">&#128279; View / Add Combination</a>
        <a href="/research" style="display:block; background:#fff; color:#333; text-decoration:none; padding:18px 20px; border-radius:12px; margin-bottom:12px; font-size:16px; font-weight:500; box-shadow:0 2px 6px rgba(0,0,0,0.08); border-left:4px solid #5e35b1;">&#128221; Research Notes</a>
        <a href="/search" style="display:block; background:#fff; color:#333; text-decoration:none; padding:18px 20px; border-radius:12px; margin-bottom:12px; font-size:16px; font-weight:500; box-shadow:0 2px 6px rgba(0,0,0,0.08); border-left:4px solid #5e35b1;">&#128269; Search</a>
        <a href="/learning" style="display:block; background:#fff; color:#333; text-decoration:none; padding:18px 20px; border-radius:12px; margin-bottom:12px; font-size:16px; font-weight:500; box-shadow:0 2px 6px rgba(0,0,0,0.08); border-left:4px solid #5e35b1;">&#128218; Learning Database</a>
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
    print("AstroKarmaPath running.")
    print("Open: http://127.0.0.1:5000")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=False)
