#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <regex>
#include <string.h>
#include <list>
#include <sstream>

#include "SchedulableInstruction.h"
#include "MultiCompiler/MultiCompilerOptions.h"
#include "MultiCompiler/AESRandomNumberGenerator.h"

using namespace std;

static const char * const nop64[] = { "nop", "movq\t%rbp, %rbp", "movq\t%rsp, %rsp", "leaq\t(%rdi), %rdi",
        "leaq\t(%rsi), %rsi" };

static const char * const nop32[] = { "nop", "movl\t%ebp, %ebp", "movl\t%esp, %esp", "leal\t(%edi), %edi",
        "leal\t(%esi), %esi" };

static const int nopSize[] = { 1, 2, 2, 2, 2 }; //Size (32/64) matters?TODO probably

static const string normLabel = "__divmap_";
static const string divLabel = "__divNOP_";

std::list<SchedulableInstruction> schedBuffer;
//static int currentGroup=0;

static int nopNumber = 0;

static int insertPercent = 30;
static int Roll;
static bool canNOP;
static bool doNOP=false;
static bool canMOVToLEA;
static bool doMOVToLEA=false;
static bool doSchedRand=false;
static bool is64bit;
static bool is32bit;
static bool doStubAdjustment;

static int subFromSpace; //CBSTUBS

void readLineAndLabel(ifstream& inFile, string& label, string& line) {
    label = "";
    getline(inFile, line);

    //if line == divmap: store and get instruction
    size_t posLabel = line.find(normLabel);
    if (posLabel != string::npos) {
        label = line;
        getline(inFile, line);
    }

    //TODO if other kind of label; then empty schedBuffer
}

void parseMC(const string& line) {
    canNOP = false;
    canMOVToLEA = false;
    size_t argPos = line.find("# MC=");
    if (argPos == string::npos){
      return;
    }
    string lineArgs = line.substr(argPos + 5);
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
            break;
        }
    }
}

std::vector<int> *parseSchedGrps(const string& line){
    std::vector<int> *grps = new std::vector<int>();
    string schArgs;

    //cerr << "READ: " << line << "\n";

    size_t schPos = line.find("# SCHED=");
    size_t startPos = line.find("[", schPos + 8);

    //Find CSV start
    if (startPos != string::npos){
        schArgs = line.substr(schPos + 9);
    }else{
        schArgs = line.substr(schPos + 8);
    }
    //Find CSV end
    size_t endPos = schArgs.find("]");
    if (endPos != string::npos){
        schArgs = schArgs.substr(0,endPos);
    }

//    cerr << schArgs << "\n";
    std::istringstream ss(schArgs);
    std::string group;

    while(std::getline(ss, group, ',')) {
//        cerr << group << "\n";
        grps->push_back(stoi(group));
    }

    return grps;
}

/*void printGroup(std::vector<int> *grps){
    for (std::vector<int>::iterator it = grps->begin() ; it != grps->end(); ++it){
        cerr << *it << ",";
    }
    cerr << "\n";
}*/

void printSchedBuffer(){
    for (std::list<SchedulableInstruction>::iterator it = schedBuffer.begin()
            ; it != schedBuffer.end(); ++it){
        cerr << "***" << it->instruction.front() << "\n";
    }
}


void addToScheduler(const string& label, const string& line){
    //TODO "# SCHED="
    SchedulableInstruction ins;
    std::vector<int> *grps = parseSchedGrps(line);

    ins.label.push_back(label);
    ins.instruction.push_back(line);
    ins.groups = *grps;


    size_t schPos = line.find("# SCHED=");
    size_t endPos = line.find("]", schPos + 8);
    //TODO while not ] then keep reading lines
    if (endPos == string::npos){
        //Read next line and add until ] or non-schedulable
    }

    schedBuffer.push_back(ins);

}

void insertNopRand(ofstream& outFile) {
    //IF mcArgs contains [N] then try NOP Insertion before current line
    if (doNOP && canNOP) {
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
}

string movToLeaReplace(const string& line) {
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


void printWithLabel(ofstream& output, const string& label, const string& input) {
    if (label.size() > 1) {
        output << label << "\n";
    }
    output << input << "\n";
//    cerr << input << "\n";
}

void movToLeaRandOrPrint(ofstream& outFile, const string& label, const string& line) {
    //IF mcArgs contains [M] then try MOVToLEA
    if (doMOVToLEA && canMOVToLEA) {
        Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
        if (Roll < insertPercent) {
            //outFile << movToLeaReplace();
            printWithLabel(outFile, label, movToLeaReplace(line));
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
}

void emitInstruction(ofstream& outFile, const string& label, const string& line) {
    parseMC(line);
    //IF mcArgs contains [N] then try NOP Insertion before current line
    insertNopRand(outFile);
    //IF mcArgs contains [M] then try MOVToLEA
    movToLeaRandOrPrint(outFile, label, line);
}

void scheduleAllInstructions(ofstream& outFile){
    string line;
    string label;

    while (!schedBuffer.empty()){
        SchedulableInstruction ins = schedBuffer.front();
        schedBuffer.pop_front();

        //cerr << "Candidate" << ins.instruction.at(0) << "\n";
        //printSchedBuffer();//DEBUG

        if ( schedBuffer.size() > 1 ) {
            //For schedBuffer that unions of groups is not null
            std::list<SchedulableInstruction>::iterator next = schedBuffer.begin();
            std::vector<int> interSet;
            std::set_intersection(
                    ins.groups.begin(), ins.groups.end(), next->groups.begin(), next->groups.end(), std::back_inserter(interSet));

            //cerr << "INTER: " << interSet.size() << "\n" ;
            bool changed = false;
            if (interSet.size() > 0 ){
                //cerr << "CAN INSERT AFTER\n";
                while ( next != schedBuffer.end() && multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(2) ) {
                    //cerr << "ROLLED!\n";
                    interSet.clear();
                    changed = true;
                    next++;
                    std::set_intersection(
                            ins.groups.begin(), ins.groups.end(), next->groups.begin(), next->groups.end(), std::back_inserter(interSet));

                    //cerr << "INTER: " << interSet.size() << "\n" ;
                    if(interSet.size() <= 0){
                        break;
                    }
                    //cerr << "CAN INSERT AFTER\n";
                }
                if (changed){
                    schedBuffer.emplace( next, ins);//TODO place after end? even worth the effort?
                    continue;
                }
            }
        }

        for(unsigned int i = 0; i < ins.instruction.size(); i++){
            label=ins.label.at(i);
            line=ins.instruction.at(i);

            emitInstruction(outFile, label, line);
        }
    }
}

int main(int argc, char* argv[]) {

    string inFileName;
    string outFileName = "";
    string seed = "";
    string percent = "";

    if (argc < 2) {
        cout << argv[0]
                << "\nUsage is -f <infile> -o <outfile> -seed <seed> -percent <percent>\n"
                << "\t-cbstubs\tEnable cbstubs 0xCC space adjustment\n"
                << "\t-nop-insertion\tEnable NOP insertion\n"
                << "\t-mov-to-lea\tEnable MOV to LEA transformation\n"
                << "\t-sched-randomize\tRandomize schedules\n";
//        cin.get();
        exit(0);
    } else {
        for (int i = 1; i < argc; i++) {
            if (i != argc) {
                if (strcmp(argv[i], "-cbstubs") == 0) {
                    doStubAdjustment = true;
                } else if (strcmp(argv[i], "-sched-randomize") == 0) {
                    doSchedRand = true;
                } else if (strcmp(argv[i], "-nop-insertion") == 0) {
                    doNOP = true;
                } else if (strcmp(argv[i], "-mov-to-lea") == 0) {
                    doMOVToLEA = true;
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

    string line;
    string label;
    while (inFile.good()) {
        readLineAndLabel(inFile, label, line);

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
        //TODO IF line is label: end of basic block; dump remaining

        if (doSchedRand){
          size_t schPos = line.find("# SCHED=");
          if (schPos != string::npos) {
            addToScheduler(label, line);
            continue;
          }
          scheduleAllInstructions(outFile);
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
                //outFile << line << "\n";
                printWithLabel(outFile, label, line);
//                scheduleAllInstructions(outFile);
            }
            continue;
        }

//        size_t posJmp = line.find("jmp");
//        if (posJmp != string::npos && doStubAdjustment) { //TODO TESTING dont diversify jump pads
//            //outFile << line << "\n";
//            printWithLabel(outFile, label, line);
//            continue;
//        }

        emitInstruction(outFile, label, line);
    }
    scheduleAllInstructions(outFile);
    inFile.close();
    outFile.close();

    return 0;
}
