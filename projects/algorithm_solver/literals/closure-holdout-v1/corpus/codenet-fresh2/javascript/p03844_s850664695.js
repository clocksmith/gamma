function main(a){
	a = a.split(" ");
	a[0]=parseInt(a[0],10);
	a[2]=parseInt(a[2],10);
	(a[1]=="+")?op(a[0]+a[2]):op(a[0]-a[2]);
	}
function op(a){
	console.log(a);
}
function stn(a){
		return a.map(function(x){return parseInt(x,10);});
}
main(require("fs").readFileSync("/dev/stdin", "utf8"));