process.stdin.resume();
process.stdin.setEncoding('utf8');

var lines = []
var reader = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});

reader.on('line', (line) => {
  lines.push(line);
});

reader.on('close', () => {
 var abc = lines[0].split(' ');
 var a = Number(abc[0]);
 var b = Number(abc[1]);
 var c = Number(abc[2]);
 var i = 0;
 var count = 0;

 while(true){
   if(a%2 == 1 || b%2 == 1 || c%2 == 1){
     break;
   }
   var tmpa = b/2 + c/2;
   
   var tmpb = a/2 + c/2;
   
   var tmpc = b/2 + a/2;

   if(tmpa == a && tmpb == b && tmpc == c){
     console.log("-1");
     count++;
     break;
   }
   
   
   a = tmpa;
   b = tmpb;
   c = tmpc;
   
   i++;
   
 }

 if(count == 0){
 console.log(i);
}
});
