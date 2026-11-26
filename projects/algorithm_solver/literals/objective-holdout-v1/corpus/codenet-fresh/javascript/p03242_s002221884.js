function Main(input){
	function a(b){
  	if(b == 1){
    	return "9";
    }
  	if(b == 9){
    	return "1";
    }
    return b;
  }
	
	h = a(input[0]) + a(input[1]) + a(input[2]);
  
  return h;
}

console.log(Main(require("fs").readFileSync("/dev/stdin", "utf8")));