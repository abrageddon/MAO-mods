#!/bin/bash
#=========================================================
# MAO Sources
#=========================================================

# UBUNTU required packages
sudo apt-get install build-essentials autoconf automake texinfo zlib1g-dev bison flex


# Set target to i686-linux or x86_64
TARGET=x86_64-linux

# On MacOS, please set the following required flag:
# BINUTILS_CONF_FLAGS=-disable-nls
# otherwise, clear the flag:
BINUTILS_CONF_FLAGS=

#Only for inital, dir is already created and we are in it
#mkdir MAO
#cd MAO

# If you haven't downloaded the source for mao:
# See http://code.google.com/p/mao/source/checkout for more info
svn checkout http://mao.googlecode.com/svn/trunk/ .

#=========================================================
# GNU Binutils sources
#=========================================================
# Fetch and patch binutils sources.
#    (note: sometimes updates are being uploaded to the ftp
#           please check for latest versions)
#
#    (note: Some Apple OS X systems don't have wget installed. Either
#           install it, or set this alias:
#           alias wget="curl -O"
#
wget http://ftp.gnu.org/gnu/binutils/binutils-2.22.tar.bz2
tar xjvf binutils-2.22.tar.bz2
(cd binutils-2.22 && patch -p1  < ../data/binutils-2.22-mao.patch)

# Configure modified binutils.
#  note: make -j 4 spawn parallel make, 4 processes. Increase
#        or decrease, according to your needs and system
(mkdir binutils-2.22-obj-${TARGET}
cd binutils-2.22-obj-${TARGET}
../binutils-2.22/configure --target=${TARGET} ${BINUTILS_CONF_FLAGS}
make -j4)

#=========================================================
# Build MAO
#=========================================================
# Please check the Makefile, as it contains a reference to the binutils
# directory. Update, if necessary
#
cd src

make -j4 TARGET=${TARGET}
#or
#make -j 4 TARGET=${TARGET} OS=MacOS
