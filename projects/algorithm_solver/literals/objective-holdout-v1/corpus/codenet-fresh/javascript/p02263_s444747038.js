function main() {
  var
  stack = [];
  input[0].split(' ').forEach(function (op) {
    var
    x, y;
    switch(op) {
    case '+':
      y = stack.pop();
      x = stack.pop();
      return stack.push(x + y);
    case '-':
      y = stack.pop();
      x = stack.pop();
      return stack.push(x - y);
    case '*':
      y = stack.pop();
      x = stack.pop();
      return stack.push(x * y);
    default:
      stack.push(Number(op));
    }
  });
  console.log(stack[0]);
}

var
input = '';

process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
  input += chunk;
});
process.stdin.on('end', function() {
  input = input.split(/\n\r|\n|\r/);
  main();
});