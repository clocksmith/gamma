(function main(){
  const lines = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split('\n');
  const n = Number(lines.shift());
  lines.shift().split(' ').map(Number).forEach(function(key, i, a) {
    console.log(`node ${i+1}: key = ${a[i]}, `+(i?`parent key = ${a[Math.floor((i-1)/2)]}, `:'')+(2*i+1<a.length?`left key = ${a[2*i+1]}, `:'')+(2*i+2<a.length?`right key = ${a[2*i+2]}, `:''));
  });
})();

