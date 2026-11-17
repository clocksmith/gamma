"""Cross-engine numerical parity (`adapter.py` <-> `doppler_fastweight.mjs`) and PyTorchEngine tests."""
from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import unittest
import torch

from gamma.fastweight import (
    FastWeightSession,
    compile_closed_form_layer_lora,
    derive_continuous_cache_knn,
    derive_fastweight,
    discover_support_anchors,
    find_default_context_split,
    make_random_layer_lora,
    make_zero_adapter,
    make_zero_layer_lora,
)
from gamma.fastweight.adapter import resolve_hop_continuation_tokens, safe_norm

REPO_ROOT = Path(__file__).resolve().parents[1]
MJS_PATH = REPO_ROOT / "gamma" / "fastweight" / "doppler_fastweight.mjs"


def _run_node_fastweight(payload: dict) -> dict:
    script = f"""
import {{
  deriveFastweight,
  evaluateQuery,
  resolveHopContinuationTokens,
  dequantizeQ4KRow,
}} from {json.dumps(MJS_PATH.as_uri())};

const req = JSON.parse(await new Promise(res => {{
  let s = '';
  process.stdin.on('data', c => s += c);
  process.stdin.on('end', () => res(s));
}}));

if (req.kind === 'q4k') {{
  const u8 = Uint8Array.from(req.bytes);
  const out = Array.from(dequantizeQ4KRow(u8, 0, 256));
  process.stdout.write(JSON.stringify({{ out }}) + '\\n');
  process.exit(0);
}}

const etRows = req.et_norm.map(r => Float32Array.from(r));
const hFlat = Float32Array.from(req.h_last_flat);
const wMap = new Map(Object.entries(req.w_lm).map(([k, v]) => [Number(k), Float32Array.from(v)]));
const ad = deriveFastweight(
  req.prompt_ids,
  req.c_len,
  req.nl_id,
  etRows,
  hFlat,
  req.d,
  id => wMap.get(id),
  {{ contextText: req.context_text || '', queryLineText: req.query_line_text || '', enableKeyGate: true, enableLooNllGate: true }},
);
const deltas = evaluateQuery(ad, ad.xqRaw, true, s => s.split('').map(c => c.charCodeAt(0)));
const outDeltas = {{}};
for (const [off, {{ uTokens, dv }}] of deltas.entries()) {{
  outDeltas[String(off)] = {{ uTokens: Array.from(uTokens), dv: Array.from(dv) }};
}}
const hop = req.gen_text
  ? resolveHopContinuationTokens(req.context_text || '', req.gen_text, s => s.split('').map(c => c.charCodeAt(0)))
  : null;
process.stdout.write(JSON.stringify({{
  mode: ad.mode,
  anchors_count: ad.anchorsCount,
  step_etas: ad.stepEtas,
  deltas: outDeltas,
  hop,
}}) + '\\n');
"""
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


class TestFastWeightCrossEngineParity(unittest.TestCase):
    def test_q4k_superblock_dequantization(self) -> None:
        # Construct one 144-byte Q4_K block: d=0.5 (f16 0x3800), dmin=0.25 (f16 0x3400)
        d_dmin = struct.pack("<HH", 0x3800, 0x3400)
        scales = bytes([2, 3, 4, 5, 1, 1, 2, 2, 0x21, 0x32, 0x11, 0x22])
        qs = bytes([(i * 17) & 0xFF for i in range(128)])
        block = list(d_dmin + scales + qs)
        self.assertEqual(len(block), 144)
        res = _run_node_fastweight({"kind": "q4k", "bytes": block})
        out = res["out"]
        self.assertEqual(len(out), 256)
        # First sub-block j=0: sc=2, mn=1 => val = 0.5*2*(qs[l] & 0xF) - 0.25*1
        for l_idx in range(32):
            q4 = qs[l_idx] & 0x0F
            expected = 0.5 * 2 * q4 - 0.25 * 1
            self.assertAlmostEqual(out[l_idx], expected, places=5)

    def test_python_and_doppler_js_numerical_parity_all_regimes(self) -> None:
        gen = torch.Generator().manual_seed(4242)
        V, d = 120, 32
        nl_id = 10
        delim_id = 11
        E_tok = torch.randn((V, d), generator=gen, dtype=torch.float32)
        W_lm = 0.1 * torch.randn((V, d), generator=gen, dtype=torch.float32)

        # 1. Window lookup regime (query line matches anchor 2 verbatim!)
        hdr = [20, 21, 22, nl_id]
        lines = []
        keys = [[30 + r, 40 + r, 50 + r] for r in range(8)]
        vals = [[60 + r, 70 + r] for r in range(8)]
        for r in range(8):
            lines.extend([15] + keys[r] + [delim_id] + vals[r] + [nl_id])
        qry_match = [15] + keys[2] + [delim_id]
        p_win = hdr + lines + qry_match
        c_len = len(hdr + lines)

        T = len(p_win)
        h_last = 0.2 * torch.randn((T, d), generator=gen, dtype=torch.float32)
        anchor_vec = torch.randn(d, generator=gen)
        for idx, tok in enumerate(p_win):
            if tok == delim_id:
                h_last[idx] = anchor_vec + 0.01 * torch.randn(d, generator=gen)

        p_t = torch.tensor([p_win], dtype=torch.long)
        ad_py, xq_py = derive_fastweight(p_t, c_len, nl_id, E_tok, h_last, W_lm)
        self.assertEqual(ad_py.mode, "window")
        del_py = ad_py.evaluate_query(xq_py)

        et_norm = safe_norm(E_tok[p_t[0]]).tolist()
        u_ids = sorted({int(x) for x in p_win})
        js_win = _run_node_fastweight({
            "kind": "derive",
            "prompt_ids": p_win,
            "c_len": c_len,
            "nl_id": nl_id,
            "et_norm": et_norm,
            "h_last_flat": h_last.reshape(-1).tolist(),
            "d": d,
            "w_lm": {str(i): W_lm[i].tolist() for i in u_ids},
        })
        self.assertEqual(js_win["mode"], "window")
        self.assertEqual(js_win["anchors_count"], ad_py.anchors_count)
        for off, (u_t, dv) in del_py.items():
            js_d = js_win["deltas"][str(off)]
            self.assertEqual(u_t.tolist(), js_d["uTokens"])
            max_diff = max(abs(a - b) for a, b in zip(dv.tolist(), js_d["dv"]))
            self.assertLess(max_diff, 1e-4)

        # 2. Multi-hop bridge regime (unseen query key -> abstains at step 0 + resolves dynamic hop!)
        qry_unseen = [15, 95, 96, 97, delim_id]
        p_mh = hdr + lines + qry_unseen
        h_mh = 0.2 * torch.randn((len(p_mh), d), generator=gen, dtype=torch.float32)
        for idx, tok in enumerate(p_mh):
            if tok == delim_id:
                h_mh[idx] = anchor_vec + 0.01 * torch.randn(d, generator=gen)
        ctx_text = "ALIAS a05 = rl_dbe\nENDPOINT rl_dbe : so-73\nCONNECT a00 => rl_000/ka-11\n"
        p_mh_t = torch.tensor([p_mh], dtype=torch.long)
        ad_mh, xq_mh = derive_fastweight(p_mh_t, c_len, nl_id, E_tok, h_mh, W_lm, context_text=ctx_text)
        self.assertEqual(ad_mh.mode, "multihop_bridge")
        self.assertEqual(ad_mh.evaluate_query(xq_mh), {})

        hop_py = resolve_hop_continuation_tokens(ctx_text, "rl_dbe/", lambda s: [ord(c) for c in s])
        self.assertEqual(hop_py, [ord(c) for c in "so-73"])

        js_mh = _run_node_fastweight({
            "kind": "derive",
            "prompt_ids": p_mh,
            "c_len": c_len,
            "nl_id": nl_id,
            "et_norm": safe_norm(E_tok[p_mh_t[0]]).tolist(),
            "h_last_flat": h_mh.reshape(-1).tolist(),
            "d": d,
            "w_lm": {str(i): W_lm[i].tolist() for i in sorted({int(x) for x in p_mh})},
            "context_text": ctx_text,
            "gen_text": "rl_dbe/",
        })
        self.assertEqual(js_mh["mode"], "multihop_bridge")
        self.assertEqual(js_mh["deltas"], {})
        self.assertEqual(js_mh["hop"], hop_py)

        # 3. Clause-bigram rule regime (many-to-2 label mapping + exact LOO NLL parity)
        lines_rule = []
        for r in range(12):
            feat_tok = 31 if (r % 2 == 0) else 32
            noise_tok = 80 + (r % 4)
            ans_tok = 61 if (r % 2 == 0) else 62
            lines_rule.extend([16, feat_tok, noise_tok, delim_id, ans_tok, 75, nl_id])
        qry_rule = [16, 31, 83, delim_id]
        p_rl = hdr + lines_rule + qry_rule
        c_rl = len(hdr + lines_rule)
        h_rl = 0.05 * torch.randn((len(p_rl), d), generator=gen, dtype=torch.float32)
        for idx, tok in enumerate(p_rl):
            if tok == delim_id:
                h_rl[idx] = anchor_vec + 0.01 * torch.randn(d, generator=gen)
        p_rl_t = torch.tensor([p_rl], dtype=torch.long)
        ad_rl, xq_rl = derive_fastweight(p_rl_t, c_rl, nl_id, E_tok, h_rl, W_lm)
        self.assertEqual(ad_rl.mode, "clause_bigram")
        del_rl = ad_rl.evaluate_query(xq_rl)

        js_rl = _run_node_fastweight({
            "kind": "derive",
            "prompt_ids": p_rl,
            "c_len": c_rl,
            "nl_id": nl_id,
            "et_norm": safe_norm(E_tok[p_rl_t[0]]).tolist(),
            "h_last_flat": h_rl.reshape(-1).tolist(),
            "d": d,
            "w_lm": {str(i): W_lm[i].tolist() for i in sorted({int(x) for x in p_rl})},
        })
        self.assertEqual(js_rl["mode"], "clause_bigram")
        self.assertEqual({int(k): float(v) for k, v in js_rl["step_etas"].items()}, ad_rl.step_etas)
        for off, (u_t, dv) in del_rl.items():
            js_d = js_rl["deltas"][str(off)]
            self.assertEqual(u_t.tolist(), js_d["uTokens"])
            max_diff = max(abs(a - b) for a, b in zip(dv.tolist(), js_d["dv"]))
            self.assertLess(max_diff, 1e-4)

        # 4. Zero adapter produces empty/zero logit modification and find_default_context_split works
        z_ad = make_zero_adapter(ad_rl)
        for _, dv in z_ad.evaluate_query(xq_rl).values():
            self.assertEqual(float(dv.abs().max().item()), 0.0)
        self.assertEqual(find_default_context_split(p_rl, nl_id), c_rl)

    def test_v4_closed_form_layer_lora_and_continuous_cache_parity(self) -> None:
        gen = torch.Generator().manual_seed(90401)
        nl_id = 10
        delim_id = 11
        d_hidden = 16
        d_inter = 24
        V = 64
        header_ids = [2, 3, 4, nl_id]
        support_ids = list(header_ids)
        classes = [40, 41, 42, 43]
        for ex in range(8):
            support_ids.extend([5, 12 + ex, 20 + (ex % 3), 25 + ex, delim_id, classes[ex % 4], nl_id])

        ancs = discover_support_anchors(support_ids, nl_id)
        self.assertEqual(len(ancs), 8)

        target_layers = [2, 3]
        iso_entries_py = []
        iso_entries_js = []
        for ex, a in enumerate(ancs):
            line_ids = header_ids + support_ids[a["line_start"] : a["line_end"]]
            rel_anchor = len(header_ids) + (a["pos"] - a["line_start"])
            h_flat = 0.4 * torch.randn(len(line_ids) * d_hidden, generator=gen, dtype=torch.float32)
            lz_py = {l_idx: torch.randn(len(line_ids) * d_inter, generator=gen, dtype=torch.float32) for l_idx in target_layers}
            bare_top = [50, 51, 52]
            iso_entries_py.append({
                "line_ids": line_ids,
                "rel_anchor": rel_anchor,
                "h_flat": h_flat,
                "layer_z_map": lz_py,
                "bare_top": bare_top,
            })
            iso_entries_js.append({
                "lineIds": line_ids,
                "relAnchor": rel_anchor,
                "hFlat": h_flat.tolist(),
                "layerZMap": {str(k): v.tolist() for k, v in lz_py.items()},
                "bareTop": bare_top,
            })

        cat_h = 0.4 * torch.randn(len(support_ids) * d_hidden, generator=gen, dtype=torch.float32)
        cat_lz = {l_idx: torch.randn(len(support_ids) * d_inter, generator=gen, dtype=torch.float32) for l_idx in target_layers}
        cat_entry_py = {"h_flat": cat_h, "layer_z_map": cat_lz}
        cat_entry_js = {"hFlat": cat_h.tolist(), "layerZMap": {str(k): v.tolist() for k, v in cat_lz.items()}}

        final_norm_g = 1.0 + 0.1 * torch.randn(d_hidden, generator=gen, dtype=torch.float32)
        pfn_map = {l_idx: 20.0 + 2.0 * torch.randn(d_hidden, generator=gen, dtype=torch.float32) for l_idx in target_layers}
        sig_map = {2: 0.085, 3: 0.092}
        W_lm = torch.randn((V, d_hidden), generator=gen, dtype=torch.float32)

        for use_pfn in (False, True):
            lora_py = compile_closed_form_layer_lora(
                support_ids=support_ids,
                header_ids=header_ids,
                nl_id=nl_id,
                d_hidden=d_hidden,
                d_inter=d_inter,
                target_layers=target_layers,
                iso_entries=iso_entries_py,
                cat_entry=cat_entry_py,
                final_norm_g=final_norm_g,
                get_lm_row=lambda tid: W_lm[tid],
                post_ffn_norm_map=(pfn_map if use_pfn else None),
                sigma_u0_map=(sig_map if use_pfn else None),
            )
            self.assertTrue(lora_py.active)
            self.assertEqual(lora_py.rank, 6)

            z_lora = make_zero_layer_lora(lora_py)
            r_lora = make_random_layer_lora(lora_py, seed=77)
            for l_idx in target_layers:
                self.assertEqual(float(z_lora.layers[l_idx][0].abs().max().item()), 0.0)
                self.assertAlmostEqual(
                    float(r_lora.layers[l_idx][0].norm().item()),
                    float(lora_py.layers[l_idx][0].norm().item()),
                    places=3,
                )

            js_script = f"""
import {{ compileClosedFormLayerLoRA, deriveContinuousCacheKnn }} from {json.dumps(MJS_PATH.as_uri())};
const req = JSON.parse(await new Promise(res => {{
  let s = ''; process.stdin.on('data', c => s += c); process.stdin.on('end', () => res(s));
}}));
const isoEntries = req.iso_entries.map(e => ({{
  lineIds: e.lineIds,
  relAnchor: e.relAnchor,
  hFlat: Float32Array.from(e.hFlat),
  layerZMap: new Map(Object.entries(e.layerZMap).map(([k, v]) => [Number(k), Float32Array.from(v)])),
  bareTop: e.bareTop,
}}));
const catEntry = {{
  hFlat: Float32Array.from(req.cat_entry.hFlat),
  layerZMap: new Map(Object.entries(req.cat_entry.layerZMap).map(([k, v]) => [Number(k), Float32Array.from(v)])),
}};
const wMap = new Map(Object.entries(req.w_lm).map(([k, v]) => [Number(k), Float32Array.from(v)]));
const pfnMap = req.pfn_map ? new Map(Object.entries(req.pfn_map).map(([k, v]) => [Number(k), Float32Array.from(v)])) : null;
const sigMap = req.sig_map ? new Map(Object.entries(req.sig_map).map(([k, v]) => [Number(k), Number(v)])) : null;
const out = compileClosedFormLayerLoRA({{
  supportIds: req.support_ids,
  headerIds: req.header_ids,
  nlId: req.nl_id,
  dHidden: req.d_hidden,
  dInter: req.d_inter,
  targetLayers: req.target_layers,
  isoEntries,
  catEntry,
  finalNormG: Float32Array.from(req.final_norm_g),
  getLmRow: tid => wMap.get(tid),
  postFfnNormMap: pfnMap,
  sigmaU0Map: sigMap,
}});
const layers = {{}};
for (const [l, obj] of out.layers.entries()) {{
  layers[String(l)] = {{ a: Array.from(obj.a), b: Array.from(obj.b) }};
}}
const knn = deriveContinuousCacheKnn(req.knn_prompt, req.c_len, req.nl_id, Float32Array.from(req.knn_h), req.d_hidden);
const knn0 = knn.get(0);
process.stdout.write(JSON.stringify({{
  rank: out.rank,
  layers,
  knn: knn0 ? {{ u: knn0.uTokens, dv: Array.from(knn0.dv) }} : null,
}}) + '\\n');
"""
            knn_prompt = support_ids + [5, 19, 21, 31, delim_id]
            knn_h = torch.randn((len(knn_prompt), d_hidden), generator=gen, dtype=torch.float32)
            knn_py = derive_continuous_cache_knn(knn_prompt, len(support_ids), nl_id, knn_h)

            proc = subprocess.run(
                ["node", "--input-type=module", "-e", js_script],
                input=json.dumps({
                    "support_ids": support_ids,
                    "header_ids": header_ids,
                    "nl_id": nl_id,
                    "d_hidden": d_hidden,
                    "d_inter": d_inter,
                    "target_layers": target_layers,
                    "iso_entries": iso_entries_js,
                    "cat_entry": cat_entry_js,
                    "final_norm_g": final_norm_g.tolist(),
                    "w_lm": {str(i): W_lm[i].tolist() for i in range(V)},
                    "pfn_map": ({str(k): v.tolist() for k, v in pfn_map.items()} if use_pfn else None),
                    "sig_map": ({str(k): v for k, v in sig_map.items()} if use_pfn else None),
                    "knn_prompt": knn_prompt,
                    "c_len": len(support_ids),
                    "knn_h": knn_h.reshape(-1).tolist(),
                }),
                text=True,
                capture_output=True,
                check=True,
            )
            js_out = json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertEqual(js_out["rank"], lora_py.rank)
            for l_idx in target_layers:
                A_py, B_py = lora_py.layers[l_idx]
                A_js = js_out["layers"][str(l_idx)]["a"]
                B_js = js_out["layers"][str(l_idx)]["b"]
                max_a = max(abs(x - y) for x, y in zip(A_py.reshape(-1).tolist(), A_js))
                max_b = max(abs(x - y) for x, y in zip(B_py.reshape(-1).tolist(), B_js))
                self.assertLess(max_a, 1e-5)
                self.assertLess(max_b, 1e-5)

            self.assertEqual(knn_py[0][0].tolist(), js_out["knn"]["u"])
            max_knn = max(abs(x - y) for x, y in zip(knn_py[0][1].tolist(), js_out["knn"]["dv"]))
            self.assertLess(max_knn, 1e-5)


if __name__ == "__main__":
    unittest.main()
