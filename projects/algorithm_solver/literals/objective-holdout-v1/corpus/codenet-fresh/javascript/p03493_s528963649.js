function main(input){
  input = input.toString()
  count = 0
  for(i=0; i<3; i++){
  	if(input[i]==1){
      count += 1
    }
  }
  console.log(count)
}
main(require("fs").readFileSync("/dev/stdin","utf8"));