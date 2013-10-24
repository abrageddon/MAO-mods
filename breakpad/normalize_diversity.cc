#include "processor/normalize_diversity.h"

namespace multicompiler{

uint64_t NormalizeAddress(string filename, uint64_t rip){
  uint64_t newAdd=rip;
  //const googlebreakpad::CodeModule *curMod = modules_->GetModuleForAddress(rip);
  //string fileStr( curMod->code_file().c_str() );
  //printf("DEBUG FILE: %s\n", filename.c_str());

  string NOPMapFile(filename.c_str());
  NOPMapFile += ".divmap";
  std::ifstream NOPMap(NOPMapFile.c_str());

  if(NOPMap.is_open()){
    string addressLine;
    while(std::getline(NOPMap, addressLine)){
      //printf("DEBUG NOPADD: %s\n", addressLine.c_str());

      uint64_t fromAdd=0;
      size_t c1 = addressLine.find(":");
      string fa = addressLine.substr(0,c1);
      sscanf(fa.c_str(), "%x", &fromAdd);

      uint64_t fromSize=0;
      size_t c2 = addressLine.find(":", c1+1);
      string fs = addressLine.substr(c1+1,c2-c1-1);
      sscanf(fs.c_str(), "%x", &fromSize);

      uint64_t toAdd=0;
      size_t c3 = addressLine.find(":", c2+2);
      string ta = addressLine.substr(c2+2,c3-c2-2);
      sscanf(ta.c_str(), "%x", &toAdd);

      uint64_t toSize=0;
      size_t c4 = addressLine.find("#", c3+1);
      string ts = addressLine.substr(c3+1,c4-c3-1);
      sscanf(ts.c_str(), "%x", &toSize);
      //TODO

      //printf("DEBUG NOPVAR: %x : %x :: %x : %x\n", fromAdd, fromSize, toAdd, toSize);

      if(rip >= fromAdd && rip < fromAdd + fromSize ){
        //printf("DEBUG NOPMAP: %s\n", mapLine.c_str());
        newAdd=toAdd;
        unsigned int delta=static_cast<unsigned int>(rip - fromAdd);
        //delta=0; //TEMP! REMOVE ONCE IMPLEMENTED
        if(delta >= toSize){
            newAdd+=toSize;
        }else{
            newAdd+=delta;
        }
        printf("DEBUG ADJUST: R=%x : D=%x : N=%x\n", rip, delta, newAdd);
        return newAdd;
      }
    }
  }
  //printf("DEBUG NEW ADDR: %x\n", newAdd);
  return rip;
}

}//namespace multicompiler
