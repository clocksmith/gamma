x=require('fs').readFileSync('/dev/stdin','utf8').trim().split(/\s/);
y=[1,2,3,4,5,6,7,8,9,10];

for(i=0;i<x.length-1;i+=3){
    count=0;
    for(j=0;j<10;j++){
        if(y[j]<=20-(x[i]*1+x[i+1]*1)&&y[j]!=x[i+2]&&y[j]!=x[i+1]&&y[j]!=x[i]){
        count++;
        }
    }
    if(count>=4){
        console.log("YES");
    }else{
        console.log("NO");
    }
}