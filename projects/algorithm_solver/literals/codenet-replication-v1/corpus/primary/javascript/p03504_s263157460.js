(function() {
    'use strict';

    var lines = [];
    require('readline').createInterface({
      input: process.stdin,
      output: process.stdout
    }).on('line', function(line) {
      lines.push(line);
    });
    process.stdin.on('end', function() {
      //lines.forEach(function(line) {
        //var tokens = line.split(' ').map(Number);
        //    console.log(tokens[0] + ' ' + tokens[1]);
      //}
      //)
      ;

    // ToDo start
      var Ntmp = (lines[0].split(" "))
      var N = parseInt(Ntmp[0])
      var C = parseInt(Ntmp[1])
      var maxT = 0

      var bangumi = []
        for (var i=0 ; i<N ;i++){
            bangumi[i] = (lines[i+1]).split(" ")
            if (bangumi[i][1] > maxT){
             maxT = bangumi[i][1]
            }
        } 
      var Cyoyaku = []
      for (var i=0;i<C;i++){
          Cyoyaku[i]=[]
          for(var t=0;t<=maxT;t++){
              (Cyoyaku[i]).push('0')
          }
      }

      for (var i=0; i<N;i++){
          for (var t=parseInt(bangumi[i][0]);t<parseInt(bangumi[i][1]);t++){
            var ch =parseInt(bangumi[i][2] )
            Cyoyaku[ch-1][t] = '1'
          }
      }

      for (var i=0;i<C;i++){
          for ( var t=0;t<maxT;t++){
              if( Cyoyaku[i][t+1] == '1' ){
                  Cyoyaku[i][t] = '1'
              }
          }
      }

      var maxcnt = 0;
      for (var t=0;t<maxT;t++){
          var tmpcnt=0;
          for (var tmpc=0;tmpc<C;tmpc++){
              if(Cyoyaku[tmpc][t]=="1"){
                  tmpcnt++;
              }
          }
          if(tmpcnt > maxcnt ){
              maxcnt = tmpcnt
          }
      }

    console.log(maxcnt);

//      console.log( Math.pow(parseInt(lines[0]),2) - parseInt(lines[1])  )
    // ToDo end

    });


})();

function dump_int(i){var s="";while(i){s=(i&1)+s;i>>>=1}return ('0000000000'+s).slice(-10)}

function matchNum(a,b){
    var tlen = 10
    var mnum = 0;
    
    for (var i=0;i<tlen;i++){
        if ( a[i]== b[i] && a[i] =="1" ){
            mnum++;
        }
    }
    return mnum;
}