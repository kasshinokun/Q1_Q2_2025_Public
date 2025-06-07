import os
import struct
import io
from typing import Dict, List, Optional, Tuple

# Constants for file paths
FB_CSV_FILE = "indexed_data/test/persons_for_fb_hashing.csv"
FB_HASH_STORAGE_FILE = "indexed_data/test/extendible_hash_storage.dat"
FB_EXTERNAL_DATA_RECORDS_FILE = "indexed_data/test/persons_external_records.dat"

def delete_if_exists(path: str) -> None:
    """Delete a file if it exists."""
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            print(f"Warning: Could not delete file: {path}")

class FileBasedPage:
    MAX_ENTRIES = 31  # Updated from 3 to 31
    HEADER_SIZE = 8  # 4 bytes for entry_count + 4 bytes for local_depth
    ENTRY_SIZE = 12  # 4 bytes for key + 8 bytes for value

    def __init__(self, file_offset: int, depth_to_set: int, raf: io.BufferedRandom):
        self.file_offset = file_offset
        self.raf = raf
        self.local_depth = depth_to_set
        self.entry_count = 0
        self.entries: Dict[int, int] = {}
        
        # Initialize if new page
        if self.is_new_page():
            self.initialize_new_page()
        else:
            self.load_existing_page()

    def is_new_page(self) -> bool:
        """Check if the page is beyond the current file length."""
        self.raf.seek(0, os.SEEK_END)
        file_end = self.raf.tell()
        return file_end <= self.file_offset or file_end < self.file_offset + self.HEADER_SIZE

    def initialize_new_page(self) -> None:
        """Write initial header for a new page."""
        self.persist_header()

    def load_existing_page(self) -> None:
        """Load page metadata and entries from file."""
        self.raf.seek(self.file_offset)
        header_data = self.raf.read(self.HEADER_SIZE)
        if len(header_data) < self.HEADER_SIZE:
            raise IOError("Incomplete page header")
        
        self.entry_count, self.local_depth = struct.unpack(">ii", header_data)
        self.entries.clear()
        
        # Read each entry
        for _ in range(self.entry_count):
            entry_data = self.raf.read(self.ENTRY_SIZE)
            if len(entry_data) < self.ENTRY_SIZE:
                break
            key, value = struct.unpack(">iq", entry_data)
            self.entries[key] = value

    def persist_header(self) -> None:
        """Write header data to file."""
        self.raf.seek(self.file_offset)
        self.raf.write(struct.pack(">ii", self.entry_count, self.local_depth))

    def persist_entries(self) -> None:
        """Write all entries to file after the header."""
        self.raf.seek(self.file_offset + self.HEADER_SIZE)
        for key, value in self.entries.items():
            self.raf.write(struct.pack(">iq", key, value))

    def contains(self, key: int) -> bool:
        return key in self.entries

    def get(self, key: int) -> Optional[int]:
        return self.entries.get(key)

    def put(self, key: int, value: int) -> None:
        """Add or update an entry. Raise exception if page is full."""
        if key not in self.entries and self.entry_count >= self.MAX_ENTRIES:
            raise RuntimeError("Page full")
        
        self.entries[key] = value
        self.entry_count = len(self.entries)
        self.persist_header()
        self.persist_entries()

    def has_space(self) -> bool:
        return self.entry_count < self.MAX_ENTRIES

    def get_entries(self) -> List[Tuple[int, int]]:
        return list(self.entries.items())

    def clear_entries(self) -> None:
        """Reset entries and update header."""
        self.entries.clear()
        self.entry_count = 0
        self.persist_header()

class FileBasedDirectory:
    INITIAL_GLOBAL_DEPTH = 1
    HEADER_SIZE = 4  # 4 bytes for global_depth

    def __init__(self, raf: io.BufferedRandom):
        self.raf = raf
        self.global_depth = self.INITIAL_GLOBAL_DEPTH
        self.page_offsets: List[int] = [0] * (1 << self.global_depth)
        self.load()

    def load(self) -> None:
        """Load directory metadata from file or initialize if empty."""
        if os.path.getsize(self.raf.name) < self.HEADER_SIZE:
            self.persist()  # Initialize new directory
            return
        
        self.raf.seek(0)
        self.global_depth = struct.unpack(">i", self.raf.read(4))[0]
        dir_size = 1 << self.global_depth
        
        # Read page offsets
        self.page_offsets = []
        for _ in range(dir_size):
            offset_data = self.raf.read(8)
            if not offset_data:
                break
            self.page_offsets.append(struct.unpack(">q", offset_data)[0])
        
        # Pad if incomplete
        if len(self.page_offsets) < dir_size:
            self.page_offsets.extend([0] * (dir_size - len(self.page_offsets)))

    def persist(self) -> None:
        """Write directory metadata to file."""
        self.raf.seek(0)
        self.raf.write(struct.pack(">i", self.global_depth))
        for offset in self.page_offsets:
            self.raf.write(struct.pack(">q", offset))
        self.raf.truncate()  # Remove any leftover data

    def get_global_depth(self) -> int:
        return self.global_depth

    def get_page_offset(self, key: int) -> int:
        """Get page offset for a given key using global depth."""
        index = key & ((1 << self.global_depth) - 1)
        return self.page_offsets[index]

    def extend(self) -> None:
        """Double directory size when splitting requires more entries."""
        new_depth = self.global_depth + 1
        new_size = 1 << new_depth
        new_offsets = [0] * new_size
        
        # Copy existing offsets to new positions
        for i in range(len(self.page_offsets)):
            new_offsets[i] = self.page_offsets[i]
            new_offsets[i | (1 << self.global_depth)] = self.page_offsets[i]
        
        self.global_depth = new_depth
        self.page_offsets = new_offsets
        self.persist()

    def update(self, index: int, offset: int) -> None:
        """Update page offset at given directory index."""
        self.page_offsets[index] = offset
        self.persist()

class FileBasedEHash:
    def __init__(self, directory: FileBasedDirectory, storage_file: io.BufferedRandom):
        self.directory = directory
        self.storage_file = storage_file
        self.data_store = self  # Simplification: using main class for data store methods

    def get_page(self, offset: int) -> FileBasedPage:
        """Retrieve or create a page at given file offset."""
        return FileBasedPage(offset, self.directory.global_depth, self.storage_file)

    def allocate_new_page(self, depth: int) -> FileBasedPage:
        """Create a new page at end of file and return it."""
        self.storage_file.seek(0, os.SEEK_END)
        offset = self.storage_file.tell()
        return FileBasedPage(offset, depth, self.storage_file)

    def put(self, key: int, value: int) -> None:
        """Insert key-value pair into hash structure."""
        global_depth = self.directory.get_global_depth()
        page_index = key & ((1 << global_depth) - 1)
        page_offset = self.directory.page_offsets[page_index]
        
        try:
            if page_offset == 0:  # Uninitialized page
                page = self.allocate_new_page(global_depth)
                self.directory.update(page_index, page.file_offset)
                page.put(key, value)
            else:
                page = self.get_page(page_offset)
                page.put(key, value)
        except RuntimeError:  # Page full
            self.split_and_redistribute(page_index, key, value)

    def split_and_redistribute(self, page_index: int, new_key: int, new_value: int) -> None:
        """Split overflowing page and redistribute entries."""
        old_offset = self.directory.page_offsets[page_index]
        old_page = self.get_page(old_offset)
        old_depth = old_page.local_depth
        
        # Extend directory if local depth equals global depth
        if old_depth == self.directory.global_depth:
            self.directory.extend()
        
        # Create new page with increased local depth
        new_page = self.allocate_new_page(old_depth + 1)
        new_page.local_depth = old_depth + 1
        new_page.persist_header()
        
        # Update directory for new page's indices
        high_bit = 1 << old_depth
        for idx in range(len(self.directory.page_offsets)):
            if idx & high_bit == page_index & high_bit and idx & (high_bit - 1) == page_index & (high_bit - 1):
                self.directory.update(idx, new_page.file_offset)
        
        # Increase local depth of old page
        old_page.local_depth += 1
        old_page.persist_header()
        
        # Redistribute entries from old page
        entries = old_page.get_entries()
        old_page.clear_entries()
        for key, value in entries:
            self.put(key, value)  # Re-insert old entries
        self.put(new_key, new_value)  # Insert new entry

    def get(self, key: int) -> Optional[int]:
        """Retrieve value associated with key."""
        page_offset = self.directory.get_page_offset(key)
        if page_offset == 0:
            return None
        try:
            page = self.get_page(page_offset)
            return page.get(key)
        except IOError:
            return None

    def close(self) -> None:
        self.storage_file.close()

def run_file_based_hashing() -> None:
    """Main function to test file-based extendible hashing."""
    print("\n--- Testing File-Based Extendible Hashing ---")
    delete_if_exists(FB_CSV_FILE)
    delete_if_exists(FB_HASH_STORAGE_FILE)
    delete_if_exists(FB_EXTERNAL_DATA_RECORDS_FILE)
    
    # Create sample CSV file
    with open(FB_CSV_FILE, 'w') as f:
        for i in range(1, 1001):
            f.write(f"{i},Person {i},Age {i % 80 + 18}\n")
    
    try:
        # Initialize hash storage
        with open(FB_HASH_STORAGE_FILE, 'wb+') as storage_file, \
             open(FB_EXTERNAL_DATA_RECORDS_FILE, 'wb+') as data_file:
            
            directory = FileBasedDirectory(storage_file)
            hashing = FileBasedEHash(directory, storage_file)
            
            # Process CSV and store positions
            with open(FB_CSV_FILE, 'r') as csv_file:
                pos = 0
                for line in csv_file:
                    key = int(line.split(',', 1)[0])
                    data_file.seek(pos)
                    # Write key and record
                    data_file.write(struct.pack(">i", key))
                    data_file.write(line.encode('utf-8'))
                    # Store position in hash
                    hashing.put(key, pos)
                    pos = data_file.tell()
            
            # Test lookups
            test_keys = [1, 2, 5, 10, 999, 1000]
            for key in test_keys:
                pos = hashing.get(key)
                if pos is None:
                    print(f"Key {key} not found")
                    continue
                data_file.seek(pos)
                rec_key = struct.unpack(">i", data_file.read(4))[0]
                if rec_key != key:
                    print(f"Key mismatch: expected {key}, got {rec_key}")
                else:
                    record = data_file.readline().decode('utf-8').strip()
                    print(f"Found {key}: {record}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_file_based_hashing()