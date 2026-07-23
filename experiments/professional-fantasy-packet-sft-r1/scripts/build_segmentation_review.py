"""Dispatch 30A-R1 — build the local segmentation review app.

Generates a SELF-CONTAINED index.html into git-ignored private-data/review-app/. Source prose is
inlined ONLY into that private (git-ignored) file so the page works over file:// without a server;
this committed generator contains NO prose. Decisions are exported by the page to a private
decisions.json (also git-ignored) and ingested by apply_segmentation_review.py.

Usage:
  py build_segmentation_review.py calibration   # 3 candidates (dialogue / action / exposition, 3 files)
  py build_segmentation_review.py full          # every candidate
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
CAND = os.path.join(EXP, "manifests", "candidate-passages.jsonl")
TARGETS = os.path.join(EXP, "private-data", "targets")
APP_DIR = os.path.join(EXP, "private-data", "review-app")


def load_rows():
    return [json.loads(l) for l in open(CAND, encoding="utf-8") if l.strip()]


def pick_calibration(rows):
    def dr(c): return c["passage_properties"]["dialogue_ratio"]
    def ac(c): return c["passage_properties"]["action_density"]
    pool = [c for c in rows if 600 <= c["target_word_count"] <= 1400
            and c["diagnostics"]["scene_coherence"] != "low"]
    if len({c["source_filename"] for c in pool}) < 3:
        pool = rows
    chosen, used = [], set()

    def take(key, reverse, tag):
        for c in sorted(pool, key=key, reverse=reverse):
            if c["source_filename"] not in used:
                used.add(c["source_filename"])
                chosen.append({**c, "calibration_role": tag})
                return
    take(lambda c: dr(c), True, "dialogue_heavy")
    take(lambda c: ac(c), True, "action_heavy")
    take(lambda c: dr(c) + ac(c), False, "exposition_or_discovery")
    return chosen


def payload(pid):
    return json.load(open(os.path.join(TARGETS, pid + ".json"), encoding="utf-8"))


def build(rows, mode):
    data = []
    for r in rows:
        pl = payload(r["passage_id"])
        data.append({
            "passage_id": r["passage_id"], "source_filename": r["source_filename"],
            "calibration_role": r.get("calibration_role"),
            "word_count": r["target_word_count"], "scene_function": r.get("scene_function"),
            "segmentation_method": r["segmentation_method"],
            "boundary_confidence": r["segmentation_confidence"],
            "diagnostics": r["diagnostics"], "passage_properties": r["passage_properties"],
            "start_offset": r["start_character_offset"], "end_offset": r["end_character_offset"],
            "paragraphs": pl["paragraphs"], "context_before": pl["context_before"],
            "context_after": pl["context_after"], "text": pl["text"],
        })
    os.makedirs(APP_DIR, exist_ok=True)
    html = TEMPLATE.replace("__MODE__", mode).replace(
        "__DATA__", json.dumps(data, ensure_ascii=False))
    with open(os.path.join(APP_DIR, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    return data


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>LW Segmentation Review (__MODE__)</title>
<style>
body{font:15px/1.55 Georgia,serif;margin:0;background:#f4f1ea;color:#222}
header{position:sticky;top:0;background:#2b2b2b;color:#eee;padding:8px 14px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
select,button,input{font:14px sans-serif;padding:4px 8px}
#wrap{max-width:820px;margin:0 auto;padding:16px}
.card{background:#fff;border:1px solid #ddd;border-radius:6px;padding:16px;margin:14px 0;box-shadow:0 1px 3px #0001}
.ctx{color:#999;font-style:italic;white-space:pre-wrap}
.para{white-space:pre-wrap;margin:6px 0;padding:4px 6px;border-left:3px solid transparent;cursor:pointer}
.para:hover{background:#f0f7ff;border-left-color:#69c}
.para.instart{border-left-color:#2a2}.para.inend{border-left-color:#a22}
.meta{font:12px sans-serif;color:#555;background:#faf8f2;padding:6px 8px;border-radius:4px;margin:6px 0}
.row{display:flex;gap:14px;flex-wrap:wrap;align-items:center;font:13px sans-serif;margin:6px 0}
.badge{background:#eee;border-radius:10px;padding:1px 8px;font:12px sans-serif}
.saved{color:#2a2}.prog{font:13px sans-serif}
label{font:13px sans-serif}
</style></head><body>
<header>
<b>Segmentation Review</b><span class="prog" id="prog"></span>
<label>reviewer <input id="rev" size="8" value="gary"></label>
<label>source <select id="filter"><option value="">all</option></select></label>
<button onclick="exportDecisions()">Export decisions.json</button>
<span id="savemsg" class="saved"></span>
</header>
<div id="wrap"></div>
<script>
const DATA = __DATA__;
const KEY = "lw-seg-review-__MODE__";
let dec = JSON.parse(localStorage.getItem(KEY) || "{}");
function save(){localStorage.setItem(KEY, JSON.stringify(dec)); document.getElementById('savemsg').textContent="saved "+new Date().toLocaleTimeString();}
function get(id){return dec[id] || (dec[id]={decision:"",adjusted_start:null,adjusted_end:null,ratings:{},scene_function:"",notes:""});}
function paraList(d){
  // context_before (as movable start anchors), candidate paragraphs, context_after (as end anchors)
  let html="", cur=get(d.passage_id);
  const cb=d.context_before.map((t,i)=>({t,off:d.start_offset,tag:"before"}));
  html+='<div class="ctx">…prev context (click a candidate paragraph edge to adjust):</div>';
  d.context_before.forEach(t=>html+='<div class="ctx">'+esc(t)+'</div>');
  d.paragraphs.forEach((p,i)=>{
    const s=(cur.adjusted_start!=null?cur.adjusted_start:d.start_offset);
    const e=(cur.adjusted_end!=null?cur.adjusted_end:d.end_offset);
    const cls="para"+(p.offset===s?" instart":"")+(i===d.paragraphs.length-1?"":"");
    html+='<div class="'+cls+'" onclick="setEdge(\''+d.passage_id+'\','+p.offset+','+(p.offset+p.text.length)+',event)">'+esc(p.text)+'</div>';
  });
  d.context_after.forEach(t=>html+='<div class="ctx">'+esc(t)+'</div>');
  html+='<div class="ctx">next context…</div>';
  return html;
}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function setEdge(id,pstart,pend,ev){
  const c=get(id);
  if(ev.shiftKey){c.adjusted_end=pend;} else {c.adjusted_start=pstart;}
  save(); render();
}
function render(){
  const f=document.getElementById('filter').value;
  const wrap=document.getElementById('wrap'); wrap.innerHTML="";
  let shown=0, done=0;
  DATA.forEach(d=>{
    if(f && d.source_filename!==f) return;
    shown++; const c=get(d.passage_id); if(c.decision) done++;
    const div=document.createElement('div'); div.className="card";
    div.innerHTML=
      '<div class="row"><b>'+d.passage_id+'</b> <span class="badge">'+d.source_filename+'</span>'+
      (d.calibration_role?' <span class="badge">'+d.calibration_role+'</span>':'')+
      ' <span class="badge">'+d.word_count+' w</span> <span class="badge">conf '+d.boundary_confidence+'</span>'+
      ' <span class="badge">'+d.segmentation_method+'</span></div>'+
      '<div class="meta">dialogue '+d.passage_properties.dialogue_ratio+' · action '+d.passage_properties.action_density+
      ' · opening-dep '+d.diagnostics.opening_context_dependency+' · closing '+d.diagnostics.closing_completeness+
      ' · vp '+d.diagnostics.viewpoint_stability+' · coherence '+d.diagnostics.scene_coherence+'</div>'+
      '<div class="hint" style="font:12px sans-serif;color:#888">Click a paragraph = set START; Shift-click = set END.</div>'+
      paraList(d)+
      controls(d,c);
    wrap.appendChild(div);
  });
  document.getElementById('prog').textContent=" — "+done+"/"+shown+" decided";
}
function controls(d,c){
  const dsel=(v)=>'<option '+(c.decision===v?'selected':'')+'>'+v+'</option>';
  const rate=(k)=>{let h='<label>'+k+' <select onchange="setRate(\''+d.passage_id+'\',\''+k+'\',this.value)">'+
    '<option value=""></option>';for(let i=1;i<=3;i++)h+='<option '+(c.ratings[k]==i?'selected':'')+'>'+i+'</option>';return h+'</select></label>';};
  return '<div class="row"><label>decision <select onchange="setDec(\''+d.passage_id+'\',this.value)">'+
    ['','accept','reject','adjust_start','adjust_end','merge_with_previous','merge_with_next','split','defer'].map(dsel).join('')+
    '</select></label>'+
    '<span>start '+(c.adjusted_start!=null?c.adjusted_start:d.start_offset)+' · end '+(c.adjusted_end!=null?c.adjusted_end:d.end_offset)+'</span>'+
    '<button onclick="resetAdj(\''+d.passage_id+'\')">reset bounds</button></div>'+
    '<div class="row">'+rate('boundary_quality')+rate('coherence')+rate('context_independence')+rate('training_value')+'</div>'+
    '<div class="row"><label>scene_function <input value="'+(c.scene_function||'')+'" onchange="setFn(\''+d.passage_id+'\',this.value)"></label>'+
    '<label>notes <input size="40" value="'+(c.notes||'').replace(/"/g,'&quot;')+'" onchange="setNote(\''+d.passage_id+'\',this.value)"></label></div>';
}
function stamp(c){c.timestamp=new Date().toISOString();c.reviewer=document.getElementById('rev').value;}
function setDec(id,v){const c=get(id);c.decision=v;stamp(c);save();render();}
function setRate(id,k,v){const c=get(id);c.ratings[k]=v?+v:null;stamp(c);save();}
function setFn(id,v){const c=get(id);c.scene_function=v;stamp(c);save();}
function setNote(id,v){const c=get(id);c.notes=v;stamp(c);save();}
function resetAdj(id){const c=get(id);c.adjusted_start=null;c.adjusted_end=null;stamp(c);save();render();}
function exportDecisions(){
  const out={reviewer:document.getElementById('rev').value,generated_at:new Date().toISOString(),
    segmentation_version:"seg-v1",mode:"__MODE__",decisions:dec};
  const b=new Blob([JSON.stringify(out,null,1)],{type:"application/json"});
  const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download="decisions.json";a.click();
}
const fsel=document.getElementById('filter');
[...new Set(DATA.map(d=>d.source_filename))].forEach(s=>{const o=document.createElement('option');o.value=o.textContent=s;fsel.appendChild(o);});
fsel.onchange=render; document.getElementById('rev').onchange=save;
render();
</script></body></html>"""


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "calibration"
    rows = load_rows()
    sel = pick_calibration(rows) if mode == "calibration" else rows
    data = build(sel, mode)
    summary = {"mode": mode, "app": os.path.relpath(os.path.join(APP_DIR, "index.html"), EXP),
               "candidates_in_app": len(data),
               "calibration": [{"passage_id": d["passage_id"], "source_filename": d["source_filename"],
                                "role": d.get("calibration_role"), "word_count": d["word_count"],
                                "boundary_method": d["segmentation_method"],
                                "boundary_confidence": d["boundary_confidence"],
                                "dialogue_ratio": d["passage_properties"]["dialogue_ratio"],
                                "action_density": d["passage_properties"]["action_density"]}
                               for d in data] if mode == "calibration" else "full"}
    json.dump(summary, open(os.path.join(EXP, "reports", "segmentation-review-build.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
