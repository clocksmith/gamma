function Main(input) {
  input = input.split("\n");
	S = input[0];
	T = input[1];

	inS = new Array(26).fill(-1);
  inT = new Array(26).fill(-1);
	var first = "a", last = "z";
  var ans="Yes";
  for(i=0;i<S.length;i++){
    Ssub=S.substr(i,1);
    Tsub=T.substr(i,1);
    if(inS[Ssub.charCodeAt(0)-first.charCodeAt(0)]!=-1){
      if(inS[Ssub.charCodeAt(0)-first.charCodeAt(0)]!=Tsub){
        ans="No";
      }
    }
    if(inT[Tsub.charCodeAt(0)-first.charCodeAt(0)]!=-1){
      if(inT[Tsub.charCodeAt(0)-first.charCodeAt(0)]!=Ssub){
        ans="No";
      }
    }
    if(inS[Ssub.charCodeAt(0)-first.charCodeAt(0)]<0){
      inS[Ssub.charCodeAt(0)-first.charCodeAt(0)]=Tsub;
    }
    if(inT[Tsub.charCodeAt(0)-first.charCodeAt(0)]<0){
      inT[Tsub.charCodeAt(0)-first.charCodeAt(0)]=Ssub;
    }
  }

	var counter = function(str,seq){
		return str.split(seq).length - 1;
  }
  
  console.log('%s', ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
