// Deterministic pure-CPU reverse-mode scalar automatic differentiation tape.
// Used identically for unrolled meta-gradients in learned initialization, conventional calibration,
// proposals, and behavioral-transcript neural regeneration.

export class Tape {
  constructor() {
    this.nodes = [];
  }

  var(val) {
    const id = this.nodes.length;
    this.nodes.push({ val, grad: 0, p1: -1, p2: -1, w1: 0, w2: 0 });
    return id;
  }

  const(val) {
    return this.var(val);
  }

  add(a, b) {
    const id = this.nodes.length;
    this.nodes.push({ val: this.nodes[a].val + this.nodes[b].val, grad: 0, p1: a, p2: b, w1: 1, w2: 1 });
    return id;
  }

  sub(a, b) {
    const id = this.nodes.length;
    this.nodes.push({ val: this.nodes[a].val - this.nodes[b].val, grad: 0, p1: a, p2: b, w1: 1, w2: -1 });
    return id;
  }

  mul(a, b) {
    const va = this.nodes[a].val;
    const vb = this.nodes[b].val;
    const id = this.nodes.length;
    this.nodes.push({ val: va * vb, grad: 0, p1: a, p2: b, w1: vb, w2: va });
    return id;
  }

  scale(a, c) {
    const id = this.nodes.length;
    this.nodes.push({ val: this.nodes[a].val * c, grad: 0, p1: a, p2: -1, w1: c, w2: 0 });
    return id;
  }

  addConst(a, c) {
    const id = this.nodes.length;
    this.nodes.push({ val: this.nodes[a].val + c, grad: 0, p1: a, p2: -1, w1: 1, w2: 0 });
    return id;
  }

  div(a, b) {
    const va = this.nodes[a].val;
    const vb = this.nodes[b].val;
    const id = this.nodes.length;
    this.nodes.push({ val: va / vb, grad: 0, p1: a, p2: b, w1: 1 / vb, w2: -va / (vb * vb) });
    return id;
  }

  tanh(a) {
    const t = Math.tanh(this.nodes[a].val);
    const id = this.nodes.length;
    this.nodes.push({ val: t, grad: 0, p1: a, p2: -1, w1: 1 - t * t, w2: 0 });
    return id;
  }

  exp(a) {
    const raw = this.nodes[a].val;
    const cv = Math.max(-12, Math.min(12, raw));
    const e = Math.exp(cv);
    const w = raw >= -12 && raw <= 12 ? e : 0;
    const id = this.nodes.length;
    this.nodes.push({ val: e, grad: 0, p1: a, p2: -1, w1: w, w2: 0 });
    return id;
  }

  sqrt(a) {
    const s = Math.sqrt(this.nodes[a].val);
    const id = this.nodes.length;
    this.nodes.push({ val: s, grad: 0, p1: a, p2: -1, w1: 0.5 / s, w2: 0 });
    return id;
  }

  backward(rootId) {
    this.nodes[rootId].grad = 1;
    for (let i = rootId; i >= 0; i -= 1) {
      const n = this.nodes[i];
      if (n.grad === 0) continue;
      if (n.p1 >= 0) this.nodes[n.p1].grad += n.grad * n.w1;
      if (n.p2 >= 0) this.nodes[n.p2].grad += n.grad * n.w2;
    }
  }
}
