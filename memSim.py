from typing import List, Dict
import argparse

class TLB: # pretty much just a cache, FIFO
    def __init__(self, size: int=16):
        self.size = size
        self.tlb = [None] * size
        self.evictionIndex = 0 # need to keep track of what we want to evict

    def add(self, pageNumber: int, frameNumber: int):
        # if the tlb is full, remove the first element
        if len(self.tlb) < self.size: # if the tlb is not full
            self.tlb.append((pageNumber, frameNumber))
        else: # if the tlb is full
            self.tlb[self.evictionIndex] = (pageNumber, frameNumber)
            self.evictionIndex = (self.evictionIndex + 1) % self.size

class PageTableFIFO: # include a loaded bit for each entry
    def __init__(self, size: int=2**8, algorithm: str="fifo"):
        self.size = size
        self.pageTable = {}
class PageTableOPT: # include a loaded bit for each entry
    def __init__(self, size: int=2**8, algorithm: str="fifo"):
        self.size = size
        self.pageTable = {}
class PageTablLRU: # include a loaded bit for each entry
    def __init__(self, size: int=2**8, algorithm: str="fifo"):
        self.size = size
        self.pageTable = {}

class Disk: # AKA Backing Store
    def __init__(self, size: int):
        self.size = size
        self.disk = {}

class RAM: # AKA Physical Memory
    def __init__(self, size: int):
        self.size = size
        self.ram = {}


    

# Main will do all the simulation logic, prob should use helper functions.
def main():
    parser = argparse.ArgumentParser(description="Memory Simulator")
    # Required argument for reference-sequence-file.txt
    parser.add_argument("reference_sequence_file", type=str,
                        help="File containing the list of logical memory addresses")
    # Optional argument for FRAMES with a default value of 256
    parser.add_argument("frames", type=int, nargs="?", default=256,
                        help="Number of frames in the system. Default is 256.")
    # Optional argument for PRA with a default value of "fifo"
    parser.add_argument("pra", type=str, choices=["fifo", "lru", "opt"], nargs="?", default="fifo",
                        help="Page Replacement Algorithm. Choices are 'fifo', 'lru', or 'opt'. Default is 'fifo'.")
    args = parser.parse_args()
    



if __name__ == "__main__":
    main()