function main(input){
    inputI = parseInt(input);
    out=0;
    out=Math.floor(inputI/2);


    if(inputI%2==1){
        out++;
    }

    console.log(out);

}

main(require("fs").readFileSync("/dev/stdin", "utf8"));