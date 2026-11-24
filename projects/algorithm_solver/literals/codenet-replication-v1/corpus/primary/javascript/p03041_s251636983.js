function main(input){
  input = input.split('\n');
  const N = Number(input[0].split(' ')[0]);
  const K = Number(input[0].split(' ')[1]) - 1;
  var S = input[1].split('');
  
  result = [];
  S.forEach((value,index) => {
    if(index == K){
      result.push(value.toLowerCase());
    }else{
     result.push(value);
    }
  })
    console.log(result.join(''));
}
main(require('fs').readFileSync('/dev/stdin','utf8'));