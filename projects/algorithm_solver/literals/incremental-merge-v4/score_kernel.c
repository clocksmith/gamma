#include <stdlib.h>
#include <stdint.h>
#include <string.h>
/* Trusted source-as-data optimizer. No parsing/evaluation of program text.
   Sparse trie built once per vocabulary; exact DP and original index tie-break. */
typedef struct {int first,terminal;} Node;
typedef struct {int target,next;unsigned char ch;} Edge;
typedef struct {Node *nodes;Edge *edges;int roots[128];int lengths[256];int count,node_count,edge_count;} Trie;
static int ascii(unsigned char c){return c==10||(c>=32&&c<=126);}
static int child(Trie *t,int node,unsigned char c){
 for(int e=t->nodes[node].first;e>=0;e=t->edges[e].next)if(t->edges[e].ch==c)return t->edges[e].target;
 return -1;
}
void gamma_trie_free(void *handle){Trie *t=handle;if(t){free(t->nodes);free(t->edges);free(t);}}
void *gamma_trie_build(const char **vocab,const int *lengths,int count){
 if(count<96||count>256)return NULL;
 size_t total=1;
 for(int i=0;i<count;i++){
  if(lengths[i]<=0||lengths[i]>10000000)return NULL;
  if(i<96){if(lengths[i]!=1||(unsigned char)vocab[i][0]!=(i==95?10:i+32))return NULL;}
  else {if(lengths[i]<2)return NULL;total+=(size_t)lengths[i];if(total>10000000)return NULL;}
 }
 Trie *t=calloc(1,sizeof(Trie));if(!t)return NULL;
 t->nodes=malloc(total*sizeof(Node));t->edges=malloc(total*sizeof(Edge));
 if(!t->nodes||!t->edges){gamma_trie_free(t);return NULL;}
 for(int i=0;i<128;i++)t->roots[i]=-1;
 memcpy(t->lengths,lengths,(size_t)count*sizeof(int));t->count=count;t->node_count=1;t->nodes[0]=(Node){-1,-1};
 for(int id=96;id<count;id++){
  int node=0;
  for(int at=0;at<lengths[id];at++){
   unsigned char c=(unsigned char)vocab[id][at];
   if(!ascii(c)){gamma_trie_free(t);return NULL;}
   int next=child(t,node,c);
   if(next<0){
    next=t->node_count++;t->nodes[next]=(Node){-1,-1};
    int e=t->edge_count++;t->edges[e]=(Edge){next,t->nodes[node].first,c};t->nodes[node].first=e;
   }
   node=next;
  }
  if(t->nodes[node].terminal>=0){gamma_trie_free(t);return NULL;}
  t->nodes[node].terminal=id;
 }
 for(int e=t->nodes[0].first;e>=0;e=t->edges[e].next)t->roots[t->edges[e].ch]=t->edges[e].target;
 return t;
}
int gamma_trie_score(void *handle,const unsigned char *text,int n,int *sequence,int *out_n,int *out_chars){
 Trie *t=handle;if(!t||n<0||n>10000000)return -1;
 int *cost=malloc(((size_t)n+1)*sizeof(int)),*pick=malloc(((size_t)n+1)*sizeof(int));
 if(!cost||!pick){free(cost);free(pick);return -2;}cost[n]=0;
 for(int at=n-1;at>=0;at--){
  unsigned char c=text[at];if(!ascii(c)){free(cost);free(pick);return -3;}
  int idx=c==10?95:c-32,best=cost[at+1]+1,node=t->roots[c],pos=at+1;
  while(node>=0){
   int id=t->nodes[node].terminal;
   if(id>=0){int candidate=cost[pos]+1;if(candidate<best||(candidate==best&&id<idx)){best=candidate;idx=id;}}
   if(pos==n)break;
   node=child(t,node,text[pos]);pos++;
  }
  cost[at]=best;pick[at]=idx;
 }
 int at=0,k=0,chars=0;
 while(at<n){int id=pick[at];sequence[k++]=id;chars+=(t->lengths[id]==1);at+=t->lengths[id];}
 *out_n=k;*out_chars=chars;free(cost);free(pick);return 0;
}
