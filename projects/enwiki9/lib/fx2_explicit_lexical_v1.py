"""Activate existing FXCM lexical contexts from the paid explicit dictionary.

No ambient files, new dictionary, neural update, or frontend change. Each arm
embeds its fixed mode in source; this avoids build-flag delivery ambiguity.
"""
import hashlib

MODEL = 'src/models/fxcmv1.cpp'
RUNNER = 'src/runner.cpp'
PREIMAGES = {
    MODEL: 'b3de8853b1577ed9b6276abdb61e9b446fdf0b4bf42a3106c4aa98d3fea70b6c',
    RUNNER: 'e8b9bc757902006bf0d2b30e1461276b172c883cece6d3c9eb3df03c804924bf',
}


def replace_once(data, before, after):
    if data.count(before) != 1:
        raise ValueError('source anchor missing or ambiguous')
    return data.replace(before, after, 1)


def materialize(source, mode):
    if mode not in (0, 1, 2):
        raise ValueError('mode must be K=0, D=1, S=2')
    for name, digest in PREIMAGES.items():
        if hashlib.sha256(source[name]).hexdigest() != digest:
            raise ValueError('source preimage differs: ' + name)
    result = dict(source)
    data = source[MODEL]
    a = data.index(b'void loaddict(FILE  *file){')
    b = data.index(b'inline int decodeCodeWord(int cw)')
    # Replace the unchecked ambient loader; reuse the original index arithmetic.
    data = data[:a] + data[b:]
    a = data.index(b'bool isDictLoaded=false;')
    b = data.index(b'char *so;     // Our decoded word')
    data = data[:a] + (r'''bool isDictLoaded=false;
static constexpr int gammaLexicalMode = MODE;
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

'''.replace('MODE', str(mode))).encode() + data[b:]
    data = replace_once(data, b'''    lastCW=j;
        /*if (j>=sizeDict) {
            printf("Bad dictionary 1 codepoint\\n");
        }*/
    so=&(*dictW[j]);''', b'''    if (j<0 || j>=sizeDict) {
        ++gammaLexicalInvalid; lastCW=0; so=&gammaLexicalEmpty; return;
    }
    ++gammaLexicalValid;
    lastCW=j;
    so=dictW[j];''')
    data = replace_once(data, b'    // Load dictionary\n    dosym();',
        b'    // The caller supplies the counted dictionary after ordinary pretraining.')
    result[MODEL] = data
    data = replace_once(source[RUNNER], b'namespace {\n  const int kMinVocabFileSize',
        b'namespace fxcmv1 { void GammaExplicitLexicon(FILE*); void GammaLexicalAudit(); }\n\nnamespace {\n  const int kMinVocabFileSize')
    for call in (b'  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);',
                 b'  Decompress(*output_bytes, &data_in, &temp_out, &p);'):
        data = replace_once(data, call,
            b'  fxcmv1::GammaExplicitLexicon(dictionary);\n' + call +
            b'\n  fxcmv1::GammaLexicalAudit();')
    result[RUNNER] = data
    return result
