function Main(input) {
	input = input.split("\n");
	var mem = input[0].split(" ");
	input.shift();
	input = arr1dto2d(input);
	for(var i=0;i<input.length;i++){
		for(var j=0;j<mem[1];j++){
			if(input[i][j]=="snuke"){
				console.log(String.fromCharCode(65+j)+(i+1));
              break;
			}
		}
	}
}Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());
function arr1dto2d (arr){
	for(var i=0;i<arr.length;i++){
		arr[i]=arr[i].split(" ");
		}
	return arr;
}