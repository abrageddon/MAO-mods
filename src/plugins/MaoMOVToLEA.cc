//
// SSL Lab
// University of California, Irvine
// SNEISIUS
//
// MOV To LEA pass - MOVToLEA
//
#include "Mao.h"

// Needed by llvm/Support/DataTypes.h
#ifndef __STDC_LIMIT_MACROS
#define __STDC_LIMIT_MACROS
#endif //__STDC_LIMIT_MACROS
#ifndef __STDC_CONSTANT_MACROS
#define __STDC_CONSTANT_MACROS
#endif //__STDC_CONSTANT_MACROS
#ifndef MAO_MULTI_COMPILER
#define MAO_MULTI_COMPILER
#endif //MAO_MULTI_COMPILER
#include "MultiCompiler/MultiCompilerOptions.h"
#include "MultiCompiler/AESRandomNumberGenerator.h"

namespace {

PLUGIN_VERSION

// --------------------------------------------------------------------
// Options
// --------------------------------------------------------------------
MAO_DEFINE_OPTIONS(MOVTOLEA, "MOV To LEA pass", 3) {
    OPTION_STR("MultiCompilerSeed", "1337", "Seed for random number generation")
,
  	                        OPTION_INT("NOPInsertionPercentage", 30, "NOP Insertion Percentage")
,
  	                        OPTION_INT("MaxNOPsPerInstruction", 1, "Maximum NOPs Per Instruction")
};

class MOVToLEA: public MaoFunctionPass {
private:
    int PreMOVtoLEAInstructionCount, MOVCandidates, ReplacedMOV;

public:
    MOVToLEA(MaoOptionMap *options, MaoUnit *mao, Function *func) :
            MaoFunctionPass("MOVTOLEA", options, mao, func) {
        multicompiler::MultiCompilerSeed = GetOptionString("MultiCompilerSeed");
        multicompiler::MOVToLEAPercentage = GetOptionInt("MOVToLEAPercentage");

        // Initialize RNG
        //	srand (multicompiler::MultiCompilerSeed);
        // TODO make it more similar to cc1_main.cpp => cc1_main
        multicompiler::Random::EntropyData = multicompiler::MultiCompilerSeed;
        PreMOVtoLEAInstructionCount = MOVCandidates = ReplacedMOV = 0;

        Trace(1, "MOVToLEA! MultiCompilerSeed: %s , MOVToLEAPercentage: %d",
                multicompiler::MultiCompilerSeed.c_str(), multicompiler::MOVToLEAPercentage);
    }

// Randomly insert nops into the code stream
//
    bool Go() {
        bool Changed = false;
        FORALL_FUNC_ENTRY(function_,entry)
        {
            ++PreMOVtoLEAInstructionCount;

            //Determine if is MOV
            if (!entry->AsInstruction()->IsOpMov()) {
                continue;
            }
//            if (entry->AsInstruction()->NumOperands() != 2 || !entry->AsInstruction()->IsRegisterOperand(0)
//                    || !entry->AsInstruction()->IsRegisterOperand(1)) {
//                continue;
//            }


            //Pick correct LEA
//            unsigned leaOpc;
//            if (entry->AsInstruction()->op() == X86::MOV32rr) {
//                leaOpc = X86::LEA32r;
//            } else if (I->getOpcode() == X86::MOV64rr) {
//                leaOpc = X86::LEA64r;
//            } else {
//                continue;
//            }

            //Found MOV, roll for insertion
            unsigned int Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
            ++MOVCandidates;
            if (Roll >= multicompiler::MOVToLEAPercentage) {
                continue;
            }

            //Replace MOV with LEA
            ++ReplacedMOV;
//            MachineBasicBlock::iterator J = I;
//            ++I;
//            addRegOffset(BuildMI(*BB, J, J->getDebugLoc(), TII->get(leaOpc), J->getOperand(0).getReg()),
//                    J->getOperand(1).getReg(), false, 0);
//            J->eraseFromParent();
            Changed = true;

            if (tracing_level() > 0)
                entry->PrintEntry(stderr);
        }

        // TODO Output stats
        TraceC(1, "Pre-MOV to LEA instruction count: %d\n", PreMOVtoLEAInstructionCount);
        TraceC(1, "Number of MOV candidates: %d\n", MOVCandidates);
        TraceC(1, "Number of substituted MOV instructions: %d\n", ReplacedMOV);

        if(Changed){
            CFG::InvalidateCFG(function_);
        }
        return Changed;
    }

};

REGISTER_PLUGIN_FUNC_PASS("MOVTOLEA", MOVToLEA)

} // namespace
