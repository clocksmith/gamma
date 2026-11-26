var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=input.split("\n");

var N = Arr[0];
var A = Arr[1].split(" ").map(Number);


var selectionSort = (N,array) =>{
    
    let cnt = 0;
    
    for(let i = 0; i < N; i++){
        var minV = i;
        for(let j = i; j < N; j++){
            if(array[j] < array[minV]){
                minV = j;
                
            }
        }
        
      	if(i !== minV){
        	var tmp = array[i];
        	array[i] = array[minV];
        	array[minV] = tmp;
      	    cnt++;
        }
    }

    return cnt;
}


var answer = selectionSort(N,A);

console.log(A.join(" "));
console.log(answer);


