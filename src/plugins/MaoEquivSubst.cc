//
// SSL Lab
// University of California, Irvine
// SNEISIUS
//
// Equivalent instruction substitution pass - EquivSubst
//
#include "Mao.h"

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
MAO_DEFINE_OPTIONS(EQUIVSUBST, "Equivalent instruction substitution pass", 2) {
 OPTION_STR("MultiCompilerSeed", "1337", "Seed for random number generation")
,OPTION_INT("EquivSubstPercentage", 30, "EquivSubst Percentage")
};

class EquivSubst: public MaoFunctionPass {
private:
    int PreEquivSubstInstructionCount, EquivSubstCandidates, EquivSubstituted;

public:
    EquivSubst(MaoOptionMap *options, MaoUnit *mao, Function *func) :
            MaoFunctionPass("EQUIVSUBST", options, mao, func) {
        multicompiler::MultiCompilerSeed = GetOptionString("MultiCompilerSeed");
        multicompiler::EquivSubstPercentage = GetOptionInt("EquivSubstPercentage");

        // Initialize RNG
        //  srand (multicompiler::MultiCompilerSeed);
        // TODO make it more similar to cc1_main.cpp => cc1_main
        multicompiler::Random::EntropyData = multicompiler::MultiCompilerSeed + "salt";
        PreEquivSubstInstructionCount = EquivSubstCandidates = EquivSubstituted = 0;

        Trace(1, "EquivSubst! MultiCompilerSeed: %s , EquivSubstPercentage: %d",
                multicompiler::MultiCompilerSeed.c_str(), multicompiler::EquivSubstPercentage);
    }

    bool Go() {
        bool Changed = false;
        FORALL_FUNC_ENTRY(function_,entry)
        {


        }

        // TODO Output stats
        TraceC(1, "Pre-equivalent substitution instruction count: %d\n", PreEquivSubstInstructionCount);
        TraceC(1, "Number of equivalent substitution candidates: %d\n", EquivSubstCandidates);
        TraceC(1, "Number of substituted equivalent instructions: %d\n", EquivSubstituted);

        if(Changed){
            CFG::InvalidateCFG(function_);
        }
        return true;
    }

};

REGISTER_PLUGIN_FUNC_PASS("EQUIVSUBST", EquivSubst)

} // namespace
