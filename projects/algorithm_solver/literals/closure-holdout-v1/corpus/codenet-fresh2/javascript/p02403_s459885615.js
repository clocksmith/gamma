var x = require('fs').readFileSync('/dev/stdin', 'utf8');

var input = x.split("\n");

for (var k = 0 ; k < input.length; k++) {

    var arr = input[k].split(" ").map(Number);
    var H = arr[0];
    var W = arr[1];
 
    if(H === 0 && W === 0) break;
    var result = "";
    for( var i = 0; i < H; i++){
        for( var j = 0; j < W; j++) {
            result += "#"
            
        }
        result += "\n";        
    }
        console.log(result);

}


