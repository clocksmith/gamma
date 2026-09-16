#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
// Dictionary reverse decoding
int wfgets(char *str, int count, FILE  *fp) {
    int c, i = 0;
    while (i<count-1 && ((c=getc(fp))!=EOF)) {
        str[i++]=c; if (c=='\n')str[i-1]=0;
        if (c=='\n')
            break;
    }
    str[i]=0;
    return i;
}
char *s;
char *dictW[44516];
int codeword2sym[256]; 
int dict1size=80;
int dict2size=32;
int dict12size=dict1size*dict2size;
int sizeDict;

inline int decodeCodeWord(int cw) {
    int i=0;
    int c=cw&255;
    if (codeword2sym[c]<dict1size) {
        i=codeword2sym[c];
        return i;
    }

    i=dict1size*(codeword2sym[c]-dict1size);
    c=(cw>>8)&255;

    if (codeword2sym[c]<dict1size) {
        i+=codeword2sym[c];
        return i+dict1size;
    }

    i=(i-dict12size)*dict2size;
    i+=dict1size*(codeword2sym[c]-dict1size);

    c=(cw>>16)&255;
    i+=codeword2sym[c];
    return i+80*49;
}

bool isDictLoaded=false;
static constexpr int gammaLexicalMode = 2;
static unsigned long long gammaLexicalValid=0, gammaLexicalInvalid=0;
static bool gammaLexicalInitialized=false;
static char gammaLexicalEmpty=0;

void GammaExplicitLexicon(FILE *file) {
    if (!file || gammaLexicalInitialized) {
        fprintf(stderr,"explicit lexical dictionary unavailable or repeated\n");
        exit(2);
    }
    long saved=ftell(file);
    if (saved<0 || fseek(file,0,SEEK_SET)) exit(2);
    char word[64]; int n=0, count=0, c;
    while ((c=getc(file))!=EOF) {
        if (c=='\n') {
            if (!n || count>=44516) exit(2);
            word[n]=0;
            dictW[count]=(char*)malloc(n+1);
            if (!dictW[count]) exit(2);
            memcpy(dictW[count++],word,n+1); n=0;
        } else {
            if (c<'a' || c>'z' || n>=63) exit(2);
            word[n++]=(char)c;
        }
    }
    if (ferror(file) || n || count!=44515 || fseek(file,saved,SEEK_SET)) exit(2);
    sizeDict=count;
    if (gammaLexicalMode==2) {
        char *first=dictW[0];
        for (int i=0;i<count-1;++i) dictW[i]=dictW[i+1];
        dictW[count-1]=first;
    }
    // K loads and validates the same table but leaves all predictive globals
    // in their original disabled state, including partial-codeword mapping.
    if (gammaLexicalMode) {
        for (int i=128;i<256;++i) codeword2sym[i]=i-128;
        isDictLoaded=true;
    }
    gammaLexicalInitialized=true;
}

void GammaLexicalAudit() {
    fprintf(stderr,"\nGAMMA_LEXICAL mode=%d words=%d valid=%llu invalid=%llu\n",
            gammaLexicalMode,sizeDict,gammaLexicalValid,gammaLexicalInvalid);
}

char *so;     // Our decoded word
int lastCW=0; // Our decoded word index (max 44515)
void decodeWord(int c){
    if (isDictLoaded==false) return;
    int j=decodeCodeWord(c);
    if (j<0 || j>=sizeDict) {
        ++gammaLexicalInvalid; lastCW=0; so=&gammaLexicalEmpty; return;
    }
    ++gammaLexicalValid;
    lastCW=j;
    so=dictW[j];
}


// Appended to the extracted, unchanged materialized dictionary block.
// This checks the production index formula against independent encoder cases.
int main(int argc,char**argv) {
    if(argc!=2) return 10;
    FILE*f=fopen(argv[1],"rb");if(!f)return 11;
    fseek(f,17,SEEK_SET);GammaExplicitLexicon(f);
    if(ftell(f)!=17 || sizeDict!=44515) return 12;
    if(isDictLoaded!=(gammaLexicalMode!=0))return 13;
    std::vector<std::string> words;char b[128];rewind(f);
    while(fgets(b,sizeof(b),f)){b[strcspn(b,"\n")]=0;words.emplace_back(b);}
    if(words.size()!=44515)return 14;
    for(int i=0;i<sizeDict;++i){
        int want=gammaLexicalMode==2?(i+1)%sizeDict:i;
        if(words[want]!=dictW[i])return 15;
    }
    char empty=0;so=&empty;
    if(gammaLexicalMode==0){
        decodeWord(128);if(so!=&empty || gammaLexicalValid)return 16;
        for(int i=0;i<256;++i)if(codeword2sym[i])return 17;
    }
    // Independent dictionary encoder from the format's three index ranges.
    for(int i=0;i<44880;++i){
        unsigned code;
        if(i<80)code=128+i;
        else if(i<3920)code=(208+(i-80)/80) | ((128+(i-80)%80)<<8);
        else {int n=i-3920;code=(240+n/2560) | ((208+(n/80)%32)<<8) | ((128+n%80)<<16);}
        if(gammaLexicalMode){
            if(decodeCodeWord(code)!=i)return 18;
            decodeWord(code);
            if(i<sizeDict){if(lastCW!=i || so!=dictW[i])return 19;}
            else if(lastCW || *so)return 20;
        }
    }
    if(gammaLexicalMode && (gammaLexicalValid!=44515 || gammaLexicalInvalid!=365))return 21;
    GammaLexicalAudit();fclose(f);
    return 0;
}
