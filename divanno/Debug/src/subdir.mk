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
src/divanno.o: ../src/divanno.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -I/usr/include -I/usr/local/include -O0 -g3 -Wall -c -fmessage-length=0 -std=c++11 -MMD -MP -MF"$(@:%.o=%.d)" -MT"src/divanno.d" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


