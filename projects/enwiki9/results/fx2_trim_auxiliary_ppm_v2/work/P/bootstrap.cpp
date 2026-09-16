#include <cstring>
#include "src/readalike_prepr/self_extract.h"
int main(int argc,char** argv){if(argc!=2)return 91;if(!strcmp(argv[1],"C"))return selfextract_comp();if(!strcmp(argv[1],"D"))return selfextract_decomp();return 92;}
