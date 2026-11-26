
function main(input){
    abc=input.split(' ');
    abc=abc.sort();
    a=parseInt(abc[0],10)
    b=parseInt(abc[1],10)
    if (a*b%2==0){
        console.log("No")
    }else{
        console.log("Yes") 
    }

}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));