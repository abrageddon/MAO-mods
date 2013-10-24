#include <iostream>
#include <fstream>
#include <string>
#include <regex>
#include <string.h>

#include "MultiCompiler/MultiCompilerOptions.h"
#include "MultiCompiler/AESRandomNumberGenerator.h"

using namespace std;

static const char * const nop64[] = { "nop", "movq\t%rbp, %rbp", "movq\t%rsp, %rsp", "leaq\t(%rdi), %rdi",
        "leaq\t(%rsi), %rsi" };

static const char * const nop32[] = { "nop", "movl\t%ebp, %ebp", "movl\t%esp, %esp", "leal\t(%edi), %edi",
        "leal\t(%esi), %esi" };

static const int nopSize[] = { 1, 2, 2, 2, 2 }; //Size (32/64) matters?TODO probably

static const string normLabel="__divmap_";
static const string divLabel="__divNOP_";

static int nopNumber = 0;

static int insertPercent = 30;
static int Roll;
static bool canNOP;
static bool canMOVToLEA;
static bool is64bit;
static bool is32bit;
static bool doStubAdjustment;

static string line;
static string label;

string movToLeaReplace() {
    size_t movLoc = 0;
    string lea = "";
    if (is64bit) {
        movLoc = line.find("movq");
        if (movLoc == string::npos) {
            return line + "\n";
        }
        lea = "leaq";
    } else if (is32bit) { //not needed? just do it?
        movLoc = line.find("movl");
        if (movLoc == string::npos) {
            return line + "\n";
        }
        lea = "leal";
    } else {
        cerr << "Unknown Arch" << endl;
        return line + "\n";
    }

    size_t pOne = line.find("%");
    size_t comma = line.find(",", pOne);
    size_t pTwo = line.find("%", comma);

    string rOne = line.substr(pOne, comma - pOne);
    string rTwo = line.substr(pTwo);

    return "\t" + lea + "\t(" + rOne + ")," + rTwo + "\t\t#MOVtoLEA";
}

void printWithLabel(ofstream& output, const string& lab, const string& input){
    if( strcmp(lab.c_str(), "") != 0 ){
        output << lab << "\n";
    }
    output << input << "\n";
}

int main(int argc, char* argv[]) {

    string inFileName;
    string outFileName = "";
    string seed = "";
    string percent = "";

    if (argc < 2) {
        cout << argv[0]
                << "\nUsage is -f <infile> -o <outfile> -seed <seed> -percent <percent>\n\t--cbstubs\tEnable cbstubs 0xCC space adjustment\n";
//        cin.get();
        exit(0);
    } else {
        for (int i = 1; i < argc; i++) {
            if (i != argc) {
                if (strcmp(argv[i], "--cbstubs") == 0) {
                    doStubAdjustment = true;
                } else if (i + 1 != argc) {
                    if (strcmp(argv[i], "-f") == 0) {
                        inFileName = argv[i + 1];
                        i++;
                    } else if (strcmp(argv[i], "-o") == 0) {
                        outFileName = argv[i + 1];
                        i++;
                    } else if (strcmp(argv[i], "-seed") == 0) {
                        seed = argv[i + 1];
                        i++;
                    } else if (strcmp(argv[i], "-percent") == 0) {
                        percent = argv[i + 1];
                        i++;
                    } else {
                        cout << "Not enough or invalid arguments, please try again.\n";
                        cout << "Error on : " << argv[i];
                        exit(0);
                    }
                }
            }
        }
    }

    if (inFileName.empty()) {
        cout << "No input file.\n";
        exit(0);
    }
    ifstream inFile(inFileName);
    ofstream outFile;

    if (outFileName.empty()) {
        size_t ext = inFileName.find_last_of(".a.s"); //TODO find LAST occurrence
        if (ext == string::npos) {
            cerr << "Incorrect extension. Needs to be '.a.s'." << endl;
            return 1;
        }
        outFile.open(inFileName.substr(0, ext) + ".div.s");
    } else {
        outFile.open(outFileName);
    }

    is64bit = true;
    is32bit = false;

    srand(time(NULL));

    if (seed.empty()) {
        multicompiler::MultiCompilerSeed = to_string(rand());
        multicompiler::Random::EntropyData = to_string(rand());
    } else {
        multicompiler::MultiCompilerSeed = seed;
        multicompiler::Random::EntropyData = seed;
    }

    if (percent.empty()) {
        insertPercent = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
    } else {
        insertPercent = stoi(percent);
    }
//    cout << insertPercent << endl;

    int subFromSpace = 0;

    if (!inFile.is_open() || !outFile.is_open()) {
        cerr << "Unable to open file" << endl;
        return 2;
    }

    while (inFile.good()) {
        label = "";
        getline(inFile, line);
        //For each line in  file
        size_t pos32 = line.find(".code32");
        if (pos32 != string::npos) {
            is64bit = false;
            is32bit = true;
        }
        size_t pos64 = line.find(".code64");
        if (pos64 != string::npos) {
            is64bit = true;
            is32bit = false;
        }
        //if line == divmap:read again store and 
        size_t posLabel = line.find(normLabel);
        if (posLabel != string::npos){
            label=line;
            getline(inFile, line);
        }

        //IF not contains '# MC=' then write and continue
        size_t argPos = line.find("# MC=");
        if (argPos == string::npos) {

            size_t posSpace = line.find(".space");
            if (posSpace != string::npos && doStubAdjustment) { // subtract from space; warn if not there
                size_t comma = line.find(",");

                string spaceLength = line.substr(posSpace + 6, comma - (posSpace + 6));

                int adjustedSpaceLength = stoi(spaceLength);
                adjustedSpaceLength -= subFromSpace;

                outFile << "\t.space\t" << adjustedSpaceLength << ", 0xCC\n";

                subFromSpace = 0;
            } else {
                outFile << line << "\n";
                //printWithLabel(outFile, label, line);
            }
            continue;
        }

        //TODO schedule randomization

        size_t posJmp = line.find("jmp");
        if (posJmp != string::npos && doStubAdjustment) { //TODO TESTING dont diversify jump pads
            //outFile << line << "\n";
            printWithLabel(outFile, label, line);
            continue;
        }

        canNOP = false;
        canMOVToLEA = false;
        string lineArgs = line.substr(argPos + 5);

        //Parse args
        for (unsigned int i = 0; i < lineArgs.length(); i++) {
            if (isspace(lineArgs[i])) {
                break;
            } else if (lineArgs[i] == 'N') {
                canNOP = true;
                continue;
            } else if (lineArgs[i] == 'M') {
                canMOVToLEA = true;
                continue;
            } else {
                cerr << "Unknown Arg: " << lineArgs[i] << endl;
            }

        }

        //IF mcArgs contains [N] then try NOP Insertion before current line
        if (canNOP) {
            Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
            if (Roll < insertPercent) {
                Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(5);
                if (is64bit) {
                    outFile << divLabel << nopNumber++ << ":\t" << nop64[Roll] << "\t\t#NOP\n";
                    //printWithLabel(outFile, label, to_string(divLabel) + to_string(nopNumber) + "\t" + nop64[Roll] + "\t\t#NOP\n");
                    subFromSpace += nopSize[Roll];
                } else if (is32bit) {
                    outFile << divLabel << nopNumber++ << ":\t" << nop32[Roll] << "\t\t#NOP\n";
                    //printWithLabel(outFile, label, to_string(divLabel) + to_string(nopNumber) + "\t" + nop32[Roll] + "\t\t#NOP\n");
                    subFromSpace += nopSize[Roll];
                } else {
                    cerr << "Unknown Arch" << endl;
                }
            }
        }

        //IF mcArgs contains [M] then try MOVToLEA
        if (canMOVToLEA) {
            Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
            if (Roll < insertPercent) {
                //outFile << movToLeaReplace();
                printWithLabel(outFile, label, movToLeaReplace());
            } else {
                //print
                //outFile << line << "\n";
                printWithLabel(outFile, label, line);
            }
        } else {
            //print
            //outFile << line << "\n";
            printWithLabel(outFile, label, line);
        }
//            cout << line << endl;
    }
    inFile.close();
    outFile.close();

    return 0;
}
