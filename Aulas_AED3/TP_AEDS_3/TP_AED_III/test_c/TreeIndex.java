package test_c;

import java.io.RandomAccessFile;
import java.io.IOException;
import java.util.TreeMap;

public class TreeIndex {
    private TreeMap<String, Long> index = new TreeMap<>();
    private RandomAccessFile file;

    public TreeIndex(String filename) throws IOException {
        file = new RandomAccessFile(filename, "rw");
    }

    public void buildIndex() throws IOException {
        // Logic to read the file and populate the index
        // Example:
        String line;
        long position = 0;
        while ((line = file.readLine()) != null) {
            String[] parts = line.split(","); // Assuming comma-separated values
            if (parts.length > 0) {
                index.put(parts[0], position); // Indexing the first value in the line
            }
            position = file.getFilePointer();
        }
    }

     public Long find(String key) {
        return index.get(key);
    }

    public void close() throws IOException {
        file.close();
    }
}
