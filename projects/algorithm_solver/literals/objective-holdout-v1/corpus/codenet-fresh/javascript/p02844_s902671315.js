function Main(input){
    input = input.split("\n");
    var arr = input[1].split("").map(Number);
    var sum = 0;
    for(var i=0;i<10;i++){
        var p_1 = -1
        for(var p=0;p<arr.length;p++){
            if(arr[p]==i){
                p_1 = p;
                break;
            }
        }
        if(p_1==-1) continue;
      //  console.log("1:"+i)
        for(var j=0;j<10;j++){
            var p_2 = p_1
            for(var p=p_2+1;p<arr.length;p++){
                if(arr[p]==j){
                    p_2 = p;
                    break;
                }
            }
            if(p_2==p_1) continue;
            //console.log("2:"+j)
            for(var k=0;k<10;k++){
                for(var p=p_2+1;p<arr.length;p++){
                    if(arr[p]==k){
                        sum++;
                        break;
                    }
                }  
            }      
        }
    }
    console.log(sum)
}Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());
