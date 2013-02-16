/*===--- Random.h - MultiCompiler Random Number Generator Interface -----
*
*
*  This file defines the interface for Multi Compiler random number generators.
*
*===----------------------------------------------------------------------===*/
#ifndef RANDOM_H_
#define RANDOM_H_

#include <inttypes.h>

#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/ilist.h"

namespace multicompiler{
namespace Random {

/* Seed information for Random Number Generators. */
extern uint64_t Seed;
extern std::string EntropyData;

/*
 * Base class for Random Number Generators.
 */
class Random{
private:
    virtual void readStateFile() = 0;
    virtual void writeStateFile() = 0;

protected:
    Random(){ };
    Random(Random const&){}
    Random& operator=(Random const&){ return *this; }

public:
    virtual uint64_t random() = 0;
    virtual uint64_t randnext(uint64_t max) = 0;

    virtual ~Random() {}

};
}
}
#endif
