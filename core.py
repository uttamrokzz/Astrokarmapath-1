# -*- coding: utf-8 -*-
import turso_serverless as turso
from config import URL, TOKEN

def conn():
    return turso.connect(URL, auth_token=TOKEN)

def q(sql, args=()):
    c = conn(); cur = c.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()
    c.close()
    return rows

def run(sql, args=()):
    c = conn(); cur = c.cursor()
    cur.execute(sql, args)
    c.commit()
    c.close()

def insert_and_id(sql, args=()):
    c = conn(); cur = c.cursor()
    cur.execute(sql, args)
    c.commit()
    cur.execute("SELECT last_insert_rowid()")
    rid = cur.fetchone()[0]
    c.close()
    return rid

LAYOUT = """<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AstroKarmaPath</title>
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system, Roboto, sans-serif; margin: 0;
       background: #f4f5f7; color: #222; padding-bottom: 40px; }
header { background: #5e35b1; color: #fff; padding: 12px 14px;
         position: sticky; top: 0; z-index: 10;
         display: flex; align-items: center; justify-content: space-between;
         flex-wrap: wrap; gap: 6px; }
header .brand { font-weight: 600; font-size: 15px; color: #fff;
                text-decoration: none; }
header .inf { font-size: 20px; margin-left: 4px; }
header nav a { color: #fff; text-decoration: none; margin-left: 10px;
               font-size: 12px; opacity: 0.9; }
main { padding: 14px; max-width: 780px; margin: 0 auto; }
.top-bar { display: flex; justify-content: space-between; align-items: center;
           margin-bottom: 14px; gap: 8px; flex-wrap: wrap; }
.top-bar h2 { margin: 0; font-size: 19px; }
.top-bar .actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn { background: #5e35b1; color: #fff; border: none; padding: 10px 14px;
       border-radius: 8px; font-size: 13px; cursor: pointer;
       text-decoration: none; display: inline-block; }
.btn-sm { padding: 6px 10px; font-size: 12px; }
.btn-secondary { background: #e8eaf6; color: #4527a0; }
.btn-danger { background: #c62828; color: #fff; }
.card { background: #fff; border-radius: 12px; padding: 14px;
        margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        position: relative; }
.card .name { font-size: 16px; font-weight: 600; margin: 0 0 8px; }
.card .name a { color: inherit; text-decoration: none; }
.card .row { font-size: 13px; color: #555; margin: 3px 0; }
.card .row b { color: #333; font-weight: 500;
               display: inline-block; min-width: 80px; }
.card .edit { position: absolute; top: 10px; right: 10px;
              color: #5e35b1; text-decoration: none; font-size: 16px; }
.pill { display: inline-block; background: #ede7f6; color: #4527a0;
        padding: 3px 9px; border-radius: 10px; font-size: 11px;
        margin: 2px 3px 0 0; }
.pill.multi { background: #e0f2f1; color: #00695c; }
.pill.ref { background: #fff3e0; color: #e65100; }
.pill.small { padding: 2px 6px; font-size: 10px; }
.label { display: block; font-size: 10px; color: #999;
         text-transform: uppercase; letter-spacing: 1px; margin-top: 8px; }
form label { font-size: 13px; color: #555; display: block;
             margin-top: 12px; font-weight: 500; }
form input[type=text], form input[type=date], form input[type=time],
form textarea, form select {
  width: 100%; padding: 10px; font-size: 14px;
  border: 1px solid #ccc; border-radius: 8px; margin-top: 4px;
  background: #fff; color: #222; font-family: inherit; }
form .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.muted { color: #999; font-size: 12px; }
.empty { text-align: center; color: #999; padding: 40px 10px; }
.search-bar { display: flex; gap: 6px; margin-bottom: 12px; }
.search-bar input { flex: 1; padding: 11px; font-size: 14px;
                    border: 1px solid #ccc; border-radius: 8px; }
.letters { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 14px; }
.letter { background: #fff; border: 1px solid #ddd; border-radius: 6px;
          padding: 6px 9px; font-size: 13px; cursor: pointer;
          color: #4527a0; font-weight: 600; min-width: 30px;
          text-align: center; }
.letter:active { background: #ede7f6; }
.section-label { font-size: 11px; color: #5e35b1; font-weight: 600;
                 text-transform: uppercase; letter-spacing: 1px;
                 margin: 16px 0 6px; display: flex;
                 justify-content: space-between; align-items: center; }
.section-label .add { font-size: 11px; color: #5e35b1; text-decoration: none;
                      background: #ede7f6; padding: 4px 10px; border-radius: 6px;
                      cursor: pointer; border: none; }
.result-box { background: #fff8e1; border-left: 4px solid #ffb300;
              padding: 10px 12px; border-radius: 6px; margin: 8px 0; }
.result-box b { color: #ef6c00; font-size: 11px;
                text-transform: uppercase; letter-spacing: 1px; }
.result-box p { margin: 4px 0 0; font-size: 14px; }
.slot-row { display: grid; grid-template-columns: 1fr 1fr 32px; gap: 6px;
            margin-top: 6px; align-items: center; }
.slot-row input { padding: 9px; font-size: 13px; border: 1px solid #ccc;
                  border-radius: 8px; width: 100%; margin: 0; }
.dasha-row { display: grid; grid-template-columns: 60px 1fr 1fr 32px;
             gap: 5px; margin-top: 5px; align-items: center; }
.dasha-row input { padding: 8px; font-size: 12px; border: 1px solid #ccc;
                   border-radius: 8px; width: 100%; margin: 0; }
.ref-row { display: grid; grid-template-columns: 1fr 32px; gap: 6px;
           margin-top: 6px; align-items: center; }
.ref-row input { padding: 9px; font-size: 13px; border: 1px solid #ccc;
                 border-radius: 8px; width: 100%; margin: 0; }
.rm-btn { background: #ffebee; color: #c62828; border: none;
          border-radius: 6px; padding: 6px 8px; font-size: 14px;
          cursor: pointer; font-weight: bold; }
.picker-row { display: flex; justify-content: space-between;
              align-items: center; padding: 10px 12px;
              background: #fff; border: 1px solid #eee; border-radius: 8px;
              margin-bottom: 6px; }
.picker-row .nm { font-size: 14px; font-weight: 500; }
.picker-row .ac { display: flex; gap: 4px; }
.sheet { background: #fff; border-radius: 12px; padding: 16px;
         box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 12px; }
.sheet h3 { margin: 0 0 10px; font-size: 16px; color: #2e7d32; }
.chk { display: flex; align-items: center; padding: 8px 0;
       font-size: 14px; }
.chk input { width: auto; margin-right: 8px; }
.modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
         background: rgba(0,0,0,0.5); z-index: 100;
         align-items: center; justify-content: center; padding: 16px; }
.modal.on { display: flex; }
.modal-inner { background: #fff; border-radius: 12px; padding: 18px;
               width: 100%; max-width: 400px; max-height: 80vh; overflow-y: auto; }
.modal-inner h3 { margin: 0 0 12px; font-size: 17px; }
</style>
</head><body>
<header>
  <a class="brand" href="/">AstroKarmaPath <span class="inf">&infin;</span></a>
  <nav>
    <a href="/people">People</a>
    <a href="/combinations">Combos</a>
    <a href="/research">Research</a>
    <a href="/search">Search</a>
  </nav>
</header>
<main>__BODY__</main>
</body></html>"""

def page(body):
    return LAYOUT.replace("__BODY__", body)

NAV = '<div class="actions"><a class="btn btn-secondary btn-sm" href="__BACK__">&larr; Back</a><a class="btn btn-secondary btn-sm" href="/">&#127968; Home</a></div>'

def nav(back):
    return NAV.replace("__BACK__", back)
