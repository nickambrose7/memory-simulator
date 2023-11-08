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
    def deleteitem(self, pageNumber: int):
        for i, (page, frame) in enumerate(self.tlb):
            if page == pageNumber:
                if i < self.evictionIndex: # so taht we keep our eviction index correct
                    self.evictionIndex-=1
                self.tlb.pop(i)
                return True
        return False


class PageTable: # include a loaded bit for each entry
    def __init__(self, size: int=PAGE_TABLE_SIZE):
        self.size = size
        self.pageTable = [PTEntry() for _ in range(size)] # list of PTEntries
    def contains(self, pageNumber: int): # check if page is loaded into memory
        return self.pageTable[pageNumber].loadedBit == 1
    def getframe(self, pageNumber: int): # get the frame associated with the page number
        return self.pageTable[pageNumber].frameNumber
    def print(self):
        for i in range(self.size):
            if self.pageTable[i].frameNumber is not None:
                print(f'Page Number: {i}, Frame Number: {self.pageTable[i].frameNumber}, Loaded Bit: {self.pageTable[i].loadedBit}')
    def findLongestUnused(self, futurePages: List[int]):
        """
        This method is needed for the OPT page replacement algorithm.
        Future pages is a list of page numbers that will be referenced in the future.
        Goal: Find the page that is currently in the page table that will not be used for the longest time.
        1.) Get all the pages that are currently loaded into memory.
        2.) For each page, find the index of the next time it will be referenced.
        3.) Return the page with the longest time until next reference.
            -- time = index in futurePages, we want to return the largest index
            -- return a page frame pair
        """
        # 1.) Get all the pages that are currently loaded into memory.
        loadedPages = []
        for i in range(self.size):
            if self.pageTable[i].loadedBit == 1:
                loadedPages.append((i, self.pageTable[i].frameNumber)) # append a tuple of (page, frame)
        # 2.) For each page, find the index of the next time it will be referenced.
        longestUnused = None
        maxInd = -1
        for page in loadedPages:
            used = False
            for i in range(len(futurePages)):
                if page[0] == futurePages[i]:
                    used = True
                    if i > maxInd:
                        maxInd = i
                        longestUnused = page
                    break
            if not used:
                return page
        if longestUnused is None: 
        # none of the currently loaded pages are reference in the future, so just evict the first one
            return loadedPages[0]
        return longestUnused
       

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

    def printList(self):
        node = self.head.next
        while node != self.tail:
            print(node.key)
            print("|")
            node = node.next

    def getLRU(self): # Get Get LRU from the cache
        node = self.tail.prev
        if not node:
            return -1
        # self._move_to_head(node)
        return node
   

    def put(self, key, value): # put a new node in the cache, evict is necessary
        node = self.hashmap.get(key)
        if not node:
            new_node = ListNode(key, value)
            self.hashmap[key] = new_node
            self._add_node(new_node)
            
            if len(self.hashmap) > self.capacity: # remove the node
                tail = self._pop_tail()
                del self.hashmap[tail.key]
        else:
            node.value = value
            self._move_to_head(node)

# print helper function so that we have less code
def printInfo(pt, memory, address, p, d, frame_number):
    frame_data = memory.getitem(pt.pageTable[p].frameNumber) # get frame data from memory
    signed_byte_data = int.from_bytes([frame_data[d]], byteorder='little', signed=True)
    frame_data_hex = ''.join(format(b, '02x') for b in frame_data).upper()
    print(f'{str(address)}, {signed_byte_data}, {str(frame_number)}, {frame_data_hex}')  

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
                printInfo(pt, memory, address, p, d, frame_number)
            else: # check page table
                tlb_misses+=1
                # check page table
                if pt.contains(p): # no page fault
                    frame_number = pt.getframe(p) # get frame number from page table
                    lruCache.put(p, frame_number) # update lru_cache
                    printInfo(pt, memory, address, p, d, frame_number)
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
                        printInfo(pt, memory, address, p, d, frame_number)
                    else: # need to invoke page replacement algorithm
                        # get the LRU node
                        lru_node = lruCache.getLRU()
                        # Delete the frame from memory & TLB and update the page table to reflect deletion
                        memory.deleteitem(lru_node.value)
                        tlb.deleteitem(lru_node.key)
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
                        frame_number = pt.pageTable[p].frameNumber
                        printInfo(pt, memory, address, p, d, frame_number)
    elif args.pra == "opt": # optimal replacement
        # read the addresses into a list
        pages = []
        while (address := f.readline().strip()):
            pages.append(int(address) // PAGE_SIZE)
        # reset file pointer
        f.seek(0)

        # while loop that goes through the addresses
        while (address := f.readline().strip()):    
            # increment counter for this page
            address = int(address)            
            num_addr+=1

            # break down into page number and offset
            p = address // PAGE_SIZE # page number
            d = address % PAGE_SIZE # page offset
            if tlb.contains(p):
                tlb_hits+=1
                frame_number = tlb.getitem(p) # get frame number from tlb
                printInfo(pt, memory, address, p, d, frame_number)
            else: # check page table
                tlb_misses+=1
                # check page table
                if pt.contains(p): # no page fault
                    frame_number = pt.getframe(p) # get frame number from page table
                    printInfo(pt, memory, address, p, d, frame_number)
                else: # page fault
                    page_faults+=1
                    # check for free frames
                    if memory.free > 0: # if there are free frames, write to memory, update page table, update tlb
                        # update page table and write to memory
                        pt.pageTable[p].frameNumber = memory.setitem(disk.disk[p]) # write frame data to memory
                        pt.pageTable[p].loadedBit = 1
                        # update tlb
                        tlb.add(p, pt.pageTable[p].frameNumber)
                        # print info
                        frame_number = pt.pageTable[p].frameNumber
                        printInfo(pt, memory, address, p, d, frame_number)
                    else: # need to invoke page replacement algorithm
                        # get frame to remove
                        rmvPage, rmvFrame = pt.findLongestUnused(pages[num_addr:])
                        # Delete the frame from memory & TLB and update the page table to reflect deletion
                        memory.deleteitem(rmvFrame)
                        tlb.deleteitem(rmvPage)
                        pt.pageTable[rmvPage].loadedBit = 0
                        pt.pageTable[rmvPage].frameNumber = None
                        # update page table
                        pt.pageTable[p].frameNumber = memory.setitem(disk.disk[p]) # write frame data to memory
                        pt.pageTable[p].loadedBit = 1
                        # update the tlb
                        tlb.add(p, pt.pageTable[p].frameNumber)
                        # print info
                        frame_number = pt.pageTable[p].frameNumber
                        printInfo(pt, memory, address, p, d, frame_number)
        
    
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
                print("{}, {}, {}, {}".format(address, byte_data, frame_number, ''.join(str(i) for i in frame_data)))
                # Question: if a page#, frame# pair is in the tlb is it guarenteed to be in memory...do we need to check for page faulting here?
            
            else:
                # increment tlb_misses
                tlb_misses+=1
                #check page table, check loaded bit
                if pt.contains(p): # if hit go to memory
                    frame_number = pt.getframe(p) # get frame number from page table
                    frame_data = memory.getitem(frame_number)
                    byte_data = frame_data[d] # get value
                    print("{}, {}, {}, {}".format(address, byte_data, frame_number, ''.join(str(i) for i in frame_data)))
                
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
                        print("{}, {}, {}, {}".format(address, byte_data, free_index, ''.join(str(i) for i in frame_data)))

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
                        print("{}, {}, {}, {}".format(address, byte_data, removal_index, ''.join(str(i) for i in frame_data)))
                    
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