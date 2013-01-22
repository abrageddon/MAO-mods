/*===--- MultiCompilerOptions.h - Multicompiler Options -----
*
*
*===----------------------------------------------------------------------===*/

#ifndef PROFILED_NOP_INSERTION_H
#define PROFILED_NOP_INSERTION_H

#include "llvm/Analysis/Passes.h"
#include "llvm/Analysis/ProfileInfo.h"
#include "llvm/MultiCompiler/MultiCompilerOptions.h"
#include "llvm/PassManager.h"
#include "llvm/Transforms/Instrumentation.h"

namespace multicompiler {

llvm::ModulePass *createProfiledNOPInsertionPass();

inline void addProfiledNOPInsertionPasses(llvm::PassManagerBase &PM) {
  // If we have profiled NOP insertion, add the passes here.
  if (ProfiledNOPInsertion == 1) {
    PM.add(llvm::createOptimalEdgeProfilerPass());
  } else if (multicompiler::ProfiledNOPInsertion == 2) {
    PM.add(llvm::createProfileLoaderPass(""));
    PM.add(createProfiledNOPInsertionPass());
  }
}

}
#endif
