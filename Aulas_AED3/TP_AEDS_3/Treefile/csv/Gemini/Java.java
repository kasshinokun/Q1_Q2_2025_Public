import java.io.*;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.zip.CRC32;

public class ExtensibleHashingCSV {

    private static final int BUCKET_SIZE = 4; // Number of entries per bucket
    private static final String DATA_FILE = "data.dat";
    private static final String INDEX_FILE = "index.dat";
    private static final String REGISTRY_FILE = "registry.dat";

    private RandomAccessFile dataFile;
    private FileChannel dataChannel;
    private RandomAccessFile indexFile;
    private FileChannel indexChannel;
    private int globalDepth;
    private List<Bucket> directory;

    public ExtensibleHashingCSV() {
        this.globalDepth = 1;
        this.directory = new ArrayList<>(1 << globalDepth);
        for (int i = 0; i < directory.size(); i++) {
            directory.add(new Bucket(globalDepth));
        }
    }

    public static void main(String[] args) {
        ExtensibleHashingCSV hashing = new ExtensibleHashingCSV();
        String csvFile = "data.csv"; // Replace with your CSV file path

        try {
            hashing.initializeFiles();
            hashing.loadRegistry();
            hashing.processCSV(csvFile, line -> line.split(",")[0]); // Assuming the first column is the key
            hashing.saveRegistry();
            hashing.closeFiles();
        } catch (IOException e) {
            e.printStackTrace();
        }

        // Example of reading a record by key
        try {
            hashing = new ExtensibleHashingCSV();
            hashing.initializeFiles();
            hashing.loadRegistry();
            String searchKey = "1"; // Example key
            long offset = hashing.findRecordOffset(searchKey);
            if (offset != -1) {
                String record = hashing.readRecord(offset);
                System.out.println("Record found for key '" + searchKey + "': " + record);
            } else {
                System.out.println("Record with key '" + searchKey + "' not found.");
            }
            hashing.closeFiles();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void initializeFiles() throws IOException {
        dataFile = new RandomAccessFile(DATA_FILE, "rw");
        dataChannel = dataFile.getChannel();
        indexFile = new RandomAccessFile(INDEX_FILE, "rw");
        indexChannel = indexFile.getChannel();
    }

    private void closeFiles() throws IOException {
        if (dataChannel != null) dataChannel.close();
        if (dataFile != null) dataFile.close();
        if (indexChannel != null) indexChannel.close();
        if (indexFile != null) indexFile.close();
    }

    private void loadRegistry() throws IOException {
        File registryFile = new File(REGISTRY_FILE);
        if (registryFile.exists()) {
            try (DataInputStream dis = new DataInputStream(new FileInputStream(registryFile))) {
                this.globalDepth = dis.readInt();
                int directorySize = 1 << this.globalDepth;
                this.directory = new ArrayList<>(directorySize);
                for (int i = 0; i < directorySize; i++) {
                    int localDepth = dis.readInt();
                    int bucketEntryCount = dis.readInt();
                    Bucket bucket = new Bucket(localDepth);
                    for (int j = 0; j < bucketEntryCount; j++) {
                        String key = dis.readUTF();
                        long offset = dis.readLong();
                        bucket.entries.put(key, offset);
                    }
                    this.directory.add(bucket);
                }
            }
        } else {
            this.globalDepth = 1;
            this.directory = new ArrayList<>(1 << globalDepth);
            for (int i = 0; i < directory.size(); i++) {
                directory.add(new Bucket(globalDepth));
            }
        }
    }

    private void saveRegistry() throws IOException {
        try (DataOutputStream dos = new DataOutputStream(new FileOutputStream(REGISTRY_FILE))) {
            dos.writeInt(this.globalDepth);
            for (Bucket bucket : this.directory) {
                dos.writeInt(bucket.localDepth);
                dos.writeInt(bucket.entries.size());
                for (Map.Entry<String, Long> entry : bucket.entries.entrySet()) {
                    dos.writeUTF(entry.getKey());
                    dos.writeLong(entry.getValue());
                }
            }
        }
    }

    public void processCSV(String csvFile, Function<String, String> keyExtractor) throws IOException {
        try (BufferedReader br = new BufferedReader(new FileReader(csvFile))) {
            String line;
            while ((line = br.readLine()) != null) {
                long currentOffset = dataFile.length();
                byte[] recordBytes = (line + "\n").getBytes(); // Add newline for easier reading later
                dataFile.write(recordBytes);
                String key = keyExtractor.apply(line);
                insert(key, currentOffset);
            }
        }
    }

    private void insert(String key, long offset) throws IOException {
        int bucketIndex = getBucketIndex(hash(key), globalDepth);
        Bucket bucket = directory.get(bucketIndex);

        if (bucket.entries.size() < BUCKET_SIZE) {
            bucket.entries.put(key, offset);
        } else {
            splitBucket(bucketIndex);
            insert(key, offset); // Retry insertion after splitting
        }
    }

    private void splitBucket(int bucketIndex) throws IOException {
        Bucket oldBucket = directory.get(bucketIndex);
        int localDepth = oldBucket.localDepth;

        if (localDepth == globalDepth) {
            // Double the directory
            int oldSize = directory.size();
            for (int i = 0; i < oldSize; i++) {
                directory.add(directory.get(i));
            }
            globalDepth++;
        }

        localDepth++;
        Bucket newBucket = new Bucket(localDepth);
        directory.set(getBucketIndex(getMask(localDepth - 1) | (1 << (localDepth - 1)), globalDepth), newBucket);
        oldBucket.localDepth = localDepth;

        // Redistribute entries
        HashMap<String, Long> oldEntries = new HashMap<>(oldBucket.entries);
        oldBucket.entries.clear();

        for (Map.Entry<String, Long> entry : oldEntries.entrySet()) {
            insert(entry.getKey(), entry.getValue());
        }
    }

    private long findRecordOffset(String key) {
        int bucketIndex = getBucketIndex(hash(key), globalDepth);
        Bucket bucket = directory.get(bucketIndex);
        return bucket.entries.getOrDefault(key, -1L);
    }

    private String readRecord(long offset) throws IOException {
        if (offset == -1) {
            return null;
        }
        dataFile.seek(offset);
        return dataFile.readLine(); // Assuming records are newline-separated
    }

    private int getBucketIndex(long hash, int depth) {
        return (int) (hash & getMask(depth));
    }

    private long hash(String key) {
        CRC32 crc = new CRC32();
        crc.update(key.getBytes());
        return crc.getValue();
    }

    private int getMask(int depth) {
        return (1 << depth) - 1;
    }

    private static class Bucket {
        int localDepth;
        HashMap<String, Long> entries;

        public Bucket(int localDepth) {
            this.localDepth = localDepth;
            this.entries = new HashMap<>(BUCKET_SIZE);
        }
    }
}
