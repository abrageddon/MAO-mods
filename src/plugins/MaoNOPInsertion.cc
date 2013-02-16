//
// SSL Lab
// University of California, Irvine
// SNEISIUS
//
// random nop insertion - NOPInsertion
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
#include "llvm/MultiCompiler/MultiCompilerOptions.h"
#include "llvm/MultiCompiler/AESRandomNumberGenerator.h"

namespace {

PLUGIN_VERSION

// --------------------------------------------------------------------
// Options
// --------------------------------------------------------------------
MAO_DEFINE_OPTIONS(NOPINSERTION, "NOP insertion pass", 3) {
	OPTION_STR("MultiCompilerSeed", "1337", "Seed for random number generation")
,
  OPTION_INT("NOPInsertionPercentage", 30, "NOP Insertion Percentage")
,
  OPTION_INT("MaxNOPsPerInstruction", 1, "Maximum NOPs Per Instruction")
};

class NOPInsertion: public MaoFunctionPass {
private:
	int InsertedInstructions, NumNOPInstructions, NumMovEBPInstructions, NumMovESPInstructions, NumLeaESIInstructions, NumLeaEDIInstructions;

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
	InsertedInstructions = NumNOPInstructions = NumMovEBPInstructions = NumMovESPInstructions = NumLeaESIInstructions = NumLeaEDIInstructions = 0;

	Trace(
			1,
			"NOPInsertion! MultiCompilerSeed: %s , NOPInsertionPercentage: %d, MaxNOPsPerInstruction: %d",
			multicompiler::MultiCompilerSeed.c_str(),
			multicompiler::NOPInsertionPercentage,
			multicompiler::MaxNOPsPerInstruction);
}

// Randomly insert nops into the code stream
//
bool Go() {
	FORALL_FUNC_ENTRY(function_,entry) {

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
//		if (BB->getBasicBlock()) {
//			BBProb = BB->getBasicBlock()->getNOPInsertionPercentage();
//			if (BBProb == multicompiler::NOPInsertionUnknown)
//				BBProb = multicompiler::NOPInsertionPercentage;
//		}

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
//			int NOPCode = NOP;

			// TODO(ahomescu): figure out if we need to preserve kill information
//			MachineInstr *NewMI = NULL;
//			unsigned reg = nopRegs[NOPCode][!!is64Bit];

			InstructionEntry *nop;
			switch (NOPCode) {
			case NOP:
//				NewMI = BuildMI(*BB, I, I->getDebugLoc(), TII->get(X86::NOOP));
				nop = unit_->CreateNopType(function_);
				entry->LinkBefore(nop);
				break;

			case MOV_EBP:
			case MOV_ESP: {
//				unsigned opc = is64Bit ? X86::MOV64rr : X86::MOV32rr;
//				NewMI = BuildMI(*BB, I, I->getDebugLoc(), TII->get(opc), reg).addReg(reg);
				break;
			}

			case LEA_ESI:
			case LEA_EDI: {
//				unsigned opc = is64Bit ? X86::LEA64r : X86::LEA32r;
//				NewMI = addRegOffset(BuildMI(*BB, I, I->getDebugLoc(), TII->get(opc), reg),reg, false, 0);
				break;
			}
			}

			if (nop != NULL) {
				numInserted++;
				IncrementCounters (NOPCode);
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
};

REGISTER_PLUGIN_FUNC_PASS("NOPINSERTION", NOPInsertion)

} // namespace
