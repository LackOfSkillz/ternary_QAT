"""Dispatch 30H — generate the self-contained HTML blind-review app for the held-out eval matrix.

Groups the 6 candidate outputs per held-out scene, randomizes A-F per scene with a fixed recorded
seed, and hides model arm + prompt condition + source + cohort + target. Emits:
  private-data/eval/runs/dispatch30h/blind-review.html   (self-contained, no network/assets)
  private-data/eval/runs/dispatch30h/blind-key.json      (PRIVATE mapping opaque -> real identity)

The generated HTML holds private generations, so it is NEVER committed; only THIS generator is.
"""
import json
import os
import random
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RUN = os.path.join(EXP, "private-data", "eval", "runs", "dispatch30h")
COMP_PACKETS = os.path.join(EXP, "private-data", "eval", "heldout-c01-compositional.jsonl")
BLIND_SEED = 20260725
ORDER = ["abercrombe-c01", "sanderson-c01", "gord-c01", "mouser-c01", "wot-c01", "pawn-c01",
         "streams-c01", "lies-c01", "lor-c01", "HP-c01", "got-c01"]
LABELS = ["A", "B", "C", "D", "E", "F"]


def brief(tp):
    """Abstracted scene brief from the compositional packet (no source/target)."""
    L = []
    L.append(f"Viewpoint: {tp.get('viewpoint','')} | Tense: {tp.get('tense','')}")
    if tp.get("scene_purpose"): L.append(f"Purpose: {tp['scene_purpose']}")
    if tp.get("opening_state"): L.append(f"Opening: {tp['opening_state']}")
    for lbl, k in (("Required beats", "required_beats"), ("Canon", "canon_facts"),
                   ("Knowledge limits", "knowledge_limits"), ("Do not", "forbidden_developments"),
                   ("Physical continuity", "physical_continuity"), ("Character goals", "character_goals")):
        if tp.get(k):
            L.append(lbl + ": " + " | ".join(tp[k]))
    if tp.get("scene_boundary"): L.append(f"Boundary: {tp['scene_boundary']}")
    if tp.get("ending_state"): L.append(f"Ending: {tp['ending_state']}")
    cp = tp.get("craft_profile") or {}
    if cp: L.append("Craft: " + "; ".join(f"{k}={v}" for k, v in cp.items()))
    return "\n".join(L)


def main():
    gens = {}
    for l in open(os.path.join(RUN, "generation-log.jsonl"), encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            gens.setdefault(r["passage_id"], []).append(r)
    comp = {json.loads(l)["record_id"][:-2]: json.loads(l)
            for l in open(COMP_PACKETS, encoding="utf-8") if l.strip()}

    rng = random.Random(BLIND_SEED)
    scenes_data = []   # for HTML (blinded)
    key = {"evaluation_id": "dispatch30h", "blind_seed": BLIND_SEED, "scenes": {}}
    for i, pid in enumerate(ORDER, 1):
        sid = f"S{i:02d}"
        cands = list(gens[pid])
        assert len(cands) == 6, f"{pid}: expected 6 candidates, got {len(cands)}"
        rng.shuffle(cands)                    # per-scene randomization (fixed seed)
        cand_html, cand_key = [], {}
        for lbl, c in zip(LABELS, cands):
            cand_html.append({"label": lbl, "text": c["generation_text"],
                              "output_tokens": c["output_token_count"], "finish": c["finish_reason"]})
            cand_key[lbl] = {"model_arm": c["model_arm"], "prompt_condition": c["prompt_condition"],
                             "generation_id": c["generation_id"]}
        scenes_data.append({"scene_id": sid, "brief": brief(comp[pid]["training_packet"]),
                            "candidates": cand_html})
        key["scenes"][sid] = {"passage_id": pid, "candidates": cand_key}

    json.dump(key, open(os.path.join(RUN, "blind-key.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    # Embed as JSON, neutralizing any "</script>" (or "<!--") that a generation might contain so it
    # cannot terminate the <script> element early and blank the page. "<\/" in a JS string is just "</".
    data_js = json.dumps(scenes_data, ensure_ascii=False).replace("</", "<\\/")
    html_out = TEMPLATE.replace("__DATA__", data_js)
    open(os.path.join(RUN, "blind-review.html"), "w", encoding="utf-8", newline="\n").write(html_out)
    # integrity for the caller (no identities)
    print(json.dumps({"scenes": len(scenes_data), "candidates_per_scene": 6,
                      "total_candidates": sum(len(s["candidates"]) for s in scenes_data),
                      "blind_seed": BLIND_SEED,
                      "html": os.path.relpath(os.path.join(RUN, "blind-review.html"), EXP),
                      "key_private": os.path.relpath(os.path.join(RUN, "blind-key.json"), EXP)}, indent=1))


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>Held-Out Eval Blind Review</title>
<style>
body{font:14px/1.55 -apple-system,Segoe UI,sans-serif;margin:0;background:#eef0f2;color:#1a1a1a}
header{position:sticky;top:0;background:#222;color:#eee;padding:8px 14px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:9}
header b{font-size:15px}#wrap{max-width:1180px;margin:0 auto;padding:14px}
button{font:13px sans-serif;padding:5px 10px;border:1px solid #555;border-radius:6px;background:#f6f7f9;cursor:pointer}
select,input{font:13px sans-serif;padding:3px 6px}
.brief{white-space:pre-wrap;background:#faf9f6;border:1px solid #e5e2da;border-radius:8px;padding:10px;font:13px/1.5 ui-monospace,monospace;max-height:230px;overflow:auto}
.cand{background:#fff;border:1px solid #d5d8dc;border-radius:8px;padding:12px;margin:12px 0;box-shadow:0 1px 3px #0001}
.cand.done{border-left:5px solid #2a8}.cand.todo{border-left:5px solid #d9a520}
.out{white-space:pre-wrap;font:14px/1.6 Georgia,serif;max-height:360px;overflow:auto;background:#fcfcfd;padding:10px;border:1px solid #eee;border-radius:6px}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:8px 0}
.badge{background:#eef;border-radius:10px;padding:1px 8px;font-size:12px}
h2{font-size:16px;margin:6px 0}h3{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#666;margin:10px 0 4px}
.scenebox{background:#f3f6ff;border:1px solid #cdd8f0;border-radius:8px;padding:12px;margin:14px 0}
label{font-size:13px}.saved{color:#2a2}.nav{display:flex;gap:8px;align-items:center}
.pill{padding:2px 8px;border-radius:10px;font-size:12px;background:#ddd}.pill.on{background:#2a8;color:#fff}
textarea{width:100%;font:13px sans-serif;border:1px solid #ccd;border-radius:6px;padding:6px;min-height:44px}
</style></head><body>
<header><b>Held-Out Eval — Blind Review</b><span id="prog"></span>
<label>reviewer <input id="rev" size="7" value="gary"></label>
<span class="nav"><button onclick="go(-1)">&larr; Prev</button><span id="idx"></span><button onclick="go(1)">Next &rarr;</button></span>
<button onclick="exportReview()">Export Review JSON</button>
<label style="background:#444;padding:4px 8px;border-radius:6px;cursor:pointer">Import JSON<input id="imp" type="file" accept="application/json" style="display:none" onchange="importReview(event)"></label>
<button onclick="exportBackup()">Export Progress Backup</button>
<button onclick="clearAll()" style="background:#b33;color:#fff;border-color:#900">Clear Saved Review</button>
<span id="msg" class="saved"></span></header>
<div id="wrap"></div>
<script>
const DATA=__DATA__;const KEY="lw-heldout-blind-dispatch30h";
const Q5=["","1","2","3","4","5"];const RC=["","none","low","medium","high"];
const DISP=["","strongest","acceptable","weak","failed","suspicious_reconstruction"];
const BEST=["","A","B","C","D","E","F","no_clear_winner"];
const SECOND=["","A","B","C","D","E","F","none"];const RETC=["","A","B","C","D","E","F","none"];
let store=JSON.parse(localStorage.getItem(KEY)||"{}");let cur=0;
function s(sid){return store[sid]||(store[sid]={cand:{},scene:{}});}
function save(){localStorage.setItem(KEY,JSON.stringify(store));document.getElementById('msg').textContent="saved "+new Date().toLocaleTimeString();render();}
function esc(t){return (t||"").replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function candDone(o){return o&&o.overall_quality&&o.packet_adherence&&o.scene_coherence&&o.prose_quality&&o.retrieval_concern&&o.disposition;}
function sceneDone(sid){const st=s(sid);const sc=DATA.find(x=>x.scene_id==sid);return !!(sc&&sc.candidates.every(c=>candDone(st.cand[c.label]))&&st.scene.best_candidate);}
function setC(sid,lb,k,v){const c=s(sid).cand;(c[lb]||(c[lb]={}))[k]=v;save();}
function setS(sid,k,v){s(sid).scene[k]=v;save();}
function go(d){cur=Math.max(0,Math.min(DATA.length-1,cur+d));render();window.scrollTo(0,0);}
function jump(i){cur=i;render();window.scrollTo(0,0);}
// build a <select> with data-attributes (no inline JS); listeners bound after innerHTML
function sel(opts,val,scene,field,cand){
 let a='data-scene="'+scene+'" data-field="'+field+'"'+(cand?' data-candidate="'+cand+'"':'');
 let h='<select '+a+'>';opts.forEach(o=>h+='<option '+(val==o?'selected':'')+' value="'+esc(o)+'">'+(o||'—')+'</option>');return h+'</select>';}
function bind(wrap){
 wrap.querySelectorAll('select[data-scene],textarea[data-scene]').forEach(el=>{
  el.addEventListener('change',()=>{const d=el.dataset;
   if(d.candidate){setC(d.scene,d.candidate,d.field,el.value);}else{setS(d.scene,d.field,el.value);}});});
 wrap.querySelectorAll('.pill[data-index]').forEach(el=>{
  el.addEventListener('click',()=>jump(parseInt(el.dataset.index,10)));});
}
function render(){
 const sc=DATA[cur];const st=s(sc.scene_id);const wrap=document.getElementById('wrap');
 let done=DATA.filter(x=>sceneDone(x.scene_id)).length;
 document.getElementById('prog').textContent=" — "+done+"/"+DATA.length+" scenes complete";
 document.getElementById('idx').textContent=(cur+1)+" / "+DATA.length;
 let nav='<div class="row">';DATA.forEach((x,i)=>nav+='<span class="pill '+(sceneDone(x.scene_id)?'on':'')+'" data-index="'+i+'" style="cursor:pointer">'+esc(x.scene_id)+'</span>');nav+='</div>';
 let h=nav+'<h2>Scene '+esc(sc.scene_id)+'</h2><h3>Scene brief (for judging adherence)</h3><div class="brief">'+esc(sc.brief)+'</div>';
 sc.candidates.forEach(c=>{const o=st.cand[c.label]||{};const dc=candDone(o)?'done':'todo';const SI=sc.scene_id;
  h+='<div class="cand '+dc+'"><div class="row"><b>Candidate '+esc(c.label)+'</b> <span class="badge">'+c.output_tokens+' tok</span> <span class="badge">'+esc(c.finish)+'</span> <span class="badge">'+(candDone(o)?'reviewed':'unreviewed')+'</span></div>'+
   '<div class="out">'+esc(c.text)+'</div>'+
   '<div class="row"><label>overall '+sel(Q5,o.overall_quality,SI,'overall_quality',c.label)+'</label>'+
   '<label>adherence '+sel(Q5,o.packet_adherence,SI,'packet_adherence',c.label)+'</label>'+
   '<label>coherence '+sel(Q5,o.scene_coherence,SI,'scene_coherence',c.label)+'</label>'+
   '<label>prose '+sel(Q5,o.prose_quality,SI,'prose_quality',c.label)+'</label>'+
   '<label>retrieval '+sel(RC,o.retrieval_concern,SI,'retrieval_concern',c.label)+'</label>'+
   '<label>disposition '+sel(DISP,o.disposition,SI,'disposition',c.label)+'</label></div>'+
   '<textarea data-scene="'+SI+'" data-candidate="'+c.label+'" data-field="notes" placeholder="notes on Candidate '+esc(c.label)+'">'+esc(o.notes||'')+'</textarea></div>';});
 const ss=st.scene;const SI=sc.scene_id;
 h+='<div class="scenebox"><h3>Scene-level comparison</h3><div class="row">'+
  '<label>best '+sel(BEST,ss.best_candidate,SI,'best_candidate')+'</label>'+
  '<label>second '+sel(SECOND,ss.second_best_candidate,SI,'second_best_candidate')+'</label>'+
  '<label>most retrieval-concerning '+sel(RETC,ss.most_retrieval_concerning,SI,'most_retrieval_concerning')+'</label></div>'+
  '<textarea data-scene="'+SI+'" data-field="scene_notes" placeholder="scene notes">'+esc(ss.scene_notes||'')+'</textarea></div>';
 wrap.innerHTML=h;bind(wrap);
}
function exportReview(){
 const out={reviewer:document.getElementById('rev').value||"gary",evaluation_id:"dispatch30h",set_id:"heldout-c01",
   generated_at:new Date().toISOString(),scenes:{}};
 DATA.forEach(sc=>{const st=s(sc.scene_id);const cr={};
   sc.candidates.forEach(c=>{const o=st.cand[c.label]||{};cr[c.label]={overall_quality:o.overall_quality||null,
     packet_adherence:o.packet_adherence||null,scene_coherence:o.scene_coherence||null,prose_quality:o.prose_quality||null,
     retrieval_concern:o.retrieval_concern||null,disposition:o.disposition||null,notes:o.notes||""};});
   out.scenes[sc.scene_id]={candidate_reviews:cr,best_candidate:st.scene.best_candidate||null,
     second_best_candidate:st.scene.second_best_candidate||null,most_retrieval_concerning:st.scene.most_retrieval_concerning||null,
     scene_notes:st.scene.scene_notes||""};});
 dl(JSON.stringify(out,null,1),"heldout-eval-blind-review-dispatch30h.json");
}
function exportBackup(){dl(JSON.stringify({key:KEY,saved:store},null,1),"heldout-eval-progress-backup-dispatch30h.json");}
function importReview(ev){const f=ev.target.files[0];if(!f)return;const r=new FileReader();
 r.onload=()=>{try{const j=JSON.parse(r.result);const src=j.saved||{};
   if(j.scenes){/* import an exported review */ Object.keys(j.scenes).forEach(sid=>{const sc=j.scenes[sid];const st=s(sid);
     Object.keys(sc.candidate_reviews||{}).forEach(lb=>{st.cand[lb]=Object.assign({},sc.candidate_reviews[lb]);});
     st.scene={best_candidate:sc.best_candidate,second_best_candidate:sc.second_best_candidate,
       most_retrieval_concerning:sc.most_retrieval_concerning,scene_notes:sc.scene_notes};});}
   else {Object.assign(store,src);} save();alert("Imported.");}catch(e){alert("Import failed: "+e);}};
 r.readAsText(f);ev.target.value="";}
function clearAll(){if(confirm("Clear ALL saved review work? This cannot be undone (export a backup first).")){localStorage.removeItem(KEY);store={};save();}}
function dl(txt,name){const b=new Blob([txt],{type:"application/json"});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;a.click();}
document.getElementById('rev').onchange=save;
try{render();}catch(err){console.error(err);
 document.getElementById('wrap').innerHTML='<pre style="color:#b00020;padding:20px;white-space:pre-wrap">Review UI error: '+esc(String(err&&err.stack||err))+'</pre>';}
</script></body></html>"""


if __name__ == "__main__":
    main()
