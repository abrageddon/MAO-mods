#ifndef _SKEIN_PORT_H_
#define _SKEIN_PORT_H_
/*******************************************************************
**
** Platform-specific definitions for Skein hash function.
**
** Source code author: Doug Whiting, 2008.
**
** This algorithm and source code is released to the public domain.
**
** Many thanks to Brian Gladman for his portable header files, which
** have been modified slightly here, to handle a few more platforms.
**
** To port Skein to an "unsupported" platform, change the definitions
** in this file appropriately.
**
********************************************************************/

/*#include "brg_types.h"*/                      /* get integer type definitions */

typedef unsigned int    uint_t;             /* native unsigned integer */
typedef uint8_t         u08b_t;             /*  8-bit unsigned integer */
typedef uint64_t        u64b_t;             /* 64-bit unsigned integer */

/*
 * Skein is "natively" little-endian (unlike SHA-xxx), for optimal
 * performance on x86 CPUs.  The Skein code requires the following
 * definitions for dealing with endianness:
 *
 *    Skein_Put64_LSB_First
 *    Skein_Get64_LSB_First
 *    Skein_Swap64
 *
 * In the reference code, these functions are implemented in a
 * very portable (and thus slow) fashion, for clarity. See the file
 * "skein_port.h" in the Optimized_Code directory for ways to make
 * these functions fast(er) on x86 platforms.
 */

uint64_t Skein_Swap64(uint64_t w64);
void     Skein_Put64_LSB_First(uint8_t *dst,const uint64_t *src,size_t bCnt);
void     Skein_Get64_LSB_First(uint64_t *dst,const uint8_t *src,size_t wCnt);

#endif   /* ifndef _SKEIN_PORT_H_ */
