"""Dispatch 30A-R1 — build the local passage review app (harvest-v1).

Generates a SELF-CONTAINED index.html into git-ignored private-data/review-app/. Source prose is
inlined ONLY into that private file (works over file://, no server); this committed generator holds
NO prose. Shows every candidate in the (private) candidate manifest — for the corrected Phase 2 that
is the eleven-source calibration batch (one representative passage per book). Decisions export to a
private decisions.json ingested by apply_segmentation_review.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
CAND = os.path.join(EXP, "manifests", "candidate-passages.jsonl")
TARGETS = os.path.join(EXP, "private-data", "targets")
APP_DIR = os.path.join(EXP, "private-data", "review-app")


def main():
    rows = [json.loads(l) for l in open(CAND, encoding="utf-8") if l.strip()]
    data = []
    for r in rows:
        pl = json.load(open(os.path.join(TARGETS, r["passage_id"] + ".json"), encoding="utf-8"))
        data.append({
            "passage_id": r["passage_id"], "source_filename": r["source_filename"],
            "narrative_region": r.get("narrative_region"),
            "approximate_source_percent": r.get("approximate_source_percent"),
            "chapter_or_section": r.get("chapter_or_section"),
            "word_count": r["target_word_count"], "scene_function": r.get("scene_function"),
            "assigned": f"{r.get('assigned_region','')}/{r.get('assigned_emphasis','')}",
            "viewpoint_summary": r.get("viewpoint_summary"),
            "segmentation_method": r["segmentation_method"], "boundary_confidence": r["segmentation_confidence"],
            "diagnostics": r["diagnostics"], "passage_properties": r["passage_properties"],
            "start_offset": r["start_character_offset"], "end_offset": r["end_character_offset"],
            "paragraphs": pl["paragraphs"], "context_before": pl["context_before"],
            "context_after": pl["context_after"],
        })
    os.makedirs(APP_DIR, exist_ok=True)
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    with open(os.path.join(APP_DIR, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    summary = {"app": os.path.relpath(os.path.join(APP_DIR, "index.html"), EXP),
               "candidates_in_app": len(data),
               "sources": sorted({d["source_filename"] for d in data})}
    print(json.dumps(summary, ensure_ascii=False, indent=1))


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>LW Passage Review (harvest-v1)</title>
<style>
body{font:15px/1.55 Georgia,serif;margin:0;background:#f4f1ea;color:#222}
header{position:sticky;top:0;background:#2b2b2b;color:#eee;padding:8px 14px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:9}
select,button,input{font:14px sans-serif;padding:4px 8px}
#wrap{max-width:840px;margin:0 auto;padding:16px}
.card{background:#fff;border:1px solid #ddd;border-radius:6px;padding:16px;margin:14px 0;box-shadow:0 1px 3px #0001}
.ctx{color:#999;font-style:italic;white-space:pre-wrap;margin:4px 0}
.para{white-space:pre-wrap;margin:6px 0;padding:4px 6px;border-left:3px solid transparent;cursor:pointer}
.para:hover{background:#f0f7ff;border-left-color:#69c}
.para.instart{border-left-color:#2a2;background:#f2fbf2}.para.inend{border-left-color:#a22;background:#fdf3f3}
.meta{font:12px sans-serif;color:#555;background:#faf8f2;padding:6px 8px;border-radius:4px;margin:6px 0}
.row{display:flex;gap:14px;flex-wrap:wrap;align-items:center;font:13px sans-serif;margin:6px 0}
.badge{background:#eee;border-radius:10px;padding:1px 8px;font:12px sans-serif}
label{font:13px sans-serif}.saved{color:#2a2}
</style></head><body>
<header><b>Passage Review — 11-source calibration</b><span id="prog"></span>
<label>reviewer <input id="rev" size="8" value="gary"></label>
<label>source <select id="filter"><option value="">all</option></select></label>
<button onclick="exportDecisions()">Export decisions.json</button><span id="savemsg" class="saved"></span>
</header><div id="wrap"></div>
<script>
const DATA = __DATA__;
const KEY = "lw-passage-review-harvest-v1";
let dec = JSON.parse(localStorage.getItem(KEY) || "{}");
const DECISIONS=['','accept','reject','adjust_start','adjust_end','replace_candidate','defer'];
const RATINGS=['active_scene','coherence','representative_prose','packet_backtranslation_value','context_independence'];
const REASONS=['','non_story_intro_or_framing_material','lore_or_recap_summary','fragment_or_incoherent','too_dependent_on_omitted_context','unrepresentative_prose','other'];
function save(){localStorage.setItem(KEY,JSON.stringify(dec));document.getElementById('savemsg').textContent="saved "+new Date().toLocaleTimeString();}
function get(id){return dec[id]||(dec[id]={decision:"",reject_reason:"",adjusted_start:null,adjusted_end:null,ratings:{},scene_function:"",notes:""});}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function paraList(d){
  let html='<div class="ctx">…prev context:</div>';
  d.context_before.forEach(t=>html+='<div class="ctx">'+esc(t)+'</div>');
  const c=get(d.passage_id);
  const s=(c.adjusted_start!=null?c.adjusted_start:d.start_offset), e=(c.adjusted_end!=null?c.adjusted_end:d.end_offset);
  d.paragraphs.forEach(p=>{
    const cls="para"+(p.offset===s?" instart":"")+((p.offset+p.text.length)===e?" inend":"");
    html+='<div class="'+cls+'" onclick="setEdge(\''+d.passage_id+'\','+p.offset+','+(p.offset+p.text.length)+',event)">'+esc(p.text)+'</div>';
  });
  d.context_after.forEach(t=>html+='<div class="ctx">'+esc(t)+'</div>');
  html+='<div class="ctx">next context…</div>';return html;
}
function setEdge(id,ps,pe,ev){const c=get(id);if(ev.shiftKey)c.adjusted_end=pe;else c.adjusted_start=ps;stamp(c);save();render();}
function controls(d,c){
  const opt=(arr,v)=>arr.map(x=>'<option '+(v===x?'selected':'')+'>'+x+'</option>').join('');
  let r='<div class="row"><label>decision <select onchange="setF(\''+d.passage_id+'\',\'decision\',this.value)">'+opt(DECISIONS,c.decision)+'</select></label>'+
   '<label>reject_reason <select onchange="setF(\''+d.passage_id+'\',\'reject_reason\',this.value)">'+opt(REASONS,c.reject_reason)+'</select></label>'+
   '<span>start '+(c.adjusted_start!=null?c.adjusted_start:d.start_offset)+' · end '+(c.adjusted_end!=null?c.adjusted_end:d.end_offset)+'</span>'+
   '<button onclick="resetAdj(\''+d.passage_id+'\')">reset bounds</button></div><div class="row">';
  RATINGS.forEach(k=>{r+='<label>'+k+' <select onchange="setRate(\''+d.passage_id+'\',\''+k+'\',this.value)"><option value=""></option>';
    for(let i=1;i<=3;i++)r+='<option '+(c.ratings[k]==i?'selected':'')+'>'+i+'</option>';r+='</select></label>';});
  r+='</div><div class="row"><label>scene_function <input value="'+(c.scene_function||'')+'" onchange="setF(\''+d.passage_id+'\',\'scene_function\',this.value)"></label>'+
     '<label>notes <input size="44" value="'+(c.notes||'').replace(/"/g,'&quot;')+'" onchange="setF(\''+d.passage_id+'\',\'notes\',this.value)"></label></div>';
  return r;
}
function render(){
  const f=document.getElementById('filter').value,wrap=document.getElementById('wrap');wrap.innerHTML="";let shown=0,done=0;
  DATA.forEach(d=>{if(f&&d.source_filename!==f)return;shown++;const c=get(d.passage_id);if(c.decision)done++;
    const div=document.createElement('div');div.className="card";
    div.innerHTML='<div class="row"><b>'+d.passage_id+'</b> <span class="badge">'+d.source_filename+'</span>'+
      ' <span class="badge">'+d.narrative_region+' ~'+d.approximate_source_percent+'%</span>'+
      ' <span class="badge">'+d.chapter_or_section+'</span> <span class="badge">'+d.word_count+' w</span>'+
      ' <span class="badge">vp: '+d.viewpoint_summary+'</span> <span class="badge">assigned '+d.assigned+'</span></div>'+
      '<div class="meta">fn '+d.scene_function+' · dialogue '+d.passage_properties.dialogue_ratio+' · action '+d.passage_properties.action_density+
      ' · open-dep '+d.diagnostics.opening_context_dependency+' · closing '+d.diagnostics.closing_completeness+
      ' · conf '+d.boundary_confidence+' · '+d.segmentation_method+'</div>'+
      '<div style="font:12px sans-serif;color:#888">Click a paragraph = set START; Shift-click = set END.</div>'+
      paraList(d)+controls(d,c);
    wrap.appendChild(div);});
  document.getElementById('prog').textContent=" — "+done+"/"+shown+" decided";
}
function stamp(c){c.timestamp=new Date().toISOString();c.reviewer=document.getElementById('rev').value;}
function setF(id,k,v){const c=get(id);c[k]=v;stamp(c);save();if(k==='decision')render();}
function setRate(id,k,v){const c=get(id);c.ratings[k]=v?+v:null;stamp(c);save();}
function resetAdj(id){const c=get(id);c.adjusted_start=null;c.adjusted_end=null;stamp(c);save();render();}
function exportDecisions(){const out={reviewer:document.getElementById('rev').value,generated_at:new Date().toISOString(),
  harvest_version:"harvest-v1",decisions:dec};const b=new Blob([JSON.stringify(out,null,1)],{type:"application/json"});
  const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download="decisions.json";a.click();}
const fsel=document.getElementById('filter');
[...new Set(DATA.map(d=>d.source_filename))].forEach(s=>{const o=document.createElement('option');o.value=o.textContent=s;fsel.appendChild(o);});
fsel.onchange=render;document.getElementById('rev').onchange=save;render();
</script></body></html>"""


if __name__ == "__main__":
    main()
