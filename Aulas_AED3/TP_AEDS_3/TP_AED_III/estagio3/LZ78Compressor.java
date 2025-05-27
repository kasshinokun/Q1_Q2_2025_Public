package estagio3;

import java.io.*;
import java.nio.file.Files; // Used for convenient file reading for verification
import java.nio.file.Paths; // Used for convenient file reading for verification
import java.util.*;

public class LZ78Compressor {

    // --- Constants ---
    private static final int INITIAL_DICTIONARY_SIZE = 256; // For single bytes (0-255)
    private static final int MAX_DICTIONARY_SIZE = 65536; // Max 2^16 entries, including the reset code (0)
    // The number of bits required to represent MAX_DICTIONARY_SIZE - 1
    // For 65536, it's 16 bits (log2(65536) = 16).
    private static final int MAX_CODE_BITS = (int) Math.ceil(Math.log(MAX_DICTIONARY_SIZE) / Math.log(2));
    private static final int BUFFER_SIZE = 8192; // 8KB buffer for Buffered streams

    // Special code to signal a dictionary reset (matches C code's 0 for null symbol)
    private static final int RESET_CODE = 0;
    // Number of bits to store the MAX_DICTIONARY_SIZE in the file header (as in C code)
    private static final int DICTIONARY_SIZE_HEADER_BITS = 20;
    // Dictionary usage ratio for triggering a reset (matches C code's DICT_MAX_USAGE_RATIO)
    private static final double DICT_RESET_USAGE_RATIO = 0.8;


    // --- Private Nested Class for Trie Node (Compression Dictionary) ---
    // This class represents a node in the Trie (prefix tree) used for the compression dictionary.
    // Each node stores its children (next possible bytes in a sequence) and the dictionary code
    // if the path to this node forms a complete, recognized sequence.
    private static class TrieNode {
        Map<Byte, TrieNode> children; // Maps a byte to the next TrieNode in the sequence
        int code; // The dictionary code assigned to the sequence ending at this node

        public TrieNode() {
            children = new HashMap<>();
            code = -1; // -1 indicates no code assigned yet, meaning this node is not an end of a dictionary entry
        }
    }

    // --- Private Static Nested Class for Bit Output Stream ---
    // This class allows writing data bit by bit to an underlying OutputStream.
    // It buffers bits into bytes and writes them when a full byte is accumulated or upon closing.
    private static class BitOutputStream implements AutoCloseable {
        private BufferedOutputStream out; // The underlying buffered output stream
        private int currentByte; // Stores bits as they are accumulated (0-255)
        private int bitsInCurrentByte; // Counts how many bits are currently in currentByte (0-7)

        public BitOutputStream(OutputStream os) {
            this.out = new BufferedOutputStream(os);
            this.currentByte = 0;
            this.bitsInCurrentByte = 0;
        }

        /**
         * Writes a specified number of bits from an integer value to the stream.
         * The bits are written from most significant to least significant.
         * @param value The integer value from which bits will be written.
         * @param numBits The number of bits to write (1 to 32).
         * @throws IOException If an I/O error occurs.
         * @throws IllegalArgumentException If numBits is out of range or value doesn't fit in numBits.
         */
        public void writeBits(int value, int numBits) throws IOException {
            if (numBits <= 0 || numBits > 32) {
                throw new IllegalArgumentException("Number of bits must be between 1 and 32.");
            }
            // Check if the value fits within the specified number of bits for positive values.
            // This is important for ensuring data integrity during compression.
            // For 32-bit values, (1 << numBits) overflows, so handle separately or use 1L.
            if (numBits < 32 && (value < 0 || value >= (1 << numBits))) {
                 throw new IllegalArgumentException(String.format("Value %d does not fit in %d bits.", value, numBits));
            }
            // For numBits == 32, value can be any int, so no range check needed for positive values.

            // Iterate from the most significant bit to the least significant bit
            for (int i = numBits - 1; i >= 0; i--) {
                // Extract the i-th bit from the value
                boolean bit = ((value >> i) & 1) == 1;

                // Set the corresponding bit in currentByte
                if (bit) {
                    currentByte |= (1 << (7 - bitsInCurrentByte)); // Set bit from left (MSB first)
                }

                bitsInCurrentByte++; // Increment bit counter

                // If a full byte is accumulated, write it to the output stream
                if (bitsInCurrentByte == 8) {
                    out.write(currentByte);
                    currentByte = 0; // Reset byte buffer
                    bitsInCurrentByte = 0; // Reset bit counter
                }
            }
        }

        /**
         * Writes a single byte to the stream. Any currently buffered partial bits are flushed
         * as a complete byte before writing the new byte. This ensures byte alignment.
         * @param b The byte to write.
         * @throws IOException If an I/O error occurs.
         */
        public void writeByte(byte b) throws IOException {
            // Flush any remaining partial bits in currentByte before writing a full byte.
            // This ensures that subsequent reads are byte-aligned.
            if (bitsInCurrentByte > 0) {
                out.write(currentByte);
                currentByte = 0;
                bitsInCurrentByte = 0;
            }
            out.write(b); // Write the actual byte
        }

        /**
         * Closes the BitOutputStream, flushing any remaining buffered bits.
         * @throws IOException If an I/O error occurs during flushing or closing the underlying stream.
         */
        @Override
        public void close() throws IOException {
            // Flush any remaining bits that haven't formed a full byte yet
            if (bitsInCurrentByte > 0) {
                out.write(currentByte);
            }
            out.close(); // Close the underlying stream
        }
    }

    // --- Private Static Nested Class for Bit Input Stream ---
    // This class allows reading data bit by bit from an underlying InputStream.
    // It buffers bytes and provides methods to read a specified number of bits or a full byte.
    private static class BitInputStream implements AutoCloseable {
        private BufferedInputStream in; // The underlying buffered input stream
        private int currentByte; // Stores the current byte read from the stream
        private int bitsInCurrentByte; // Counts how many bits are remaining in currentByte (0-8)
        private boolean eofReached = false; // Flag to indicate if underlying stream EOF has been reached

        public BitInputStream(InputStream is) {
            this.in = new BufferedInputStream(is);
            this.currentByte = 0;
            this.bitsInCurrentByte = 0;
        }

        /**
         * Reads a single bit from the stream.
         * @return 0 or 1 if a bit is read, or -1 if the end of the stream is reached.
         * @throws IOException If an I/O error occurs.
         */
        private int readBit() throws IOException {
            // If no bits are left in currentByte, read a new byte from the underlying stream
            if (bitsInCurrentByte == 0) {
                int read = in.read();
                if (read == -1) {
                    eofReached = true; // Mark EOF when underlying stream returns -1
                    return -1; // Signal EOF
                }
                currentByte = read; // Store the new byte
                bitsInCurrentByte = 8; // Set bit counter to 8
            }

            // Extract the most significant bit from currentByte
            int bit = (currentByte >> (bitsInCurrentByte - 1)) & 1;
            bitsInCurrentByte--; // Decrement bit counter
            return bit;
        }

        /**
         * Reads a specified number of bits from the stream and reconstructs an integer.
         * Bits are read from most significant to least significant.
         * @param numBits The number of bits to read (1 to 32).
         * @return The integer value reconstructed from the bits.
         * @throws IOException If an I/O error occurs or unexpected end of stream is reached.
         * @throws IllegalArgumentException If numBits is out of range.
         * @throws EOFException If the end of the stream is reached before all bits can be read.
         */
        public int readBits(int numBits) throws IOException {
            if (numBits <= 0 || numBits > 32) {
                throw new IllegalArgumentException("Number of bits must be between 1 and 32.");
            }
            if (eofReached) { // Check EOF flag before attempting to read
                throw new EOFException("Attempted to read bits after end of stream.");
            }

            int value = 0;
            for (int i = 0; i < numBits; i++) {
                int bit = readBit();
                if (bit == -1) {
                    eofReached = true; // Ensure EOF flag is set on partial read failure
                    throw new EOFException("Unexpected end of stream while reading " + numBits + " bits.");
                }
                value = (value << 1) | bit; // Append the bit to the value
            }
            return value;
        }

        /**
         * Reads a single byte from the stream. This method handles cases where the stream
         * might not be on a byte boundary after a previous bit read by discarding remaining bits.
         * @return The byte read.
         * @throws IOException If an I/O error occurs.
         * @throws EOFException If the end of the stream is reached.
         */
        public byte readByte() throws IOException {
            // If there are partial bits buffered from a previous readBits() call,
            // discard them to align to the next full byte boundary.
            // This is crucial for the LZ78 format where a full byte follows a variable-length code.
            if (bitsInCurrentByte > 0) {
                currentByte = 0; // Clear the partial byte
                bitsInCurrentByte = 0; // Reset bit counter
            }
            // Now, read the next full byte from the underlying stream.
            int b = in.read();
            if (b == -1) {
                eofReached = true;
                throw new EOFException("Unexpected end of stream while reading a byte.");
            }
            return (byte) b;
        }

        /**
         * Checks if the end of the stream has been reached.
         * @return true if EOF, false otherwise.
         */
        public boolean isEOF() {
            // EOF is truly reached when the underlying stream has hit EOF and all buffered bits are consumed.
            // We need to attempt a read on the underlying stream to confirm EOF if bitsInCurrentByte is 0
            // and eofReached is not yet set (meaning we haven't tried to read past the last byte).
            if (bitsInCurrentByte == 0 && !eofReached) {
                try {
                    in.mark(1); // Mark current position to reset later
                    if (in.read() == -1) { // Try to read one byte to check for EOF
                        eofReached = true;
                    }
                    in.reset(); // Reset to marked position
                } catch (IOException e) {
                    // If an exception occurs during mark/read/reset, it's safer to assume not EOF
                    // or handle the specific exception if it indicates EOF. For now, just ignore.
                }
            }
            return eofReached && bitsInCurrentByte == 0;
        }

        /**
         * Closes the BitInputStream.
         * @throws IOException If an I/O error occurs during closing the underlying stream.
         */
        @Override
        public void close() throws IOException {
            in.close();
        }
    }

    // --- Compression Method ---
    /**
     * Compresses the input file using the LZ78 algorithm and writes the compressed data to the output file.
     * @param inputFilePath The path to the input file to be compressed.
     * @param outputFilePath The path to the output file where compressed data will be written.
     * @throws IOException If an I/O error occurs during file operations.
     */
    public void compress(String inputFilePath, String outputFilePath) throws IOException {
        TrieNode root = new TrieNode();
        int nextCode; // Next available code for new sequences

        // Use try-with-resources for automatic closing of streams.
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath), BUFFER_SIZE);
             BitOutputStream bos = new BitOutputStream(new FileOutputStream(outputFilePath))) {

            // Write MAX_DICTIONARY_SIZE as a header. This allows the decompressor to know the limit.
            bos.writeBits(MAX_DICTIONARY_SIZE, DICTIONARY_SIZE_HEADER_BITS);

            // Initialize dictionary for compression.
            // Code 0 is reserved for RESET_CODE. Codes 1-256 for single bytes.
            // `nextCode` will start from INITIAL_DICTIONARY_SIZE + 1 (i.e., 257).
            nextCode = initializeCompressionDictionary(root);

            // The number of bits required to represent the current dictionary codes.
            // Starts at 9 bits because codes 1-256 fit in 8, but 257 needs 9.
            int currentCodeBits = 9;

            TrieNode currentNode = root; // Start matching from the root of the Trie
            int byteRead;

            // Read the input file byte by byte
            while ((byteRead = bis.read()) != -1) {
                byte currentByte = (byte) byteRead;

                // Try to extend the current sequence by appending the currentByte.
                TrieNode nextNode = currentNode.children.get(currentByte);

                if (nextNode != null) {
                    // The extended sequence is found in the dictionary.
                    // Continue building the current sequence by moving to the next node in the Trie.
                    currentNode = nextNode;
                } else {
                    // The extended sequence is NOT found in the dictionary.
                    // This means `currentNode` represents the longest sequence found so far that IS in the dictionary.

                    // Output the code for the `currentNode` (the longest matched prefix).
                    bos.writeBits(currentNode.code, currentCodeBits);
                    // Output the `currentByte` that caused the mismatch. This byte is appended to the
                    // decoded sequence during decompression.
                    bos.writeByte(currentByte);

                    // Add the new sequence (represented by `currentNode` + `currentByte`) to the dictionary.
                    if (nextCode < MAX_DICTIONARY_SIZE) {
                        TrieNode newNode = new TrieNode();
                        newNode.code = nextCode++; // Assign a new code to this new sequence
                        currentNode.children.put(currentByte, newNode); // Add it to the Trie

                        // Dynamically increase the number of bits used for codes if the dictionary size
                        // crosses a power-of-2 boundary. This ensures that all codes can be represented.
                        if (nextCode > (1 << currentCodeBits) && currentCodeBits < MAX_CODE_BITS) {
                            currentCodeBits++;
                        }
                    }

                    // Check if dictionary needs to be reset
                    if (nextCode >= MAX_DICTIONARY_SIZE * DICT_RESET_USAGE_RATIO && nextCode < MAX_DICTIONARY_SIZE) {
                        // Write the special RESET_CODE to signal the decompressor
                        bos.writeBits(RESET_CODE, currentCodeBits); // Use currentCodeBits for reset code
                        // Reinitialize the dictionary
                        root = new TrieNode(); // Clear the old Trie
                        nextCode = initializeCompressionDictionary(root); // Re-populate with initial bytes
                        currentCodeBits = 9; // Reset code bits to initial value
                    }

                    // Reset `currentNode` to the node representing the `currentByte`.
                    // This `currentByte` becomes the start of the next sequence search.
                    // It's guaranteed to be in the dictionary because all single bytes are pre-initialized.
                    currentNode = root.children.get(currentByte);
                }
            }

            // After the loop, if `currentNode` is not the root (meaning the last few bytes formed a sequence
            // that was found in the dictionary up to EOF), output its code.
            // There is no trailing byte for this last sequence.
            if (currentNode != root && currentNode.code != -1) {
                bos.writeBits(currentNode.code, currentCodeBits);
            }
        }
    }

    // Helper to initialize/reset compression dictionary
    // Returns the next available code after initialization
    private int initializeCompressionDictionary(TrieNode root) {
        root.children.clear(); // Clear existing entries in the Trie
        // Codes start from 1 for single bytes (0-255). Code 0 is RESET_CODE.
        int codeCounter = 1;
        for (int i = 0; i < INITIAL_DICTIONARY_SIZE; i++) {
            TrieNode node = new TrieNode();
            node.code = codeCounter++; // Assign codes 1-256 for bytes 0-255
            root.children.put((byte) i, node);
        }
        return codeCounter; // Returns 257 (the next code for new sequences)
    }


    // --- Decompression Method ---
    /**
     * Decompresses the input file (compressed with LZ78) and writes the original data to the output file.
     * @param inputFilePath The path to the compressed input file.
     * @param outputFilePath The path to the output file where decompressed data will be written.
     * @throws IOException If an I/O error occurs during file operations or if the compressed file is corrupted.
     */
    public void decompress(String inputFilePath, String outputFilePath) throws IOException {
        List<byte[]> dictionary = new ArrayList<>(); // Decompression dictionary
        int nextCode; // Next available code for new sequences

        // Use try-with-resources for automatic closing of streams.
        try (BitInputStream bis = new BitInputStream(new FileInputStream(inputFilePath));
             BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream(outputFilePath), BUFFER_SIZE)) {

            // Read MAX_DICTIONARY_SIZE from header
            int maxDictSizeFromHeader = bis.readBits(DICTIONARY_SIZE_HEADER_BITS);
            // Optionally, validate maxDictSizeFromHeader against MAX_DICTIONARY_SIZE constant.
            // For simplicity, we'll assume it matches.

            // Initialize dictionary for decompression.
            // Code 0 is reserved for RESET_CODE. Codes 1-256 for single bytes.
            nextCode = initializeDecompressionDictionary(dictionary);

            // The number of bits expected for reading current dictionary codes.
            // Starts at 9 bits because codes 1-256 fit in 8, but 257 needs 9.
            int currentCodeBits = 9;

            byte[] previousSequence = null; // Stores the previously decoded sequence
            boolean isFirstCodeOfSegment = true; // Flag to track if it's the first code after header or reset

            // Read codes and bytes from the compressed file
            while (true) {
                int code;
                try {
                    code = bis.readBits(currentCodeBits); // Read the next code
                } catch (EOFException e) {
                    break; // End of file reached, exit loop
                }

                // Check for dictionary reset code
                if (code == RESET_CODE) {
                    // Reinitialize the dictionary
                    nextCode = initializeDecompressionDictionary(dictionary);
                    currentCodeBits = 9; // Reset code bits to initial value
                    previousSequence = null; // Reset previous sequence
                    isFirstCodeOfSegment = true; // Next code will be the first of a new segment
                    continue; // Skip to next iteration to read the next actual code/byte
                }

                byte newByte;
                try {
                    newByte = bis.readByte(); // Read the byte associated with the code
                } catch (EOFException e) {
                    // This handles the special case of the very last sequence in the file,
                    // which is just a code without a trailing byte.
                    if (code < dictionary.size()) {
                        byte[] sequence = dictionary.get(code); // Retrieve the sequence for the last code
                        bos.write(sequence); // Write it to output
                    } else {
                        // This case should theoretically not happen if the compressed file is valid
                        // and the compression logic is correct for the very last code.
                        throw new IOException("Decompression error: Unexpected EOF after code " + code +
                                ". Possible corrupted file or compression logic error for last sequence.");
                    }
                    break; // Exit loop after handling the last code
                }

                byte[] decodedSequence;
                // Check if the read code is already in the dictionary
                if (code < dictionary.size()) {
                    decodedSequence = dictionary.get(code); // Retrieve the sequence directly
                } else {
                    // Diagnostic check: If it's the first code of a segment and it's not in the initial dictionary range, it's an error.
                    if (isFirstCodeOfSegment) {
                        throw new IOException("Decompression error: First code of segment (" + code + ") is invalid. Expected 1-" + INITIAL_DICTIONARY_SIZE + ".");
                    }
                    // This is the "K-K-c" case (code == dictionary.size()).
                    // It means the code refers to the sequence that is *just about to be added* to the dictionary.
                    // This sequence is formed by the `previousSequence` plus the `newByte`.
                    if (previousSequence == null) {
                        // This should ideally not be reached if the `isFirstCodeOfSegment` check is correct
                        // and the compressed stream is valid. It implies a deeper logic flaw or corruption.
                        throw new IOException("Decompression error: Invalid code " + code + " (previousSequence is null, but not first code of segment).");
                    }
                    // Construct the new sequence: previousSequence + newByte
                    decodedSequence = Arrays.copyOf(previousSequence, previousSequence.length + 1);
                    decodedSequence[previousSequence.length] = newByte;
                }

                // Write the decoded sequence to the output file
                bos.write(decodedSequence);

                // Add the new sequence (decodedSequence + newByte) to the dictionary.
                // This new entry is formed from the *current* decoded sequence and the *current* newByte.
                // It applies for all entries as long as the dictionary is not full.
                if (nextCode < maxDictSizeFromHeader) { // Use header's max dict size
                    byte[] newEntry = Arrays.copyOf(decodedSequence, decodedSequence.length + 1);
                    newEntry[decodedSequence.length] = newByte; // Append the newByte
                    dictionary.add(newEntry); // Add the new sequence to the dictionary
                    nextCode++; // Increment the next available code

                    // Dynamically increase the number of bits for codes, mirroring compression logic.
                    if (nextCode > (1 << currentCodeBits) && currentCodeBits < MAX_CODE_BITS) {
                        currentCodeBits++;
                    }
                }

                // Update `previousSequence` to the sequence that was just decoded.
                // This will be used in the next iteration to form new dictionary entries.
                previousSequence = decodedSequence;
                isFirstCodeOfSegment = false; // Not the first code of the segment anymore
            }
        }
    }

    // Helper to initialize/reset decompression dictionary
    // Returns the next available code after initialization
    private int initializeDecompressionDictionary(List<byte[]> dictionary) {
        dictionary.clear();
        dictionary.add(null); // Index 0 reserved for RESET_CODE
        int codeCounter = 1; // Codes for single bytes start from 1
        for (int i = 0; i < INITIAL_DICTIONARY_SIZE; i++) {
            dictionary.add(new byte[]{(byte) i}); // Codes 1-256 map to bytes 0-255
            codeCounter++;
        }
        return codeCounter; // Returns 257 (the next code for new sequences)
    }

    // --- Main Method for Testing and Execution ---
    public static void main(String[] args) {
        LZ78Compressor lz78 = new LZ78Compressor(); // Create an instance of the unified LZ78 algorithm
        System.out.println("----------- Process LZ78 (Unified & Optimized) ----------------------------------------------------");

        // Define file paths for input, compressed output, and decompressed output
        String inputFile = "traffic_accidents.db"; // Example input file name
        String compressedFile = "LZW/traffic_accidents_lzw.lz78"; // Compressed output file
        String decompressedFile = "LZW/traffic_accidents_lzw.db"; // Decompressed output file

        // Check if the input file exists or is empty. If not, create some sample data for testing.
        File testFile = new File(inputFile);
        if (!testFile.exists() || testFile.length() == 0) {
            System.out.println("Creating dummy input file for testing: " + inputFile);
            createSampleData(inputFile);
        }

        System.out.println("Compression Process ---------------------------------------------------------");
        try {
            long startTime = System.currentTimeMillis(); // Record start time for compression
            lz78.compress(inputFile, compressedFile); // Execute compression
            long endTime = System.currentTimeMillis(); // Record end time
            System.out.println("Compression successful! Time taken: " + (endTime - startTime) + "ms");
            long inputSize = getSize(inputFile);
            long compressedSize = getSize(compressedFile);
            System.out.println("Input size: " + inputSize + " bytes");
            System.out.println("Compressed size: " + compressedSize + " bytes");
            if (inputSize > 0) {
                float compressionPercentage = ((float) compressedSize / inputSize) * 100;
                System.out.println(String.format("Compression percentage: %.2f%% of original file.", compressionPercentage));
            } else {
                System.out.println("Cannot calculate compression percentage for empty input file.");
            }
        } catch (IOException e) {
            System.err.println("Compression failed: " + e.getMessage());
            e.printStackTrace(); // Print stack trace for debugging
        }

        System.out.println("\nDecompression Process -------------------------------------------------------");
        try {
            long startTime = System.currentTimeMillis(); // Record start time for decompression
            lz78.decompress(compressedFile, decompressedFile); // Execute decompression
            long endTime = System.currentTimeMillis(); // Record end time
            System.out.println("Decompression successful! Time taken: " + (endTime - startTime) + "ms");
            long decompressedSize = getSize(decompressedFile);
            System.out.println("Decompressed size: " + decompressedSize + " bytes");
        } catch (IOException e) {
            System.err.println("Decompression failed: " + e.getMessage());
            e.printStackTrace(); // Print stack trace for debugging
        }

        // Verify that the original and decompressed files are identical (for smaller files)
        try {
            // Only perform byte-by-byte verification for files smaller than 1MB to avoid memory issues with very large files.
            if (getSize(inputFile) < 1000000) {
                byte[] original = Files.readAllBytes(Paths.get(inputFile));
                byte[] decompressed = Files.readAllBytes(Paths.get(decompressedFile));
                if (Arrays.equals(original, decompressed)) {
                    System.out.println("\nVerification: Original and decompressed files are identical.");
                } else {
                    System.err.println("\nVerification: Mismatch between original and decompressed files!");
                }
            } else {
                System.out.println("\nSkipping byte-by-byte verification for large files (>" + (1000000 / (1024 * 1024)) + "MB).");
            }
        } catch (IOException e) {
            System.err.println("Error during verification: " + e.getMessage());
        }
        System.out.println("----------- Process Done ----------------------------------------------------");
    }

    // --- Helper Method to Get File Size ---
    /**
     * Returns the size of a file in bytes.
     * @param filename The path to the file.
     * @return The size of the file in bytes, or -1 if the file does not exist or an error occurs.
     */
    public static long getSize(String filename) {
        File file = new File(filename);
        if (file.exists()) {
            return file.length();
        }
        return -1; // Indicate file not found or error
    }

    // --- Helper Method to Create Sample Data for Testing ---
    /**
     * Creates a dummy input file with repetitive text data for testing compression and decompression.
     * @param filePath The path where the sample file will be created.
     */
    private static void createSampleData(String filePath) {
        try (FileOutputStream fos = new FileOutputStream(filePath)) {
            // A repetitive string to demonstrate the effectiveness of compression
            String data = "SIXTY-SIX SILLY SHEEP SLEPT SOUNDLY. FIFTY-FIVE FURRY FERRETS FROLICKED FRANTICALLY. " +
                          "THIRTY-THREE THICK THISTLES THRIVED THERE. TWENTY-TWO TINY TURTLES TREKKED TIREDLY.";
            // Repeat the data multiple times to make the file a bit larger for more meaningful compression results
            for (int i = 0; i < 500; i++) {
                fos.write(data.getBytes());
            }
            // Add some unique data at the end to ensure EOF handling is robust and the last sequence is handled correctly
            fos.write("END_OF_FILE_MARKER_XYZ".getBytes());
        } catch (IOException e) {
            System.err.println("Error creating sample data file: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
