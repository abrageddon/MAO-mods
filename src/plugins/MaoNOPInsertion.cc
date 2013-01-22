//
// SSL Lab
// University of California, Irvine
// SNEISIUS
//
// random nop insertion - NOPInsertion
//
#include "Mao.h"

#include "MultiCompiler/AESRandomNumberGenerator.h"

using namespace multicompiler::Random;

namespace {

PLUGIN_VERSION

// --------------------------------------------------------------------
// Options
// --------------------------------------------------------------------
MAO_DEFINE_OPTIONS(NOPINSERTION, "NOP insertion pass", 3) {
	OPTION_INT("seed", 17, "Seed for random number generation")
,
  OPTION_INT("NOPInsertionPercentage", 30, "NOP Insertion Percentage")
,
  OPTION_INT("MaxNOPsPerInstruction", 3, "Maximum NOPs Per Instruction")

};

class NOPInsertion: public MaoFunctionPass {
public:
NOPInsertion(MaoOptionMap *options, MaoUnit *mao, Function *func) :
		MaoFunctionPass("NOPINSERTION", options, mao, func) {
	seed_ = GetOptionInt("seed");
	NOPInsertionPercentage_ = GetOptionInt("NOPInsertionPercentage");
	MaxNOPsPerInstruction_ = GetOptionInt("MaxNOPsPerInstruction");

	srand(seed_);
	Trace(
			1,
			"NOPInsertion! Seed: %d, NOPInsertionPercentage: %d, MaxNOPsPerInstruction: %d",
			seed_,
			NOPInsertionPercentage_,
			MaxNOPsPerInstruction_);
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

		int BBProb = NOPInsertionPercentage_;

		// TODO use profiling data
//		if (BB->getBasicBlock()) {
//			BBProb = BB->getBasicBlock()->getNOPInsertionPercentage();
//			if (BBProb == multicompiler::NOPInsertionUnknown)
//				BBProb = multicompiler::NOPInsertionPercentage;
//		}

		if (BBProb <= 0)
			continue;

		int numInserted = 0;

		for (unsigned int i = 0; i < multicompiler::MaxNOPsPerInstruction;
				i++) {

			int Roll = AESRandomNumberGenerator::Generator().randnext(100);
			if (Roll >= BBProb)
				continue;

			int NOPCode = AESRandomNumberGenerator::Generator().randnext(
					MAX_NOPS);

			//EXAMPLE
			InstructionEntry *nop = unit_->CreateNopType(function_);
			entry->LinkBefore(nop);
			TraceC(1, "Inserted %d nops, before:", numInserted);
			if (tracing_level() > 0)
				entry->PrintEntry(stderr);
			//EXAMPLE END

			// TODO(ahomescu): figure out if we need to preserve kill information
//			MachineInstr *NewMI = NULL;
//			unsigned reg = nopRegs[NOPCode][!!is64Bit];
			switch (NOPCode) {
			case NOP:
//				NewMI = BuildMI(*BB, I, I->getDebugLoc(), TII->get(X86::NOOP));
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

//			if (NewMI != NULL) {
//				IncrementCounters(NOPCode);
//			}

		}
	}

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

enum {
	NOP, MOV_EBP, MOV_ESP, LEA_ESI, LEA_EDI, MAX_NOPS
};

//static const unsigned nopRegs[MAX_NOPS][2] = {
//		{ 0, 0 },
//		{ X86::EBP, X86::RBP },
//		{ X86::ESP, X86::RSP },
//		{ X86::ESI, X86::RSI },
//		{ X86::EDI, X86::RDI }, };

private:
int seed_;
int NOPInsertionPercentage_;
int MaxNOPsPerInstruction_;
};

REGISTER_PLUGIN_FUNC_PASS("NOPINSERTION", NOPInsertion)
} // namespace
