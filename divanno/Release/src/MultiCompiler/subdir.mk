################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../src/MultiCompiler/AESCounterModeRNG.cpp \
../src/MultiCompiler/AESRandomNumberGenerator.cpp \
../src/MultiCompiler/MultiCompilerOptions.cpp \
../src/MultiCompiler/Rand48.cpp \
../src/MultiCompiler/Random.cpp \
../src/MultiCompiler/Skein.cpp \
../src/MultiCompiler/SkeinBlock.cpp \
../src/MultiCompiler/SkeinPBKDF2.cpp 

OBJS += \
./src/MultiCompiler/AESCounterModeRNG.o \
./src/MultiCompiler/AESRandomNumberGenerator.o \
./src/MultiCompiler/MultiCompilerOptions.o \
./src/MultiCompiler/Rand48.o \
./src/MultiCompiler/Random.o \
./src/MultiCompiler/Skein.o \
./src/MultiCompiler/SkeinBlock.o \
./src/MultiCompiler/SkeinPBKDF2.o 

CPP_DEPS += \
./src/MultiCompiler/AESCounterModeRNG.d \
./src/MultiCompiler/AESRandomNumberGenerator.d \
./src/MultiCompiler/MultiCompilerOptions.d \
./src/MultiCompiler/Rand48.d \
./src/MultiCompiler/Random.d \
./src/MultiCompiler/Skein.d \
./src/MultiCompiler/SkeinBlock.d \
./src/MultiCompiler/SkeinPBKDF2.d 


# Each subdirectory must supply rules for building sources it contributes
src/MultiCompiler/%.o: ../src/MultiCompiler/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -DMAO_MULTI_COMPILER -D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS -I. -I/usr/include -O3 -Wall -c -std=c++11 -fPIC -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


