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


CSS = """*{box-sizing:border-box}
body{font-family:-apple-system,Roboto,sans-serif;margin:0;background:#f4f5f7;color:#222;padding-bottom:60px}
header{background:#5e35b1;color:#fff;padding:12px 14px;position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
header .brand{font-weight:600;font-size:15px;color:#fff;text-decoration:none}
header .inf{font-size:20px;margin-left:4px}
header nav a{color:#fff;text-decoration:none;margin-left:10px;font-size:12px;opacity:.9}
main{padding:14px;max-width:820px;margin:0 auto}
.top-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;gap:8px;flex-wrap:wrap}
.top-bar h2{margin:0;font-size:20px}
.top-bar .actions{display:flex;gap:6px;flex-wrap:wrap}
.btn{background:#5e35b1;color:#fff;border:none;padding:11px 16px;border-radius:8px;font-size:14px;cursor:pointer;text-decoration:none;display:inline-block}
.btn-sm{padding:7px 11px;font-size:12px}
.btn-secondary{background:#e8eaf6;color:#4527a0}
.btn-danger{background:#c62828;color:#fff}
.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 2px 6px rgba(0,0,0,.08);position:relative}
.card-title{font-size:17px;font-weight:600;margin:0 0 8px}
.card-title a{color:inherit;text-decoration:none}
.card .edit{position:absolute;top:12px;right:12px;color:#5e35b1;text-decoration:none;font-size:16px}
.row{font-size:13px;color:#555;margin:4px 0}
.row b{color:#333;font-weight:500;display:inline-block;min-width:80px}
.muted{color:#999;font-size:13px}
.empty{text-align:center;color:#999;padding:40px 10px}
.label{display:block;font-size:10px;color:#999;text-transform:uppercase;letter-spacing:1px;margin-top:8px}
.section-label{font-size:11px;color:#5e35b1;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin:18px 0 8px;display:flex;justify-content:space-between;align-items:center}
.section-label .add{font-size:11px;color:#5e35b1;text-decoration:none;background:#ede7f6;padding:4px 10px;border-radius:6px;cursor:pointer;border:none}
form label{font-size:13px;color:#555;display:block;margin-top:14px;font-weight:500}
input[type=text],input[type=date],input[type=time],input[type=number],textarea,select{width:100%;padding:11px;font-size:14px;border:1px solid #ccc;border-radius:8px;margin-top:5px;background:#fff;color:#222;font-family:inherit}
textarea{resize:vertical;min-height:80px}
input:focus,textarea:focus,select:focus{outline:none;border-color:#5e35b1;box-shadow:0 0 0 2px rgba(94,53,177,.15)}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:500px){.row2{grid-template-columns:1fr}}
.pill{display:inline-block;background:#ede7f6;color:#4527a0;padding:3px 10px;border-radius:10px;font-size:11px;margin:2px 3px 0 0}
.pill.multi{background:#e0f2f1;color:#00695c}
.pill.ref{background:#fff3e0;color:#e65100}
.pill.small{padding:2px 7px;font-size:10px}
.chip{display:inline-block;width:22px;height:22px;border-radius:50%;text-align:center;line-height:22px;font-size:11px;font-weight:700;color:#fff;vertical-align:middle}
.chip.p{background:#5e35b1}
.chip.c{background:#ef6c00}
.chip.r{background:#2e7d32}
.result-box{background:#fff8e1;border-left:4px solid #ffb300;padding:12px 14px;border-radius:6px;margin:10px 0}
.result-box b{color:#ef6c00;font-size:11px;text-transform:uppercase;letter-spacing:1px}
.result-box p{margin:5px 0 0;font-size:14px}
.slot-row{display:grid;grid-template-columns:1fr 1fr 36px;gap:8px;margin-top:8px;align-items:center}
.dasha-row{display:grid;grid-template-columns:80px 1fr 1fr 36px;gap:6px;margin-top:6px;align-items:center}
.ref-row{display:grid;grid-template-columns:1fr 36px;gap:8px;margin-top:6px;align-items:center}
.slot-row input,.dasha-row input,.ref-row input{padding:9px;font-size:13px;border:1px solid #ccc;border-radius:8px;width:100%;margin:0}
.rm-btn{background:#ffebee;color:#c62828;border:none;border-radius:6px;padding:8px;font-size:14px;cursor:pointer;font-weight:700}
.search-bar{display:flex;gap:6px;margin-bottom:14px}
.search-bar input{flex:1;padding:12px;font-size:15px;border:1px solid #ccc;border-radius:8px;margin:0}
.letters{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:14px}
.letter{background:#fff;border:1px solid #ddd;border-radius:6px;padding:7px 10px;font-size:13px;cursor:pointer;color:#4527a0;font-weight:600;min-width:32px;text-align:center}
.letter:active{background:#ede7f6}
.picker-row{display:flex;justify-content:space-between;align-items:center;padding:11px 13px;background:#fff;border:1px solid #eee;border-radius:8px;margin-bottom:6px}
.picker-row .nm{font-size:14px;font-weight:500}
.picker-row .ac{display:flex;gap:4px}
.save-sheet{background:#fff;border-radius:12px;padding:18px;box-shadow:0 4px 12px rgba(0,0,0,.1);margin-bottom:14px}
.save-sheet h3{margin:0 0 12px;font-size:17px;color:#2e7d32}
.chk{display:flex;align-items:center;padding:9px 0;font-size:14px;cursor:pointer}
.chk input{width:auto;margin-right:10px}
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);z-index:100;align-items:center;justify-content:center;padding:16px}
.modal.on{display:flex}
.modal-inner{background:#fff;border-radius:12px;padding:20px;width:100%;max-width:440px;max-height:85vh;overflow-y:auto}
.modal-inner h3{margin:0 0 14px;font-size:18px}
.body-display{font-size:14px;color:#333;line-height:1.5;white-space:pre-wrap;word-wrap:break-word;padding:10px 0}
.obs-card{background:#fff;border-radius:12px;padding:14px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,.08);position:relative;border-left:4px solid #7e57c2}
.obs-card.main{border-left-color:#ffb300}
.obs-card .obs-title{font-size:15px;font-weight:600;margin:0 0 4px}
.obs-card .obs-slots{font-size:12px;color:#888;margin:0 0 8px}
.obs-card .obs-actions{margin-top:10px;display:flex;gap:6px;flex-wrap:wrap}
.badge-main{display:inline-block;background:#ffb300;color:#fff;font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;margin-left:6px;text-transform:uppercase;letter-spacing:.5px}
.home-menu a{display:block;background:#fff;color:#333;text-decoration:none;padding:18px 20px;border-radius:12px;margin-bottom:12px;font-size:16px;font-weight:500;box-shadow:0 2px 6px rgba(0,0,0,.08);border-left:4px solid #5e35b1}
.home-title{text-align:center;margin:30px 0}
.home-title h1{font-size:28px;color:#5e35b1;margin:0;letter-spacing:-.5px}
.home-title p{color:#888;font-size:13px;margin:8px 0 0;letter-spacing:2px;text-transform:uppercase}

/* AUTOCOMPLETE */
.ac-wrap{position:relative}
.ac-drop{position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;max-height:280px;overflow-y:auto;z-index:50;box-shadow:0 6px 14px rgba(0,0,0,.12)}
.ac-drop:empty{display:none}
.ac-item{padding:11px 14px;font-size:14px;cursor:pointer;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center}
.ac-item:hover,.ac-item.on{background:#ede7f6;color:#4527a0}
.ac-item:last-child{border-bottom:none}
.ac-item .ac-lbl{font-weight:500}
.ac-item .ac-sub{font-size:11px;color:#999;margin-left:8px}
.ac-empty{padding:12px 14px;font-size:13px;color:#999}
.ac-clear{position:absolute;top:50%;right:10px;transform:translateY(-50%);cursor:pointer;color:#999;font-size:16px;display:none}
.ac-wrap.has-val .ac-clear{display:block}
"""


LAYOUT = (
    '<!doctype html>\n'
    '<html><head>\n'
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    '<title>AstroKarmaPath</title>\n'
    '<style>' + CSS + '</style>\n'
    '</head><body>\n'
    '<header>\n'
    '  <a class="brand" href="/">AstroKarmaPath <span class="inf">&infin;</span></a>\n'
    '  <nav>\n'
    '    <a href="/people">People</a>\n'
    '    <a href="/combinations">Combos</a>\n'
    '    <a href="/research">Research</a>\n'
    '    <a href="/search">Search</a>\n'
    '  </nav>\n'
    '</header>\n'
    '<main>__BODY__</main>\n'
    '<script>\n'
    '(function(){\n'
    '  function attach(input){\n'
    '    if (input.__ac) return;\n'
    '    input.__ac = true;\n'
    '    var src = input.getAttribute("data-src") || "people";\n'
    '    var wrap = document.createElement("div");\n'
    '    wrap.className = "ac-wrap";\n'
    '    input.parentNode.insertBefore(wrap, input);\n'
    '    wrap.appendChild(input);\n'
    '    var clr = document.createElement("span");\n'
    '    clr.className = "ac-clear";\n'
    '    clr.innerHTML = "&#10005;";\n'
    '    wrap.appendChild(clr);\n'
    '    var drop = document.createElement("div");\n'
    '    drop.className = "ac-drop";\n'
    '    wrap.appendChild(drop);\n'
    '    var tmr = null, last = "";\n'
    '    function render(items){\n'
    '      if (!items || !items.length){\n'
    '        drop.innerHTML = "<div class=\'ac-empty\'>No matches</div>";\n'
    '        return;\n'
    '      }\n'
    '      var html = "";\n'
    '      for (var i=0;i<items.length;i++){\n'
    '        var it = items[i];\n'
    '        var label = it.name || it.title || it.event || "";\n'
    '        var sub = it.sub || it.place || it.body || "";\n'
    '        html += "<div class=\'ac-item\' data-id=\'"+it.id+"\' data-label=\'"+label.replace(/\'/g,"&#39;")+"\'>"+\n'
    '                "<span class=\'ac-lbl\'>"+label+"</span>"+\n'
    '                (sub ? "<span class=\'ac-sub\'>"+sub+"</span>" : "")+"</div>";\n'
    '      }\n'
    '      drop.innerHTML = html;\n'
    '    }\n'
    '    function search(term){\n'
    '      if (!term || term.length < 2){ drop.innerHTML = ""; return; }\n'
    '      fetch("/api/"+src+"/search?q="+encodeURIComponent(term))\n'
    '        .then(function(r){return r.json();})\n'
    '        .then(render)\n'
    '        .catch(function(){ drop.innerHTML = ""; });\n'
    '    }\n'
    '    input.addEventListener("input", function(){\n'
    '      clearTimeout(tmr);\n'
    '      var v = input.value.trim();\n'
    '      wrap.classList.toggle("has-val", v.length > 0);\n'
    '      if (v === last) return;\n'
    '      last = v;\n'
    '      tmr = setTimeout(function(){ search(v); }, 180);\n'
    '    });\n'
    '    input.addEventListener("blur", function(){\n'
    '      setTimeout(function(){ drop.innerHTML = ""; }, 200);\n'
    '    });\n'
    '    input.addEventListener("focus", function(){\n'
    '      if (input.value.trim().length >= 2) search(input.value.trim());\n'
    '    });\n'
    '    clr.addEventListener("mousedown", function(e){\n'
    '      e.preventDefault();\n'
    '      input.value = "";\n'
    '      input.removeAttribute("data-picked-id");\n'
    '      wrap.classList.remove("has-val");\n'
    '      drop.innerHTML = "";\n'
    '      input.focus();\n'
    '    });\n'
    '    drop.addEventListener("mousedown", function(e){\n'
    '      var el = e.target.closest ? e.target.closest(".ac-item") : null;\n'
    '      if (!el) return;\n'
    '      e.preventDefault();\n'
    '      input.value = el.getAttribute("data-label");\n'
    '      input.setAttribute("data-picked-id", el.getAttribute("data-id"));\n'
    '      drop.innerHTML = "";\n'
    '      wrap.classList.add("has-val");\n'
    '      input.dispatchEvent(new Event("change", {bubbles:true}));\n'
    '    });\n'
    '  }\n'
    '  function init(){\n'
    '    document.querySelectorAll("input.ac-search").forEach(attach);\n'
    '  }\n'
    '  if (document.readyState === "loading"){\n'
    '    document.addEventListener("DOMContentLoaded", init);\n'
    '  } else { init(); }\n'
    '})();\n'
    '</script>\n'
    '</body></html>'
)


def page(body):
    return LAYOUT.replace('__BODY__', body)


def nav(back_to, back_label="Back"):
    return (
        '<div class="actions">'
        '<a class="btn btn-secondary btn-sm" href="%s">&larr; %s</a>'
        '<a class="btn btn-secondary btn-sm" href="/">&#127968; Home</a>'
        '</div>'
    ) % (back_to, back_label)
