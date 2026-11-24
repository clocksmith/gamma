function Main(input) {
	input = input.split("\n");
	var mem = input[0].split(" ").map(Number);
	var arr = input[1].split(" ").map(Number);
	var sum = 0;
	var st = -1;
	var end = -1;
	for(var i=0;i<arr.length;i++){
	    if(end<arr[i]){
	        sum += end-st;
	        st = arr[i];
	        end = arr[i]+mem[1];
	    }else{
	        end = arr[i]+mem[1];
	    }
	}
	sum += end-st;
	console.log(sum)
}Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());
