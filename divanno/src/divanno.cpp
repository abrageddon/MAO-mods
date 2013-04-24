#include <iostream>
#include <fstream>
#include <string>

#include "MultiCompiler/AESRandomNumberGenerator.h"

using namespace std;

static const char * const nop64[] = { "\tnop", "\tmovq\t%rbp, %rbp", "\tmovq\t%rsp, %rsp", "\tleaq\t(%rdi), %rdi",
        "\tleaq\t(%rsi), %rsi" };

static const char * const nop32[] = { "\tnop", "\tmovl\t%ebp, %ebp", "\tmovl\t%esp, %esp", "\tleal\t(%edi), %edi",
        "\tleal\t(%esi), %esi" };

static const int insertPercent = 30;
static int Roll;

int main() {
    //TODO read filename from commandline
    string line;
    //TODO check correct file
    ifstream inFile("hellofunc.a.s");
    ofstream outFile("hellofunc.div.s");

    multicompiler::Random::EntropyData = "hellofunc.a.s";

    if (inFile.is_open() && outFile.is_open()) {
        while (inFile.good()) {
            getline(inFile, line);
            //For each line in  file

            //IF not contains '# MC=' then write and continue
            size_t argPos = line.find("# MC=");
            if (argPos==std::string::npos) {
                outFile << line << endl;
                continue;
            }


            //IF mcArgs contains [Nn] then try NOP Insertion before current line
            if (true) {//64bit
                Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
                if (Roll <= insertPercent){
                    Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(5);
                    outFile << nop64[Roll] << endl;
                }
            }else if (Roll <= insertPercent){//32bit
                Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
                if (Roll <= insertPercent){
                    Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(5);
                    outFile << nop32[Roll] << endl;
                }
            }


            //IF mcArgs contains [Mm] then try MOVToLEA
            if (false) {
                Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
                if (Roll <= insertPercent){
//##TODO: change SUF to arch compatable version
//outf.write(re.sub(reMov2Lea,
//                   'lea\g<SUF>\t(\g<ONE>), \g<TWO>'
//                   ,line))
                }else{
                    //print
                    outFile << line << endl;
                    continue;
                }
            }else{
                //print
                cout << line << endl;
                outFile << line << endl;
                continue;
            }
//            cout << line << endl;
        }
        inFile.close();
    } else {
        cout << "Unable to open file";
    }

    return 0;
}
