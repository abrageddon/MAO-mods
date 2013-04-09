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
#include "MultiCompiler/MultiCompilerOptions.h"
#include "MultiCompiler/AESRandomNumberGenerator.h"

namespace {

PLUGIN_VERSION

// --------------------------------------------------------------------
// Options
// --------------------------------------------------------------------
MAO_DEFINE_OPTIONS(MOVTOLEA, "MOV To LEA pass", 2) {
 OPTION_STR("MultiCompilerSeed", "1337", "Seed for random number generation")
,OPTION_INT("MOVToLEAPercentage", 30, "MOV To LEA Percentage")
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
        multicompiler::Random::EntropyData = multicompiler::MultiCompilerSeed + "salt";
        PreMOVtoLEAInstructionCount = MOVCandidates = ReplacedMOV = 0;

        Trace(1, "MOVToLEA! MultiCompilerSeed: %s , MOVToLEAPercentage: %d",
                multicompiler::MultiCompilerSeed.c_str(), multicompiler::MOVToLEAPercentage);
    }

    bool Go() {
        bool Changed = false;
        FORALL_FUNC_ENTRY(function_,entry)
        {
            ++PreMOVtoLEAInstructionCount;

            //Determine if is MOV between registers
            if (!entry->IsInstruction() || !entry->AsInstruction()->IsOpMov() || !entry->AsInstruction()->IsRegisterOperand(0)  || !entry->AsInstruction()->IsRegisterOperand(1) ) {
                continue;
            }

            //Found MOV candidate, roll for insertion
            unsigned int Roll = multicompiler::Random::AESRandomNumberGenerator::Generator().randnext(100);
            ++MOVCandidates;
            if (Roll >= multicompiler::MOVToLEAPercentage) {
                continue;
            }

            if (tracing_level() > 0){
                entry->PrintEntry(stderr);
            }

            //Pick correct LEA
//            i386_insn insn;
            if (entry->AsInstruction()->op()==OP_movq) {
                MOVQ_To_LEAQ(entry->AsInstruction()->instruction() );
            } else if (entry->AsInstruction()->op()==OP_cmovl) {
            	MOVL_To_LEAL(entry->AsInstruction()->instruction() );
            } else {
                fprintf(stderr, "NEW MOV TYPE: ");
                entry->PrintEntry(stderr);
                continue;
            }


            //Replace MOV with LEA
            ++ReplacedMOV;

            if (tracing_level() > 0){
                fprintf(stderr, " -> ");
                entry->PrintEntry(stderr);
            }

            Changed = true;

        }

        // TODO Output stats
        TraceC(1, "Pre-MOV to LEA instruction count: %d\n", PreMOVtoLEAInstructionCount);
        TraceC(1, "Number of MOV candidates: %d\n", MOVCandidates);
        TraceC(1, "Number of substituted MOV instructions: %d\n", ReplacedMOV);

        if(Changed){
            CFG::InvalidateCFG(function_);
        }
        return true;
    }
	void MOVL_To_LEAL(i386_insn *i) {
		i->tm.name = strdup("lea");
		i->tm.base_opcode = 141;
		i->tm.opcode_modifier.d = 0;
		i->tm.opcode_modifier.w = 0;
		i->tm.opcode_modifier.checkregsize = 0;
		i->tm.opcode_modifier.no_bsuf = 1;
		int j;

		j = 0;
		i->tm.operand_types[j].bitfield.reg8 = 0;
		i->tm.operand_types[j].bitfield.reg16 = 0;
		i->tm.operand_types[j].bitfield.reg32 = 0;
		i->tm.operand_types[j].bitfield.reg64 = 0;
		i->tm.operand_types[j].bitfield.disp8 = 1;
		i->tm.operand_types[j].bitfield.disp16 = 1;
		i->tm.operand_types[j].bitfield.disp32 = 1;
		i->tm.operand_types[j].bitfield.disp32s = 1;
		i->tm.operand_types[j].bitfield.baseindex = 1;
		i->tm.operand_types[j].bitfield.anysize = 1;

		j = 1;
		i->tm.operand_types[j].bitfield.reg8 = 0;
		i->tm.operand_types[j].bitfield.disp8 = 0;
		i->tm.operand_types[j].bitfield.disp16 = 0;
		i->tm.operand_types[j].bitfield.disp32 = 0;
		i->tm.operand_types[j].bitfield.disp32s = 0;
		i->tm.operand_types[j].bitfield.baseindex = 0;
		i->tm.operand_types[j].bitfield.byte = 0;
		i->tm.operand_types[j].bitfield.word = 0;
		i->tm.operand_types[j].bitfield.dword = 0;
		i->tm.operand_types[j].bitfield.qword = 0;
		i->tm.operand_types[j].bitfield.unspecified = 0;
		i->reg_operands= 1;
		i->mem_operands= 1;


		j = 0;
		i->types[j].bitfield.reg32 = 0;
		i->types[j].bitfield.baseindex = 1;


		j = 1;
		i->types[j].bitfield.reg32 = 1;
		i->types[j].bitfield.dword = 0;
		i->rm.mode = 0;
		i->prefixes = 1;
		i->sib.index = 4;


		i->base_reg = GetRegFromName(i->op[0].regs->reg_name);

		//FOR OP1
		//TODO figure out i->rm.reg
		i->rm.reg = i->op[1].regs->reg_num;

		//FOR OP0
		//TODO figure out i->rm.regmem
		i->rm.regmem = i->op[0].regs->reg_num;
		//TODO figure out i->sib.base
		i->sib.base = i->base_reg->reg_num;

		i->op[0].regs = NULL;

	}
	void MOVQ_To_LEAQ(i386_insn *i) {
		i->tm.name = strdup("lea");
		i->tm.base_opcode = 141;
		i->tm.opcode_modifier.d = 0;
		i->tm.opcode_modifier.w = 0;
		i->tm.opcode_modifier.size64 = 0;
		i->tm.opcode_modifier.no_wsuf = 0;
		i->tm.opcode_modifier.no_lsuf = 0;
		i->tm.opcode_modifier.no_qsuf = 0;
		int j;

		j = 0;
		i->tm.operand_types[j].bitfield.reg64 = 0;
		i->tm.operand_types[j].bitfield.disp8 = 1;
		i->tm.operand_types[j].bitfield.disp16 = 1;
		i->tm.operand_types[j].bitfield.disp32 = 1;
		i->tm.operand_types[j].bitfield.disp32s = 1;
		i->tm.operand_types[j].bitfield.baseindex = 1;
		i->tm.operand_types[j].bitfield.anysize = 1;

		j = 1;
		i->tm.operand_types[j].bitfield.reg16 = 1;
		i->tm.operand_types[j].bitfield.reg32 = 1;
		i->tm.operand_types[j].bitfield.disp8 = 0;
		i->tm.operand_types[j].bitfield.disp32 = 0;
		i->tm.operand_types[j].bitfield.disp32s = 0;
		i->tm.operand_types[j].bitfield.baseindex = 0;
		i->tm.operand_types[j].bitfield.qword = 0;
		i->tm.operand_types[j].bitfield.unspecified = 0;
		i->reg_operands = 1;
		i->mem_operands = 1;

		j = 0;
		i->types[j].bitfield.reg64 = 0;
		i->types[j].bitfield.baseindex = 1;

		j = 1;
		i->types[j].bitfield.qword = 0;
		i->base_reg = GetRegFromName(i->op[0].regs->reg_name);
		i->rm.mode = 0;
		i->sib.index = 4;


		//FOR OP1
		//TODO figure out i->rm.reg
		i->rm.reg = i->op[1].regs->reg_num;


		//FOR OP0
		//TODO figure out i->rm.regmem
		i->rm.regmem = i->op[0].regs->reg_num;
		//TODO figure out i->sib.base
		i->sib.base = i->base_reg->reg_num;

		i->op[0].regs = NULL; //Guessing here


	}
    void LEAQ(i386_insn *i, i386_insn *movIns) {
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
          i->suffix = 113;
          i->operands= 2;
          i->reg_operands= 1;
          i->disp_operands= 0;
          i->mem_operands= 1;
          i->imm_operands= 0;

          j = 0;
          i->types[j].bitfield.baseindex = 1;

          j = 1;
          i->types[j].bitfield.reg64 = 1;
          i->op[1].regs = movIns->op[1].regs;
          i->reloc[0] = static_cast<bfd_reloc_code_real>(70);
          i->reloc[1] = static_cast<bfd_reloc_code_real>(70);
          i->reloc[2] = static_cast<bfd_reloc_code_real>(70);
          i->reloc[3] = static_cast<bfd_reloc_code_real>(70);
          i->reloc[4] = static_cast<bfd_reloc_code_real>(70);
          i->base_reg = movIns->op[0].regs;
          i->prefixes = 1;
          i->rm = movIns->rm;
          i->rex = 8;
          i->sib = movIns->sib;
    }

    //TODO 32 bit
    void LEAL(i386_insn *i, i386_insn *movIns) {
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
        i->op[1].regs = movIns->op[1].regs;
        i->reloc[0] = static_cast<bfd_reloc_code_real>(70);
        i->reloc[1] = static_cast<bfd_reloc_code_real>(70);
        i->reloc[2] = static_cast<bfd_reloc_code_real>(70);
        i->reloc[3] = static_cast<bfd_reloc_code_real>(70);
        i->reloc[4] = static_cast<bfd_reloc_code_real>(70);
        i->base_reg = movIns->op[0].regs;
        i->prefixes = 1;
        i->rm = movIns->rm;
        i->sib = movIns->sib;
    }

};

REGISTER_PLUGIN_FUNC_PASS("MOVTOLEA", MOVToLEA)

} // namespace
