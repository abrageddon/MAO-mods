/*===--- MultiCompilerOptions.h - Multicompiler Options -----
*
*
*  This file defines the Multi Compiler Options interface.
*
*===----------------------------------------------------------------------===*/

#ifndef MULTI_COMPILER_OPTIONS_H
#define MULTI_COMPILER_OPTIONS_H
#include <stdio.h>
#include <stdint.h>
#include <string>
#include <map>

#ifndef MAO_MULTI_COMPILER
#include <llvm/Function.h>
#endif // MAO_MULTI_COMPILER

#include <llvm/Support/CommandLine.h>
#include <llvm/Support/raw_ostream.h>

namespace multicompiler {

extern bool ShuffleStackFrames;
extern unsigned int MaxStackFramePadding;
extern std::string MultiCompilerSeed;
extern int PreRARandomizerRange;
extern std::string RNGStateFile;
extern unsigned int NOPInsertionPercentage;
extern unsigned int MaxNOPsPerInstruction;
extern unsigned int MOVToLEAPercentage;
extern unsigned int EquivSubstPercentage;
extern unsigned int RandomizeFunctionList;
extern unsigned int FunctionAlignment;
extern bool RandomizeRegisters;
extern unsigned int ISchedRandPercentage;
extern unsigned int ProfiledNOPInsertion;
extern unsigned int NOPInsertionRange;
extern bool NOPInsertionUseLog;
extern unsigned int ProfiledNOPMinThreshold;
extern bool UseFunctionOptions;
extern std::string FunctionOptionsFile;

static const int NOPInsertionUnknown = -1;

#ifndef MAO_MULTI_COMPILER
typedef std::pair<std::string, std::string> FunctionOptionKey;
typedef std::map<FunctionOptionKey, std::string> FunctionOptionMap;

struct FunctionOptionInfo {
  void *Loc;
  llvm::cl::Option *Opt;
};

extern FunctionOptionInfo FunctionOptions[];

extern bool findFunctionOption(
    const FunctionOptionKey &Key,
    std::string *Val);

template<typename T>
T getFunctionOption(T &OptLoc, const llvm::Function &Fn) {
  if (!UseFunctionOptions)
    return OptLoc;

  // FIXME: use extern templates???
  FunctionOptionInfo *O;
  for (O = FunctionOptions; O->Loc != NULL && O->Loc != &OptLoc; O++) {
  }
  assert(O->Loc == &OptLoc && "Invalid option");

  FunctionOptionKey optKey =
      std::make_pair(Fn.getName(), O->Opt->ArgStr);
  std::string optVal;
  if (findFunctionOption(optKey, &optVal)) {
    llvm::cl::parser<T> p;
    T val;
    if (!p.parse(*O->Opt, O->Opt->ArgStr, optVal, val)) {
      return val;
    }
    llvm::errs() << "Error: couldn't parse option for " << Fn.getName().data()
                 << "::" << O->Opt->ArgStr << ", reverting to global value\n";
  }
  return OptLoc;
}
#endif // MAO_MULTI_COMPILER

}

#endif
