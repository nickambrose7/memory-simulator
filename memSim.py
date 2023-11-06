from typing import List, Dict
from queue import Queue
import argparse

PAGE_TABLE_SIZE = 2**8
PAGE_SIZE = 2**8 # bytes
FRAME_SIZE = PAGE_SIZE
DISK_SIZE = PAGE_TABLE_SIZE * PAGE_SIZE # bytes
TLB_SIZE = 16


#Ethan's TLB:
# class TLB: # pretty much just a cache, FIFO TLB, might be better to make this a dictionary with key is page number better for searching
#     def __init__(self, size: int=TLB_SIZE):
#         self.size = size
#         self.tlb = {} #changed this to a dictionary 
#         self.evictionIndex = 0 # need to keep track of what we want to evict

#     def add(self, pageNumber: int, frameNumber: int):
#         # if the tlb is full, remove the first element
#         if len(self.tlb) < self.size: # if the tlb is not full
#             self.tlb[pageNumber] = frameNumber
#         else: # if the tlb is full
#             removal_key = list(self.tlb)[self.evictionIndex]
#             self.tlb.pop(removal_key)
#             self.tlb[pageNumber] = frameNumber
#             #self.evictionIndex = (self.evictionIndex + 1) % self.size  ### what does this do?
#             #  --> that's the FIFO part, it's a circular queue (or it used to be)

class TLB: 
    """
    Pretty much just a cache, FIFO. Implementing using a circular queue. 
    The .add() method will add a page, frame pair to the tlb.
    The .contains() method will check if a page is in the tlb.
    The .getitem() method will return the frame number associated with a page number.
    We are doing a linear search here becasue the tlb is small.
    """
    def __init__(self, size: int=16):
        self.size = size
        self.tlb = []
        self.evictionIndex = 0 # need to keep track of what we want to evict

    def add(self, pageNumber: int, frameNumber: int):
        # if the tlb is full, remove the first element
        if len(self.tlb) < self.size: # if the tlb is not full
            self.tlb.append((pageNumber, frameNumber))
        else: # if the tlb is full
            self.tlb[self.evictionIndex] = (pageNumber, frameNumber)
            self.evictionIndex = (self.evictionIndex + 1) % self.size
    def contains(self, pageNumber: int):
        for page, frame in self.tlb:
            if page == pageNumber:
                return True
        return False
    def getitem(self, pageNumber: int):
        for page, frame in self.tlb:
            if page == pageNumber:
                return frame
        return None # if not found


class PageTable: # include a loaded bit for each entry
    def __init__(self, size: int=PAGE_TABLE_SIZE):
        self.size = size
        self.pageTable = [PTEntry()] * size # list of PTEntries

class Disk:  # AKA Backing Store
    """
    The backing store can be represented by a dictionary of size 256
    where the key is the page number and the value is all 256 bytes in the frame.
    We can make the value an array of size 256, making it easy to offset into the frame.
    """
    def __init__(self, filename: str):
        self.disk = self.file_to_frames(filename)

    @staticmethod
    def file_to_frames(filename):
        frames = {}
        with open(filename, 'rb') as f:
            for i in range(256):
                frames[i] = list(f.read(256))
        return frames

class RAM: # AKA Physical Memory
    def __init__(self, size: int):
        self.size = size
        self.free = size # decrement free frames when adding intial pages
        self.ram = [None] * size # list of frames, each frame is a list/string of 256 bytes

class PTEntry:
    def __init__(self, frameNumber: int=None, loadedBit: int=0):
        self.frameNumber = frameNumber
        self.loadedBit = loadedBit 

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
    disk = Disk("BACKING_STORE.bin")

    # open file to read
    f = open(args.reference_sequence_file, 'r')

    # statistics to keep track of
    num_addr = 0
    page_faults = 0
    tlb_hits = 0
    tlb_misses = 0

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
        while address := f.readline() is not None:
            # increment addresses read
            num_addr+=1

            # page number
            p = address // PAGE_SIZE
            # page offset
            d = address % PAGE_SIZE

            # check tlb, check loaded bit
            inTLB = p in tlb.tlb
            if inTLB:
                tlb_hits+=1 # increment tlb_hits
                page = tlb.tlb[p] # get page, frame pair
                frame_number = page.frameNumber # get frame number from tlb
                frame_data = memory[frame_number]
                byte_data = frame_data[d]
                print(f'{address}, {byte_data}, {frame_number}, {"".join(frame_data)}\n')
                # Question: if a page#, frame# pair is in the tlb is it guarenteed to be in memory...do we need to check for page faulting here?
            
            else:
                # increment tlb_misses
                tlb_misses+=1
                #check page table, check loaded bit
                page = pt.pageTable[p]
                if page.loadedBit == 1: # if hit go to memory
                    frame_number = page.frameNumber # get frame number from tlb
                    frame_data = memory[frame_number]
                    byte_data = frame_data[d] # get value
                    print(f'{address}, {byte_data}, {frame_number}, {"".join(frame_data)}\n')
                
                else: # page fault
                    page_faults+=1
                    # check for free frames
                    if memory.free != 0:
                        free_index = frames - memory.free
                        memory[free_index] = disk[p]
                        memory.free-=1

                        # update pageTable
                        page.frameNumber = free_index
                        page.loadedBit = 1
                        pt[p] = page # necessary? I do not know if these things update in python --> don't think so.

                        # update tlb
                        tlb.add(p, free_index)

                        # put frame in queue
                        fifo.put(free_index)

                    else: # page swap
                        # pop queue
                        removal_index = fifo.pop()
                        # QUESTION: should we remove entries in the tlb if they correspond to this frame number?
                        # Nick's Answer-> I don't think so, the TLB keeps track of its own FIFO data structure.

                        # remove from memory - do this by overwriting with new page
                        # add disk page into memory
                        memory[removal_index] = disk[p]
                        memory.free-=1

                        # update pageTable
                        page.frameNumber = removal_index
                        page.loadedBit = 1
                        pt[p] = page # necessary? I do not know if these things update in python

                        # update tlb
                        tlb.add(p, removal_index)

                        # put frame in queue
                        fifo.put(removal_index)
                    
                    # restart instruction, sike just print the info in the if, else block to simulate restarting
                    # restarting means looking at only the page table, not the tlb
        
        # print statistics
        print(f'Number of Translated Addresses = {num_addr}\n')
        print(f'Page Faults = {page_faults}\n')
        print(f'Page Fault Rate = {(page_faults/num_addr):.3f}\n')
        print(f'TLB Hits = {tlb_hits}\n')
        print(f'TLB Misses = {tlb_misses}\n')
        print(f'TLB Hit Rate = {(tlb_hits/tlb_misses):.3f}\n')
        
    f.close()

if __name__ == "__main__":
    main()