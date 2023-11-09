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
        self.pageTable = [PTEntry() for _ in range(size)] # list of PTEntries
    def contains(self, pageNumber: int): # check if page is loaded into memory
        return self.pageTable[pageNumber].loadedBit == 1
    def getframe(self, pageNumber: int): # get the frame associated with the page number
        return self.pageTable[pageNumber].frameNumber

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
    def getitem(self, frameNumber: int):
        return self.ram[frameNumber]
    def setitem(self, frameData: List[int]):
        """
        Write frameData to RAM at the first empty spot. Since we are using LRU, 
        we can't just append to the RAM array, becasue we might be evicting frames out
        of order. This will be O(N), This function returns the frame number where the data was written.
        If memory is full it will return None.
        """
        for i in range(self.size):
            if self.ram[i] is None:
                self.ram[i] = frameData
                self.free-=1
                return i
        return None
    def deleteitem(self, frameNumber: int):
        self.ram[frameNumber] = None
        self.free+=1
        
    

class PTEntry:
    def __init__(self, frameNumber: int=None, loadedBit: int=0):
        self.frameNumber = frameNumber # 0 == not loaded into RAM, 1 == loaded
        self.loadedBit = loadedBit 


# OBJECTS FOR THE LRU IMPLEMENTATION:
class ListNode: # doubly linked list node
    def __init__(self, key, value):
        self.key = key # page number
        self.value = value # frame number
        self.prev = None
        self.next = None

class LRUCache: # keeps track of the LRU page IN MEMORY
    def __init__(self, capacity):
        self.capacity = capacity
        self.hashmap = {}
        self.head = ListNode(-1, -1) # dummy head
        self.tail = ListNode(-1, -1) # dummy tail
        self.head.next = self.tail
        self.tail.prev = self.head

    def _add_node(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node):
        prev = node.prev
        new = node.next
        prev.next = new
        new.prev = prev

    def _move_to_head(self, node):
        self._remove_node(node)
        self._add_node(node)

    def _pop_tail(self):
        res = self.tail.prev
        self._remove_node(res)
        return res

    def get(self, key):
        node = self.hashmap.get(key, None)
        if not node:
            return -1
        self._move_to_head(node)
        return node.value
   
    def getLRU(self):
        return self.tail.prev # get the node of the LRU page

    def put(self, key, value):
        node = self.hashmap.get(key)
        if not node:
            new_node = ListNode(key, value)
            self.hashmap[key] = new_node
            self._add_node(new_node)
            
            if len(self.hashmap) > self.capacity:
                tail = self._pop_tail()
                del self.hashmap[tail.key]
        else:
            node.value = value
            self._move_to_head(node)

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
        lruCache = LRUCache(frames)

        # while loop that goes through the addresses
        while (address := f.readline().strip()):      
            # increment counter for this page
            address = int(address)            
            num_addr+=1

            # break down into page number and offset
            p = address // PAGE_SIZE # page number
            d = address % PAGE_SIZE # page offset

            # check tlb
            if tlb.contains(p):
                tlb_hits+=1
                frame_number = tlb.getitem(p) # get frame number from tlb
                lruCache.put(p, frame_number) # update lru_cache
                frame_data = memory.getitem(frame_number) # get frame data from memory
                byte_data = frame_data[d] # get specific byte data
                frame_data_hex = ''.join(format(b, '02x') for b in frame_data).upper()
                print(f'{str(address)}, {str(byte_data)}, {str(frame_number)}, {frame_data_hex}')
            else: # check page table
                tlb_misses+=1
                # check page table
                if pt.contains(p): # no page fault
                    frame_number = pt.getframe(p) # get frame number from page table
                    lruCache.put(p, frame_number) # update lru_cache
                    frame_data = memory.getitem(frame_number) # get frame data from memory
                    byte_data = frame_data[d]
                    frame_data_hex = ''.join(format(b, '02x') for b in frame_data).upper()
                    print(f'{str(address)}, {str(byte_data)}, {str(frame_number)}, {frame_data_hex}')
                else: # page fault
                    page_faults+=1
                    # check for free frames
                    if memory.free > 0: # if there are free frames, write to memory, update page table, update tlb
                        # update page table and write to memory
                        pt.pageTable[p].frameNumber = memory.setitem(disk.disk[p]) # write frame data to memory
                        pt.pageTable[p].loadedBit = 1
                        # update tlb
                        tlb.add(p, pt.pageTable[p].frameNumber)
                        # update lru_cache
                        lruCache.put(p, pt.pageTable[p].frameNumber)
                        # print info
                        frame_number = pt.pageTable[p].frameNumber
                        frame_data = memory.getitem(pt.pageTable[p].frameNumber) # get frame data from memory
                        byte_data = frame_data[d]
                        frame_data_hex = ''.join(format(b, '02x') for b in frame_data).upper()
                        print(f'{str(address)}, {str(byte_data)}, {str(frame_number)}, {frame_data_hex}')
                    else: # need to invoke page replacement algorithm
                        # get the LRU node
                        lru_node = lruCache.getLRU()
                        # remove the node from the lru_cache, since it will no longer be in memory
                        lruCache._remove_node(lru_node)
                        # Delete the frame from memory and update the page table to reflect deletion
                        memory.deleteitem(lru_node.value)
                        pt.pageTable[lru_node.key].loadedBit = 0
                        pt.pageTable[lru_node.key].frameNumber = None
                        # update page table
                        pt.pageTable[p].frameNumber = memory.setitem(disk.disk[p]) # write frame data to memory
                        pt.pageTable[p].loadedBit = 1
                        # update the tlb
                        tlb.add(p, pt.pageTable[p].frameNumber)
                        # update the lru_cache
                        lruCache.put(p, pt.pageTable[p].frameNumber)
                        # print info
                        frame_data = memory.getitem(pt.pageTable[p].frameNumber) # get frame data from memory
                        byte_data = frame_data[d]
                        frame_data_hex = ''.join(format(b, '02x') for b in frame_data).upper()
                        print(f'{str(address)}, {str(byte_data)}, {str(frame_number)}, {frame_data_hex}')



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
        while address := f.readline().strip():
            # increment addresses read
            num_addr+=1

            # page number
            p = int(address) // PAGE_SIZE
            # page offset
            d = int(address) % PAGE_SIZE

            # check tlb, check loaded bit
            if tlb.contains(p):
                tlb_hits+=1 # increment tlb_hits
                frame_number = tlb.getitem(p) # get frame number from page-frame pair
                frame_data = memory.getitem(frame_number)
                byte_data = frame_data[d]
                print("{}, {}, {}, {}".format(address, byte_data, frame_number, ''.join(format(i, '02x') for i in frame_data).upper()))
                # Question: if a page#, frame# pair is in the tlb is it guarenteed to be in memory...do we need to check for page faulting here?
            
            else:
                # increment tlb_misses
                tlb_misses+=1
                #check page table, check loaded bit
                if pt.contains(p): # if hit go to memory
                    frame_number = pt.getframe(p) # get frame number from page table
                    frame_data = memory.getitem(frame_number)
                    byte_data = frame_data[d] # get value
                    print("{}, {}, {}, {}".format(address, byte_data, frame_number, ''.join(format(i, '02x') for i in frame_data).upper()))
                
                else: # page fault
                    page_faults+=1
                    # check for free frames
                    if memory.free != 0:
                        free_index = frames - memory.free
                        memory.ram[free_index] = disk.disk.get(p) # could change memory method setitem -> additem and make a true setitem
                        memory.free = memory.free - 1

                        # update pageTable
                        pt.pageTable[p].frameNumber = free_index
                        pt.pageTable[p].loadedBit = 1

                        # update tlb
                        tlb.add(p, free_index)

                        # put frame in queue
                        fifo.put(free_index)
                        
                        # get data and print
                        frame_data = memory.ram[free_index]
                        byte_data = frame_data[d]
                        print("{}, {}, {}, {}".format(address, byte_data, free_index, ''.join(format(i, '02x') for i in frame_data).upper()))

                    else: # page swap
                        # pop queue
                        removal_index = fifo.pop()
                        # QUESTION: should we remove entries in the tlb if they correspond to this frame number?

                        # remove from memory - do this by overwriting with new page
                        # add disk page into memory
                        memory.ram[removal_index] = disk.disk.get(p)
                        memory.free-=1

                        # update pageTable
                        pt_reset = findPagePT(pt, removal_index)
                        if pt_reset is not None:
                            pt.pageTable[pt_reset].frameNumber = None
                            pt.pageTable[pt_reset].loadedBit = 0

                        pt.pageTable[p].frameNumber = removal_index
                        pt.pageTable[p].loadedBit = 1



                        # update tlb
                        tlb_remove = findPageTLB(tlb.tlb, removal_index)
                        if tlb_remove is not None:
                            tlb.tlb.pop(tlb_remove)
                        tlb.add(p, removal_index)

                        # put frame in queue
                        fifo.put(removal_index)

                        # get data and print result
                        frame_data = memory.ram[removal_index]
                        byte_data = frame_data[d]
                        print("{}, {}, {}, {}".format(address, byte_data, removal_index, ''.join(format(i, '02x') for i in frame_data).upper()))
                    
                    # restart instruction, sike just print the info in the if, else block to simulate restarting
                    # restarting means looking at only the page table, not the tlb
        
    # print statistics
    print(f'Number of Translated Addresses = {num_addr}')
    print(f'Page Faults = {page_faults}')
    print(f'Page Fault Rate = {(page_faults/num_addr):.3f}')
    print(f'TLB Hits = {tlb_hits}')
    print(f'TLB Misses = {tlb_misses}')
    print(f'TLB Hit Rate = {(tlb_hits/tlb_misses):.3f}')
    f.close()

def findPageTLB(tlb, frame_num):
    index = None
    for x in range(len(tlb)):
        if frame_num == tlb[x][1]:
            index = x
    
    if index is None:
        return index
    return tlb[index][0]

def findPagePT(pt, frame_num):
    index = None
    for x in range(len(pt)):
        if frame_num == pt.pageTable[x].frameNumber:
            index = x

    return index


if __name__ == "__main__":
    main()