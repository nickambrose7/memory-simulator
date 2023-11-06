from typing import List, Dict
from queue import Queue
import argparse

PAGE_TABLE_SIZE = 2**8
PAGE_SIZE = 2**8 # bytes
FRAME_SIZE = PAGE_SIZE
DISK_SIZE = PAGE_TABLE_SIZE * PAGE_SIZE # bytes
TLB_SIZE = 16

class TLB: # pretty much just a cache, FIFO
    def __init__(self, size: int=TLB_SIZE):
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

class PageTable: # include a loaded bit for each entry
    def __init__(self, size: int=PAGE_TABLE_SIZE):
        self.size = size
        self.pageTable = {}

class Disk: # AKA Backing Store
    def __init__(self, size: int=DISK_SIZE):
        self.size = size
        self.disk = {}

class RAM: # AKA Physical Memory
    def __init__(self, size: int):
        self.size = size
        self.ram = {}

class PTEntry: # page table entry has frame number and loaded bit, the page number is the index of the entry
    def __init__(self, frame: int):
        self.frame = None
        self.loaded = 0    

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
    
    # get frames from args
    frames = args.frames

    #initialize page table
    pt = PageTable()
    #initialize tlb
    tlb = TLB()
    #initialize ram
    memory = RAM(size=frames)
    #initialize disk
    disk = Disk()

    # open file to read
    f = open(args.reference_sequence_file, 'r')

    if args.pra == "lru": # least recently used
        # lru counters
        lru_counter = [0]*256
        fifo = Queue(maxsize=frames) # to break ties, but could also just use the first value that pops out of min?
        # while loop that goes through the addresses
            # increment counter for this page
        # check tlb, check loaded bit

        #check page table, check loaded bit
            # if hit go to memory
            # get value

            #else 
                # page swap
                    # check for free frames
                    # get least from lru_counter that is in memory currently
                    # remove from memory
                    # add disk page into memory
                # restart instruction
    
    elif args.pra == "opt": # optimal replacement
        fifo = Queue(maxsize=frames) # to break ties, but could also just use the first value that pops out of min?
        # read all of addresses.txt
            # do conversions and add all instances of each page
            # store in array
        # while loop that goes through the addresses
            # decement counter for this page
        # check tlb, check loaded bit

        #check page table, check loaded bit
            # if hit go to memory
            # get value

            #else 
                # page swap
                    # check for free frames
                    # get least from lru_counter that is in memory currently
                    # remove from memory
                    # add disk page into memory
                # restart instruction
        pass
    
    else:   # first in first out
        # fifo queue
        fifo = Queue(maxsize=frames)

        # while loop that goes through the addresses

        # check tlb, check loaded bit

        #check page table, check loaded bit
            # if hit go to memory
            # get value

            #else 
                # page swap
                    # pop queue
                    # remove from memory
                    # add disk page into memory
                # restart instruction
    f.close()

if __name__ == "__main__":
    main()