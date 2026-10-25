#include <stdlib.h>
#include <string.h>
#include <stdint.h>
/* Trusted source-as-data DP. Never parses or executes the text as a program. */
int gamma_score(const unsigned char *text,int n,const char **vocab,const int *lengths,int count,int *sequence,int *out_n,int *out_chars){
 if(n<0||count<96||count>256)return -1;
 int *cost=malloc(((size_t)n+1)*sizeof(int));
 int *pick=malloc(((size_t)n+1)*sizeof(int));
 if(!cost||!pick){free(cost);free(pick);return -2;}
 cost[n]=0;
 for(int at=n-1;at>=0;--at){
  int idx=text[at]==10?95:(int)text[at]-32;
  if(text[at]!=10&&(text[at]<32||text[at]>126)){free(cost);free(pick);return -3;}
  int best=cost[at+1]+1;
  for(int j=96;j<count;++j){int len=lengths[j];
   if(len<=0||len>n-at||(unsigned char)vocab[j][0]!=text[at])continue;
   if(memcmp(text+at,vocab[j],(size_t)len))continue;
   int candidate=cost[at+len]+1;
   if(candidate<best||(candidate==best&&j<idx)){best=candidate;idx=j;}
  }
  cost[at]=best;pick[at]=idx;
 }
 int at=0,k=0,chars=0;
 while(at<n){int idx=pick[at];sequence[k++]=idx;chars+=(lengths[idx]==1);at+=lengths[idx];}
 *out_n=k;*out_chars=chars;free(cost);free(pick);return 0;
}
