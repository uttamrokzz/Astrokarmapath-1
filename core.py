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
         background: #f4f5f7; color: #222; padding-bottom: 30px; }
  header { background: #5e35b1; color: #fff; padding: 14px 16px;
           position: sticky; top: 0; z-index: 10;
           display: flex; align-items: center; justify-content: space-between; }
  header .brand { font-weight: 600; font-size: 16px; color: #fff;
                  text-decoration: none; }
  header .brand .inf { font-size: 22px; margin-left: 4px; }
  header nav a { color: #fff; text-decoration: none; margin-left: 10px;
                 font-size: 12px; opacity: 0.9; }
  main { padding: 14px; max-width: 780px; margin: 0 auto; }
  .title { text-align: center; margin: 30px 0; }
  .title h1 { font-size: 28px; color: #5e35b1; margin: 0; letter-spacing: -0.5px; }
  .title p  { color: #888; font-size: 13px; margin: 8px 0 0;
              letter-spacing: 2px; text-transform: uppercase; }
  .menu a { display: block; background: #fff; color: #333;
            text-decoration: none; padding: 18px 20px; border-radius: 12px;
            margin-bottom: 12px; font-size: 16px; font-weight: 500;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            border-left: 4px solid #5e35b1; }
  .menu a .arrow { float: right; color: #b0b0b0; }
  .btn { background: #5e35b1; color: #fff; border: none; padding: 11px 16px;
         border-radius: 8px; font-size: 14px; cursor: pointer;
         text-decoration: none; display: inline-block; }
  .btn-secondary { background: #e8eaf6; color: #4527a0; }
  .btn-danger { background: #c62828; color: #fff; }
  .top-bar { display: flex; justify-content: space-between;
             align-items: center; margin-bottom: 14px;
             gap: 8px; flex-wrap: wrap; }
  .top-bar h2 { margin: 0; font-size: 20px; }
  .top-bar .actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .card { background: #fff; border-radius: 12px; padding: 14px;
          margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);
          position: relative; }
  .card .name { font-size: 17px; font-weight: 600; margin: 0 0 8px; }
  .card .row { font-size: 14px; color: #555; margin: 3px 0; }
  .card .row b { color: #333; font-weight: 500;
                 display: inline-block; min-width: 50px; }
  .card .edit { position: absolute; top: 12px; right: 12px;
                color: #5e35b1; text-decoration: none; font-size: 18px; }
  .tags { margin-top: 10px; }
  .tags .pill { display: inline-block; background: #ede7f6; color: #4527a0;
                padding: 4px 10px; border-radius: 12px; font-size: 12px;
                margin: 3px 4px 0 0; }
  .tags .pill.multi { background: #e0f2f1; color: #00695c; }
  .tags .label { display: block; font-size: 11px; color: #999;
                 text-transform: uppercase; letter-spacing: 1px;
                 margin-top: 8px; }
  form label { font-size: 13px; color: #555; display: block;
               margin-top: 12px; font-weight: 500; }
  form input[type=text], form input[type=date], form input[type=time],
  form textarea, form select {
    width: 100%; padding: 11px; font-size: 15px;
    border: 1px solid #ccc; border-radius: 8px; margin-top: 4px;
    background: #fff; color: #222; }
  form .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .muted { color: #999; font-size: 13px; }
  .empty { text-align: center; color: #999; padding: 40px 10px; }
  .search-bar { display: flex; gap: 8px; margin-bottom: 12px; }
  .search-bar input { flex: 1; padding: 12px; font-size: 15px;
                      border: 1px solid #ccc; border-radius: 8px; }
  .letters { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 14px; }
  .letter { background: #fff; border: 1px solid #ddd; border-radius: 6px;
            padding: 6px 10px; font-size: 14px; cursor: pointer;
            color: #4527a0; font-weight: 600; min-width: 32px;
            text-align: center; }
  .letter:active { background: #ede7f6; }
  .section-label { font-size: 12px; color: #5e35b1; font-weight: 600;
                   text-transform: uppercase; letter-spacing: 1px;
                   margin: 18px 0 6px; }
  .result-box { background: #fff8e1; border-left: 4px solid #ffb300;
                padding: 12px; border-radius: 8px; margin: 10px 0; }
  .result-box b { color: #ef6c00; font-size: 12px;
                  text-transform: uppercase; letter-spacing: 1px; }
  .result-box p { margin: 6px 0 0; font-size: 15px; }
  .slot-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
              margin-top: 6px; }
  .slot-row input { padding: 10px; font-size: 14px; border: 1px solid #ccc;
                    border-radius: 8px; }
  .dasha-row { display: grid; grid-template-columns: 60px 1fr 1fr;
               gap: 6px; margin-top: 6px; }
  .dasha-row input { padding: 9px; font-size: 13px; border: 1px solid #ccc;
                     border-radius: 8px; }
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
