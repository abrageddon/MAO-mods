/*
 * =====================================================================================
 *
 *       Filename:  SkeinPBKDF2.h
 *
 *    Description:  Interface for PBKDF2 using Skein
 *
 *        Version:  1.0
 *        Created:  12/24/2011 03:03:20 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Todd Jackson
 *        Company:
 *
 * =====================================================================================
 */

#ifndef SKEINPBKDF2_H_
#define SKEINPBKDF2_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

uint8_t *skein_pbkdf2(uint8_t const *password, const unsigned int pLen, uint8_t const *salt, const unsigned int sLen,
        const unsigned int iterations, const unsigned int dkLen);

#ifdef __cplusplus
}
#endif

#endif
