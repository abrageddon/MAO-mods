//
// SSL Lab
// University of California, Irvine
// SNEISIUS
//
// MOV To LEA pass - MOVToLEA
//
#include "Mao.h"

#ifndef MAO_MULTI_COMPILER
#define MAO_MULTI_COMPILER
#endif //MAO_MULTI_COMPILER


namespace {

PLUGIN_VERSION

// --------------------------------------------------------------------
// Options
// --------------------------------------------------------------------
MAO_DEFINE_OPTIONS(MOVTOLEAA, "MOV To LEA Annotation pass", 0) {
};

class MOVToLEAA: public MaoFunctionPass {
private:
    int PreMOVtoLEAInstructionCount, MOVCandidates;

public:
    MOVToLEAA(MaoOptionMap *options, MaoUnit *mao, Function *func) :
            MaoFunctionPass("MOVTOLEAA", options, mao, func) {

        PreMOVtoLEAInstructionCount = MOVCandidates = 0;

        Trace(1, "MOVToLEA Annotation!");
    }

    bool Go() {
        FORALL_FUNC_ENTRY(function_,entry)
        {
            ++PreMOVtoLEAInstructionCount;

            //Determine if is MOV between registers
            if (!entry->IsInstruction()
                    || !entry->AsInstruction()->IsOpMov()
                    || !entry->AsInstruction()->IsRegisterOperand(0)
                    || !entry->AsInstruction()->IsRegisterOperand(1)
                    || entry->AsInstruction()->instruction()->types[0].bitfield.regmmx == 1
                    || entry->AsInstruction()->instruction()->types[1].bitfield.regmmx == 1
                    || entry->AsInstruction()->instruction()->types[0].bitfield.regxmm == 1
                    || entry->AsInstruction()->instruction()->types[1].bitfield.regxmm == 1
                    || entry->AsInstruction()->instruction()->types[0].bitfield.regymm == 1
                    || entry->AsInstruction()->instruction()->types[1].bitfield.regymm == 1) {
                continue;
            }

            //Found MOV candidate, roll for insertion
            ++MOVCandidates;
            entry->AsInstruction()->SetCanMOVToLEA(true);

            if (tracing_level() > 0){
                entry->PrintEntry(stderr);
            }

        }

        // TODO Output stats
        TraceC(1, "Pre-MOV to LEA instruction count: %d\n", PreMOVtoLEAInstructionCount);
        TraceC(1, "Number of MOV candidates: %d\n", MOVCandidates);

        return true;
    }

};

REGISTER_PLUGIN_FUNC_PASS("MOVTOLEAA", MOVToLEAA)

} // namespace
