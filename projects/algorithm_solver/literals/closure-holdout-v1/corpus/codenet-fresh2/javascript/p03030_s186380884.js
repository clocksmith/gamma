function Main(input) {

	input = input.split("\n");
	var N = parseInt(input[0]);
	var lists = [];
	
	function List(name,score,num){
	    this.name = name;
	    this.score = score;
	    this.num = num;
	}
	
	List.prototype.show = function(){
	    return this.num;
	}
	
	for(var i = 0;i < N;i++){
	     pass = input[i+1].split(" ");
	     lists[i] = new List(pass[0],parseInt(pass[1]),parseInt(i+1));
	}
	
	lists.sort((a,b) => { return (a.name > b.name) ? 1
    						   : (a.name < b.name) ? -1
      				           : (b.score >= a.score)? 1 : -1; });
    for(var j = 0;j < N;j++){
        console.log(lists[j].show());
    }
    //console.log(lists);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));