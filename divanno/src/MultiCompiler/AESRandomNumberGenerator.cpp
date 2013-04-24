/*
 *  FIPS-197 compliant AES implementation
 *
 *  Copyright (C) 2006-2010, Brainspark B.V.
 *
 *  This file is part of PolarSSL (http://www.polarssl.org)
 *  Lead Maintainer: Paul Bakker <polarssl_maintainer at polarssl.org>
 *
 *  All rights reserved.
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License along
 *  with this program; if not, write to the Free Software Foundation, Inc.,
 *  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */
/*
 *  The AES block cipher was designed by Vincent Rijmen and Joan Daemen.
 *
 *  http://csrc.nist.gov/encryption/aes/rijndael/Rijndael.pdf
 *  http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
 */
/*
 * C++-ified by Todd Jackson
 */

//#define DEBUG_TYPE "aesrng"
#define MAO_MULTI_COMPILER

#include "MultiCompilerOptions.h"
#include "AESRandomNumberGenerator.h"
#include "AESCounterModeRNG.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fstream>
#include <errno.h>

extern int errno;


#ifndef MAO_MULTI_COMPILER
STATISTIC(RandomNumbersGenerated, "multicompiler: Number of random numbers generated");
#endif //MAO_MULTI_COMPILER

namespace multicompiler
{
namespace Random
{

AESRandomNumberGenerator::AESRandomNumberGenerator( ) : Random()
{
#ifndef MAO_MULTI_COMPILER
    DEBUG(errs() << "AES RNG: Initializing context ");
#endif //MAO_MULTI_COMPILER
    if(!MultiCompilerSeed.empty() && !EntropyData.empty()){
#ifndef MAO_MULTI_COMPILER
        DEBUG(errs() << " with command line seed and entropy data\n");
#endif //MAO_MULTI_COMPILER

        // TODO(tmjackso): Replace checks with a proper assert
        errno = 0;
        Seed = strtoul(MultiCompilerSeed.c_str(), NULL, 10);
        if(errno == ERANGE || errno == EINVAL){
#ifndef MAO_MULTI_COMPILER
            llvm::report_fatal_error("MultiCompilerSeed is out of range!");
#endif //MAO_MULTI_COMPILER
        }
        // Seed properly
        aesrng_initialize_with_random_data(&ctx, 16,
                reinterpret_cast<const uint8_t*>(EntropyData.c_str()),
                EntropyData.length(), Seed);
    }
    else if(multicompiler::RNGStateFile != ""){
        // Fall back on state file...if provided.
#ifndef MAO_MULTI_COMPILER
        DEBUG(errs() << " with file\n");
#endif //MAO_MULTI_COMPILER
        aesrng_initialize_to_empty(&ctx);
        readStateFile();
    }
    else{
#ifndef MAO_MULTI_COMPILER
        DEBUG(errs() << " to default\n");
        DEBUG(errs() << "Warning! Using unseeded random number generator\n");
#endif //MAO_MULTI_COMPILER
        aesrng_initialize_to_default(&ctx);

    }
#ifndef MAO_MULTI_COMPILER
    errs().flush();
#endif //MAO_MULTI_COMPILER
}

void AESRandomNumberGenerator::Reseed(uint64_t salt, uint8_t const* password, unsigned int length)
{
#ifndef MAO_MULTI_COMPILER
    DEBUG(errs() << "Re-Seeding AES RNG context from salt and password\n");
    DEBUG(errs() << "Salt: " << salt << "\n");
#endif //MAO_MULTI_COMPILER
    aesrng_destroy(ctx);
    aesrng_initialize_with_random_data(&ctx, 16, password, length, salt);
}

AESRandomNumberGenerator::AESRandomNumberGenerator(AESRandomNumberGenerator const& a) : Random()
{
#ifndef MAO_MULTI_COMPILER
    DEBUG(errs() << "Initialising AES RNG context from copy constructor\n");
#endif //MAO_MULTI_COMPILER
    aesrng_initialize_to_empty(&ctx);
    memcpy(&ctx, &a.ctx, sizeof(aesrng_context));
    ctx->key = new uint8_t[a.ctx->keylength];
    memcpy(ctx->key, &a.ctx->key, a.ctx->keylength);
}

AESRandomNumberGenerator::~AESRandomNumberGenerator()
{
    if(multicompiler::RNGStateFile != ""){
        writeStateFile();
    }
    aesrng_destroy(ctx);
}

void AESRandomNumberGenerator::readStateFile()
{
#ifndef MAO_MULTI_COMPILER
    DEBUG(errs() << "Reading RNG state file from " << multicompiler::RNGStateFile << "\n");
#endif //MAO_MULTI_COMPILER
    aesrng_restore_state(ctx, multicompiler::RNGStateFile.c_str());
}

void AESRandomNumberGenerator::writeStateFile()
{
#ifndef MAO_MULTI_COMPILER
    DEBUG(errs() << "Writing RNG state file to " << multicompiler::RNGStateFile << "\n");
#endif //MAO_MULTI_COMPILER
    aesrng_write_state(ctx, multicompiler::RNGStateFile.c_str());
}

uint64_t AESRandomNumberGenerator::random()
{
    assert(ctx != NULL);
#ifndef MAO_MULTI_COMPILER
    RandomNumbersGenerated++;
#endif //MAO_MULTI_COMPILER
    return aesrng_random_u64(ctx);
}

uint64_t AESRandomNumberGenerator::randnext(uint64_t max)
{
    assert(ctx != NULL);
#ifndef MAO_MULTI_COMPILER
    RandomNumbersGenerated++;
#endif //MAO_MULTI_COMPILER
    return aesrng_random_u64(ctx) % max;
}

} // namespace Random

} // namespace multicompiler
