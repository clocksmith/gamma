function Main(inputs) {
	const inputlines = inputs.split("\n");
 	const testcase = inputlines[0];
  
  	let counts = ["AC", "WA", "TLE", "RE"];
  	counts["AC"] = counts["WA"] = counts["TLE"] = counts["RE"] = 0;
  
	for(let i=1;i <= testcase;i++){
  		let key = inputlines[i];
  		counts[key] = (counts[key] != 0) ? counts[key] + 1 : 1;
	}
  
  	console.log("AC x "+counts['AC']);
	console.log("WA x "+counts['WA']);
  	console.log("TLE x "+counts['TLE']);
  	console.log("RE x "+counts['RE']);
}
 
Main(require("fs").readFileSync("/dev/stdin", "utf8"));