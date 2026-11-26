function Main(input) {
    input = input.trim().split("\n");
    tmp = input[0].split(" ");
    var N = parseInt(tmp[0],10);
    var A = parseInt(tmp[1],10);
    var B = parseInt(tmp[2],10);
    var C = parseInt(tmp[3],10);
    var D = parseInt(tmp[4],10);
    var S = input[1];
    var output = "Yes";

    if(C < D){
        for(var i = A; i < C; i++){
            if(S[i-1] == "#" && S[i] == "#"){
                output = "No";
                break;
            }
        }
        for(var i = B; i < D; i++){
            if(S[i-1] == "#" && S[i] == "#"){
                output = "No";
                break;
            }
        }
    }
    else{
        var NG = true;
        for(var i = B-1; i < D; i++){
            if(S[i-1] == "." && S[i] == "." && S[i+1] == "."){
                NG = false;
            }
        }
        if(NG){
            output = "No";
        }
        else{
            for(var i = A; i < C; i++){
                if(S[i-1] == "#" && S[i] == "#"){
                    output = "No";
                    break;
                }
            }
            for(var i = B; i < D; i++){
                if(S[i-1] == "#" && S[i] == "#"){
                    output = "No";
                    break;
                }
            }
        }
    }
    console.log(output);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));