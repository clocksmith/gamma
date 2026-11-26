var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var mod = 1e9+7;
function abmod(){for(var a=arguments,r=a[0],i=1;i<a.length;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i++])%mod;return r;}
var fac=[1,1];
function fSet(n){for(var i=2;i<=n;)fac[i]=abmod(fac[i-1],i++);}

console.log(main());
function main(){
  var n = o.a();
  var s = o.a(1);
  if(s[0] === "W")return 0;
  fSet(n);
  var ans = fac[n];
  var l=1;
  var cnt = 1;
  for(var i = 1; i < 2*n; i++){
    if(s[i] === "W"){
      if(l&1){
        l++;
      }else{
        cnt = abmod(cnt,l);
        l--;
      }
    }else{
      if(l&1){
        cnt = abmod(cnt,l);
        l--;
      }else{
        l++;
      }
    }
  }
  if(l !== 0)return 0;
  return abmod(ans,cnt);
}