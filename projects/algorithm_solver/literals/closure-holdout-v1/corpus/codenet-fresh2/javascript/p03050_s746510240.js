function judge(N, number){
  var devide = Math.floor(N/number);
  return (N%number==devide)
}

function main(input){
  const lines = input.split('\n');
  const N = parseInt(lines[0]);

  var result = 0;
  for(var i=1;i<Math.sqrt(N);i++){
//  console.log('---');
//  console.log(i);
    if(N/i-Math.floor(N/i)>0){continue;}
    var favorited_number = N/i-1
    if(judge(N,favorited_number)){result+=favorited_number}
//  console.log(favorited_number);
  }

  console.log(result);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));

