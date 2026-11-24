function Main(input) {
	input = input.trim();
	var s = input.split("\n")[1];
	var max = 0;
	for(var i=0; i<s.length; i++){
		var a = sortMarge(s.substring(0,i+1));
		var b = sortMarge(s.substring(i+1,s.length));
		var count = 0;
		for(var j=0;j<a.length;j++){
			if(b.indexOf(a[j]) > -1){
				count++;
			}
		}
		if(max < count){
			max = count;
		}
	}
	console.log(max);
	return ;
}
function sortMarge(arg){
	var mySet = new Set();
	for(var i=0;i<arg.length;i++){
		mySet.add(arg[i]);
	}
	var array = [];
	mySet.forEach(function(value){
		array.push(value);
	})
	array.sort();
	var ret = "";
	array.forEach(function(value){
		ret+=value;
	})
	return ret;
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
