/*===--- Random.cpp - Base Random Number Generator Implementation -----
*
*
*  This file implements defines the Random Number Generator interface
*  where necessary.
*
*  Author: Todd Jackson
*  Date: February 3, 2012
*
*===----------------------------------------------------------------------===*/

#include "llvm/MultiCompiler/Random.h"

namespace multicompiler{

namespace Random{

uint64_t Seed;
std::string EntropyData;
}
}
