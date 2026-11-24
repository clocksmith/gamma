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

console.log(main());
function main(){
  var n = o.a();
  if(n === 1)return "Yes\n2\n1 1\n1 1"
  var m = Math.sqrt(n*2)|0;
  if(m * (m+1) / 2 !== n)return "No";
  var ans = Array(m+1).fill(0).map(a=>[]);
  var a = Array(m+1).fill(0).map(a=>[]);
  ans[0][0] = m;
  var k = 1;
  for(var i = 1; i <= m; i++){ans[0][i] = k; a[0].push(k++)}
  for(var i = 1; i <= m; i++){
    ans[i][0] = m;
    for(var j = 0; j < i; j++){
      ans[i][j+1] = a[j].pop();
    }
    for(; j < m; j++){
      ans[i][j+1] = k;
      a[i].push(k++);
    }
  }
  console.log("Yes");
  console.log(m+1);
  return ans.map(a=>a.join(" ")).join("\n");
}