// parameter "input" gets all data

function nbrDividor(n){
	var nbr=0;
	for (var i = 1; i <=n; i++) {
		if(n%i==0)
			nbr++;
	}
	return nbr;

}
function Main(input) {

	var a = parseInt(input, 10);
	var ans = 0;
	for (var i = 1; i <=a; i++) {
		if(nbrDividor(i)==8 && i%2==1){
			ans++;
		}
	}
	//output
	console.log('%d',ans);
}
// Don't edit this line!


Main(require("fs").readFileSync("/dev/stdin", "utf8"));