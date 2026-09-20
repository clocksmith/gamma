#include "predictors/causal_relational_v1.hpp"
#include <iostream>
#include <iomanip>
int main(){std::string raw="<title>alpha</title><text xml:space=\"preserve\">beta</text>";gamma_relational::Model m({},raw.size(),'S');gamma_xml_field::Bytes output;auto feed=[&](unsigned char c){for(int bit=7;bit>=0;--bit){m.predict(32768);m.observe((c>>bit)&1,output);}};feed(7);for(unsigned char c:raw)feed(gamma_xml_field::unswap(c));for(auto c:m.state())std::cout<<std::hex<<std::setfill('0')<<std::setw(2)<<unsigned(c);std::cout<<'\n';}
