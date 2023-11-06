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

class PageTable: # include a loaded bit for each entry
    def __init__(self, size: int=2**8, algorithm: str="fifo"):
        self.size = size
        self.pageTable = {}

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
    

    # Read in the reference sequence file

    # Read in the entire backing store file into an easy to access data structure
    disk = Disk("BACKING_STORE.bin")

    #For each logical address in the reference sequence file:

    # 1. Determine the page number and offset
    # 2. Check the TLB for the page number
    # 3. If the page number is in the TLB, get the frame number
    # 4. If the page number is not in the TLB, check the page table
    # 5. If the page number is in the page table, get the frame number
    # 6. If the page number is not in the page table, get a free frame from RAM
    # 7. If there are no free frames, use the page replacement algorithm to select a victim frame
    # 8. Update the page table and TLB, getting the correct page from the disk if necessary.
    




if __name__ == "__main__":
    main()