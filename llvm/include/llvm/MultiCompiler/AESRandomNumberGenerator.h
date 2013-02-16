#ifndef AESRANDOMNUMBERGENERATOR_H_
#define AESRANDOMNUMBERGENERATOR_H_

#include <inttypes.h>
#include "llvm/MultiCompiler/Random.h"
#include "llvm/MultiCompiler/AESCounterModeRNG.h"

namespace multicompiler
{
namespace Random
{

/* Random number generator based on the AES block cipher.
 *
 * Because the block size in AES is 128 bit, we can generate
 * 128 bit random numbers.  However, there isn't an easy way to get a 128
 * bit number, we're going to have to do some magic to get 64-bit numbers out.
 */
class AESRandomNumberGenerator : public Random
{
private:
    /** Imports state file from disk */
    void readStateFile();

    /** Writes current RNG state to disk */
    void writeStateFile();

    AESRandomNumberGenerator();
    AESRandomNumberGenerator(AESRandomNumberGenerator const&);
    AESRandomNumberGenerator& operator=(AESRandomNumberGenerator const&) {
        return *this;
    }

    aesrng_context* ctx;

public:
    uint64_t random();
    uint64_t randnext(uint64_t max);

    void Reseed(uint64_t salt, uint8_t const* password, unsigned int length);

    static AESRandomNumberGenerator& Generator() {
        static AESRandomNumberGenerator instance;
        return instance;
    };

    ~AESRandomNumberGenerator();

// Include shuffling code
#include "Shuffle.h"

};
}
}

#endif
