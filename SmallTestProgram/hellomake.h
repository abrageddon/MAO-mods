/*
example include file
*/
#ifndef HELLOMAKE_H
#define HELLOMAKE_H

#include "client/linux/handler/exception_handler.h"

static bool dumpCallback(const google_breakpad::MinidumpDescriptor& descriptor, void* context, bool succeeded)
{
  printf("Dump path: %s\n", descriptor.path());
  return succeeded;
}

static void crash(){
  volatile int* a = (int*)(NULL);
  *a = 1;
}

void myPrintHelloMake(void);

#endif //HELLOMAKE_H
