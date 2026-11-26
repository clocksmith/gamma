function gets(str){
  this._s = str.split("\n");
  this._y = 0;
};
gets.prototype = {
  a: function(f){
    var s = this._s, y = this._y, r;
    if(typeof s[y] === "string")s[y] = s[y].split(" ").reverse();
    r = s[y].pop();
    if(!s[y].length)this._y++;
    return f?r:+r;
  },
  l: function(f){
    var s = this._s[this._y++].split(" ");
    return f?s:s.map(a=>+a);
  },
  m: function(n,f){
    var s = this._s, y = this._y, r = [], i = 0;
    if(f)for(;i < n; i++)r[i] = s[y+i].split(" ");
    else for(;i < n; i++)r[i] = s[y+i].split(" ").map(a=>+a);
    this._y += n;
    return r;
  },
};
var o=new gets(require("fs").readFileSync("/dev/stdin","utf8"));
var comb = [[1]];
var mod = 998244353;
function abmod(){var a=arguments,r=a[0],i=1;for(;i<a.length;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i++])%mod;return r;}

function fcomb(n,r){
  r++;
  for(var i = 1; i < n; i++){
    comb[i] = [1];
    var m = Math.min(i,r)
    for(var j = 1; j < m; j++){
      comb[i][j] = comb[i-1][j] + comb[i-1][j-1];
      comb[i][j] %= mod;
    }
    comb[i][i] = 1;
  }
}

console.log(main());
function main(){
  var k = o.a();
  var n = o.a();
  var ans = [];
  var nk1 = n + k - 1;
  fcomb(k + n, Math.max(n, k >> 1));
  for(var i = 0; i < k; i++){
    var u = i + 2 >> 1, v = Math.min(u, n >> 1), w = 1;
    ans[i] = 0;
    for(var j = 0; j <= v; j++){
      ans[i] += abmod(comb[u][j], comb[nk1-2*j][n-2*j]) * w;
      ans[i] %= mod;
      w *= -1;
    }
    if(ans[i] < 0)ans[i] += mod;
    i++;
    if(i < k)ans[i] = ans[i-1];
  }
  var k2 = 2*k-2;
  for(i = k; i <= k2; i++)ans[i] = ans[k2-i];
  return ans.join("\n");
}