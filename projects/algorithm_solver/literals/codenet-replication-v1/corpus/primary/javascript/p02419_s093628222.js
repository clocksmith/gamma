var input = require('fs').readFileSync('/dev/stdin', 'utf8');
input = input.toLowerCase();
var a = input.split('\n');
var W = a[0];
var result = [];
for(var i=1;i<a.length;i++){
    b = a[i].split(' ');
    var count = 0;
    for(var j=0;j<b.length;j++){
        if(b[j] === 'END'){
            break;
        }
        if(b[j] === W){
            count += 1;
            result.push(count);
        }
    }
}
console.log(result.length);

