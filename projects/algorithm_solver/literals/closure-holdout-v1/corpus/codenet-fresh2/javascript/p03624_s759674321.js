function Main(input){
    var str = 'abcdefghijklmnopqrstuvwxyz';
    var arr =[];

    for(var i = 0, len = str.length; i < len; i++){
        if(input.indexOf(str[i]) < 0){
            arr.push(str[i]);
            continue;
        }
    }
    if(arr.length === 0){
        console.log('None');
    }else{
        arr.sort();
        console.log(arr[0]);
    }
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
