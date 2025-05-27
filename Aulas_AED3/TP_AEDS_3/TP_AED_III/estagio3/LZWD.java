package estagio3;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class LZWD {

    private static final int MAX_DICTIONARY_SIZE = 1 << 24; // Must match compressor's MAX_DICTIONARY_SIZE

    public void decompress(String inputFilePath, String outputFilePath) throws IOException {
        try (DataInputStream dis = new DataInputStream(new FileInputStream(inputFilePath));
             BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream(outputFilePath))) {

            List<String> dictionary = new ArrayList<>();
            int dictionarySize = 256; // ASCII characters

            // Initialize dictionary with single ASCII characters
            for (int i = 0; i < dictionarySize; i++) {
                dictionary.add("" + (char) i);
            }

            int currentCode;
            int previousCode;
            String currentSequence;

            // Read the first code
            if (dis.available() > 0) {
                previousCode = dis.readInt();
                currentSequence = dictionary.get(previousCode);
                bos.write(currentSequence.getBytes()); // Write initial sequence
            } else {
                System.out.println("Input file is empty.");
                return;
            }

            int nextCode = dictionarySize; // Next available code for dictionary

            while (dis.available() > 0) {
                currentCode = dis.readInt();

                String entry;
                if (dictionary.size() > currentCode) { // Code exists in dictionary
                    entry = dictionary.get(currentCode);
                } else if (currentCode == dictionary.size()) { // Special case: P + P[0]
                    entry = dictionary.get(previousCode) + dictionary.get(previousCode).charAt(0);
                } else {
                    throw new IllegalStateException("Bad compressed code: " + currentCode);
                }

                bos.write(entry.getBytes());

                // Add previous + current[0] to dictionary
                if (nextCode < MAX_DICTIONARY_SIZE) {
                    dictionary.add(dictionary.get(previousCode) + entry.charAt(0));
                    nextCode++;
                }
                previousCode = currentCode;
            }
            System.out.println("The choosed file was "+inputFilePath);
            System.out.println("File decompressed successfully as: " + outputFilePath);
            System.out.println("Decompression complete. Dictionary size: " + dictionary.size());
        }
    }

    public static void main(String[] args) {
        LZWD decompressor = new LZWD();
        String compressedFile = "large_file.lzw";
        String decompressedFile = "large_file_decompressed.csv";

        try {
            long startTime = System.nanoTime();
            decompressor.decompress(compressedFile, decompressedFile);
            long endTime = System.nanoTime();
            long duration = (endTime - startTime) / 1_000_000; // milliseconds
            System.out.println("Decompression time: " + duration + " ms");

            // Optional: Verify decompression by comparing original and decompressed files
            // For large files, direct comparison might be slow.
            // A checksum or hash comparison would be more efficient.
            // For this example, you can manually check the content.

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}