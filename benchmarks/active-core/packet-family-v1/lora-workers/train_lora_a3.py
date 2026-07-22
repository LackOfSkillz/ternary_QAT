"""Dispatch 27 Phase B — conservative Qwen3-8B LoRA pilot on Dataset A.3.
Runs inside linewright-ternary-train:d26 on a GX10. Frozen config qwen3-8b-lora-pilot-v1.
Frequent checkpoints (adapters); per-checkpoint metadata (examples/tokens/loss/grad-norm/hash).
NON-THINKING enforced. NO QAT.
"""
import json, os, hashlib, time
import torch
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments,
                          TrainerCallback)
from peft import LoraConfig, get_peft_model

QWEN="/hf/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218"
RECS="/work/a3-pilot.jsonl"
OUT="/work/lora-out"
SEED=20260722
MAXLEN=2048
SYS=("You are LineWright, a fiction-craft writing assistant. You serve the author and the task, "
     "not a house style. Obey the task authority; preserve canon; obey declared constraints; "
     "respect the invention budget; preserve the author's voice; revise only authorized elements; "
     "prefer no change when the passage is already right; reduce repetitive generic habits at the "
     "craft level; and do not explain your work unless asked. For structured tasks, return valid "
     "output in exactly the requested shape and nothing else.")
VAL_FAMS=["scene_drafting","focused_revision","voice_preservation","no_change_and_restraint",
          "canon_application","structured_protocol"]

torch.manual_seed(SEED)
tok=AutoTokenizer.from_pretrained(QWEN)
if tok.pad_token_id is None: tok.pad_token=tok.eos_token

recs=[json.loads(l) for l in open(RECS,encoding="utf-8") if l.strip()]
def user_text(r):
    u=r["prompt"]
    if r.get("source"): u+="\n\nSOURCE:\n"+r["source"]
    return u
def encode(r):
    msgs=[{"role":"system","content":SYS},{"role":"user","content":user_text(r)}]
    enc=tok.apply_chat_template(msgs,add_generation_prompt=True,enable_thinking=False,tokenize=True)
    prompt_ids=enc["input_ids"] if hasattr(enc,"keys") else enc
    if prompt_ids and isinstance(prompt_ids[0],list): prompt_ids=prompt_ids[0]
    gold=tok(r["gold_output"],add_special_tokens=False)["input_ids"]+[tok.eos_token_id]
    ids=(prompt_ids+gold)[:MAXLEN]
    labels=([-100]*len(prompt_ids)+gold)[:MAXLEN]
    return {"input_ids":ids,"labels":labels,"attention_mask":[1]*len(ids)}

# deterministic diverse val: first record of each of 6 families
val_ids=set(); 
for fam in VAL_FAMS:
    for r in recs:
        if r["task_family"]==fam and r["record_id"] not in val_ids:
            val_ids.add(r["record_id"]); break
train=[encode(r) for r in recs if r["record_id"] not in val_ids]
val=[encode(r) for r in recs if r["record_id"] in val_ids]
print(f"train={len(train)} val={len(val)} (held out {sorted(val_ids)})",flush=True)

class Coll:
    def __call__(self,feats):
        m=max(len(f["input_ids"]) for f in feats)
        def pad(x,v): return x+[v]*(m-len(x))
        import torch as T
        return {"input_ids":T.tensor([pad(f["input_ids"],tok.pad_token_id) for f in feats]),
                "attention_mask":T.tensor([pad(f["attention_mask"],0) for f in feats]),
                "labels":T.tensor([pad(f["labels"],-100) for f in feats])}

model=AutoModelForCausalLM.from_pretrained(QWEN,torch_dtype=torch.bfloat16,device_map="cuda")
model.enable_input_require_grads()
lcfg=LoraConfig(r=16,lora_alpha=16,lora_dropout=0.05,bias="none",task_type="CAUSAL_LM",
                target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
model=get_peft_model(model,lcfg)
trainable=sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"trainable params: {trainable}",flush=True)

meta=[]
class MetaCb(TrainerCallback):
    def on_save(self,args,state,control,**kw):
        step=state.global_step
        ex=step*args.per_device_train_batch_size*args.gradient_accumulation_steps
        ck=os.path.join(OUT,f"checkpoint-{step}","adapter_model.safetensors")
        h=hashlib.sha256(open(ck,"rb").read()).hexdigest() if os.path.exists(ck) else None
        last={k:v for lg in state.log_history for k,v in lg.items()}
        meta.append({"optimizer_step":step,"examples_seen":ex,
                     "estimated_dataset_passes":round(ex/len(train),2),
                     "training_loss":last.get("loss"),"validation_loss":last.get("eval_loss"),
                     "learning_rate":last.get("learning_rate"),"grad_norm":last.get("grad_norm"),
                     "adapter_hash":h})
        json.dump(meta,open(os.path.join(OUT,"checkpoint-meta.json"),"w"),indent=1)
        print(f"[ckpt {step}] ex={ex} passes={round(ex/len(train),2)} loss={last.get('loss')} adapter={h[:12] if h else None}",flush=True)

args=TrainingArguments(output_dir=OUT,num_train_epochs=1,per_device_train_batch_size=2,
    gradient_accumulation_steps=1,learning_rate=1e-5,lr_scheduler_type="cosine",warmup_ratio=0.03,
    weight_decay=0.0,max_grad_norm=1.0,bf16=True,logging_steps=1,save_steps=3,save_strategy="steps",
    eval_strategy="steps",eval_steps=3,seed=SEED,report_to=[],dataloader_num_workers=0,
    save_total_limit=20,remove_unused_columns=False)
tr=Trainer(model=model,args=args,train_dataset=train,eval_dataset=val,data_collator=Coll(),
           callbacks=[MetaCb()])
t0=time.time()
tr.train()
# final save
model.save_pretrained(os.path.join(OUT,"final"))
fh=hashlib.sha256(open(os.path.join(OUT,"final","adapter_model.safetensors"),"rb").read()).hexdigest()
peak=torch.cuda.max_memory_allocated()/1e9
summary={"trainable_params":trainable,"train_records":len(train),"val_records":len(val),
         "held_out":sorted(val_ids),"train_seconds":round(time.time()-t0,1),"peak_gpu_gb":round(peak,2),
         "final_adapter_hash":fh,"checkpoints":meta,"seed":SEED,"lr":1e-5,"rank":16,"alpha":16,
         "base_revision":"b968826d9c46dd6066d109eabc6255188de91218","thinking":"disabled"}
json.dump(summary,open(os.path.join(OUT,"training-summary.json"),"w"),indent=1)
print("TRAIN_DONE",json.dumps({"seconds":summary["train_seconds"],"peak_gb":summary["peak_gpu_gb"],
      "n_ckpt":len(meta),"final":fh[:12]}),flush=True)
