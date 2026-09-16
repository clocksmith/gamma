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
