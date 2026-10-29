"use strict";
class Fancy {
 constructor(){this.values=[];this.scale=1n;this.offset=0n;this.inverseScale=1n;}
 append(val){const p=1000000007n;this.values.push(((BigInt(val)-this.offset+p)%p)*this.inverseScale%p);}
 addAll(inc){this.offset=(this.offset+BigInt(inc))%1000000007n;}
 multAll(m){const p=1000000007n,value=BigInt(m);this.scale=this.scale*value%p;this.offset=this.offset*value%p;let base=value,exponent=1000000005n,inverse=1n;while(exponent){if(exponent&1n)inverse=inverse*base%p;base=base*base%p;exponent>>=1n;}this.inverseScale=this.inverseScale*inverse%p;}
 getIndex(idx){return idx>=this.values.length?-1:Number((this.values[idx]*this.scale+this.offset)%1000000007n);}
}
module.exports={Fancy};
