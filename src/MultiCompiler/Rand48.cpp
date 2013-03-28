#include "MultiCompilerOptions.h"
#include "Rand48.h"
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fstream>
#include <cstdlib>

using namespace llvm;

namespace multicompiler
{
namespace Random
{

Rand48::Rand48(uint32_t seed) : state(0)
{
    if (multicompiler::RNGStateFile == "") state = (static_cast<uint64_t>(seed) << 16) | LOW;
    else readStateFile();

}

Rand48::Rand48(Rand48 const& a) : Random(), state(0)
{
    state = a.state;
}

Rand48::~Rand48()
{
    writeStateFile();
}

void Rand48::readStateFile()
{
    struct stat s;
    // Don't read if there's no file specified.
    if (multicompiler::RNGStateFile == "" || stat(multicompiler::RNGStateFile.c_str(), &s) != 0) {
        return;
    }

    std::ifstream statefile(multicompiler::RNGStateFile.c_str(), std::ios::in);
#ifndef MAO_MULTI_COMPILER
    DEBUG(errs() << "Reading RNG state file from " << multicompiler::RNGStateFile << "\n");
#endif //MAO_MULTI_COMPILER
    statefile >> state;
#ifndef MAO_MULTI_COMPILER
    DEBUG(errs() << "  state: " << state << "\n");
#endif //MAO_MULTI_COMPILER
}

void Rand48::writeStateFile()
{
    //Don't serialise without a file name
    if (multicompiler::RNGStateFile == "") return;

    std::ofstream statefile(multicompiler::RNGStateFile.c_str(), std::ios::out);
#ifndef MAO_MULTI_COMPILER
    DEBUG(errs() << "Writing RNG state file to " << multicompiler::RNGStateFile << "\n");
#endif //MAO_MULTI_COMPILER
    statefile << state << std::endl;
}

/* This RNG only generates 32 bits of randomness, so we have to cast it down
 * and then up
 */
uint64_t Rand48::random()
{
    state = (A * state + C) & M;
    return static_cast<uint32_t>(state >> 17);
}

/*
 * With only 32 bits of randomness, we do a proportional shift to ensure we
 * get even distribution over the potential max.
 */
uint64_t Rand48::randnext(uint64_t max)
{
    return (static_cast<double>(random()) / UINT32_MAX) * max;
}

} // namespace Random

} // namespace multicompiler
