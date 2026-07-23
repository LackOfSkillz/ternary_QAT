"""Dispatch 30A-R1 — build the private packet review viewer.

Generates a self-contained index.html into git-ignored private-data/packet-viewer/. For each of the
11 passages it shows: the private source passage, the provenance packet (read-only), the model-visible
compositional and atomic packets (editable), constraint counts, exact Qwen token counts
(input/target/total per arm, fit at 4096/6144/8192), and the two-field retrieval risk
(lexical + structural). Decisions/ratings/edits export to a private decisions file. This committed
generator holds NO source content; prose is inlined only into the private page.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
TARGETS = os.path.join(EXP, "private-data", "targets")
COMPO = os.path.join(EXP, "manifests", "compositional-records.jsonl")
ATOMIC = os.path.join(EXP, "manifests", "atomic-records.jsonl")
PROV = os.path.join(EXP, "manifests", "provenance-packets.jsonl")
TOK = os.path.join(EXP, "private-data", "tokcount-output.json")
RISK = os.path.join(EXP, "private-data", "structural-risk.json")
APP = os.path.join(EXP, "private-data", "packet-viewer")


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main():
    comp = {r["record_id"].rsplit("-", 1)[0]: r for r in load(COMPO)}
    atom = {r["record_id"].rsplit("-", 1)[0]: r for r in load(ATOMIC)}
    prov = {r["passage_id"]: r for r in load(PROV)}
    tok = json.load(open(TOK, encoding="utf-8")) if os.path.exists(TOK) else {}
    risk = json.load(open(RISK, encoding="utf-8")) if os.path.exists(RISK) else {}
    data = []
    for pid in comp:
        seg = json.load(open(os.path.join(TARGETS, pid + ".json"), encoding="utf-8"))
        c, a = comp[pid], atom.get(pid, {})
        data.append({
            "passage_id": pid, "source_filename": c["target"]["source_filename"],
            "source_text": seg["text"], "provenance": prov.get(pid, {}).get("provenance_packet", {}),
            "compositional_packet": c["training_packet"], "atomic_packet": a.get("training_packet", {}),
            "constraint_accounting": c.get("constraint_accounting", {}),
            "tokens": {"compositional": tok.get(pid + "-C", {}), "atomic": tok.get(pid + "-A", {})},
            "lexical_risk": c.get("retrieval_risk", "low"),
            "structural_risk": risk.get(pid, {}),
        })
    os.makedirs(APP, exist_ok=True)
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    with open(os.path.join(APP, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    print(json.dumps({"viewer": os.path.relpath(os.path.join(APP, "index.html"), EXP),
                      "passages": len(data)}, indent=1))


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>LW Packet Review</title>
<style>
body{font:14px/1.5 -apple-system,Segoe UI,sans-serif;margin:0;background:#eef0f2;color:#1a1a1a}
header{position:sticky;top:0;background:#222;color:#eee;padding:8px 14px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:9}
#wrap{max-width:1000px;margin:0 auto;padding:14px}
.card{background:#fff;border:1px solid #d5d8dc;border-radius:8px;padding:14px;margin:14px 0;box-shadow:0 1px 3px #0001}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
h3{margin:8px 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#555}
.src{white-space:pre-wrap;font:14px/1.6 Georgia,serif;max-height:340px;overflow:auto;background:#faf9f6;padding:10px;border:1px solid #eee;border-radius:6px}
pre{white-space:pre-wrap;background:#f6f8fa;padding:8px;border-radius:6px;font:12px ui-monospace,monospace;max-height:300px;overflow:auto}
textarea{width:100%;height:220px;font:12px ui-monospace,monospace;border:1px solid #ccd;border-radius:6px;padding:8px}
.badge{background:#eef;border-radius:10px;padding:1px 8px;font-size:12px;margin-right:4px}
.risk-low{background:#e7f6e7}.risk-medium{background:#fdf3d8}.risk-high{background:#fbe2e2}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:6px 0;font-size:13px}
label{font-size:13px}select,input{font:13px sans-serif;padding:3px 6px}
.saved{color:#2a2}
</style></head><body>
<header><b>Packet Review — 11 records</b><span id="prog"></span>
<label>reviewer <input id="rev" size="8" value="gary"></label>
<button onclick="exportD()">Export packet-decisions.json</button><span id="msg" class="saved"></span></header>
<div id="wrap"></div>
<script>
const DATA=__DATA__;const KEY="lw-packet-review";
let dec=JSON.parse(localStorage.getItem(KEY)||"{}");
const DECS=['','accept','accept_with_medium_retrieval_risk','revise_compositional_packet','revise_atomic_packet','revise_both','exclude_passage'];
const RATES=['packet_matches_target','constraints_are_load_bearing','production_realism','abstraction_quality','structural_retrieval_safety'];
function save(){localStorage.setItem(KEY,JSON.stringify(dec));document.getElementById('msg').textContent="saved "+new Date().toLocaleTimeString();}
function g(id){return dec[id]||(dec[id]={decision:"",ratings:{},notes:"",edited_compositional:"",edited_atomic:""});}
function esc(s){return (s||"").replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function tk(t){return t&&t.total_tokens?('in '+t.input_tokens+' + tgt '+t.target_tokens+' = '+t.total_tokens+' ['+(t.fits_4096?'4k':t.fits_6144?'6k':t.fits_8192?'8k':'>8k')+']'):'—';}
function riskBadge(r){const s=(r&&r.rating)||'low';return '<span class="badge risk-'+s+'">'+s+'</span>';}
function render(){
 const wrap=document.getElementById('wrap');wrap.innerHTML="";let done=0;
 DATA.forEach(d=>{const c=g(d.passage_id);if(c.decision)done++;
  const sr=d.structural_risk||{};const div=document.createElement('div');div.className="card";
  div.innerHTML='<div class="row"><b>'+d.passage_id+'</b> <span class="badge">'+d.source_filename+'</span>'+
   ' <span class="badge">comp '+tk(d.tokens.compositional)+'</span> <span class="badge">atom '+tk(d.tokens.atomic)+'</span>'+
   ' <span class="badge">constraints '+(d.constraint_accounting.meaningful_constraints||'?')+' ('+(d.constraint_accounting.load_bearing_constraints||'?')+' LB)</span></div>'+
   '<div class="row">lexical risk <span class="badge risk-'+d.lexical_risk+'">'+d.lexical_risk+'</span>'+
   ' structural risk '+riskBadge(sr.structural_reconstruction_risk)+
   (sr.recommendation?' <span class="badge">'+sr.recommendation+'</span>':'')+
   (sr.distinctive_elements?' <span class="badge">'+ (sr.distinctive_elements.count||0)+' distinctive: '+((sr.distinctive_elements.categories||[]).join(', '))+'</span>':'')+'</div>'+
   '<div class="grid"><div><h3>Source passage (private)</h3><div class="src">'+esc(d.source_text)+'</div>'+
   '<h3>Provenance packet (read-only)</h3><pre>'+esc(JSON.stringify(d.provenance,null,1))+'</pre></div>'+
   '<div><h3>Compositional packet (editable)</h3><textarea onchange="edit(\''+d.passage_id+'\',\'edited_compositional\',this.value)">'+esc(c.edited_compositional||JSON.stringify(d.compositional_packet,null,1))+'</textarea>'+
   '<h3>Atomic packet (editable)</h3><textarea style="height:120px" onchange="edit(\''+d.passage_id+'\',\'edited_atomic\',this.value)">'+esc(c.edited_atomic||JSON.stringify(d.atomic_packet,null,1))+'</textarea></div></div>'+
   controls(d,c);
  wrap.appendChild(div);});
 document.getElementById('prog').textContent=" — "+done+"/"+DATA.length+" decided";
}
function controls(d,c){
 let r='<div class="row"><label>decision <select onchange="setF(\''+d.passage_id+'\',\'decision\',this.value)">'+
  DECS.map(x=>'<option '+(c.decision===x?'selected':'')+'>'+x+'</option>').join('')+'</select></label>';
 RATES.forEach(k=>{r+='<label>'+k+' <select onchange="setR(\''+d.passage_id+'\',\''+k+'\',this.value)"><option value=""></option>';
  for(let i=1;i<=3;i++)r+='<option '+(c.ratings[k]==i?'selected':'')+'>'+i+'</option>';r+='</select></label>';});
 r+='<label>notes <input size="40" value="'+esc(c.notes).replace(/"/g,'&quot;')+'" onchange="setF(\''+d.passage_id+'\',\'notes\',this.value)"></label></div>';
 return r;
}
function stamp(c){c.timestamp=new Date().toISOString();c.reviewer=document.getElementById('rev').value;}
function setF(id,k,v){const c=g(id);c[k]=v;stamp(c);save();if(k==='decision')render();}
function setR(id,k,v){const c=g(id);c.ratings[k]=v?+v:null;stamp(c);save();}
function edit(id,k,v){const c=g(id);c[k]=v;stamp(c);save();}
function exportD(){const out={reviewer:document.getElementById('rev').value,generated_at:new Date().toISOString(),decisions:dec};
 const b=new Blob([JSON.stringify(out,null,1)],{type:"application/json"});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download="packet-decisions.json";a.click();}
document.getElementById('rev').onchange=save;render();
</script></body></html>"""


if __name__ == "__main__":
    main()
