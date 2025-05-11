import java.io.*;
import java.nio.ByteBuffer;
import java.nio.IntBuffer;
import java.nio.LongBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.stream.Stream;

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
}

class EHashStats {
    // Placeholder for statistics
}

interface Page<K, V> {
    boolean contains(K key);

    V get(K key);

    void put(K key, V value);

    boolean hasSpaceFor(K key, V value);

    int depth();

    long getId();

    Collection<Entry<K, V>> getEntries();
}

class FileBasedPage implements Page<Integer, Long> {
    private static final int MAX_ENTRIES = 3; // Example capacity
    private final long fileOffset;
    private final int depth;
    private final RandomAccessFile raf;

    public FileBasedPage(long fileOffset, int depth, RandomAccessFile raf) throws IOException {
        this.fileOffset = fileOffset;
        this.depth = depth;
        this.raf = raf;
        // Initialize if new page
        if (raf.length() <= fileOffset) {
            raf.seek(fileOffset);
            raf.writeInt(0); // Entry count
            raf.writeInt(depth);
            // Space for MAX_ENTRIES * (key: int, value: long)
            raf.seek(fileOffset + Integer.BYTES + Integer.BYTES + MAX_ENTRIES * (Integer.BYTES + Long.BYTES));
        }
    }

    @Override
    public boolean contains(Integer key) {
        try {
            raf.seek(fileOffset + Integer.BYTES); // Skip entry count
            int storedDepth = raf.readInt();
            if (storedDepth != depth)
                return false;

            int entryCount = readEntryCount();
            for (int i = 0; i < entryCount; i++) {
                raf.seek(fileOffset + 2 * Integer.BYTES + i * (Integer.BYTES + Long.BYTES));
                if (raf.readInt() == key) {
                    return true;
                }
            }
            return false;
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public Long get(Integer key) {
        try {
            raf.seek(fileOffset + Integer.BYTES); // Skip entry count
            int storedDepth = raf.readInt();
            if (storedDepth != depth)
                return null;

            int entryCount = readEntryCount();
            for (int i = 0; i < entryCount; i++) {
                raf.seek(fileOffset + 2 * Integer.BYTES + i * (Integer.BYTES + Long.BYTES));
                if (raf.readInt() == key) {
                    return raf.readLong();
                }
            }
            return null;
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public void put(Integer key, Long value) {
        try {
            int entryCount = readEntryCount();
            if (entryCount >= MAX_ENTRIES) {
                throw new IllegalStateException("Page is full");
            }

            // Check if key exists, update if so (for simplicity, we don't in this basic example)

            raf.seek(fileOffset + 2 * Integer.BYTES + entryCount * (Integer.BYTES + Long.BYTES));
            raf.writeInt(key);
            raf.writeLong(value);
            incrementEntryCount();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public boolean hasSpaceFor(Integer key, Long value) {
        return readEntryCount() < MAX_ENTRIES;
    }

    @Override
    public int depth() {
        try {
            raf.seek(fileOffset + Integer.BYTES);
            return raf.readInt();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public long getId() {
        return fileOffset; // Using file offset as ID for simplicity
    }

    @Override
    public Collection<Entry<Integer, Long>> getEntries() {
        List<Entry<Integer, Long>> entries = new ArrayList<>();
        try {
            int entryCount = readEntryCount();
            for (int i = 0; i < entryCount; i++) {
                raf.seek(fileOffset + 2 * Integer.BYTES + i * (Integer.BYTES + Long.BYTES));
                int key = raf.readInt();
                long value = raf.readLong();
                entries.add(Entry.createEntry(key, value));
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return entries;
    }

    private int readEntryCount() {
        try {
            raf.seek(fileOffset);
            return raf.readInt();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private void incrementEntryCount() {
        try {
            raf.seek(fileOffset);
            raf.writeInt(readEntryCount() + 1);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}

interface Directory {
    long get(int hashCode);

    int getDepth();

    void extend();

    void put(long index, long bucketOffset);

    void load(RandomAccessFile raf) throws IOException;

    void save(RandomAccessFile raf) throws IOException;
}

class FileBasedDirectory implements Directory {
    private static final int INITIAL_DEPTH = 1;
    private static final int DIRECTORY_ENTRY_SIZE = Long.BYTES; // Stores file offset of the bucket
    private static final long DIRECTORY_OFFSET = 0;
    private int depth = INITIAL_DEPTH;
    private final Map<Long, Long> directory = new HashMap<>(); // In-memory representation for faster access
    private long directorySizeInBytes;

    public FileBasedDirectory(RandomAccessFile raf) throws IOException {
        load(raf);
    }

    @Override
    public long get(int hashCode) {
        long mask = (1L << depth) - 1;
        return directory.get((long) (hashCode & mask));
    }

    @Override
    public int getDepth() {
        return depth;
    }

    @Override
    public void extend() {
        int newDepth = depth + 1;
        long newSize = 1L << newDepth;
        long oldSize = 1L << depth;
        Map<Long, Long> newDirectory = new HashMap<>(directory);
        for (long i = 0; i < oldSize; i++) {
            newDirectory.put(i | oldSize, directory.get(i));
        }
        depth = newDepth;
        directory.clear();
        directory.putAll(newDirectory);
        directorySizeInBytes = newSize * DIRECTORY_ENTRY_SIZE;
    }

    @Override
    public void put(long index, long bucketOffset) {
        directory.put(index, bucketOffset);
    }

    @Override
    public void load(RandomAccessFile raf) throws IOException {
        if (raf.length() > DIRECTORY_OFFSET) {
            raf.seek(DIRECTORY_OFFSET);
            depth = raf.readInt();
            long directorySize = 1L << depth;
            directorySizeInBytes = directorySize * DIRECTORY_ENTRY_SIZE;
            for (long i = 0; i < directorySize; i++) {
                directory.put(i, raf.readLong());
            }
        } else {
            // Initialize directory
            depth = INITIAL_DEPTH;
            long initialDataOffset = 2 * Integer.BYTES + (1L << INITIAL_DEPTH) * Long.BYTES;
            directory.put(0L, initialDataOffset);
            directory.put(1L, initialDataOffset);
            directorySizeInBytes = (1L << INITIAL_DEPTH) * DIRECTORY_ENTRY_SIZE;
        }
    }

    @Override
    public void save(RandomAccessFile raf) throws IOException {
        raf.seek(DIRECTORY_OFFSET);
        raf.writeInt(depth);
        long directorySize = 1L << depth;
        for (long i = 0; i < directorySize; i++) {
            raf.writeLong(directory.get(i));
        }
    }
}

interface DataStore<K, V> {
    Page<K, V> get(long bucketOffset);

    Page<K, V> allocate(int depth) throws IOException;

    void remove(long bucketOffset); // Not typically needed in basic extendible hashing

    void put(Page<K, V> page); // Updates are done directly on the FileBasedPage

    long getNextAvailableOffset();
}

class FileBasedDataStore implements DataStore<Integer, Long> {
    private final RandomAccessFile raf;
    private long nextAvailableOffset;

    public FileBasedDataStore(RandomAccessFile raf) throws IOException {
        this.raf = raf;
        // Calculate initial offset after directory
        long initialDataOffset = 2 * Integer.BYTES + (1L << 1) * Long.BYTES;
        if (raf.length() <= initialDataOffset) {
            nextAvailableOffset = initialDataOffset;
        } else {
            nextAvailableOffset = raf.length();
        }
    }

    @Override
    public Page<Integer, Long> get(long bucketOffset) {
        try {
            return new FileBasedPage(bucketOffset, -1, raf); // Depth is read from the page
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public Page<Integer, Long> allocate(int depth) throws IOException {
        long currentOffset = nextAvailableOffset;
        // Allocate space for the page header (entry count, depth) and initial entries
        long pageSize = Integer.BYTES + Integer.BYTES + 3 * (Integer.BYTES + Long.BYTES); // Example capacity 3
        nextAvailableOffset += pageSize;
        return new FileBasedPage(currentOffset, depth, raf);
    }

    @Override
    public void remove(long bucketOffset) {
        // Not typically needed in basic extendible hashing as buckets are split, not deleted.
        // A more advanced implementation might handle merging.
    }

    @Override
    public void put(Page<Integer, Long> page) {
        // Updates to the page are handled directly by the FileBasedPage methods.
    }

    @Override
    public long getNextAvailableOffset() {
        return nextAvailableOffset;
    }
}

class BinUtils {
    public static long[] enumerateValues(int globalDepth, int localDepth, long prefix) {
        long count = 1L << (globalDepth - localDepth);
        long[] result = new long[(int) count];
        for (int i = 0; i < count; i++) {
            result[i] = (prefix << (globalDepth - localDepth)) | i;
        }
        return result;
    }
}

public class FileBasedExtendibleHashing {

    private static final String CSV_FILE = "persons.csv";
    private static final String HASH_FILE = "extendible_hash.dat";
    private static final String DATA_FILE = "persons_data.dat";
    private static final int RECORD_SIZE = 100; // Example fixed record size

    private FileBasedEHash<Integer, Long> extendibleHash;

    public FileBasedExtendibleHashing() throws IOException {
        RandomAccessFile raf = new RandomAccessFile(HASH_FILE, "rw");
        FileBasedDirectory directory = new FileBasedDirectory(raf);
        FileBasedDataStore dataStore = new FileBasedDataStore(raf);
        this.extendibleHash = new FileBasedEHash<>(directory, dataStore, raf);
    }

    public void processCSVAndStorePositions() throws IOException {
        try (RandomAccessFile raf = new RandomAccessFile(DATA_FILE, "rw")) {
            raf.setLength(0); // Clear existing data

            try (Stream<String> lines = Files.lines(Paths.get(CSV_FILE))) {
                long currentPosition = 0;
                for (String line : (Iterable<String>) lines::iterator) {
                    String[] parts = line.split(",");
                    if (parts.length > 0) {
                        try {
                            int id = Integer.parseInt(parts[0].trim());
                            // Simulate writing person data to RandomAccessFile
                            raf.writeInt(id);
                            raf.writeLong(currentPosition); // Store the position
                            byte[] padding = new byte[RECORD_SIZE - Integer.BYTES - Long.BYTES];
                            raf.write(padding);

                            extendibleHash.put(id, currentPosition);
                            currentPosition += RECORD_SIZE;
                        } catch (NumberFormatException e) {
                            System.err.println("Skipping invalid ID: " + parts[0]);
                        }
                    }
                }
            } catch (IOException e) {
                System.err.println("Error reading CSV file: " + e.getMessage());
            }
        }
        extendibleHash.save(); // Persist the hash table to file
    }

    public Long getPosition(int id) throws IOException {
        return extendibleHash.get(id);
    }

    public void close() throws IOException {
        extendibleHash.close();
    }

    public static void main(String[] args) {
        // Create a dummy CSV file
        try (PrintWriter writer = new PrintWriter(new File(CSV_FILE))) {
            Random random = new Random();
            for (int i = 1; i <= 2000; i++) {
                writer.println(i + ",Person " + i + ",Age " + random.nextInt(80));
            }
        } catch (FileNotFoundException e) {
            System.err.println("Error creating dummy CSV: " + e.getMessage());
            return;
        }

        FileBasedExtendibleHashing storage = null;
        try {
            storage = new FileBasedExtendibleHashing();
            storage.processCSVAndStorePositions();

            int searchId = 1500;
            Long position = storage.getPosition(searchId);
            if (position != null) {
                System.out.println("Position of person with ID " + searchId + " in persons_data.dat: " + position);
                try (RandomAccessFile raf = new RandomAccessFile("persons_data.dat", "r")) {
                    raf.seek(position);
                    int retrievedId = raf.readInt();
                    long retrievedPosition = raf.readLong();
                    System.out.println("Verifying from data file: ID=" + retrievedId + ", Position=" + retrievedPosition);
                } catch (IOException e) {
                    System.err.println("Error reading from data file: " + e.getMessage());
                }
            } else {
                System.out.println("Person with ID " + searchId + " not found.");
            }

        } catch (IOException e) {
            System.err.println("Error during storage operation: " + e.getMessage());
        } finally {
            if (storage != null) {
                try {
                    storage.close();
                } catch (IOException e) {
                    System.err.println("Error closing storage: " + e.getMessage());
                }
            }
            new File(CSV_FILE).delete();
            new File("extendible_hash.dat").delete();
            new File("persons_data.dat").delete();
        }
    }
}

class FileBasedEHash<K, V> {
    private final Directory directory;
    private final DataStore<K, V> dataStore;
    private final RandomAccessFile raf;
    private final EHashStats stats = new EHashStats();
    private long size = 0;
    private boolean dirty = false; // Flag to track changes

    public FileBasedEHash(Directory directory, DataStore<K, V> dataStore, RandomAccessFile raf) throws IOException {
        this.directory = directory;
        this.dataStore = dataStore;
        this.raf = raf;
        loadSize();
    }

    public boolean contains(K key) {
        long hashCode = key.hashCode();
        long bucketOffset = directory.get(hashCode);
        if (bucketOffset != 0) {
            Page<K, V> page = dataStore.get(bucketOffset);
            return page.contains(key);
        }
        return false;
    }

    public V get(K key) throws IOException {
        long hashCode = key.hashCode();
        long bucketOffset = directory.get(hashCode);
        if (bucketOffset != 0) {
            Page<K, V> page = dataStore.get(bucketOffset);
            return page.get(key);
        }
        return null;
    }

    public void put(K key, V value) throws IOException {
        long hashCode = key.hashCode();
        long bucketOffset = directory.get(hashCode);

        Page<K, V> page;
        if (bucketOffset == 0) {
            page = dataStore.allocate(directory.getDepth());
            bucketOffset = ((FileBasedPage) page).getId();
            directory.put(hashCode, bucketOffset);
        } else {
            page = dataStore.get(bucketOffset);
            if (page.contains(key)) {
                return;
            }
        }

        if (!page.hasSpaceFor(key, value)) {
            int localDepth = page.depth();
            if (localDepth == directory.getDepth()) {
                directory.extend();
            }

            int newBucketsDepth = localDepth + 1;
            Page<K, V> bucket1 = dataStore.allocate(newBucketsDepth);
            long bucket1Offset = ((FileBasedPage) bucket1).getId();
            Page<K, V> bucket2 = dataStore.allocate(newBucketsDepth);
            long bucket2Offset = ((FileBasedPage) bucket2).getId();

            Collection<Entry<K, V>> swapElements = page.getEntries();
            swapElements.add(Entry.createEntry(key, value));
            for (Entry<K, V> e : swapElements) {
                long h = e.key.hashCode();
                if (((h >> (newBucketsDepth - 1)) & 1) == 1) {
                    bucket2.put(e.key, e.value);
                } else {
                    bucket1.put(e.key, e.value);
                }
            }

            long[] bucketCodes = BinUtils.enumerateValues(directory.getDepth(), localDepth, hashCode & ((1 << localDepth) - 1));
            for (long i : bucketCodes) {
                if (((i >> (newBucketsDepth - 1)) & 1) == 1) {
                    directory.put(i, bucket2Offset);
                } else {
                    directory.put(i, bucket1Offset);
                }
            }

            // No need to remove the old page, its data is overwritten.
            dataStore.put(bucket1);
            dataStore.put(bucket2);
            dirty = true;
        } else {
            page.put(key, value);
            directory.put(hashCode, bucketOffset);
            dataStore.put(page);
            dirty = true;
        }
        size++;
    }

    public long size() {
        return size;
    }

    public Directory getDirectory() {
        return directory;
    }

    public DataStore<K, V> getDataStore() {
        return dataStore;
    }

    public EHashStats getStats() {
        return stats;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("EXTENDIBLE HASH { directory = ").append(directory.getClass().getSimpleName())
                .append(", dataStore = ").append(dataStore.getClass().getSimpleName())
                .append(", size = ").append(size).append(" }");
        sb.append(stats);
        return sb.toString();
    }

    public void save() throws IOException {
        if (dirty) {
            directory.save(raf);
            saveSize();
            dirty = false;
        }
    }

    private void loadSize() throws IOException {
        if (raf.length() > 0) {
            raf.seek(raf.length() - Long.BYTES);
            size = raf.readLong();
        } else {
            size = 0;
        }
    }

    private void saveSize() throws IOException {
        raf.seek(raf.length() - Long.BYTES);
        raf.writeLong(size);
    }

    public void close() throws IOException {
        save();
        raf.close();
    }
}

