
## Authors 

Ethan Wagner, Nick Ambrose

## About

The Memory Simulator, is a Python script designed to emulate the functionalities of a computer's memory system. This simulator
   translates logical memory addresses into physical addresses, while also replicating the operations of critical components such as the 
   Translation-Lookaside-Buffer (TLB), Page Table, Disk, and RAM. A focal point of the simulator is its tracking of page faults and TLB hits, 
   allowing us to analize the effectivness of different page replacement algorithms. It incorporates three page replacement algorithms, including 
   First In First Out (FIFO), Least Recently Used (LRU), and Optimal.

## Usage
python3 memSim <reference-sequence-file.txt> <FRAMES> <PRA>