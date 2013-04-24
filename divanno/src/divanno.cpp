#include <iostream>
#include <fstream>
#include <string>
#include <regex>

#include "MultiCompiler/MultiCompilerOptions.h"
#include "MultiCompiler/AESRandomNumberGenerator.h"

using namespace std;

static const char * const nop64[] = { "\tnop\n", "\tmovq\t%rbp, %rbp\n"
        , "\tmovq\t%rsp, %rsp\n", "\tleaq\t(%rdi), %rdi\n",
        "\tleaq\t(%rsi), %rsi\n" };

static const char * const nop32[] = { "\tnop\n", "\tmovl\t%ebp, %ebp\n"
        , "\tmovl\t%esp, %esp\n", "\tleal\t(%edi), %edi\n",
        "\tleal\t(%esi), %esi\n" };

static int insertPercent = 30;
static int Roll;
static bool canNOP;
static bool canMOVToLEA;
static bool is64bit;
static bool is32bit;

static string line;

string movToLeaReplace(){
    size_t movLoc = 0;
    string lea = "";
    if (is64bit){
        movLoc = line.find("movq");
        if (movLoc==string::npos) {
            return line + "\n";
        }
        lea = "leaq";
    }else if (is32bit){//not needed? just do it?
        movLoc = line.find("movl");
        if (movLoc==string::npos) {
            return line + "\n";
        }
        lea = "leal";
    }else{
        cerr << "Unknown Arch" << endl;
        return line + "\n";
    }

    size_t pOne = line.find("%");
    size_t comma = line.find(",",pOne);
    size_t pTwo = line.find("%",comma);

    string rOne = line.substr(pOne, comma-pOne);
    string rTwo = line.substr(pTwo);

    return "\t" + lea + "\t(" + rOne + ")," + rTwo + "\n";
}

int main(int argc, char* argv[]) {
    string inFileName(argv[1]);

    size_t ext = inFileName.find(".a.s");
    if (ext==string::npos) {
        cerr << "Incorrect extension." <<endl;
        return 1;
    }

    ifstream inFile(inFileName);
    ofstream outFile(inFileName.substr(0,ext) + ".div.s");

    //TODO read arch from file
    is64bit = true;
    is32bit = false;


    //TODO read seed and percentages from cmdline
    srand (time(NULL));
    multicompiler::MultiCompilerSeed = to_string(rand());
    multicompiler::Random::EntropyData = to_string(rand());
    insertPercent = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
//    cout << insertPercent << endl;

    if (inFile.is_open() && outFile.is_open()) {
        while (inFile.good()) {
            getline(inFile, line);
            //For each line in  file

            //IF not contains '# MC=' then write and continue
            size_t argPos = line.find("# MC=");
            if (argPos==string::npos) {
                outFile << line << "\n";
                continue;
            }

            canNOP = false;
            canMOVToLEA = false;
            string lineArgs = line.substr(argPos+5);

            //Parse args
            for (unsigned int i = 0; i < lineArgs.length(); i++){
                if (isspace(lineArgs[i])){
                    break;
                }else if (lineArgs[i]=='N'){
                    canNOP = true;
                    continue;
                }else if (lineArgs[i]=='M'){
                    canMOVToLEA = true;
                    continue;
                }else {
                    cerr << "Unknown Arg: " << lineArgs[i] << endl;
                }

            }


            //IF mcArgs contains [N] then try NOP Insertion before current line
            if (canNOP) {
                Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
                if (Roll <= insertPercent){
                    Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(5);
                    if(is64bit){
                        outFile << nop64[Roll] ;
                    }else if (is32bit){
                        outFile << nop32[Roll] ;
                    }else{
                        cerr << "Unknown Arch" << endl;
                    }
                }
            }


            //IF mcArgs contains [M] then try MOVToLEA
            if (canMOVToLEA) {
                Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
                if (Roll <= insertPercent){
                    outFile << movToLeaReplace() ;
                }else{
                    //print
                    outFile << line << "\n";
                }
            }else{
                //print
//                cout << line << endl;
                outFile << line << "\n";
            }
//            cout << line << endl;
        }
        inFile.close();
        outFile.close();
    } else {
        cerr << "Unable to open file"<<endl;
        return 2;
    }

    return 0;
}
