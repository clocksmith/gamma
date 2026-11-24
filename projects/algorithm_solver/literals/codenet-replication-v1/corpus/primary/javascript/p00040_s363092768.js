// 標準入力
var fs = require('fs'),
length = fs.fstatSync(process.stdin.fd).size,
buffer = new Buffer(length),
bytesRead = fs.readSync(process.stdin.fd, buffer, 0, length, 0),
input = buffer.toString('utf8', 0, bytesRead).split('\n');
main();

function main(){
  // 26と互いに素の値
  var multiply = new Int8Array([1,3,5,7,9,11,15,17,19,21,23,25]);

  // 対象
  FIRST:for(var i = 1, len = +input[0]; i <= len; i++){
    var inp = input[i];
    for(var j = 0, lenj = multiply.length; j < lenj; j++){
      var alpha = multiply[j];
      for(var beta = 26; beta--;){
        var alphabets = new Int8Array(26);
        for(var conv = 26; conv--;){
          alphabets[conv] = (conv * alpha + beta) % 26 + 97;
        }

        var thChar = String.fromCharCode(alphabets[19], alphabets[7]);
        var atChar = String.fromCharCode(alphabets[0], alphabets[19]);
        var isChar = String.fromCharCode(alphabets[8], alphabets[18]);

        if(new RegExp(thChar + "("+atChar+"|"+isChar+")").test(inp)){
          console.log(inp.replace(/[a-z]/g,function(a){for(var b = 26, c=a.charCodeAt(0); b--;)if(c==alphabets[b]){return String.fromCharCode(b+97)}}));
          continue FIRST;
        }
      }
    }
  }
}
     