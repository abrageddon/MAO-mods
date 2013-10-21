//
// SSL Lab
// University of California, Irvine
// SNEISIUS
//
// Label every instruction
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
MAO_DEFINE_OPTIONS(LABELALL, "Label every instruction", 0) {
};

class LabelAll: public MaoFunctionPass {
private:
    static long mapID;
public:
    LabelAll(MaoOptionMap *options, MaoUnit *mao, Function *func) :
            MaoFunctionPass("LABELALL", options, mao, func) {

        //TODO look into mapID issues with multifile
        //mapID=0;

        Trace(3, "LabelAll!");
    }

// Randomly insert nops into the code stream
//
    bool Go() {
        FORALL_FUNC_ENTRY(function_,entry)
        {

            if (entry->IsLabel()){
                Trace(3, "L: %s", entry->AsLabel()->name());
                continue;
            }

            if (entry->IsDirective()){
                std::string *dir;
                dir = new std::string();
                entry->AsDirective()->ToString(dir);
                Trace(3, "D: %s", dir->c_str());
                delete dir;
                continue;
            }

            if (!entry->IsInstruction()){
                continue;}

            std::string *ins;
            ins = new std::string();
            entry->AsInstruction()->ToString(ins);

            MaoEntry *prev_entry = entry->prev();
            if ( false && prev_entry->IsLabel() ) { //TODO IF PREV LABEL MATCHES FORMAT?
                LabelEntry *prev_label = prev_entry->AsLabel();
                Trace(1, "PREV: %s\tINST: %s", prev_label->name(), ins->c_str());
                
            }else{
                char labelName[512];
                MAO_ASSERT(mapID <= LONG_MAX);
		sprintf(labelName, "__divmap_%ld", mapID++);
                char *name = strdup(labelName);
                LabelEntry *newLabel = unit_->CreateLabel(name, function_, function_->GetSubSection());
                Trace(1, "L: %s", newLabel->name());
                entry->LinkBefore(newLabel);
            }
            Trace(1, "I: %s", ins->c_str());
            delete ins;
        }


        return true;
    }


};

long LabelAll::mapID=0;

REGISTER_PLUGIN_FUNC_PASS("LABELALL", LabelAll)

} // namespace
