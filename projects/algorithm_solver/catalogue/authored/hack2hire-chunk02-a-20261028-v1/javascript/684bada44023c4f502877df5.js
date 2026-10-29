"use strict";
// Hack2Hire 684bada44023c4f502877df5 (IP CIDR Firewall); INFERRED spec (default deny); qualification unknown.
function toInt(ip) { let v = 0; for (const p of ip.split('.')) v = (v * 256) + Number(p); return v >>> 0; }
class IpFirewall {
  constructor(rules) {
    this.rules = rules.map(([action, target]) => {
      const slash = target.indexOf('/');
      const base = slash < 0 ? target : target.slice(0, slash), bits = slash < 0 ? 32 : Number(target.slice(slash + 1));
      const mask = bits === 0 ? 0 : (0xFFFFFFFF << (32 - bits)) >>> 0;
      return [mask, (toInt(base) & mask) >>> 0, action === 'ALLOW'];
    });
  }
  isAllowed(ip) {
    const v = toInt(ip);
    for (const [mask, base, allow] of this.rules) if (((v & mask) >>> 0) === base) return allow;
    return false;
  }
}
function solve(operations, args) {
  const receiver = new IpFirewall(...args[0]), out = [null];
  for (let i = 1; i < operations.length; i++) { const v = receiver[operations[i]](...args[i]); out.push(v === undefined ? null : v); }
  return out;
}
module.exports = solve;
module.exports.IpFirewall = IpFirewall;
