"""Real-model Python (`gamma.fastweight`) vs JavaScript (`doppler_fastweight.mjs`) transformation parity check.

Runs 6 real prompts (1 per v3 domain) through `Qwen3-0.6B-NHS` to extract real `(prompt_ids, embed_tokens, h_last, lm_head)`
tensors, executes BOTH Python `derive_fastweight` + `evaluate_query` and Node.js `deriveFastweight` + `evaluateQuery`,
and verifies exact agreement on `mode`, `anchors_count`, `step_etas`, candidate `u_t`, and `< 1e-4` logit-delta max error.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
for d in (REPO_ROOT, THIS_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from gamma.fastweight import derive_fastweight
from gamma.fastweight.adapter import safe_norm
from tasks_v3 import build_v3_unseen_tasks


def main() -> None:
    model_path = REPO_ROOT / ".work" / "models" / "Qwen3-0.6B-NHS-786708b3"
    out_json = REPO_ROOT / ".work" / "query-swiglu-fastweight-v3" / "python_js_real_tensor_parity.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    mjs_uri = (REPO_ROOT / "gamma" / "fastweight" / "doppler_fastweight.mjs").as_uri()

    tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True, fix_mistral_regex=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).to("mps").eval()
    nl_id = tok.encode("\n", add_special_tokens=False)[-1]

    all_tasks = build_v3_unseen_tasks(seed=990001, count_per_domain=1)
    records = []

    with torch.inference_mode():
        for t in all_tasks:
            c_ids = tok.encode(t["context_text"], add_special_tokens=False)
            f_ids = tok.encode(t["prompt"], add_special_tokens=False)
            c_len = len(c_ids)
            p_gpu = torch.tensor([f_ids], device="mps", dtype=torch.long)
            out = model.model(input_ids=p_gpu, use_cache=False, return_dict=True)
            hl_gpu = out.last_hidden_state[0]

            ad_py, xq_py = derive_fastweight(
                p_gpu, c_len, nl_id, model.model.embed_tokens.weight, hl_gpu, model.lm_head.weight,
                context_text=t["context_text"], query_line_text=t["query_text"],
            )
            del_py = ad_py.evaluate_query(
                xq_py, encode_fn=lambda s: tok.encode(s, add_special_tokens=False)
            )

            # Export exact float32 inputs to Node.js `doppler_fastweight.mjs`
            et_norm_f32 = safe_norm(model.model.embed_tokens.weight[p_gpu[0]].float()).cpu().tolist()
            hl_f32_flat = hl_gpu.float().cpu().reshape(-1).tolist()
            u_ids = sorted({int(x) for x in f_ids})
            w_lm_map = {
                str(uid): model.lm_head.weight[uid].float().cpu().tolist()
                for uid in u_ids
            }
            healed_tok_map = {}
            for raw_ln in t["context_text"].splitlines():
                ln = raw_ln.strip()
                qc = t["query_text"].strip()
                if ln.startswith(qc) and len(ln) > len(qc):
                    suf = ln[len(qc):]
                    healed_tok_map[suf] = tok.encode(suf, add_special_tokens=False)

            node_code = f"""
import {{ deriveFastweight, evaluateQuery }} from {json.dumps(mjs_uri)};
const req = JSON.parse(await new Promise(res => {{
  let s = '';
  process.stdin.on('data', c => s += c);
  process.stdin.on('end', () => res(s));
}}));
const etRows = req.et_norm.map(r => Float32Array.from(r));
const hFlat = Float32Array.from(req.hl_flat);
const wMap = new Map(Object.entries(req.w_lm).map(([k, v]) => [Number(k), Float32Array.from(v)]));
const ad = deriveFastweight(
  req.f_ids, req.c_len, req.nl_id, etRows, hFlat, req.d,
  id => wMap.get(id),
  {{ contextText: req.ctx_txt, queryLineText: req.qry_txt, enableKeyGate: true, enableLooNllGate: true }},
);
const deltas = evaluateQuery(ad, ad.xqRaw, true, s => req.healed_map[s] || []);
const dOut = {{}};
for (const [off, {{ uTokens, dv }}] of deltas.entries()) {{
  dOut[String(off)] = {{ uTokens: Array.from(uTokens), dv: Array.from(dv) }};
}}
process.stdout.write(JSON.stringify({{
  mode: ad.mode,
  anchors_count: ad.anchorsCount,
  step_etas: ad.stepEtas,
  deltas: dOut,
}}) + '\\n');
"""
            proc = subprocess.run(
                ["node", "--input-type=module", "-e", node_code],
                input=json.dumps({
                    "f_ids": f_ids,
                    "c_len": c_len,
                    "nl_id": nl_id,
                    "d": int(hl_gpu.shape[-1]),
                    "et_norm": et_norm_f32,
                    "hl_flat": hl_f32_flat,
                    "w_lm": w_lm_map,
                    "ctx_txt": t["context_text"],
                    "qry_txt": t["query_text"],
                    "healed_map": healed_tok_map,
                }),
                text=True,
                capture_output=True,
                check=True,
            )
            js_res = json.loads(proc.stdout.strip().splitlines()[-1])
            assert js_res["mode"] == ad_py.mode, f"Mode mismatch on {t['domain']}: {js_res['mode']} vs {ad_py.mode}"
            assert js_res["anchors_count"] == ad_py.anchors_count
            assert {int(k): float(v) for k, v in js_res["step_etas"].items()} == ad_py.step_etas

            max_logit_err = 0.0
            for off, (u_t, dv) in del_py.items():
                jd = js_res["deltas"][str(off)]
                assert u_t.cpu().tolist() == jd["uTokens"]
                for a, b in zip(dv.cpu().tolist(), jd["dv"]):
                    max_logit_err = max(max_logit_err, abs(a - b))
            assert max_logit_err < 1e-3, f"Logit delta mismatch on {t['domain']}: {max_logit_err}"

            records.append({
                "id": t["id"],
                "domain": t["domain"],
                "mode": ad_py.mode,
                "anchors_count": ad_py.anchors_count,
                "active_steps": len(del_py),
                "max_abs_logit_delta_diff_py_vs_js": max_logit_err,
            })

    summary = {
        "schema": "gamma.reconfiguration.query_swiglu_fastweight_v3.py_js_parity/v1",
        "all_passed": True,
        "global_max_abs_logit_delta_diff": max(r["max_abs_logit_delta_diff_py_vs_js"] for r in records),
        "domains_verified": records,
    }
    out_json.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
