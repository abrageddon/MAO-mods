#ifndef RAND48_H_
#define RAND48_H_

#define MAO_MULTI_COMPILER
#define __STDC_LIMIT_MACROS

#include "Random.h"
#include "MultiCompilerOptions.h"
#include "Rand48.h"
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fstream>
#include <cstdlib>
#include <inttypes.h>
#include <stdint.h>
#include <cstdint>


namespace multicompiler
{
namespace Random
{

/* Linear congruential generator
 *
 */
class Rand48 : public Random
{
private:
    uint64_t state;

    static const uint64_t LOW = 0x330e;
    static const uint64_t A = 0x5deece66dULL;
    static const uint64_t C = 0xb;
    static const uint64_t M = 0x0000ffffffffffffULL;

    void readStateFile();
    void writeStateFile();

    Rand48(uint32_t);
    Rand48(Rand48 const&);
    Rand48& operator=(Rand48 const&) {
        return *this;
    }

public:
    uint64_t random();
    uint64_t randnext(uint64_t max);

    static Rand48& Generator() {
        static Rand48 instance(0x87651234);
        return instance;
    };

    ~Rand48();

// Include shuffling code
#include "Shuffle.h"

};
}
}

#endif
