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
 * Modified to act as random number generator by Todd Jackson
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>

#include "AESCounterModeRNG.h"
#include "MultiCompilerOptions.h"
#include "Random.h"
#include "SkeinPBKDF2.h"

static const int INVALID_KEY_LENGTH = -0x0800;
static const int INVALID_INPUT_LENGTH = -0x0810;

static unsigned int aes_init_done = 0;

/* Round Constants */
uint32_t RCON[10];

/*
 * Forward S-box & tables
 */
uint8_t FSb[256];
uint32_t FT0[256];
uint32_t FT1[256];
uint32_t FT2[256];
uint32_t FT3[256];

/*
 * 32-bit integer manipulation macros (little endian)
 */
#ifndef GET_ULONG_LE
#define GET_ULONG_LE(n,b,i)                             \
		{                                                       \
			(n) = ( (uint32_t) (b)[(i)    ]       )        \
			| ( (uint32_t) (b)[(i) + 1] <<  8 )        \
			| ( (uint32_t) (b)[(i) + 2] << 16 )        \
			| ( (uint32_t) (b)[(i) + 3] << 24 );       \
		}
#endif

#ifndef PUT_ULONG_LE
#define PUT_ULONG_LE(n,b,i)                             \
		{                                                       \
			(b)[(i)    ] = (unsigned char) ( (n)       );       \
			(b)[(i) + 1] = (unsigned char) ( (n) >>  8 );       \
			(b)[(i) + 2] = (unsigned char) ( (n) >> 16 );       \
			(b)[(i) + 3] = (unsigned char) ( (n) >> 24 );       \
		}
#endif

/*
 * Tables generation code
 */
#define ROTL8(x) ( ( x << 8 ) & 0xFFFFFFFF ) | ( x >> 24 )
#define XTIME(x) ( ( x << 1 ) ^ ( ( x & 0x80 ) ? 0x1B : 0x00 ) )
#define MUL(x,y) ( ( x && y ) ? pow[(log[x]+log[y]) % 255] : 0 )


void incrementBigEndianUInt64(uint8_t* val)
{
    if (val[7] == 0xff) {
        val[7] = 0x00;
        val[6]++;
    } else if (val[7] == 0xff && val[6] == 0xff) {
        val[7] = val[6] = 0x00;
        val[5]++;
    } else if (val[7] == 0xff && val[6] == 0xff && val[5] == 0xff) {
        val[7] = val[6] = val[5] = 0x00;
        val[4]++;
    } else if (val[7] == 0xff && val[6] == 0xff && val[5] == 0xff && val[4] == 0xff) {
        val[7] = val[6] = val[5] = val[4] = 0x00;
        val[3]++;
    } else if (val[7] == 0xff && val[6] == 0xff && val[5] == 0xff && val[4] == 0xff
               && val[2] == 0xff) {
        val[7] = val[6] = val[5] = val[4] = val[3] = val[2] = 0x00;
        val[1]++;
    } else if (val[7] == 0xff && val[6] == 0xff && val[5] == 0xff && val[4] == 0xff
               && val[2] == 0xff && val[1] == 0xff) {
        val[7] = val[6] = val[5] = val[4] = val[3] = val[2] = val[1] = 0x00;
        val[0]++;
    } else if (val[7] == 0xff && val[6] == 0xff && val[5] == 0xff && val[4] == 0xff
               && val[2] == 0xff && val[1] == 0xff && val[0] == 0xff) {
        memset(val, 0x00, 8);
    } else val[7]++;
}

void aes_gen_tables(void)
{
    int32_t i, x, y, z;
    int32_t pow[256];
    int32_t log[256];

    /*
     * compute pow and log tables over GF(2^8)
     */
    for ( i = 0, x = 1; i < 256; i++ ) {
        pow[i] = x;
        log[x] = i;
        x = ( x ^ XTIME( x ) ) & 0xFF;
    }

    /*
     * calculate the round constants
     */
    for ( i = 0, x = 1; i < 10; i++ ) {
        RCON[i] = (uint32_t) x;
        x = XTIME( x ) & 0xFF;
    }

    /*
     * generate the forward and reverse S-boxes
     */
    FSb[0x00] = 0x63;

    for ( i = 1; i < 256; i++ ) {
        x = pow[255 - log[i]];

        y  = x;
        y = ( (y << 1) | (y >> 7) ) & 0xFF;
        x ^= y;
        y = ( (y << 1) | (y >> 7) ) & 0xFF;
        x ^= y;
        y = ( (y << 1) | (y >> 7) ) & 0xFF;
        x ^= y;
        y = ( (y << 1) | (y >> 7) ) & 0xFF;
        x ^= y ^ 0x63;

        FSb[i] = (unsigned char) x;
    }

    /*
     * generate the forward and reverse tables
     */
    for ( i = 0; i < 256; i++ ) {
        x = FSb[i];
        y = XTIME( x ) & 0xFF;
        z =  ( y ^ x ) & 0xFF;

        FT0[i] = ( (uint32_t) y       ) ^
                 ( (uint32_t) x <<  8 ) ^
                 ( (uint32_t) x << 16 ) ^
                 ( (uint32_t) z << 24 );

        FT1[i] = ROTL8( FT0[i] );
        FT2[i] = ROTL8( FT1[i] );
        FT3[i] = ROTL8( FT2[i] );
    }
}

void aes_gen_round_keys(aesrng_context* ctx)
{
    uint32_t *RK;
    uint32_t i;
    uint32_t keysize = ctx->keylength * 8;
    RK = ctx->buf;

    for ( i = 0; i < (keysize >> 5); i++ ) {
        GET_ULONG_LE( RK[i], ctx->key, i << 2 );
    }

    switch(ctx->nr) {
    case 10:
        for ( i = 0; i < 10; i++, RK += 4 ) {
            RK[4]  = RK[0] ^ RCON[i] ^
                     ( (uint32_t) FSb[ ( RK[3] >>  8 ) & 0xFF ]       ) ^
                     ( (uint32_t) FSb[ ( RK[3] >> 16 ) & 0xFF ] <<  8 ) ^
                     ( (uint32_t) FSb[ ( RK[3] >> 24 ) & 0xFF ] << 16 ) ^
                     ( (uint32_t) FSb[ ( RK[3]       ) & 0xFF ] << 24 );

            RK[5]  = RK[1] ^ RK[4];
            RK[6]  = RK[2] ^ RK[5];
            RK[7]  = RK[3] ^ RK[6];
        }
        break;
    case 12:
        for ( i = 0; i < 8; i++, RK += 6 ) {
            RK[6]  = RK[0] ^ RCON[i] ^
                     ( (uint32_t) FSb[ ( RK[5] >>  8 ) & 0xFF ]       ) ^
                     ( (uint32_t) FSb[ ( RK[5] >> 16 ) & 0xFF ] <<  8 ) ^
                     ( (uint32_t) FSb[ ( RK[5] >> 24 ) & 0xFF ] << 16 ) ^
                     ( (uint32_t) FSb[ ( RK[5]       ) & 0xFF ] << 24 );

            RK[7]  = RK[1] ^ RK[6];
            RK[8]  = RK[2] ^ RK[7];
            RK[9]  = RK[3] ^ RK[8];
            RK[10] = RK[4] ^ RK[9];
            RK[11] = RK[5] ^ RK[10];
        }
        break;
    case 14:
        for ( i = 0; i < 7; i++, RK += 8 ) {
            RK[8]  = RK[0] ^ RCON[i] ^
                     ( (uint32_t) FSb[ ( RK[7] >>  8 ) & 0xFF ]       ) ^
                     ( (uint32_t) FSb[ ( RK[7] >> 16 ) & 0xFF ] <<  8 ) ^
                     ( (uint32_t) FSb[ ( RK[7] >> 24 ) & 0xFF ] << 16 ) ^
                     ( (uint32_t) FSb[ ( RK[7]       ) & 0xFF ] << 24 );

            RK[9]  = RK[1] ^ RK[8];
            RK[10] = RK[2] ^ RK[9];
            RK[11] = RK[3] ^ RK[10];

            RK[12] = RK[4] ^
                     ( (uint32_t) FSb[ ( RK[11]       ) & 0xFF ]       ) ^
                     ( (uint32_t) FSb[ ( RK[11] >>  8 ) & 0xFF ] <<  8 ) ^
                     ( (uint32_t) FSb[ ( RK[11] >> 16 ) & 0xFF ] << 16 ) ^
                     ( (uint32_t) FSb[ ( RK[11] >> 24 ) & 0xFF ] << 24 );

            RK[13] = RK[5] ^ RK[12];
            RK[14] = RK[6] ^ RK[13];
            RK[15] = RK[7] ^ RK[14];
        }
        break;
    default:
        break;
    }
}

int aes_set_rounds(aesrng_context* ctx)
{
    switch (ctx->keylength) {
    case 16:
        ctx->nr = 10;
        break;
    case 24:
        ctx->nr = 12;
        break;
    case 32:
        ctx->nr = 14;
        break;
    default:
        return INVALID_KEY_LENGTH;
    }
    return 0;
}

/*
 * AES key schedule (encryption)
 */
int aes_setkey_enc(aesrng_context* ctx)
{
    if(aes_init_done == 0){
        aes_gen_tables();
        aes_init_done = 1;
    }

    aes_set_rounds(ctx);

    ctx->rk = ctx->buf;

    aes_gen_round_keys(ctx);

    return 0;
}

#define AES_FROUND(X0,X1,X2,X3,Y0,Y1,Y2,Y3)     \
		{                                               \
			X0 = *RK++ ^ FT0[ ( Y0       ) & 0xFF ] ^   \
			FT1[ ( Y1 >>  8 ) & 0xFF ] ^   \
			FT2[ ( Y2 >> 16 ) & 0xFF ] ^   \
			FT3[ ( Y3 >> 24 ) & 0xFF ];    \
			\
			X1 = *RK++ ^ FT0[ ( Y1       ) & 0xFF ] ^   \
			FT1[ ( Y2 >>  8 ) & 0xFF ] ^   \
			FT2[ ( Y3 >> 16 ) & 0xFF ] ^   \
			FT3[ ( Y0 >> 24 ) & 0xFF ];    \
			\
			X2 = *RK++ ^ FT0[ ( Y2       ) & 0xFF ] ^   \
			FT1[ ( Y3 >>  8 ) & 0xFF ] ^   \
			FT2[ ( Y0 >> 16 ) & 0xFF ] ^   \
			FT3[ ( Y1 >> 24 ) & 0xFF ];    \
			\
			X3 = *RK++ ^ FT0[ ( Y3       ) & 0xFF ] ^   \
			FT1[ ( Y0 >>  8 ) & 0xFF ] ^   \
			FT2[ ( Y1 >> 16 ) & 0xFF ] ^   \
			FT3[ ( Y2 >> 24 ) & 0xFF ];    \
		}

/*
 * AES-ECB block encryption/decryption
 */
int aes_crypt_ecb(aesrng_context *ctx, const unsigned char input[16], unsigned char output[16])
{
    int i;
    uint32_t *RK, X0, X1, X2, X3, Y0, Y1, Y2, Y3;

    RK = ctx->rk;

    GET_ULONG_LE( X0, input,  0 );
    X0 ^= *RK++;
    GET_ULONG_LE( X1, input,  4 );
    X1 ^= *RK++;
    GET_ULONG_LE( X2, input,  8 );
    X2 ^= *RK++;
    GET_ULONG_LE( X3, input, 12 );
    X3 ^= *RK++;

        for ( i = (ctx->nr >> 1) - 1; i > 0; i-- ) {
            AES_FROUND( Y0, Y1, Y2, Y3, X0, X1, X2, X3 );
            AES_FROUND( X0, X1, X2, X3, Y0, Y1, Y2, Y3 );
        }

        AES_FROUND( Y0, Y1, Y2, Y3, X0, X1, X2, X3 );

        X0 = *RK++ ^ \
             ( (uint32_t) FSb[ ( Y0       ) & 0xFF ]       ) ^
             ( (uint32_t) FSb[ ( Y1 >>  8 ) & 0xFF ] <<  8 ) ^
             ( (uint32_t) FSb[ ( Y2 >> 16 ) & 0xFF ] << 16 ) ^
             ( (uint32_t) FSb[ ( Y3 >> 24 ) & 0xFF ] << 24 );

        X1 = *RK++ ^ \
             ( (uint32_t) FSb[ ( Y1       ) & 0xFF ]       ) ^
             ( (uint32_t) FSb[ ( Y2 >>  8 ) & 0xFF ] <<  8 ) ^
             ( (uint32_t) FSb[ ( Y3 >> 16 ) & 0xFF ] << 16 ) ^
             ( (uint32_t) FSb[ ( Y0 >> 24 ) & 0xFF ] << 24 );

        X2 = *RK++ ^ \
             ( (uint32_t) FSb[ ( Y2       ) & 0xFF ]       ) ^
             ( (uint32_t) FSb[ ( Y3 >>  8 ) & 0xFF ] <<  8 ) ^
             ( (uint32_t) FSb[ ( Y0 >> 16 ) & 0xFF ] << 16 ) ^
             ( (uint32_t) FSb[ ( Y1 >> 24 ) & 0xFF ] << 24 );

        X3 = *RK++ ^ \
             ( (uint32_t) FSb[ ( Y3       ) & 0xFF ]       ) ^
             ( (uint32_t) FSb[ ( Y0 >>  8 ) & 0xFF ] <<  8 ) ^
             ( (uint32_t) FSb[ ( Y1 >> 16 ) & 0xFF ] << 16 ) ^
             ( (uint32_t) FSb[ ( Y2 >> 24 ) & 0xFF ] << 24 );
    PUT_ULONG_LE( X0, output,  0 );
    PUT_ULONG_LE( X1, output,  4 );
    PUT_ULONG_LE( X2, output,  8 );
    PUT_ULONG_LE( X3, output, 12 );

    return( 0 );
}

void aesrng_initialize_to_default(aesrng_context** ctx)
{
    const uint8_t default_key[] = {0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6, 0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c};
    const uint8_t default_plaintext[] = {0x6b, 0xc1, 0xbe, 0xe2, 0x2e, 0x40, 0x9f, 0x96, 0xe9, 0x3d, 0x7e, 0x11, 0x73, 0x93, 0x17, 0x2a};
    const uint8_t default_testvector[] = {0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9, 0xfa, 0xfb, 0xfc, 0xfd, 0xfe, 0xff};

    *ctx = (aesrng_context*)malloc(sizeof(aesrng_context));
    (*ctx)->keylength = 16;
    (*ctx)->key = (uint8_t*)malloc((*ctx)->keylength * sizeof(uint8_t));
    (*ctx)->counter = 0;
    (*ctx)->reseed_counter = 0;
    memcpy((*ctx)->key, default_key, (*ctx)->keylength * sizeof(uint8_t));
    memcpy((*ctx)->nonce, default_testvector, 8 * sizeof(uint8_t));
    memcpy(&((*ctx)->counter), default_testvector + 8, sizeof(uint64_t));
    memcpy((*ctx)->plaintext, default_plaintext, 16 * sizeof(uint8_t));

    aes_setkey_enc(*ctx);
}

void aesrng_initialize(aesrng_context** ctx, uint64_t counter, uint16_t keylength)
{
    (*ctx) = (aesrng_context*)malloc(sizeof(aesrng_context));
    (*ctx)->counter = counter;
    (*ctx)->reseed_counter = 0;
    (*ctx)->keylength = keylength;
}

void aesrng_initialize_to_empty(aesrng_context** ctx)
{
    (*ctx) = (aesrng_context*)malloc(sizeof(aesrng_context));
    memset(*ctx, 0x00, sizeof(aesrng_context));
}

void aesrng_initialize_with_random_data(aesrng_context** ctx, unsigned int keylen,
        uint8_t const* password, unsigned int passwordlen, uint64_t salt)
{
    (*ctx) = (aesrng_context*)malloc(sizeof(aesrng_context));
    unsigned int length = 16 /* plaintext */ + 2 * sizeof(uint64_t) /* nonce, counter */;
    if(keylen != 16 && keylen != 20 && keylen != 24){
        printf("Invalid keylength! Defaulting to 16\n");
        keylen = 16;
    }
    length += keylen;

    uint8_t *randomdata = skein_pbkdf2(password, passwordlen, (uint8_t*)&salt,
            sizeof(uint64_t), DEFAULT_KDF_ITERATIONS, length);

    (*ctx)->keylength = keylen;
    (*ctx)->reseed_counter = 0;
    (*ctx)->key = (uint8_t*)malloc((*ctx)->keylength * sizeof(uint8_t));
    memcpy((*ctx)->key, randomdata, keylen);
    memcpy((*ctx)->nonce, randomdata + keylen, sizeof(uint64_t));
    memcpy(&((*ctx)->counter), randomdata + keylen + 8, sizeof(uint64_t));
    memcpy((*ctx)->plaintext, randomdata + keylen + 2 * sizeof(uint64_t), 16);

    aes_setkey_enc(*ctx);
    delete[] randomdata;
}

void aesrng_destroy(aesrng_context* ctx)
{
    free(ctx->key);
    free(ctx);
}

void aesrng_restore_state(aesrng_context* ctx, const char* filename)
{
    struct stat s;
    /* Don't read if there's no file specified.
     * TODO(tmjackso): This probably shouldn't fail silently. */
    if (filename == NULL || stat(filename, &s) != 0) {
        return;
    }

    int fhandle = open(filename, O_RDONLY);
    int bytes_read = 0;

    /* uint16_t: keysize */
    bytes_read += read(fhandle, (char *)&(ctx->keylength), sizeof(uint16_t));

    /* Create key, now that we know how big it is */
    ctx->key = (uint8_t *)malloc(ctx->keylength * sizeof(uint8_t));

    /* keylength * uint8_t: key */
    bytes_read += read(fhandle, (char *)(ctx->key), ctx->keylength * sizeof(uint8_t));

    /* 16 * uint8_t: plaintext */
    bytes_read += read(fhandle, (char *)(ctx->plaintext), 16 * sizeof(uint8_t));

    /* 8 * uint8_t: nonce */
    bytes_read += read(fhandle, (char *)(ctx->nonce), 8 * sizeof(uint8_t));

    /* uint64_t: counter */
    bytes_read += read(fhandle, (char *)&(ctx->counter), sizeof(uint64_t));

    if (bytes_read != s.st_size) {
        // We didn't read the whole file
        printf("Warning: Did not read the entire state file!\n");
    }
    ctx->rk = ctx->buf;

    ctx->reseed_counter = 0;

    /* Global AES init */
    if(aes_init_done == 0) {
        aes_gen_tables();
        aes_init_done = 1;
    }

    aes_set_rounds(ctx);
    aes_gen_round_keys(ctx);
}

void aesrng_write_state(aesrng_context* ctx, const char* filename)
{
    /* Don't serialise without a file name */
    if (filename == NULL) return;

    int fhandle = open(filename, O_WRONLY);
    int byte_count = 0;
    byte_count += write(fhandle, (char *)&(ctx->keylength), sizeof(uint16_t));
    byte_count += write(fhandle, (char *)(ctx->key), ctx->keylength * sizeof(uint8_t));
    byte_count += write(fhandle, (char *)(ctx->plaintext), 16 * sizeof(uint8_t));
    byte_count += write(fhandle, (char *)(ctx->nonce), 8 * sizeof(uint8_t));
    byte_count += write(fhandle, (char *)&(ctx->counter), sizeof(uint64_t));
}

void aesrng_random_u128(aesrng_context* ctx, uint128_t* val)
{
    uint8_t input[16];
    uint8_t output[16];
    int i;

    memcpy(input, (char *)ctx->nonce, sizeof(uint64_t));
    memcpy(input + 8, (char *)&(ctx->counter), sizeof(uint64_t));
    aes_crypt_ecb(ctx, input, output);
    for (i = 0; i < 16; i++) output[i] ^= ctx->plaintext[i];
    memcpy((char *)&(val->hi), (char *)output, sizeof(uint64_t));
    memcpy((char *)&(val->lo), (char *)(output + 8), sizeof(uint64_t));

    /* Counter increment */
    incrementBigEndianUInt64((uint8_t *)&(ctx->counter));
    ctx->reseed_counter++;

    if(ctx->reseed_counter == RESEED_INTERVAL){
        printf("Warning: Reseeding required...");
        memcpy(input, (char *)ctx->nonce, sizeof(uint64_t));
        memcpy(input + 8, (char *)&(ctx->counter), sizeof(uint64_t));
        aes_crypt_ecb(ctx, input, output);
        for(i = 0; i < 16; i++) output[i] ^= ctx->plaintext[i];

        printf("Reseeding...\n");
        //TODO(tmjackso): Assert that Seed is actually defined.
        aesrng_initialize_with_random_data(&ctx, ctx->keylength, output, 16, multicompiler::Random::Seed);
    }
}

uint64_t aesrng_random_u64(aesrng_context* ctx)
{
    uint128_t val;
    aesrng_random_u128(ctx, &val);
    return val.lo;
}

uint32_t aesrng_random_u32(aesrng_context* ctx)
{
    uint128_t val;
    uint32_t i;
    aesrng_random_u128(ctx, &val);
    memcpy((char *)&i, (char *)(val.lo + 4), sizeof(uint32_t));
    return i;
}
