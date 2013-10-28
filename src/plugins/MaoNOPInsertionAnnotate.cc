//
// SSL Lab
// University of California, Irvine
// SNEISIUS
//
// random nop insertion - NOPInsertion
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
MAO_DEFINE_OPTIONS(NOPINSERTIONA, "NOP insertion annotation pass", 0) {
};

class NOPInsertionA: public MaoFunctionPass {
public:
    NOPInsertionA(MaoOptionMap *options, MaoUnit *mao, Function *func) :
            MaoFunctionPass("NOPINSERTIONA", options, mao, func) {



        Trace(1, "NOPInsertionA!");
    }

    bool Go() {
        FORALL_FUNC_ENTRY(function_,entry)
        {

            if (!entry->IsInstruction())
                continue;

            MaoEntry *prev_entry = entry->prev();
            if (prev_entry->IsInstruction()) {
                InstructionEntry *prev_ins = prev_entry->AsInstruction();
                //lock appears as separate instruction but in reality is a prefix
                //Inserting nops between lock and the next instruction is bad as
                //'lock nop' is an illegal instruction sequence
                if (prev_ins->IsLock())
                    continue;
            }
            //std::string s;
            //entry->AsInstruction()->ToString(&s);
            //Trace(2, s.c_str());
            entry->AsInstruction()->SetCanNOPInsert(true);

        }


        return true;
    }


};

REGISTER_PLUGIN_FUNC_PASS("NOPINSERTIONA", NOPInsertionA)

} // namespace
