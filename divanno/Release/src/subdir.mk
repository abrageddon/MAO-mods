################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../src/divanno.cpp 

OBJS += \
./src/divanno.o 

CPP_DEPS += \
./src/divanno.d 


# Each subdirectory must supply rules for building sources it contributes
src/%.o: ../src/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -DMAO_MULTI_COMPILER -D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS -I. -I/usr/include -O3 -Wall -c -std=c++11 -fPIC -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


