function Main(input) {
  input = input.split("\n");
  input = input[0];
  if(input == 'RSS' || input == 'SRS' || input == 'SSR' || input == 'RSR'){
  	console.log('1');
  }else if(input == 'SRR' || input == 'RRS'){
  	console.log('2');
  }else if(input == 'RRR'){
  	console.log('3');
  }else{
  	console.log('0')
  }
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));