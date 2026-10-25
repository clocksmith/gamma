#include <stdlib.h>
#include <stdint.h>
#include <string.h>
/* Trusted source-as-data optimizer. No parsing/evaluation of program text.
   Arbitrary exact UTF8 basis; explicit unreachable status, no implicit alphabet.
   Character flags reflect Unicode literal length, never dictionary ID or byte length. */
typedef struct {int first,terminal;} Node;
typedef struct {int target,next;unsigned char ch;} Edge;
typedef struct {Node *nodes;Edge *edges;int roots[256];int lengths[256];int single[256];int count,node_count,edge_count;} Trie;
static int child(Trie *t,int node,unsigned char c){
 for(int e=t->nodes[node].first;e>=0;e=t->edges[e].next)if(t->edges[e].ch==c)return t->edges[e].target;
 return -1;
}
void gamma_trie_free(void *handle){Trie *t=handle;if(t){free(t->nodes);free(t->edges);free(t);}}
void *gamma_trie_build(const char **vocab,const int *lengths,const int *single,int count){
 if(count<1||count>256)return NULL;
 size_t total=1;
 for(int i=0;i<count;i++){
  if(lengths[i]<=0||lengths[i]>10000000)return NULL;
  if(single[i]!=0&&single[i]!=1)return NULL;
  total+=(size_t)lengths[i];if(total>10000000)return NULL;
 }
 Trie *t=calloc(1,sizeof(Trie));if(!t)return NULL;
 t->nodes=malloc(total*sizeof(Node));t->edges=malloc(total*sizeof(Edge));
 if(!t->nodes||!t->edges){gamma_trie_free(t);return NULL;}
 for(int i=0;i<256;i++)t->roots[i]=-1;
 memcpy(t->lengths,lengths,(size_t)count*sizeof(int));memcpy(t->single,single,(size_t)count*sizeof(int));t->count=count;t->node_count=1;t->nodes[0]=(Node){-1,-1};
 for(int id=0;id<count;id++){
  int node=0;
  for(int at=0;at<lengths[id];at++){
   unsigned char c=(unsigned char)vocab[id][at];
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
 int *cost=malloc(((size_t)n+1)*sizeof(int)),*pick=malloc(((size_t)n+1)*sizeof(int)),*charcost=malloc(((size_t)n+1)*sizeof(int));
 if(!cost||!pick||!charcost){free(cost);free(pick);free(charcost);return -2;}cost[n]=0;charcost[n]=0;
 for(int at=n-1;at>=0;at--){
  unsigned char c=text[at];
  int idx=-1,best=-1,bestchars=-1,node=t->roots[c],pos=at+1;
  while(node>=0){
   int id=t->nodes[node].terminal;
   if(id>=0&&cost[pos]>=0){int candidate=cost[pos]+1,characters=charcost[pos]+t->single[id];if(best<0||candidate<best||(candidate==best&&(characters<bestchars||(characters==bestchars&&id<idx)))){best=candidate;bestchars=characters;idx=id;}}
   if(pos==n)break;
   node=child(t,node,text[pos]);pos++;
  }
  cost[at]=best;charcost[at]=bestchars;pick[at]=idx;
 }
 if(cost[0]<0){*out_n=0;*out_chars=0;free(cost);free(pick);free(charcost);return 1;}
 int at=0,k=0,chars=0;
 while(at<n){int id=pick[at];sequence[k++]=id;chars+=t->single[id];at+=t->lengths[id];}
 *out_n=k;*out_chars=chars;free(cost);free(pick);free(charcost);return 0;
}
