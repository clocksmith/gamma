process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data',function(chunk){

var inputs = chunk.toString().trim();
var data = inputs.toString().split(' ').map(Number);

var a = data[0];
var b = data[1];
var c = data[2];
var count = 0;

for(var i = a; i < b+1 ; i++){

if(c % i === 0){
    count++;
  }
 }
console.log(count);
});