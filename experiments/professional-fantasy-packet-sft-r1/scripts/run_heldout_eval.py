"""Dispatch 30H — held-out evaluation generation. 3 model arms x 2 prompt conditions x 11 scenes = 66.
Frozen greedy decoding. Prompt = system + packet only (targets never sent). Writes generation-log.jsonl
incrementally + DONE sentinel. Runs in linewright-ternary-train:d26 on the GX10.
Mounts: /work (prompts+outputs), /sft (adapters), /hf (model cache). NON-THINKING."""
import json, os, time, datetime, contextlib
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

QWEN = "/hf/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218"
BASE_REV = "b968826d9c46dd6066d109eabc6255188de91218"
WORK = "/work"
SEED = 20260722
MAXNEW = 6144
ADAPT = {"atomic_packet_sft": ("/sft/atomic/lora-out/final", "810461f6f60a"),
         "compositional_packet_sft": ("/sft/compositional/lora-out/final", "232ee7e7103d")}
ARMS = ["frozen_base", "atomic_packet_sft", "compositional_packet_sft"]
CONDS = ["atomic_packet", "compositional_packet"]


def now():
    return datetime.datetime.utcnow().isoformat() + "Z"


torch.manual_seed(SEED)
tok = AutoTokenizer.from_pretrained(QWEN)
prompts = {c: [json.loads(l) for l in open(f"{WORK}/prompts-{c}.jsonl", encoding="utf-8") if l.strip()]
           for c in CONDS}

base = AutoModelForCausalLM.from_pretrained(QWEN, torch_dtype=torch.bfloat16, device_map="cuda")
base.config.use_cache = True
model = PeftModel.from_pretrained(base, ADAPT["atomic_packet_sft"][0], adapter_name="atomic")
model.load_adapter(ADAPT["compositional_packet_sft"][0], adapter_name="comp")
model.eval()
print("model+adapters loaded", flush=True)

logf = open(f"{WORK}/generation-log.jsonl", "w", encoding="utf-8", newline="\n")
n = 0
for arm in ARMS:
    if arm == "frozen_base":
        ctx = model.disable_adapter(); adp_prefix = None
    else:
        model.set_adapter("atomic" if arm == "atomic_packet_sft" else "comp")
        ctx = contextlib.nullcontext(); adp_prefix = ADAPT[arm][1]
    with ctx:
        for cond in CONDS:
            for p in prompts[cond]:
                pid = p["passage_id"]
                gid = f"{arm}__{cond}__{pid}"
                msgs = [{"role": "system", "content": p["system"]}, {"role": "user", "content": p["prompt"]}]
                enc = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False,
                                              return_tensors="pt", return_dict=True)
                input_ids = enc["input_ids"].to("cuda"); attn = enc["attention_mask"].to("cuda")
                t0 = now()
                err = None
                try:
                    with torch.no_grad():
                        out = model.generate(input_ids=input_ids, attention_mask=attn, max_new_tokens=MAXNEW,
                                             do_sample=False, temperature=None, top_p=None, top_k=None,
                                             repetition_penalty=1.0, pad_token_id=tok.eos_token_id)
                    new = out[0, input_ids.shape[1]:]
                    text = tok.decode(new, skip_special_tokens=True)
                    outn = int(new.shape[0])
                    finish = "length" if outn >= MAXNEW else "eos"
                except Exception as e:
                    text = ""; outn = 0; finish = "error"; err = str(e)[:200]
                rec = {"generation_id": gid, "model_arm": arm, "prompt_condition": cond, "passage_id": pid,
                       "set_id": "heldout-c01", "seed": SEED,
                       "decoding_config": {"do_sample": False, "temperature": 0.0, "top_p": 1.0, "top_k": 0,
                                           "max_new_tokens": MAXNEW, "repetition_penalty": 1.0, "enable_thinking": False},
                       "input_token_count": int(input_ids.shape[1]), "output_token_count": outn,
                       "finish_reason": finish, "generation_text": text, "adapter_hash_prefix": adp_prefix,
                       "base_revision": BASE_REV, "generation_started_at": t0, "generation_completed_at": now(),
                       "error": err}
                logf.write(json.dumps(rec, ensure_ascii=False) + "\n"); logf.flush()
                n += 1
                print(f"[{n}/66] {gid} out={outn} {finish}", flush=True)
logf.close()
open(f"{WORK}/DONE", "w").write(f"{n}\n")
print("GEN_DONE", n, flush=True)
