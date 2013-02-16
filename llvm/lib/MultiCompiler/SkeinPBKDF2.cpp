/*
 * =====================================================================================
 *
 *       Filename:  skein_test.c
 *
 *    Description:  Prototype program for using Skein
 *
 *        Version:  1.0
 *        Created:  12/10/2011 14:38:03
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Todd Jackson
 *        Company:
 *
 * =====================================================================================
 */
#include <math.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "llvm/MultiCompiler/Skein.h"
#include "llvm/MultiCompiler/SkeinPBKDF2.h"

const unsigned int SKEIN_512_512_BITLENGTH = 512;
const unsigned int SKEIN_512_512_BYTELENGTH = 64;
const unsigned int SKEIN_512_512_BLOCKSIZE = 64;

void skein_hash(const uint8_t * const data, const unsigned int length,
        uint8_t * const output) {
    Skein_512_Ctxt_t ctx;
    Skein_512_Init(&ctx, SKEIN_512_512_BITLENGTH);
    Skein_512_Update(&ctx, data, length);
    Skein_512_Final(&ctx, output);
}

void skein_hmac(const uint8_t * const password,
        const unsigned int passwordlen, const uint8_t * const salt,
        const unsigned int saltlen, uint8_t * const output) {

    uint8_t key[SKEIN_512_512_BLOCKSIZE];
    unsigned int keylength = passwordlen;

    // Shrink password to block size if necessary by hashing
    if(passwordlen > SKEIN_512_512_BLOCKSIZE){
        skein_hash(password, passwordlen, key);
        keylength = SKEIN_512_512_BYTELENGTH;
    }

    // Stretch password to block size if necessary by zero padding
    if(passwordlen < SKEIN_512_512_BLOCKSIZE){
        memset(key, 0x00, SKEIN_512_512_BLOCKSIZE);
        memcpy(key, password, passwordlen);
        keylength = SKEIN_512_512_BLOCKSIZE;
    }

    uint8_t o_key_pad[SKEIN_512_512_BLOCKSIZE];
    uint8_t i_key_pad[SKEIN_512_512_BLOCKSIZE];

    for(unsigned int i = 0; i < keylength; i++){
        o_key_pad[i] = 0x5c ^ key[i];
        i_key_pad[i] = 0x36 ^ key[i];
    }

    // Compute inner hash
    // hash(i_key_pad || message) == hash(i_key_pad || salt)
    // according to PBKDF2 spec
    uint8_t *inner_hash = new uint8_t[saltlen + SKEIN_512_512_BLOCKSIZE];
    memcpy(inner_hash, i_key_pad, SKEIN_512_512_BLOCKSIZE);
    memcpy(inner_hash + SKEIN_512_512_BLOCKSIZE, salt, saltlen);

    uint8_t outputblock[SKEIN_512_512_BYTELENGTH];
    skein_hash(inner_hash, saltlen + SKEIN_512_512_BLOCKSIZE, outputblock);

    // Compute outer hash
    // hash(o_key_pad || hash(i_key_pad || message))
    uint8_t outer_hash[SKEIN_512_512_BYTELENGTH + SKEIN_512_512_BLOCKSIZE];
    memcpy(outer_hash, o_key_pad, SKEIN_512_512_BLOCKSIZE);
    memcpy(outer_hash + SKEIN_512_512_BLOCKSIZE, outputblock,
            SKEIN_512_512_BLOCKSIZE);

    skein_hash(outer_hash, SKEIN_512_512_BYTELENGTH +
            SKEIN_512_512_BLOCKSIZE, output);

    delete[] inner_hash;
}

void skein_pbkdf2_F(const uint8_t * const password,
        const unsigned int passwordlen, const uint8_t * const salt,
        const unsigned int saltlen, const unsigned int iterations,
        const uint32_t index, uint8_t * const output){
    unsigned int i, j;
    uint8_t *prevblock = new uint8_t[SKEIN_512_512_BYTELENGTH];
    uint8_t *outputblock = new uint8_t[SKEIN_512_512_BYTELENGTH];

    /* First round
     * U_1 = PRF(password, salt || UINT32(index)
     * RFC 2898 says that iterations is a 4 byte encoding */
    unsigned int inputlen = saltlen + sizeof(index);
    uint8_t* input = new uint8_t[inputlen];
    memset(input, 0x00, inputlen);
    memcpy(input, salt, saltlen);
    memcpy(input + saltlen, &index, sizeof(index));

    //input[0] = 0xff;
    //inputlen = 1;

    /* Init and Do HMAC-Skein-512-512 */
    skein_hmac(password, passwordlen, input, inputlen, prevblock);

    memcpy(outputblock, prevblock, SKEIN_512_512_BYTELENGTH);

    /* Done with input...for now. Will use a new one inside the loop */
    delete[] input;

    uint8_t *tempdata = new uint8_t[SKEIN_512_512_BYTELENGTH];
    for(i = 0; i < iterations; i++){
        /* PRF(P, U_[i-1]) */
        skein_hmac(password, passwordlen, prevblock,
                SKEIN_512_512_BYTELENGTH, tempdata);

        /* XOR */
        for(j = 0; j < SKEIN_512_512_BYTELENGTH; j++){
            outputblock[j] ^= tempdata[j];
        }

        /* Save the previous block */
        memcpy(prevblock, tempdata, SKEIN_512_512_BYTELENGTH);
    }

    memcpy(output, outputblock, SKEIN_512_512_BYTELENGTH);

    delete[] prevblock;
    delete[] tempdata;
    delete[] outputblock;
}

/**
 * Driver function for Skein-based PBKDF2.
 *
 * password - Password data
 * pLen - Length of password in bytes
 * salt - Salt
 * sLen - Length of salt in bytes
 * iterations - Iteration count, a positive integer
 * dkLen - Desired output length in bytes
 */
uint8_t *skein_pbkdf2(uint8_t const *password, const unsigned int pLen, uint8_t const *salt, const unsigned int sLen,
        const unsigned int iterations, const unsigned int dkLen) {
    const unsigned int hLen = SKEIN_512_512_BYTELENGTH; /* Assume Skein 512-512 -- length of output in bytes */
    if(dkLen > (UINT32_MAX - 1) * hLen) {
        printf("Desired derived key too long\n");
        return NULL;
    }
    unsigned int i;

    /* Number of PRF blocks */
    const unsigned int l = ceil((float)dkLen / hLen);

    /* Number of bytes that get copied from a remainder block */
    const unsigned int r = dkLen - (l - 1) * hLen;

    uint8_t *output = new uint8_t[dkLen];
    uint8_t *h_block = new uint8_t[hLen];

    /* Generate l - 1 blocks */
    for(i = 0; i < l - 1; i++){
        skein_pbkdf2_F(password, pLen, salt, sLen, iterations, i + 1, h_block);
        memcpy(output + (hLen * i), h_block, hLen);
    }

    skein_pbkdf2_F(password, pLen, salt, sLen, iterations, l, h_block);

    /* Copy r bytes out of the remainder block */
    if(r > 0){
        memcpy(output + (hLen * (l - 1)), h_block, r);
    }
    else{
        memcpy(output + (hLen * (l - 1)), h_block, hLen);
    }

    delete[] h_block;
    return output;
}
