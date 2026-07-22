"""Dispatch 27 Phase B — evaluate Qwen3-8B base + every LoRA checkpoint on the frozen 14-item
subset. Non-thinking, greedy, identical prompts/settings across base and all checkpoints. Writes
one normalized-generation-result per (item, role). Runs in linewright-ternary-train:d26 on a GX10.
"""
import json, os, hashlib, glob, time, re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

QWEN="/hf/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218"
PLAN="/work/generation-plan.json"
LORA="/work/lora-out"
OUT="/work/eval-out"
SEED=20260722; MAXNEW=1024
EVAL=['lwdb-a-length-short','lwdb-a-length-long','lwdb-g-turn-single','lwdb-b-voice-terse',
 'lwdb-b-voice-lyrical','lwdb-c-restraint-clean','lwdb-c-restraint-fix','lwdb-d-canon-apply',
 'lwdb-e-scene-contract','lwdb-d-constraint-low','lwdb-f-surface-bare','pf-scene_drafting-realistic',
 'lwdb-i-stability-long','lwdb-g-turn-multi']
THINK=re.compile(r"<think>.*?</think>\s*",re.DOTALL)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
plan=json.load(open(PLAN,encoding="utf-8"))
tok=AutoTokenizer.from_pretrained(QWEN)
if tok.pad_token_id is None: tok.pad_token=tok.eos_token
base=AutoModelForCausalLM.from_pretrained(QWEN,torch_dtype=torch.bfloat16,device_map="cuda").eval()

def gen(model,item):
    p=json.loads(plan["items"][item]["prompt"])
    msgs=[{"role":"system","content":p["system"]},{"role":"user","content":p["user"]}]
    enc=tok.apply_chat_template(msgs,add_generation_prompt=True,enable_thinking=False,tokenize=True,
                                return_dict=True,return_tensors="pt")
    ids=enc["input_ids"].to(model.device); attn=enc["attention_mask"].to(model.device)
    torch.manual_seed(SEED)
    with torch.no_grad():
        out=model.generate(input_ids=ids,attention_mask=attn,max_new_tokens=MAXNEW,do_sample=False,
                           pad_token_id=tok.pad_token_id)
    new=out[0][ids.shape[1]:]; raw=tok.decode(new,skip_special_tokens=True)
    had=bool(THINK.search(raw)) or raw.strip().startswith("<think>")
    text=THINK.sub("",raw).strip(); cap=int(new.shape[0])>=MAXNEW
    return text,had,int(new.shape[0]),cap

def run_role(model,role):
    d=os.path.join(OUT,role); os.makedirs(d,exist_ok=True)
    for it in EVAL:
        of=os.path.join(d,it+".json")
        if os.path.exists(of): continue
        text,had,ntok,cap=gen(model,it)
        r={"schema":"normalized-generation-result","run_id":"qwen3-lora-checkpoint-curve-v1",
           "benchmark_item_id":it,"model_role":role,"prompt_hash":plan["item_hashes"][it],
           "output_tokens":ntok,"hit_token_cap":cap,"reasoning_mode":"non_thinking",
           "reasoning_trace_detected":had,"output_text":text,"output_hash":sha(text),"status":"completed"}
        json.dump(r,open(os.path.join(d,it+".json"),"w",encoding="utf-8"),ensure_ascii=False)
    print(f"[{role}] done {len(EVAL)} items",flush=True)

# base first (raw)
run_role(base,"qwen3_8b_base")
# checkpoints via adapter switching
ckpts=sorted([p for p in glob.glob(os.path.join(LORA,"checkpoint-*")) if os.path.isdir(p)],key=lambda p:int(os.path.basename(p).split("-")[-1]))
if os.path.isdir(os.path.join(LORA,"final")): ckpts.append(os.path.join(LORA,"final"))
pm=None
for i,ck in enumerate(ckpts):
    name="a%d"%i
    if pm is None:
        pm=PeftModel.from_pretrained(base,ck,adapter_name=name).eval()
    else:
        pm.load_adapter(ck,adapter_name=name)
    pm.set_adapter(name)
    role="lora_"+os.path.basename(ck).replace("checkpoint-","step-")
    run_role(pm,role)
print("EVAL_DONE",json.dumps({"roles":["qwen3_8b_base"]+["lora_"+os.path.basename(c).replace("checkpoint-","step-") for c in ckpts]}),flush=True)
