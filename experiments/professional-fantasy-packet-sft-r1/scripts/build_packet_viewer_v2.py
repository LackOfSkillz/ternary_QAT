"""Dispatch 30A-R1 — private bulk-packet review viewer for a batch (default batch1 = c02).

Self-contained index.html into git-ignored private-data/packet-review-<batch>/. Per record shows the
source passage, read-only provenance packet, editable compositional + atomic packets, target hash
prefix + word count + exact tokens (target / atomic input+total / compositional input+total),
meaningful + load-bearing counts, lexical + structural retrieval risk, and distinctive elements.
Decisions + 7 ratings + edits export to a private decisions file. Committed generator holds no prose;
source text is inlined only into the private page.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
BATCH = sys.argv[1] if len(sys.argv) > 1 else "batch1"
TP = os.path.join(EXP, "private-data", "training-packets")
TARGETS = os.path.join(EXP, "private-data", "targets")
TOK = os.path.join(EXP, "private-data", f"tokcount-output-{BATCH}.json")
RISK = os.path.join(EXP, "private-data", f"structural-risk-{BATCH}.json")
VAL = os.path.join(EXP, "reports", f"{BATCH}-validation.json")
APP = os.path.join(EXP, "private-data", f"packet-review-{BATCH}")


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def main():
    comp = {r["record_id"].rsplit("-", 1)[0]: r for r in load(os.path.join(TP, f"{BATCH}-compositional.jsonl"))}
    atom = {r["record_id"].rsplit("-", 1)[0]: r for r in load(os.path.join(TP, f"{BATCH}-atomic.jsonl"))}
    prov = {r["passage_id"]: r for r in load(os.path.join(TP, f"{BATCH}-provenance.jsonl"))}
    tok = json.load(open(TOK, encoding="utf-8")) if os.path.exists(TOK) else {}
    risk = json.load(open(RISK, encoding="utf-8")) if os.path.exists(RISK) else {}
    val = {r["passage_id"]: r for r in json.load(open(VAL, encoding="utf-8"))["records"]} if os.path.exists(VAL) else {}
    # optional before/after: same-calibration original ratings + reviser's generalized categories
    orig_p = os.path.join(EXP, "private-data", "structural-risk-batch1-recal.json")
    notes_p = os.path.join(EXP, "private-data", "revision-notes-batch1.json")
    orig = json.load(open(orig_p, encoding="utf-8")) if os.path.exists(orig_p) else {}
    notes = json.load(open(notes_p, encoding="utf-8")) if os.path.exists(notes_p) else {}
    data = []
    for pid in comp:
        seg = json.load(open(os.path.join(TARGETS, pid + ".json"), encoding="utf-8"))
        c, a = comp[pid], atom.get(pid, {})
        ca = c["training_packet"]["constraint_accounting"]
        data.append({
            "passage_id": pid, "source_filename": c["target"]["source_filename"],
            "source_text": seg["text"], "provenance": prov.get(pid, {}),
            "compositional_packet": c["training_packet"], "atomic_packet": a.get("training_packet", {}),
            "target_sha_prefix": c["target"]["target_sha256"][:12], "target_word_count": c["target"]["target_word_count"],
            "meaningful": ca["meaningful_constraints"], "load_bearing": ca["load_bearing_constraints"],
            "atomic_meaningful": a.get("training_packet", {}).get("constraint_accounting", {}).get("meaningful_constraints"),
            "tokens": {"target": (tok.get(pid + "-C", {}) or {}).get("target_tokens"),
                       "comp_input": (tok.get(pid + "-C", {}) or {}).get("input_tokens"),
                       "comp_total": (tok.get(pid + "-C", {}) or {}).get("total_tokens"),
                       "atom_input": (tok.get(pid + "-A", {}) or {}).get("input_tokens"),
                       "atom_total": (tok.get(pid + "-A", {}) or {}).get("total_tokens"),
                       "fits": (tok.get(pid + "-C", {}) or {}).get("fits_8192")},
            "lexical_risk": (val.get(pid, {}) or {}).get("lexical_risk", "low"),
            "structural": risk.get(pid, {}),
            "orig_structural": (orig.get(pid, {}) or {}).get("structural_reconstruction_risk", {}),
            "categories_generalized": (notes.get(pid, {}) or {}).get("categories_generalized", []),
        })
    os.makedirs(APP, exist_ok=True)
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__BATCH__", BATCH)
    open(os.path.join(APP, "index.html"), "w", encoding="utf-8", newline="\n").write(html)
    print(json.dumps({"viewer": os.path.relpath(os.path.join(APP, "index.html"), EXP), "records": len(data)}, indent=1))


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>LW Bulk Packet Review __BATCH__</title>
<style>
body{font:14px/1.5 -apple-system,Segoe UI,sans-serif;margin:0;background:#eef0f2;color:#1a1a1a}
header{position:sticky;top:0;background:#222;color:#eee;padding:8px 14px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:9}
#wrap{max-width:1040px;margin:0 auto;padding:14px}
.card{background:#fff;border:1px solid #d5d8dc;border-radius:8px;padding:14px;margin:14px 0;box-shadow:0 1px 3px #0001}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
h3{margin:8px 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#555}
.src{white-space:pre-wrap;font:14px/1.6 Georgia,serif;max-height:320px;overflow:auto;background:#faf9f6;padding:10px;border:1px solid #eee;border-radius:6px}
pre{white-space:pre-wrap;background:#f6f8fa;padding:8px;border-radius:6px;font:12px ui-monospace,monospace;max-height:280px;overflow:auto}
textarea{width:100%;font:12px ui-monospace,monospace;border:1px solid #ccd;border-radius:6px;padding:8px}
.badge{background:#eef;border-radius:10px;padding:1px 8px;font-size:12px;margin-right:4px}
.risk-low{background:#e7f6e7}.risk-medium{background:#fdf3d8}.risk-high{background:#fbe2e2}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:6px 0;font-size:13px}
label{font-size:13px}select,input{font:13px sans-serif;padding:3px 6px}.saved{color:#2a2}
</style></head><body>
<header><b>Bulk Packet Review — __BATCH__</b><span id="prog"></span>
<label>reviewer <input id="rev" size="8" value="gary"></label>
<button onclick="exportD()">Export packet-decisions-__BATCH__.json</button><span id="msg" class="saved"></span></header>
<div id="wrap"></div>
<script>
const DATA=__DATA__;const KEY="lw-bulk-review-__BATCH__";
let dec=JSON.parse(localStorage.getItem(KEY)||"{}");
const DECS=['','accept','accept_with_medium_risk','accept_as_retrieval_sensitive','revise_compositional','revise_atomic','revise_both','revise_provenance','exclude'];
function rateOf(s){return (s&&s.structural_reconstruction_risk||{}).rating||'?';}
// authoritative cohort assignment from (preserved rating, human decision) + contradiction check
function assign(rating,decision){
 if(!decision) return {cohort:'(undecided)',invalid:false,msg:''};
 if(decision==='exclude') return {cohort:'excluded',invalid:false,msg:''};
 if(decision.indexOf('revise_')===0) return {cohort:'pending_revision',invalid:false,msg:''};
 if(decision==='accept') return rating==='low'
   ? {cohort:'primary_instruction_learning',invalid:false,msg:''}
   : {cohort:'INVALID',invalid:true,msg:'accept is only valid for a low rating'};
 if(decision==='accept_with_medium_risk') return rating==='medium'
   ? {cohort:'primary_instruction_learning',invalid:false,msg:''}
   : {cohort:'INVALID',invalid:true,msg:'accept_with_medium_risk requires a medium rating (never for high)'};
 if(decision==='accept_as_retrieval_sensitive') return rating==='high'
   ? {cohort:'retrieval_sensitive',invalid:false,msg:''}
   : {cohort:'INVALID',invalid:true,msg:'accept_as_retrieval_sensitive requires a high rating'};
 return {cohort:'(undecided)',invalid:false,msg:''};
}
const RATES=['packet_matches_target','constraint_accuracy','load_bearing_quality','production_realism','abstraction_quality','structural_retrieval_safety','atomic_purity'];
function save(){localStorage.setItem(KEY,JSON.stringify(dec));document.getElementById('msg').textContent="saved "+new Date().toLocaleTimeString();}
function g(id){return dec[id]||(dec[id]={decision:"",ratings:{},notes:"",edited_compositional:"",edited_atomic:""});}
function esc(s){return (s||"").replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function badge(r){const s=(r&&r.rating)||'?';return '<span class="badge risk-'+s+'">'+s+'</span>';}
function distinct(s){const d=(s&&s.distinctive_elements)||{};return Object.keys(d).filter(k=>d[k]).join(', ')||'none';}
function render(){
 const wrap=document.getElementById('wrap');wrap.innerHTML="";let done=0;
 DATA.forEach(d=>{const c=g(d.passage_id);if(c.decision)done++;const s=d.structural||{};const t=d.tokens;
  const div=document.createElement('div');div.className="card";
  div.innerHTML='<div class="row"><b>'+d.passage_id+'</b> <span class="badge">'+d.source_filename+'</span>'+
   ' <span class="badge">sha '+d.target_sha_prefix+'</span> <span class="badge">'+d.target_word_count+' w</span>'+
   ' <span class="badge">tgt '+t.target+' tok</span> <span class="badge">comp in '+t.comp_input+' / total '+t.comp_total+'</span>'+
   ' <span class="badge">atom in '+t.atom_input+' / total '+t.atom_total+'</span> <span class="badge">fits8192 '+t.fits+'</span></div>'+
   '<div class="row"><span class="badge">meaningful '+d.meaningful+' ('+d.load_bearing+' LB)</span> <span class="badge">atomic '+d.atomic_meaningful+'</span>'+
   ' lexical '+'<span class="badge risk-'+d.lexical_risk+'">'+d.lexical_risk+'</span> structural '+
   (d.orig_structural&&d.orig_structural.rating?'orig '+badge(d.orig_structural)+' &rarr; revised ':'')+badge(s.structural_reconstruction_risk)+
   (s.recommendation?' <span class="badge">'+s.recommendation+'</span>':'')+' <span class="badge">distinctive: '+distinct(s)+'</span>'+
   (d.categories_generalized&&d.categories_generalized.length?' <span class="badge">generalized: '+d.categories_generalized.join(', ')+'</span>':'')+'</div>'+
   '<div class="grid"><div><h3>Source passage (private)</h3><div class="src">'+esc(d.source_text)+'</div>'+
   '<h3>Provenance packet (read-only)</h3><pre>'+esc(JSON.stringify(d.provenance,null,1))+'</pre></div>'+
   '<div><h3>Compositional packet (editable)</h3><textarea style="height:250px" onchange="edit(\''+d.passage_id+'\',\'edited_compositional\',this.value)">'+esc(c.edited_compositional||JSON.stringify(d.compositional_packet,null,1))+'</textarea>'+
   '<h3>Atomic packet (editable)</h3><textarea style="height:110px" onchange="edit(\''+d.passage_id+'\',\'edited_atomic\',this.value)">'+esc(c.edited_atomic||JSON.stringify(d.atomic_packet,null,1))+'</textarea></div></div>'+
   controls(d,c);
  wrap.appendChild(div);});
 document.getElementById('prog').textContent=" — "+done+"/"+DATA.length+" decided";
}
function controls(d,c){
 const rating=rateOf(d.structural);const asg=assign(rating,c.decision);
 let r='<div class="row"><label>decision <select onchange="setF(\''+d.passage_id+'\',\'decision\',this.value)">'+
  DECS.map(x=>'<option '+(c.decision===x?'selected':'')+'>'+x+'</option>').join('')+'</select></label>';
 r+='<span class="badge">independent rating: '+rating+'</span>'+
    '<span class="badge">disposition: '+(c.decision||'(none)')+'</span>'+
    '<span class="badge" style="'+(asg.invalid?'background:#fbe2e2;color:#900;font-weight:700':'background:#e7f0ff')+'">assigned cohort: '+asg.cohort+'</span>'+
    (asg.invalid?'<span class="badge" style="background:#900;color:#fff">INVALID: '+asg.msg+'</span>':'');
 RATES.forEach(k=>{r+='<label>'+k+' <select onchange="setR(\''+d.passage_id+'\',\''+k+'\',this.value)"><option value=""></option>';
  for(let i=1;i<=3;i++)r+='<option '+(c.ratings[k]==i?'selected':'')+'>'+i+'</option>';r+='</select></label>';});
 r+='<label>notes <input size="40" value="'+esc(c.notes).replace(/"/g,'&quot;')+'" onchange="setF(\''+d.passage_id+'\',\'notes\',this.value)"></label></div>';return r;
}
function stamp(c){c.timestamp=new Date().toISOString();c.reviewer=document.getElementById('rev').value;}
function setF(id,k,v){const c=g(id);c[k]=v;stamp(c);save();if(k==='decision')render();}
function setR(id,k,v){const c=g(id);c.ratings[k]=v?+v:null;stamp(c);save();}
function edit(id,k,v){const c=g(id);c[k]=v;stamp(c);save();}
function exportD(){const out={reviewer:document.getElementById('rev').value,batch:"__BATCH__",generated_at:new Date().toISOString(),decisions:dec};
 const b=new Blob([JSON.stringify(out,null,1)],{type:"application/json"});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download="packet-decisions-__BATCH__.json";a.click();}
document.getElementById('rev').onchange=save;render();
</script></body></html>"""


if __name__ == "__main__":
    main()
