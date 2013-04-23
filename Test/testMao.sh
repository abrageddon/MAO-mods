LD_PRELOAD="/usr/lib/libprofiler.so" CPUPROFILE="/home/sneisius/Test/PROFILE.OUT"  /home/sneisius/bin/mao --mao=-T --mao=\
--plugin=/home/sneisius/lib/MaoMOVToLEA-x86_64-linux.so:MOVTOLEA=MultiCompilerSeed[1234567890]+MOVToLEAPercentage[30]:\
--plugin=/home/sneisius/lib/MaoNOPInsertion-x86_64-linux.so:NOPINSERTION=MultiCompilerSeed[1234567890]+NOPInsertionPercentage[30]:\
ASM=o[/home/sneisius/Test/vim.blob.div.s] /home/sneisius/Test/vim.blob.s
