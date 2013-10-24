#ifndef PROCESSOR_NORMALIZE_NOPS
#define PROCESSOR_NORMALIZE_NOPS

#include <stdio.h>
#include <string>
#include <fstream>
#include <iostream>

//#include <vector>

#include "google_breakpad/common/breakpad_types.h"
//#include "google_breakpad/common/minidump_format.h"
//#include "google_breakpad/processor/stackwalker.h"
//#include "google_breakpad/processor/stack_frame_cpu.h"
//#include "processor/cfi_frame_info.h"
#include "processor/stackwalker_amd64.h"

namespace multicompiler{

uint64_t NormalizeAddress(string, uint64_t );

}
#endif //PROCESSOR_NORMALIZE_NOPS
