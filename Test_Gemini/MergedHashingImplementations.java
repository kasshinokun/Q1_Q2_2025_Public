/*
@uthor: Gabriel da Silva Cassino
@created on: 11-05-2025
@tools: Gemini AI 2.0 and Gemini AI 2.5
Code developed using Java, combined with knowledge about Hashing, Extensible Hashing, Bucket and other data structures in External Memory, and having the code developed verified by the AIs described above to remove
some Java Language I/O Exceptions that occurred during code development.

@Description of Functionalities:
- Creation of CSV Files with random oriented data
- Insertion of data into index in External Memory
- Insertion into Bucket Index
- Search for records.

@Standard Class
Person---|
         |--Id
         |--Name
         |--Age
@Standard Folder inside Project:
  Path: ./csv/AI/
*/
import java.io.*;
import java.nio.ByteBuffer; // Retained from original, though not explicitly used in merged logic
import java.nio.channels.FileChannel; // Retained from original, though not explicitly used in merged logic
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Stream;
import java.util.zip.CRC32;
import java.nio.charset.StandardCharsets; // Added for robust string to byte conversion

// --- Shared Helper Classes/Interfaces ---

interface Entry<K, V> {
    K key();
    V value();

    static <K, V> Entry<K, V> createEntry(K key, V value) {
        return new SimpleEntry<>(key, value);
    }
}

class SimpleEntry<K, V> implements Entry<K, V> {
    private final K key;
    private final V value;

    public SimpleEntry(K key, V value) {
        this.key = key;
        this.value = value;
    }

    @Override
    public K key() {
        return key;
    }

    @Override
    public V value() {
        return value;
    }

    @Override
    public String toString() {
        return "Entry{" + "key=" + key + ", value=" + value + '}';
    }
}

class EHashStats {
    // Placeholder for statistics, can be expanded
    @Override
    public String toString() {
        return " EHashStats{}"; // Basic representation
    }
}

interface Page<K, V> {
    boolean contains(K key) throws IOException;
    V get(K key) throws IOException;
    void put(K key, V value) throws IOException;
    boolean hasSpaceFor(K key, V value) throws IOException;
    int depth() throws IOException;
    long getId(); // Typically the file offset
    Collection<Entry<K, V>> getEntries() throws IOException;
    void incrementLocalDepth() throws IOException;
    void clearEntriesForSplit() throws IOException; // Added helper
}

interface Directory {
    long getPageOffset(long hashCode);
    int getGlobalDepth();
    void extend() throws IOException;
    void put(long directoryIndex, long pageOffset) throws IOException; // Changed from bucketOffset to pageOffset
    void load(RandomAccessFile raf) throws IOException;
    void save(RandomAccessFile raf) throws IOException;
    long getDirectoryIndex(long hashCode);
}

interface DataStore<K, V> {
    Page<K, V> getPage(long pageOffset) throws IOException;
    Page<K, V> allocateNewPage(int depth) throws IOException;
    void writePage(Page<K,V> page) throws IOException;
    long getNextAvailableOffset();
}


// --- ExtensibleHashingCSV Implementation ---

@SuppressWarnings("unused")
class ExtensibleHashingCSV {

    private static final int BUCKET_SIZE = 1024;
    private static final String DATA_FILE_CSV = "csv/AI/data_csv.dat";
    private static final String INDEX_FILE_CSV = "csv/AI/index_csv.dat";
    private static final String REGISTRY_FILE_CSV = "csv/AI/registry_csv.dat";
    private static final String CSV_INPUT_FILE = "csv/AI/random_people_for_csv_hashing.csv";

    private RandomAccessFile dataFile;
    private FileChannel dataChannel; // Not actively used in logic but part of original structure
    private RandomAccessFile indexFile;
    private FileChannel indexChannel; // Not actively used
    private int globalDepth;
    private List<Bucket> directory;

    private static class Bucket {
        int localDepth;
        HashMap<String, Long> entries;

        public Bucket(int localDepth) {
            this.localDepth = localDepth;
            this.entries = new HashMap<>(BUCKET_SIZE);
        }

        @Override
        public String toString() {
            return "Bucket@"+Integer.toHexString(hashCode()) + "{" + "ld=" + localDepth + ", entries=" + entries.size() + '}';
        }
    }

    public ExtensibleHashingCSV() {
        this.globalDepth = 1;
        int initialDirectorySize = 1 << globalDepth;
        this.directory = new ArrayList<>(initialDirectorySize);
        for (int i = 0; i < initialDirectorySize; i++) {
            directory.add(new Bucket(globalDepth));
        }
    }

    private void initializeFiles() throws IOException {
        dataFile = new RandomAccessFile(DATA_FILE_CSV, "rw");
        dataChannel = dataFile.getChannel();
        indexFile = new RandomAccessFile(INDEX_FILE_CSV, "rw");
        indexChannel = indexFile.getChannel();
    }

    private void closeFiles() throws IOException {
        if (dataChannel != null) dataChannel.close();
        if (dataFile != null) dataFile.close();
        if (indexChannel != null) indexChannel.close();
        if (indexFile != null) indexFile.close();
        System.out.println("ExtensibleHashingCSV files closed.");
    }

    private void loadRegistry() throws IOException {
        File registry = new File(REGISTRY_FILE_CSV);
        if (registry.exists() && registry.length() > 0) {
            try (DataInputStream dis = new DataInputStream(new BufferedInputStream(new FileInputStream(registry)))) {
                this.globalDepth = dis.readInt();
                int directorySize = 1 << this.globalDepth;
                this.directory = new ArrayList<>(directorySize); // Initialize with correct capacity
                for (int i = 0; i < directorySize; i++) {
                    if (dis.available() < (Integer.BYTES * 2) ) { // Basic check for enough data for bucket header
                         System.err.println("Registry file corrupted or incomplete at directory index " + i);
                         // Fallback: add a default bucket or handle error more gracefully
                         this.directory.add(new Bucket(this.globalDepth)); // Add a default new bucket
                         continue; // Or break, depending on desired error handling
                    }
                    int localDepth = dis.readInt();
                    Bucket bucket = new Bucket(localDepth);
                    int bucketEntryCount = dis.readInt();
                    for (int j = 0; j < bucketEntryCount; j++) {
                         if (dis.available() == 0 ) { // Check before reading key/offset
                            System.err.println("Registry file ended unexpectedly while reading entries for bucket " + i);
                            break;
                        }
                        String key = dis.readUTF();
                        long offset = dis.readLong();
                        bucket.entries.put(key, offset);
                    }
                    this.directory.add(bucket);
                }
                System.out.println("Registry loaded. Global Depth: " + this.globalDepth + ", Directory Size: " + directory.size());
                 if(directory.size() != directorySize){
                    System.err.println("Registry load warning: Expected directory size " + directorySize + " but loaded " + directory.size());
                    // Potentially fill remaining with new buckets
                    for(int k=directory.size(); k < directorySize; k++){
                        directory.add(new Bucket(this.globalDepth));
                    }
                }

            }
        } else {
            System.out.println("No registry found or empty, initializing new. Global Depth: " + this.globalDepth);
            int initialDirectorySize = 1 << globalDepth;
            this.directory = new ArrayList<>(initialDirectorySize);
            for (int i = 0; i < initialDirectorySize; i++) {
                directory.add(new Bucket(globalDepth));
            }
        }
    }

    private void saveRegistry() throws IOException {
        try (DataOutputStream dos = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(REGISTRY_FILE_CSV)))) {
            dos.writeInt(this.globalDepth);
            for (Bucket bucket : this.directory) {
                dos.writeInt(bucket.localDepth);
                dos.writeInt(bucket.entries.size());
                for (Map.Entry<String, Long> entry : bucket.entries.entrySet()) {
                    dos.writeUTF(entry.getKey());
                    dos.writeLong(entry.getValue());
                }
            }
            System.out.println("Registry saved. Global Depth: " + this.globalDepth);
        }
    }

    public void processCSV(String csvFilePath, Function<String, String> keyExtractor) throws IOException {
        File csvFileObj = new File(csvFilePath);
        if (!csvFileObj.exists()) {
            System.err.println("CSV file not found: " + csvFilePath);
            System.out.println("Creating dummy CSV file: " + csvFilePath);
            try (PrintWriter writer = new PrintWriter(csvFileObj)) {
                for (int i = 1; i <= 210000; i++) {
                    writer.println(i + ", FirstName" + i + ", LastName" + i + ", Value" + (i * 10));
                }
            }
        }

        try (BufferedReader br = new BufferedReader(new FileReader(csvFilePath))) {
            String line;
            dataFile.seek(dataFile.length()); // Start writing at the end of the data file
            long currentOffset = dataFile.getFilePointer();

            while ((line = br.readLine()) != null) {
                if (line.trim().isEmpty()) continue;
                String key;
                try {
                    key = keyExtractor.apply(line);
                } catch (ArrayIndexOutOfBoundsException e) {
                    System.err.println("Skipping malformed CSV line (key extraction failed): " + line);
                    continue;
                }
                byte[] recordBytes = (line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8);
                dataFile.write(recordBytes);
                insert(key, currentOffset); // Store offset where record *starts*
                currentOffset = dataFile.getFilePointer(); // Update for *next* record
            }
            System.out.println("CSV processing complete for ExtensibleHashingCSV.");
        }
    }

    private int hash(String key) {
        CRC32 crc = new CRC32();
        crc.update(key.getBytes(StandardCharsets.UTF_8));
        return (int) crc.getValue();
    }

    private int getBucketIndex(int hashValue, int depth) {
        if (depth == 0) return 0; // Avoid issues with 1<<0 - 1
        return hashValue & ((1 << depth) - 1);
    }

    private void insert(String key, long offset) throws IOException {
        int bucketIndex = getBucketIndex(hash(key), globalDepth);
        Bucket bucket = directory.get(bucketIndex);

        if (bucket.entries.containsKey(key) || bucket.entries.size() < BUCKET_SIZE) {
            bucket.entries.put(key, offset);
        } else {
            splitBucket(bucketIndex, key, offset); // Pass key/offset that caused split
            // After split, the key that caused the split still needs to be inserted.
            // The splitBucket now re-inserts all, including the new one.
            // So, a direct recursive call might not be needed if split handles it.
            // Let's retry the insert for the specific key if splitBucket doesn't guarantee its placement.
            // For safety, let splitBucket handle redistribution, and we retry insert.
            insert(key,offset); // Recursive call after split attempt
        }
    }


    private void splitBucket(int bucketIndexToSplit, String keyCausingSplit, long offsetCausingSplit) throws IOException {
        Bucket oldBucket = directory.get(bucketIndexToSplit);
        int oldLocalDepth = oldBucket.localDepth;

        if (oldLocalDepth == globalDepth) {
            int oldDirSize = directory.size();
            if (oldDirSize >= (Integer.MAX_VALUE / 2)) {
                 System.err.println("Max directory size reached, cannot double further.");
                 // Potentially try to handle overflow by other means or stop
                 // For now, we might get stuck if BUCKET_SIZE is too small and keys collide badly.
                 // This would lead to stack overflow on repeated insert calls.
                 return; // Cannot split further if directory cannot grow
            }
            for (int i = 0; i < oldDirSize; i++) {
                directory.add(directory.get(i)); // Duplicate pointers for now
            }
            globalDepth++;
            System.out.println("ExtHashingCSV: Global depth increased to: " + globalDepth);
        }

        int newLocalDepth = oldLocalDepth + 1;
        Bucket newBucket = new Bucket(newLocalDepth);
        oldBucket.localDepth = newLocalDepth; // Old bucket also gets new local depth

        // Update directory pointers
        // Iterate through the whole directory. For each entry, if it used to point to oldBucket,
        // re-evaluate based on the newLocalDepth'th bit of the hash.
        for (int i = 0; i < directory.size(); i++) {
            // Check if this directory entry's hash pattern (up to oldLocalDepth) matches the bucket that split
            // AND if this entry was indeed pointing to the oldBucket instance
            int prefixMaskForOldBucket = (1 << oldLocalDepth) -1;
            if ((getBucketIndex(hash("any_key_that_would_map_to_original_bucket"), oldLocalDepth) == (i & prefixMaskForOldBucket))
                && directory.get(i) == oldBucket) { // More robust check: directory.get(i) == oldBucket (or a list of pointers to oldBucket)

                // The new distinguishing bit is at position 'oldLocalDepth' (0-indexed)
                // If that bit in 'i' (the directory index) is 1, it points to newBucket
                if (((i >> oldLocalDepth) & 1) == 1) {
                    directory.set(i, newBucket);
                }
                // else it continues to point to oldBucket (which is already there by duplication or was the original)
            }
        }
        // Ensure the specific index that was `bucketIndexToSplit` and its pair are correct
        // The one that differs by the (oldLocalDepth)-th bit from bucketIndexToSplit now points to newBucket
        int pairIndex = bucketIndexToSplit ^ (1 << oldLocalDepth);
        if (pairIndex < directory.size()) { // Check bounds, esp. if globalDepth didn't grow but local did
             directory.set(pairIndex, newBucket);
        }
         // And original bucketIndexToSplit should still point to oldBucket (already set or duplicated).
        directory.set(bucketIndexToSplit, oldBucket);


        // Redistribute entries
        Map<String, Long> tempEntries = new HashMap<>(oldBucket.entries);
        oldBucket.entries.clear();
        tempEntries.put(keyCausingSplit, offsetCausingSplit); // Add the entry that caused the split

        for (Map.Entry<String, Long> entry : tempEntries.entrySet()) {
            // Re-insert: this will use the updated globalDepth and new localDepths
            // This re-insert is crucial and must correctly place items.
            int targetBucketIndex = getBucketIndex(hash(entry.getKey()), globalDepth);
            Bucket targetBucket = directory.get(targetBucketIndex);
            if (targetBucket.entries.size() < BUCKET_SIZE || targetBucket.entries.containsKey(entry.getKey())) {
                targetBucket.entries.put(entry.getKey(), entry.getValue());
            } else {
                // This case should ideally not happen if BUCKET_SIZE > 0 and split logic is perfect,
                // unless we have a key that cannot be placed even after a split (e.g. BUCKET_SIZE too small)
                // This could lead to StackOverflowError if we recursively call insert/split from here.
                // For now, we assume BUCKET_SIZE is adequate.
                // If it happens, print error. The outer insert will retry.
                 System.err.println("ExtHashingCSV: Error during redistribution in split. Bucket still full for key: " + entry.getKey());
                 System.err.println("Target Bucket: " + targetBucket + " index: " + targetBucketIndex);
                 System.err.println("Directory size: " + directory.size() + " globalDepth: " + globalDepth);
            }
        }
    }


    public long findRecordOffset(String key) throws IOException {
        int hashVal = hash(key);
        int bucketIndex = getBucketIndex(hashVal, globalDepth);
        if (bucketIndex < 0 || bucketIndex >= directory.size()) {
            System.err.println("ExtHashingCSV Error: Bucket index " + bucketIndex + " out of bounds. Key: " + key + ", Global Depth: " + globalDepth);
            return -1L;
        }
        Bucket bucket = directory.get(bucketIndex);
        return bucket.entries.getOrDefault(key, -1L);
    }

    public String readRecord(long offset) throws IOException {
        if (offset == -1L) {
            return null;
        }
        if (offset >= dataFile.length()) {
            System.err.println("ExtHashingCSV Error: Offset " + offset + " is beyond data file length " + dataFile.length());
            return null;
        }
        dataFile.seek(offset);
        return dataFile.readLine(); // Note: readLine() has charset implications.
    }

    public static void runExtensibleHashingCSV() {
        System.out.println("--- Running ExtensibleHashingCSV Test ---");
        ExtensibleHashingCSV hashing = new ExtensibleHashingCSV();

        new File(DATA_FILE_CSV).delete();
        new File(REGISTRY_FILE_CSV).delete();
        new File(INDEX_FILE_CSV).delete();

        try {
            hashing.initializeFiles();
            hashing.loadRegistry();
            hashing.processCSV(CSV_INPUT_FILE, line -> line.split(",")[0]);
            hashing.saveRegistry();

            System.out.println("ExtHashingCSV: Directory state after processing:");
            for (int i = 0; i < hashing.directory.size(); i++) {
                Bucket b = hashing.directory.get(i);
                System.out.println("Dir[" + i + "] -> " + b + " (Entries: " + b.entries.keySet() + ")");
            }

        } catch (IOException e) {
            System.err.println("IOException in ExtensibleHashingCSV main processing: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("General Exception in ExtensibleHashingCSV main processing: " + e.getMessage());
            e.printStackTrace();
        } finally {
            try {
                hashing.closeFiles();
            } catch (IOException e) {
                System.err.println("IOException during closeFiles: " + e.getMessage());
            }
        }

        System.out.println("\n--- Reading Test for ExtensibleHashingCSV ---");
        ExtensibleHashingCSV hashingRead = new ExtensibleHashingCSV();
        try {
            hashingRead.initializeFiles();
            hashingRead.loadRegistry();

            String[] searchKeys = {"1", "5", "10", "15", "20", "1000" }; // Test existing and non-existing
            for(String searchKey : searchKeys) {
                System.out.println("Searching for key: " + searchKey);
                long offset = hashingRead.findRecordOffset(searchKey);
                if (offset != -1L) {
                    String record = hashingRead.readRecord(offset);
                    System.out.println("Record found for key '" + searchKey + "': " + record);
                } else {
                    System.out.println("Record with key '" + searchKey + "' not found.");
                }
            }
        } catch (IOException e) {
            System.err.println("IOException in ExtensibleHashingCSV read test: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("General Exception in ExtensibleHashingCSV read test: " + e.getMessage());
            e.printStackTrace();
        } finally {
            try {
                hashingRead.closeFiles();
            } catch (IOException e) {
                System.err.println("IOException during read test closeFiles: " + e.getMessage());
            }
        }
        System.out.println("--- ExtensibleHashingCSV Test Finished ---");
    }
}


// --- FileBasedExtendibleHashing Implementation ---

class FileBasedPage implements Page<Integer, Long> {
    private static final int MAX_ENTRIES = 3;
    private final long fileOffset;
    private int localDepth;
    private final RandomAccessFile raf;
    private int entryCount;
    private Map<Integer, Long> entriesMap; // In-memory cache

    private static final int HEADER_SIZE = Integer.BYTES * 2; // entryCount, localDepth
    private static final int ENTRY_SIZE = Integer.BYTES + Long.BYTES; // key, value

    public FileBasedPage(long fileOffset, int depthToSetIfNew, RandomAccessFile raf) throws IOException {
        this.fileOffset = fileOffset;
        this.raf = raf;
        this.entriesMap = new LinkedHashMap<>(); // Preserve insertion order for consistent rewrite if needed

        boolean isNewPage = raf.length() <= fileOffset || (raf.length() < fileOffset + HEADER_SIZE);

        raf.seek(fileOffset);
        if (isNewPage) {
            this.localDepth = depthToSetIfNew;
            this.entryCount = 0;
            raf.writeInt(this.entryCount);
            raf.writeInt(this.localDepth);
            // Optional: Extend file to reserve space for MAX_ENTRIES (can be slow)
            // raf.setLength(Math.max(raf.length(), fileOffset + HEADER_SIZE + MAX_ENTRIES * ENTRY_SIZE));
        } else {
            this.entryCount = raf.readInt();
            this.localDepth = raf.readInt();
            for (int i = 0; i < this.entryCount; i++) {
                // Check if enough bytes remain for an entry
                if (raf.getFilePointer() + ENTRY_SIZE > raf.length()) {
                     System.err.println("FBPage Error: File ended prematurely while reading entries for page at offset " + fileOffset);
                     this.entryCount = i; // Adjust entry count to what was actually read
                     break;
                }
                entriesMap.put(raf.readInt(), raf.readLong());
            }
            // If entryCount from header mismatches what was read (e.g. due to corruption)
             if (this.entryCount != entriesMap.size() && this.entryCount > 0) {
                System.err.println("FBPage Warning: Mismatch entries for page " + fileOffset + ". Header: " + this.entryCount + ", Loaded: " + entriesMap.size());
                this.entryCount = entriesMap.size(); // Correct entryCount based on loaded data
                persistHeader(); // Persist corrected header
            }
        }
    }

    private void persistHeader() throws IOException {
        raf.seek(fileOffset);
        raf.writeInt(entryCount);
        raf.writeInt(localDepth);
    }

    private void persistEntries() throws IOException {
        raf.seek(fileOffset + HEADER_SIZE);
        for (Map.Entry<Integer, Long> mapEntry : entriesMap.entrySet()) {
            raf.writeInt(mapEntry.getKey());
            raf.writeLong(mapEntry.getValue());
        }
        // Optional: clear any trailing old data if new entryCount is less than before
        // long endOfValidData = fileOffset + HEADER_SIZE + entriesMap.size() * ENTRY_SIZE;
        // if (raf.getFilePointer() < endOfValidData + ENTRY_SIZE) { /* pad or truncate */ }
    }


    @Override
    public boolean contains(Integer key) {
        return entriesMap.containsKey(key);
    }

    @Override
    public Long get(Integer key) {
        return entriesMap.get(key);
    }

    @Override
    public void put(Integer key, Long value) throws IOException {
        boolean newKey = !entriesMap.containsKey(key);
        if (newKey && entryCount >= MAX_ENTRIES) {
            throw new IllegalStateException("FBPage full at offset " + fileOffset + ". Cannot add new key: " + key);
        }
        entriesMap.put(key, value);
        if (newKey) {
            entryCount++;
        }
        persistHeader();
        persistEntries(); // Rewrite all entries for simplicity
    }

    @Override
    public boolean hasSpaceFor(Integer key, Long value) {
        return entriesMap.containsKey(key) || entryCount < MAX_ENTRIES;
    }

    @Override
    public int depth() {
        return localDepth;
    }

    @Override
    public void incrementLocalDepth() throws IOException {
        this.localDepth++;
        persistHeader();
    }

    @Override
    public long getId() {
        return fileOffset;
    }

    @Override
    public Collection<Entry<Integer, Long>> getEntries() {
        List<Entry<Integer, Long>> currentEntries = new ArrayList<>();
        for (Map.Entry<Integer, Long> mapEntry : entriesMap.entrySet()) {
            currentEntries.add(Entry.createEntry(mapEntry.getKey(), mapEntry.getValue()));
        }
        return currentEntries;
    }

    @Override
    public void clearEntriesForSplit() throws IOException {
        this.entriesMap.clear();
        this.entryCount = 0;
        persistHeader(); // Write empty state
        // PersistEntries is not strictly needed if header is 0, but good for full clear
        raf.seek(fileOffset + HEADER_SIZE); // Position after header
        // Optional: fill with zeros or truncate if this page's space is fixed.
        // For now, just updating header and in-memory map is enough before redistribution.
    }
}

class FileBasedDirectory implements Directory {
    private static final int INITIAL_GLOBAL_DEPTH = 1;
    private static final long DIR_METADATA_OFFSET = 0; // Global depth
    private static final int GLOBAL_DEPTH_BYTES = Integer.BYTES;
    private static final long DIR_ENTRIES_OFFSET = GLOBAL_DEPTH_BYTES; // Page offsets start after global depth

    private int globalDepth;
    private List<Long> pageOffsets; // In-memory list of page offsets (Long: file offset of a Page)
    // RandomAccessFile ref not stored here, passed to methods.

    public FileBasedDirectory(RandomAccessFile raf) throws IOException {
        this.pageOffsets = new ArrayList<>();
        load(raf);
    }

    @Override
    public int getGlobalDepth() {
        return globalDepth;
    }

    @Override
    public long getDirectoryIndex(long hashCode) {
        if (globalDepth == 0) return 0;
        return hashCode & ((1L << globalDepth) - 1);
    }

    @Override
    public long getPageOffset(long hashCode) {
        int index = (int) getDirectoryIndex(hashCode);
        if (index >= 0 && index < pageOffsets.size()) {
            return pageOffsets.get(index);
        }
        System.err.println("FBDirectory Error: Index " + index + " out of bounds. Hash: " + hashCode + ", GD: " + globalDepth);
        return 0L; // 0L indicates no page allocated or error
    }

    @Override
    public void extend() throws IOException {
        int oldSize = 1 << globalDepth;
        this.globalDepth++;
        int newSize = 1 << globalDepth;
        
        if (newSize < oldSize || newSize > (Integer.MAX_VALUE / Long.BYTES) ) { // Overflow check or practical limit
            System.err.println("FBDirectory: Cannot extend directory further. New size too large or overflow.");
            this.globalDepth--; // Revert
            throw new IOException("Directory size limit reached.");
        }

        List<Long> newPageOffsets = new ArrayList<>(Collections.nCopies(newSize, 0L));
        for (int i = 0; i < oldSize; i++) {
            newPageOffsets.set(i, pageOffsets.get(i));
            newPageOffsets.set(i | oldSize, pageOffsets.get(i)); // Duplicate pointers
        }
        this.pageOffsets = newPageOffsets;
        System.out.println("FBDirectory: Extended. New global depth: " + this.globalDepth + ", New size: " + newSize);
    }

    @Override
    public void put(long directoryIndex, long pageOffset) throws IOException {
        if (directoryIndex >= 0 && directoryIndex < pageOffsets.size()) {
            pageOffsets.set((int) directoryIndex, pageOffset);
        } else {
            System.err.println("FBDirectory Error: Attempt to put at invalid index " + directoryIndex + " (size: " + pageOffsets.size() + ")");
            throw new IOException("Invalid directory index for put: " + directoryIndex);
        }
    }

    @Override
    public void load(RandomAccessFile raf) throws IOException {
        if (raf.length() >= DIR_METADATA_OFFSET + GLOBAL_DEPTH_BYTES) {
            raf.seek(DIR_METADATA_OFFSET);
            this.globalDepth = raf.readInt();
            if(this.globalDepth < 0 || this.globalDepth > 30) { // Sanity check depth
                System.err.println("FBDirectory Warning: Unreasonable global depth " + this.globalDepth + " loaded. Resetting.");
                initializeDefaultDirectoryState();
                return;
            }

            int expectedSize = 1 << this.globalDepth;
            this.pageOffsets = new ArrayList<>(Collections.nCopies(expectedSize, 0L)); // Initialize with default 0L

            if (raf.length() >= DIR_ENTRIES_OFFSET + (long) expectedSize * Long.BYTES) {
                raf.seek(DIR_ENTRIES_OFFSET);
                for (int i = 0; i < expectedSize; i++) {
                     if (raf.getFilePointer() + Long.BYTES > raf.length()) {
                        System.err.println("FBDirectory Error: File ended while reading page offsets at index " + i);
                        // Fill rest with 0L or handle error. Current loop will break.
                        break;
                    }
                    pageOffsets.set(i, raf.readLong());
                }
                System.out.println("FBDirectory: Loaded from file. Global depth: " + globalDepth + ", Size: " + expectedSize);
                 if (pageOffsets.stream().filter(p -> p != 0L).count() == 0 && expectedSize > 2) {
                    System.out.println("FBDirectory Warning: Loaded directory seems to have all zero offsets.");
                }
            } else {
                System.out.println("FBDirectory: File exists but incomplete for entries. Loaded depth: " + globalDepth + ". Initializing page offsets to 0L.");
            }
        } else {
            System.out.println("FBDirectory: File not found or too small. Initializing new directory.");
            initializeDefaultDirectoryState();
        }
    }

    private void initializeDefaultDirectoryState() {
        this.globalDepth = INITIAL_GLOBAL_DEPTH;
        int initialSize = 1 << this.globalDepth;
        this.pageOffsets = new ArrayList<>(Collections.nCopies(initialSize, 0L));
    }

    @Override
    public void save(RandomAccessFile raf) throws IOException {
        raf.seek(DIR_METADATA_OFFSET);
        raf.writeInt(this.globalDepth);
        raf.seek(DIR_ENTRIES_OFFSET);
        for (Long offset : this.pageOffsets) {
            raf.writeLong(offset);
        }
        // Ensure file is at least this long
        // raf.setLength(Math.max(raf.length(), DIR_ENTRIES_OFFSET + (long)pageOffsets.size() * Long.BYTES));
        System.out.println("FBDirectory: Saved. Global depth: " + this.globalDepth);
    }
}

class FileBasedDataStore implements DataStore<Integer, Long> {
    private final RandomAccessFile dataRaf;
    private long nextAvailablePageOffset;
    // Start data pages after some reserved space for directory and hash metadata
    private static final long DATA_PAGES_START_OFFSET = 4096; // e.g. 4KB
    private static final long PAGE_ALLOCATION_SIZE = 512; // Allocate in chunks of this size (approx page size)


    public FileBasedDataStore(RandomAccessFile raf) throws IOException {
        this.dataRaf = raf;
        if (dataRaf.length() < DATA_PAGES_START_OFFSET) {
            this.nextAvailablePageOffset = DATA_PAGES_START_OFFSET;
        } else {
            this.nextAvailablePageOffset = dataRaf.length();
        }
        // Align to a block boundary for neatness
        if (this.nextAvailablePageOffset % PAGE_ALLOCATION_SIZE != 0) {
            this.nextAvailablePageOffset = ((this.nextAvailablePageOffset / PAGE_ALLOCATION_SIZE) + 1) * PAGE_ALLOCATION_SIZE;
        }
        System.out.println("FBDataStore: Initialized. Next available page offset: " + this.nextAvailablePageOffset);
    }

    @Override
    public Page<Integer, Long> getPage(long pageOffset) throws IOException {
        if (pageOffset < DATA_PAGES_START_OFFSET && pageOffset != 0L) { // 0L might be legit if it means "no page"
            System.err.println("FBDataStore Warning: Attempt to get page at suspicious offset: " + pageOffset);
        }
        return new FileBasedPage(pageOffset, -1, dataRaf); // -1 depth, Page constructor reads actual
    }

    @Override
    public Page<Integer, Long> allocateNewPage(int depthForNewPage) throws IOException {
        long newPageFileOffset = nextAvailablePageOffset;
        Page<Integer, Long> newPage = new FileBasedPage(newPageFileOffset, depthForNewPage, dataRaf); // Initializes on disk
        nextAvailablePageOffset += PAGE_ALLOCATION_SIZE; // Advance by fixed allocation chunk
        System.out.println("FBDataStore: Allocated new page at " + newPageFileOffset + " depth " + depthForNewPage + ". Next free: " + nextAvailablePageOffset);
        return newPage;
    }

    @Override
    public void writePage(Page<Integer, Long> page) throws IOException {
        // FileBasedPage.put() already persists. This method is a placeholder
        // or could be used if Page interface was more abstract about persistence.
    }

    @Override
    public long getNextAvailableOffset() {
        return nextAvailablePageOffset;
    }
}

class BinUtils {
    public static long[] enumerateValues(int globalDepth, int localDepth, long prefix) {
        if (globalDepth < localDepth) return new long[]{prefix}; // Or throw error
        long count = 1L << (globalDepth - localDepth);
        long[] result = new long[(int) count]; // Potential cast issue if count is huge
        for (int i = 0; i < count; i++) {
            result[i] = (prefix << (globalDepth - localDepth)) | i;
        }
        return result;
    }
}

class FileBasedEHash<K extends Number & Comparable<K>, V> { // Key type for example
    private final Directory directory;
    private final DataStore<K, V> dataStore;
    private final RandomAccessFile metadataFile;
    private final EHashStats stats = new EHashStats();
    private long size = 0;
    private boolean dirty = false;

    // Using a distinct offset for hash table size within the metadata/hash file
    private static final long HASH_SIZE_METADATA_OFFSET = 2048; // Example offset, after directory space

    public FileBasedEHash(Directory directory, DataStore<K, V> dataStore, RandomAccessFile metadataRaf) throws IOException {
        this.directory = directory;
        this.dataStore = dataStore;
        this.metadataFile = metadataRaf; // Can be same RAF as directory/datastore
        loadSize();
    }

    public boolean contains(K key) throws IOException {
        long hashCode = key.hashCode();
        long pageOffset = directory.getPageOffset(hashCode);
        if (pageOffset != 0L) {
            Page<K, V> page = dataStore.getPage(pageOffset);
            return page.contains(key);
        }
        return false;
    }

    public V get(K key) throws IOException {
        long hashCode = key.hashCode();
        long pageOffset = directory.getPageOffset(hashCode);
        if (pageOffset != 0L) {
            Page<K, V> page = dataStore.getPage(pageOffset);
            return page.get(key);
        }
        return null;
    }

    public void put(K key, V value) throws IOException {
        long hashCode = key.hashCode();
        long pageOffset = directory.getPageOffset(hashCode);
        Page<K, V> page;

        if (pageOffset == 0L) { // No page for this hash directory entry yet
            page = dataStore.allocateNewPage(directory.getGlobalDepth());
            pageOffset = page.getId();
            long dirIndex = directory.getDirectoryIndex(hashCode);
            directory.put(dirIndex, pageOffset);
            // If other directory entries also map to this newly created page due to global_depth,
            // they should also be updated. This simple put(dirIndex, pageOffset) only sets one.
            // A robust system might initialize multiple dir entries pointing to the first page.
            // For now, this relies on splits to propagate pointers.
        } else {
            page = dataStore.getPage(pageOffset);
        }

        if (page.contains(key)) { // Update existing key
            page.put(key, value);
            dirty = true;
            // dataStore.writePage(page); // If page.put() doesn't auto-persist fully. Assumed it does.
            return; // Size doesn't change on update
        }

        if (!page.hasSpaceFor(key, value)) {
            // Page is full, perform split
            int oldPageLocalDepth = page.depth();

            if (oldPageLocalDepth == directory.getGlobalDepth()) {
                directory.extend(); // This increases global depth
            }

            int newSplitPagesLocalDepth = oldPageLocalDepth + 1;
            Page<K, V> newPage1 = dataStore.allocateNewPage(newSplitPagesLocalDepth);
            Page<K, V> newPage2 = dataStore.allocateNewPage(newSplitPagesLocalDepth);

            // Collect all entries from the old page + the new entry to be inserted
            List<Entry<K, V>> entriesToRedistribute = new ArrayList<>(page.getEntries());
            entriesToRedistribute.add(Entry.createEntry(key, value));
            page.clearEntriesForSplit(); // Old page is now empty, ready to be potentially reused or its space noted as free

            // Redistribute entries to newPage1 and newPage2
            for (Entry<K, V> entry : entriesToRedistribute) {
                long entryHash = entry.key().hashCode();
                // Use the bit at position 'oldPageLocalDepth' (0-indexed) to decide
                if (((entryHash >> oldPageLocalDepth) & 1) == 0) {
                    newPage1.put(entry.key(), entry.value());
                } else {
                    newPage2.put(entry.key(), entry.value());
                }
            }
            // dataStore.writePage(newPage1); // Assumed page.put persists
            // dataStore.writePage(newPage2);

            // Update directory pointers. All directory entries that previously pointed to the
            // original 'page' need to be updated.
            long oldPageDirPrefix = directory.getDirectoryIndex(hashCode) & ((1L << oldPageLocalDepth) - 1);

            for (long i = 0; i < (1L << directory.getGlobalDepth()); i++) {
                if ((i & ((1L << oldPageLocalDepth) - 1)) == oldPageDirPrefix) {
                    if (((i >> oldPageLocalDepth) & 1) == 0) {
                        directory.put(i, newPage1.getId());
                    } else {
                        directory.put(i, newPage2.getId());
                    }
                }
            }
            // The new entry (key, value) has now been placed into either newPage1 or newPage2.
        } else { // Page has space
            page.put(key, value);
            // dataStore.writePage(page);
        }
        size++;
        dirty = true;
    }

    public long size() {
        return size;
    }

    public void save() throws IOException {
        if (dirty) {
            directory.save(metadataFile); // Directory saves itself using the RAF
            saveSize(); // Hash table's own size
            dirty = false;
            System.out.println("FileBasedEHash: Saved. Size: " + size);
        }
    }

    private void loadSize() throws IOException {
        if (metadataFile.length() >= HASH_SIZE_METADATA_OFFSET + Long.BYTES) {
            metadataFile.seek(HASH_SIZE_METADATA_OFFSET);
            this.size = metadataFile.readLong();
            System.out.println("FileBasedEHash: Size loaded: " + this.size);
        } else {
            this.size = 0;
            System.out.println("FileBasedEHash: Size metadata not found or file too small, size set to 0.");
        }
    }

    private void saveSize() throws IOException {
        metadataFile.seek(HASH_SIZE_METADATA_OFFSET);
        metadataFile.writeLong(size);
    }

    public void close() throws IOException {
        save();
        // RAF for metadataFile is managed externally (by MergedHashingImplementations)
        System.out.println("FileBasedEHash: Closed (RAF managed externally).");
    }
}


public class MergedHashingImplementations {
    private static final String FB_CSV_FILE = "csv/AI/persons_for_fb_hashing.csv";
    private static final String FB_HASH_STORAGE_FILE = "csv/AI/extendible_hash_storage.dat"; // For directory, pages, metadata
    private static final String FB_EXTERNAL_DATA_RECORDS_FILE = "csv/AI/persons_external_records.dat"; // Actual person data

    private FileBasedEHash<Integer, Long> extendibleHash;
    private RandomAccessFile hashStorageRaf; // RAF for the hash structure itself
    // RAF for externalDataStorageFile is managed per operation for simplicity or could be member

    public MergedHashingImplementations() throws IOException {
        hashStorageRaf = new RandomAccessFile(FB_HASH_STORAGE_FILE, "rw");

        FileBasedDirectory directory = new FileBasedDirectory(hashStorageRaf);
        FileBasedDataStore dataStore = new FileBasedDataStore(hashStorageRaf); // Both use same RAF
        this.extendibleHash = new FileBasedEHash<>(directory, dataStore, hashStorageRaf); // Metadata also in same RAF
    }

    public void processCSVAndStorePositions() throws IOException {
        // Create dummy CSV if it doesn't exist
        File csvFileObj = new File(FB_CSV_FILE);
        if (!csvFileObj.exists()) {
            System.out.println("Creating dummy CSV for FileBasedHashing: " + FB_CSV_FILE);
            try (PrintWriter writer = new PrintWriter(csvFileObj)) {
                Random random = new Random();
                for (int i = 1; i <= 210000; i++) { // Enough to cause some splits
                    writer.println(i + ", Person " + i + ", Age " + random.nextInt(18, 80));
                }
            }
        }
        
        try (RandomAccessFile externalDataRaf = new RandomAccessFile(FB_EXTERNAL_DATA_RECORDS_FILE, "rw")) {
            externalDataRaf.setLength(0); // Clear existing external data

            try (Stream<String> lines = Files.lines(Paths.get(FB_CSV_FILE), StandardCharsets.UTF_8)) {
                long currentPosition = 0;
                for (String line : (Iterable<String>) lines::iterator) {
                    if (line.trim().isEmpty()) continue;
                    String[] parts = line.split(",");
                    if (parts.length > 0) {
                        try {
                            int id = Integer.parseInt(parts[0].trim());
                            externalDataRaf.seek(currentPosition);
                            externalDataRaf.writeInt(id); // Store ID for verification
                            externalDataRaf.writeUTF(line); // Store full line (UTF handles length)

                            extendibleHash.put(id, currentPosition); // Store offset of record start
                            currentPosition = externalDataRaf.getFilePointer(); // Update for next record

                        } catch (NumberFormatException e) {
                            System.err.println("Skipping invalid ID in FileBasedHashing: " + parts[0]);
                        } catch (IOException e) {
                            System.err.println("IOException during CSV processing for FileBasedHashing (ID: " + parts[0] + "): " + e.getMessage());
                            e.printStackTrace(); // More detail
                        }
                    }
                }
            }
        } // externalDataRaf is closed here by try-with-resources
        
        extendibleHash.save();
        System.out.println("FileBasedHashing CSV processing and storage complete.");
    }

    public String getPersonData(int id) throws IOException {
        Long position = extendibleHash.get(id);
        if (position != null) {
            try (RandomAccessFile raf = new RandomAccessFile(FB_EXTERNAL_DATA_RECORDS_FILE, "r")) {
                raf.seek(position);
                int retrievedId = raf.readInt();
                String line = raf.readUTF();
                if (retrievedId == id) {
                    return line;
                } else {
                    System.err.println("FB Hashing: ID mismatch at offset for key " + id + ". Expected " + id + ", found " + retrievedId);
                    return null;
                }
            }
        }
        return null;
    }

    public void close() throws IOException {
        if (extendibleHash != null) extendibleHash.close(); // Saves hash metadata
        if (hashStorageRaf != null) hashStorageRaf.close();
        System.out.println("FileBasedExtendibleHashing resources closed.");
    }

    public static void runFileBasedExtendibleHashing() {
        System.out.println("\n--- Running FileBasedExtendibleHashing Test ---\n");
        
        //Exclusão de arquivos
        new File(FB_CSV_FILE).delete();
        new File(FB_HASH_STORAGE_FILE).delete();
        new File(FB_EXTERNAL_DATA_RECORDS_FILE).delete();

        MergedHashingImplementations storage = null;
        try {
            storage = new MergedHashingImplementations();
            storage.processCSVAndStorePositions();

            int[] searchIds = {1, 15, 30, 49, 50, 100, 7,210000}; // Test existing and non-existing
            for (int searchId : searchIds) {
                System.out.println("\nSearching for person with ID (FB): " + searchId);
                String personData = storage.getPersonData(searchId);
                if (personData != null) {
                    System.out.println("Data for ID " + searchId + ": " + personData);
                } else {
                    System.out.println("Person with ID " + searchId + " not found.");
                }
            }

        } catch (IOException e) {
            System.err.println("Error during FileBasedHashing storage operation: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) { // Catch any other unexpected runtime exceptions
            System.err.println("General error during FileBasedHashing storage operation: " + e.getMessage());
            e.printStackTrace();
        } finally {
            if (storage != null) {
                try {
                    storage.close();
                } catch (IOException e) {
                    System.err.println("Error closing FileBasedHashing storage: " + e.getMessage());
                }
            }
        }
        System.out.println("--- FileBasedExtendibleHashing Test Finished ---");
    }

    public static void main(String[] args) {
        System.out.println("Starting Hashing Implementations Test Suite...");
        System.out.println("Current Date/Time: " + new Date());
        System.out.println("Current working directory: " + Paths.get(".").toAbsolutePath().normalize().toString());
        System.out.println("Note: File operations depend on IDE/environment permissions.");

        ExtensibleHashingCSV.runExtensibleHashingCSV();
        System.out.println("\n=================================================\n");
        MergedHashingImplementations.runFileBasedExtendibleHashing();

        System.out.println("\nHashing Implementations Test Suite Finished.");
        System.out.println("Review console for output, errors, and check for created .dat/.csv files.");
    }
}
