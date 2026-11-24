function main(input){
  input = input.split("\n");
  var n = parseInt(input[0].split(" ")[0]);
  var d = parseInt(input[0].split(" ")[1]);

  var number = 1 + 2 * d ;
  number =  n / number; 
  console.log(Math.ceil(number));
}
 
 
main(require('fs').readFileSync('/dev/stdin', 'utf8'));