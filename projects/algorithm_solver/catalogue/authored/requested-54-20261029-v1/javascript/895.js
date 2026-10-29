"use strict";
class FreqStack {
 constructor(){this.frequency=new Map();this.groups=new Map();this.maximum=0;}
 push(val){const f=(this.frequency.get(val)||0)+1;this.frequency.set(val,f);if(!this.groups.has(f))this.groups.set(f,[]);this.groups.get(f).push(val);this.maximum=Math.max(this.maximum,f);}
 pop(){const a=this.groups.get(this.maximum),v=a.pop();this.frequency.set(v,this.frequency.get(v)-1);if(!a.length)this.maximum--;return v;}
}
module.exports={FreqStack};
