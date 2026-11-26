var mini = -1;
var iValue = 0;

function Main(input) {

	input = input.split(" ");
	var N = parseInt(input[0]);
	var L = parseInt(input[1]);
	
	var before = 0.5*N*N + (L-0.5)*N;
	var after  = 0.5*N*N + (L-0.5)*N - L + 1;
	
	for(var i = 1;i < N + 1 ;i++){
	    var value = before - after + i;
	    value = Math.abs(value);
	    
	    if(mini === -1){
	        mini = value;
	        iValue = i;
	    }
	    
	    if(mini > value){
	        mini = value;
	        iValue = i;
	    }
	}
	
	console.log(after - iValue);
	
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));