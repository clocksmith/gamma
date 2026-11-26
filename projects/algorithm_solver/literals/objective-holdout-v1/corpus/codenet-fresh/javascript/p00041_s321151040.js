// 標準入力
var fs = require('fs'),
length = fs.fstatSync(process.stdin.fd).size,
buffer = new Buffer(length),
bytesRead = fs.readSync(process.stdin.fd, buffer, 0, length, 0),
input = buffer.toString('utf8', 0, bytesRead).trim().split('\n');
main();
 
function main(){
  var operands = ['+', '-', '*'];
  var inp;
  for(var i = 0; (inp = input[i]) != '0 0 0 0'; i++){
    inp = inp.split(' ').map(Number);
    var found = false;
 
  FIRST:for(var a = 0; a < 4; a++){
    for(var b = 0; b < 4; b++){
      if(a==b)continue;
      for(var c = 0; c < 4; c++){
        if(a==c||b==c)continue;
        for(var d = 0; d < 4; d++){
          if(a==d||b==d||c==d)continue;
 
          for(var op1 = 0; op1 < 3; op1++){
            for(var op2 = 0; op2 < 3; op2++){
              for(var op3 = 0; op3 < 3; op3++){
                if(op1 == 1 && op2 == 1 && op3 == 1)continue;
                
                for(var pattern = 0; pattern < 3; pattern++){
                  var polish = [];
                  switch(pattern){
                  case 0:
                    // pattern1:num num op num op num op (((a op1 b) op2 c) op3 d)
                    polish = [inp[a], inp[b], operands[op1], inp[c], operands[op2], inp[d], operands[op3]];
                    break;
                  case 1:
                    // pattern2:num num num op op num op ((a op2 (b op1 c)) op3 d)
                    polish = [inp[a], inp[b], inp[c], operands[op1], operands[op2], inp[d], operands[op3]];
                    break;
                  case 2:
                    // pattern3:num num num num op op op ((c op1 d) op3 (a op2 b))
                    polish = [inp[a], inp[b], operands[op1],inp[c], inp[d], operands[op2], operands[op3]];
                    break;
                  }
 
                  var stack = [];
                  for(var j = 0; j < 7; j++){
                    var h = polish[j];
                    switch(h){
                    case '+':
                      stack.push(stack.pop() + stack.pop());
                      break;
                    case '-':
                      stack.push(-stack.pop() + stack.pop());
                      break;
                    case '*':
                      stack.push(stack.pop() * stack.pop());
                      break;
                    default:
                      stack.push(h);
                      break;
                    }
                  }
 
                  if(stack.pop() == 10){
                    found = true;
 
                    var result = [];
                    var l, r;
                    for(var j = 0; j < 7; j++){
                    var h = polish[j];
                      if(h == '+' || h == '-' || h == '*'){
                        r = result.pop();
                        l = result.pop();
                        result.push("(" + l + " " + h + " " + r + ")");
                      }else{
                        result.push(h);
                      }
                    }
                     
                    console.log(result.pop());
                    break FIRST;
                  }
                }
              }
            }
          }
        }
      }
    }
  }
 
    if(!found)
      console.log(0);
     
  }
}