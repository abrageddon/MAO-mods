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
#include "MultiCompiler/MultiCompilerOptions.h"
#include "MultiCompiler/AESRandomNumberGenerator.h"
#include "as.h"//maybe these two?
#include "tc-i386.h"

namespace {

PLUGIN_VERSION

// --------------------------------------------------------------------
// Options
// --------------------------------------------------------------------
MAO_DEFINE_OPTIONS(NOPINSERTION, "NOP insertion pass", 3) {
 OPTION_STR("MultiCompilerSeed", "1337", "Seed for random number generation")
,OPTION_INT("NOPInsertionPercentage", 30, "NOP Insertion Percentage")
,OPTION_INT("MaxNOPsPerInstruction", 1, "Maximum NOPs Per Instruction")
};

class NOPInsertion: public MaoFunctionPass {
private:
    int InsertedInstructions, NumNOPInstructions, NumMovEBPInstructions, NumMovESPInstructions,
            NumLeaESIInstructions, NumLeaEDIInstructions;

    enum {
        NOP, MOV_EBP, MOV_ESP, LEA_ESI, LEA_EDI, MAX_NOPS
    };

    //static const unsigned nopRegs[MAX_NOPS][2] = {
    //		{ 0, 0 },
    //		{ X86::EBP, X86::RBP },
    //		{ X86::ESP, X86::RSP },
    //		{ X86::ESI, X86::RSI },
    //		{ X86::EDI, X86::RDI }, };

public:
    NOPInsertion(MaoOptionMap *options, MaoUnit *mao, Function *func) :
            MaoFunctionPass("NOPINSERTION", options, mao, func) {
        multicompiler::MultiCompilerSeed = GetOptionString("MultiCompilerSeed");
        multicompiler::NOPInsertionPercentage = GetOptionInt("NOPInsertionPercentage");
        multicompiler::MaxNOPsPerInstruction = GetOptionInt("MaxNOPsPerInstruction");

        // Initialize RNG
        //	srand (multicompiler::MultiCompilerSeed);
        // TODO make it more similar to cc1_main.cpp => cc1_main
        multicompiler::Random::EntropyData = multicompiler::MultiCompilerSeed;
        InsertedInstructions = NumNOPInstructions = NumMovEBPInstructions = NumMovESPInstructions =
                NumLeaESIInstructions = NumLeaEDIInstructions = 0;

        Trace(1, "NOPInsertion! MultiCompilerSeed: %s , NOPInsertionPercentage: %d, MaxNOPsPerInstruction: %d",
                multicompiler::MultiCompilerSeed.c_str(), multicompiler::NOPInsertionPercentage,
                multicompiler::MaxNOPsPerInstruction);
    }

// Randomly insert nops into the code stream
//
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

            int BBProb = multicompiler::NOPInsertionPercentage;

            // TODO use profiling data
//			if (BB->getBasicBlock()) {
//				BBProb = BB->getBasicBlock()->getNOPInsertionPercentage();
//				if (BBProb == multicompiler::NOPInsertionUnknown)
//					BBProb = multicompiler::NOPInsertionPercentage;
//			}

            if (BBProb <= 0)
                continue;

            int numInserted = 0;

            for (unsigned int i = 0; i < multicompiler::MaxNOPsPerInstruction; i++) {

                // Insert or not
                int Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
                if (Roll >= BBProb)
                    continue;

                // Type of NOP
                // TODO implement other types of NOPs
                int NOPCode = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(MAX_NOPS);

                i386_insn insn;
				InstructionEntry *nop;
                switch (NOPCode) {
                case NOP:
                    nop = unit_->CreateNop(function_);
                    entry->LinkBefore(nop);
                    break;

                case MOV_EBP:
                	MOV_EBP_EBP(&insn);
                	nop = unit_->CreateInstruction(&insn, function_);
                	entry->LinkBefore(nop);
                	break;

                case MOV_ESP:
                	MOV_ESP_ESP(&insn);
                	nop = unit_->CreateInstruction(&insn, function_);
                	entry->LinkBefore(nop);
                    break;

                case LEA_ESI:
                	LEA_ESI_ESI(&insn);
                	nop = unit_->CreateInstruction(&insn, function_);
                	entry->LinkBefore(nop);
                	break;

                case LEA_EDI:
                	LEA_EDI_EDI(&insn);
                	nop = unit_->CreateInstruction(&insn, function_);
                	entry->LinkBefore(nop);
                    break;
                }

                if (nop != NULL) {
                    numInserted++;
                    IncrementCounters(NOPCode);
                }

            }
            //			if (NewMI != NULL) {
            //				IncrementCounters(NOPCode);
            //			}
            TraceC(1, "Inserted %d Instructions, before:", numInserted);
            if (tracing_level() > 0)
                entry->PrintEntry(stderr);
        }

        // TODO Output stats
        TraceC(1, "Total of %d Instructions\n", InsertedInstructions);
        TraceC(1, "Total of %d NOPs\n", NumNOPInstructions);
        TraceC(1, "Total of %d MovEBPs\n", NumMovEBPInstructions);
        TraceC(1, "Total of %d MovESPs\n", NumMovESPInstructions);
        TraceC(1, "Total of %d LeaESIs\n", NumLeaESIInstructions);
        TraceC(1, "Total of %d LeaEDIs\n", NumLeaEDIInstructions);

        CFG::InvalidateCFG(function_);
        return true;
    }

    void IncrementCounters(int const code) {
        ++InsertedInstructions;
        switch (code) {
        case NOP:
            ++NumNOPInstructions;
            break;
        case MOV_EBP:
            ++NumMovEBPInstructions;
            break;
        case MOV_ESP:
            ++NumMovESPInstructions;
            break;
        case LEA_ESI:
            ++NumLeaESIInstructions;
            break;
        case LEA_EDI:
            ++NumLeaEDIInstructions;
            break;
        }
    }
	void MOV_ESP_ESP(i386_insn *i) {
		// Zero out the structure.
		memset(i, 0, sizeof(*i));
		i->tm.name = strdup("mov");
		i->tm.operands = 2;
		i->tm.base_opcode = 137;
		i->tm.extension_opcode = 65535;
		i->tm.opcode_length = 1;
		i->tm.opcode_modifier.d = 1;
		i->tm.opcode_modifier.w = 1;
		i->tm.opcode_modifier.modrm = 1;
		i->tm.opcode_modifier.checkregsize = 1;
		i->tm.opcode_modifier.no_ssuf = 1;
		i->tm.opcode_modifier.no_ldsuf = 1;
		int j;

		j = 0;
		i->tm.operand_types[j].bitfield.reg8 = 1;
		i->tm.operand_types[j].bitfield.reg16 = 1;
		i->tm.operand_types[j].bitfield.reg32 = 1;
		i->tm.operand_types[j].bitfield.reg64 = 1;

		j = 1;
		i->tm.operand_types[j].bitfield.reg8 = 1;
		i->tm.operand_types[j].bitfield.reg16 = 1;
		i->tm.operand_types[j].bitfield.reg32 = 1;
		i->tm.operand_types[j].bitfield.reg64 = 1;
		i->tm.operand_types[j].bitfield.disp8 = 1;
		i->tm.operand_types[j].bitfield.disp16 = 1;
		i->tm.operand_types[j].bitfield.disp32 = 1;
		i->tm.operand_types[j].bitfield.disp32s = 1;
		i->tm.operand_types[j].bitfield.baseindex = 1;
		i->tm.operand_types[j].bitfield.byte = 1;
		i->tm.operand_types[j].bitfield.word = 1;
		i->tm.operand_types[j].bitfield.dword = 1;
		i->tm.operand_types[j].bitfield.qword = 1;
		i->tm.operand_types[j].bitfield.unspecified = 1;
		i->suffix = 108;
		i->operands = 2;
		i->reg_operands = 2;
		i->disp_operands = 0;
		i->mem_operands = 0;
		i->imm_operands = 0;

		j = 0;
		i->types[j].bitfield.reg32 = 1;

		j = 1;
		i->types[j].bitfield.reg32 = 1;
		i->op[0].regs = GetRegFromName("esp");
		i->op[1].regs = GetRegFromName("esp");
		i->reloc[0] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[1] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[2] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[3] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[4] = static_cast<bfd_reloc_code_real>(70);
		i->rm.regmem = 4;
		i->rm.reg = 4;
		i->rm.mode = 3;
	}
	void MOV_EBP_EBP(i386_insn *i) {
		// Zero out the structure.
		memset(i, 0, sizeof(*i));
		i->tm.name = strdup("mov");
		i->tm.operands = 2;
		i->tm.base_opcode = 137;
		i->tm.extension_opcode = 65535;
		i->tm.opcode_length = 1;
		i->tm.opcode_modifier.d = 1;
		i->tm.opcode_modifier.w = 1;
		i->tm.opcode_modifier.modrm = 1;
		i->tm.opcode_modifier.checkregsize = 1;
		i->tm.opcode_modifier.no_ssuf = 1;
		i->tm.opcode_modifier.no_ldsuf = 1;
		int j;

		j = 0;
		i->tm.operand_types[j].bitfield.reg8 = 1;
		i->tm.operand_types[j].bitfield.reg16 = 1;
		i->tm.operand_types[j].bitfield.reg32 = 1;
		i->tm.operand_types[j].bitfield.reg64 = 1;

		j = 1;
		i->tm.operand_types[j].bitfield.reg8 = 1;
		i->tm.operand_types[j].bitfield.reg16 = 1;
		i->tm.operand_types[j].bitfield.reg32 = 1;
		i->tm.operand_types[j].bitfield.reg64 = 1;
		i->tm.operand_types[j].bitfield.disp8 = 1;
		i->tm.operand_types[j].bitfield.disp16 = 1;
		i->tm.operand_types[j].bitfield.disp32 = 1;
		i->tm.operand_types[j].bitfield.disp32s = 1;
		i->tm.operand_types[j].bitfield.baseindex = 1;
		i->tm.operand_types[j].bitfield.byte = 1;
		i->tm.operand_types[j].bitfield.word = 1;
		i->tm.operand_types[j].bitfield.dword = 1;
		i->tm.operand_types[j].bitfield.qword = 1;
		i->tm.operand_types[j].bitfield.unspecified = 1;
		i->suffix = 108;
		i->operands = 2;
		i->reg_operands = 2;
		i->disp_operands = 0;
		i->mem_operands = 0;
		i->imm_operands = 0;

		j = 0;
		i->types[j].bitfield.reg32 = 1;

		j = 1;
		i->types[j].bitfield.reg32 = 1;
		i->op[0].regs = GetRegFromName("ebp");
		i->op[1].regs = GetRegFromName("ebp");
		i->reloc[0] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[1] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[2] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[3] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[4] = static_cast<bfd_reloc_code_real>(70);
		i->rm.regmem = 5;
		i->rm.reg = 5;
		i->rm.mode = 3;
	}
	void LEA_ESI_ESI(i386_insn *i) {
		// Zero out the structure.
		memset(i, 0, sizeof(*i));
		i->tm.name = strdup("lea");
		i->tm.operands = 2;
		i->tm.base_opcode = 141;
		i->tm.extension_opcode = 65535;
		i->tm.opcode_length = 1;
		i->tm.opcode_modifier.modrm = 1;
		i->tm.opcode_modifier.no_bsuf = 1;
		i->tm.opcode_modifier.no_ssuf = 1;
		i->tm.opcode_modifier.no_ldsuf = 1;
		int j;

		j = 0;
		i->tm.operand_types[j].bitfield.disp8 = 1;
		i->tm.operand_types[j].bitfield.disp16 = 1;
		i->tm.operand_types[j].bitfield.disp32 = 1;
		i->tm.operand_types[j].bitfield.disp32s = 1;
		i->tm.operand_types[j].bitfield.baseindex = 1;
		i->tm.operand_types[j].bitfield.anysize = 1;

		j = 1;
		i->tm.operand_types[j].bitfield.reg16 = 1;
		i->tm.operand_types[j].bitfield.reg32 = 1;
		i->tm.operand_types[j].bitfield.reg64 = 1;
		i->suffix = 108;
		i->operands = 2;
		i->reg_operands = 1;
		i->disp_operands = 0;
		i->mem_operands = 1;
		i->imm_operands = 0;

		j = 0;
		i->types[j].bitfield.baseindex = 1;

		j = 1;
		i->types[j].bitfield.reg32 = 1;
		i->op[1].regs = GetRegFromName("esi");
		i->reloc[0] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[1] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[2] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[3] = static_cast<bfd_reloc_code_real>(70);
		i->reloc[4] = static_cast<bfd_reloc_code_real>(70);
		i->base_reg = GetRegFromName("esi");
		i->prefixes = 1;
		i->rm.regmem = 6;
		i->rm.reg = 6;
		i->sib.base = 6;
		i->sib.index = 4;
	}
	void LEA_EDI_EDI(i386_insn *i) {
	  // Zero out the structure.
	  memset(i, 0, sizeof(*i));
	  i->tm.name = strdup("lea");
	  i->tm.operands = 2;
	  i->tm.base_opcode = 141;
	  i->tm.extension_opcode = 65535;
	  i->tm.opcode_length = 1;
	  i->tm.opcode_modifier.modrm = 1;
	  i->tm.opcode_modifier.no_bsuf = 1;
	  i->tm.opcode_modifier.no_ssuf = 1;
	  i->tm.opcode_modifier.no_ldsuf = 1;
	  int j;

	  j = 0;
	  i->tm.operand_types[j].bitfield.disp8 = 1;
	  i->tm.operand_types[j].bitfield.disp16 = 1;
	  i->tm.operand_types[j].bitfield.disp32 = 1;
	  i->tm.operand_types[j].bitfield.disp32s = 1;
	  i->tm.operand_types[j].bitfield.baseindex = 1;
	  i->tm.operand_types[j].bitfield.anysize = 1;

	  j = 1;
	  i->tm.operand_types[j].bitfield.reg16 = 1;
	  i->tm.operand_types[j].bitfield.reg32 = 1;
	  i->tm.operand_types[j].bitfield.reg64 = 1;
	  i->suffix = 108;
	  i->operands= 2;
	  i->reg_operands= 1;
	  i->disp_operands= 0;
	  i->mem_operands= 1;
	  i->imm_operands= 0;

	  j = 0;
	  i->types[j].bitfield.baseindex = 1;

	  j = 1;
	  i->types[j].bitfield.reg32 = 1;
	  i->op[1].regs = GetRegFromName ("edi");
	  i->reloc[0] = static_cast<bfd_reloc_code_real>(70);
	  i->reloc[1] = static_cast<bfd_reloc_code_real>(70);
	  i->reloc[2] = static_cast<bfd_reloc_code_real>(70);
	  i->reloc[3] = static_cast<bfd_reloc_code_real>(70);
	  i->reloc[4] = static_cast<bfd_reloc_code_real>(70);
	  i->base_reg = GetRegFromName ("edi");
	  i->prefixes = 1;
	  i->rm.regmem = 7;
	  i->rm.reg = 7;
	  i->sib.base = 7;
	  i->sib.index = 4;
	}

};

REGISTER_PLUGIN_FUNC_PASS("NOPINSERTION", NOPInsertion)

} // namespace
