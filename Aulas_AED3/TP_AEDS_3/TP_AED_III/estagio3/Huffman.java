package estagio3;

import java.io.*;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Scanner;

import estagio1.leitura.Functions;

import java.util.ArrayList;
import java.util.BitSet; // For efficient bit manipulation

public class Huffman {
    // --- Main Method for Demonstration ---
    public static void main(String[] args) {
        processing();
        //compressProcess("fruits_data.csv","fruits_data.huff");
        //decompressProcess("fruits_data.csv","fruits_data.huff","fruits_data_2.csv");
        //compressProcess("traffic_accidents.db","traffic_accidents_huffman.huff");
        //decompressProcess("traffic_accidents.db","traffic_accidents_huffman.huff","traffic_accidents_2.db");
    }

    // --- Node Class for Huffman Tree ---
    static class Node {
        char character;
        int frequency;
        Node left;
        Node right;

        public Node(char character, int frequency) {
            this.character = character;
            this.frequency = frequency;
            this.left = null;
            this.right = null;
        }

        public Node(int frequency, Node left, Node right) {
            this.character = '\0'; // Internal node, no specific character
            this.frequency = frequency;
            this.left = left;
            this.right = right;
        }

        // Check if this node is a leaf (contains a character)
        public boolean isLeaf() {
            return left == null && right == null;
        }
    }

    // --- Comparator for PriorityQueue (Min-Heap) ---
    static class NodeComparator implements Comparator<Node> {
        @Override
        public int compare(Node n1, Node n2) {
            return Integer.compare(n1.frequency, n2.frequency);
        }
    }

    // --- HuffmanContext Class (for encapsulation) ---
    static class HuffmanContext {
        Node huffmanTreeRoot;
        Map<Character, String> huffmanCodes; // Character -> Binary Code String
        Map<Character, CodeMetadata> decompressionMetadata; // For rebuilding tree metadata
        int totalOriginalChars; // Total characters in the original file

        public HuffmanContext() {
            huffmanTreeRoot = null;
            huffmanCodes = new HashMap<>();
            decompressionMetadata = new HashMap<>();
            totalOriginalChars = 0;
        }
    }

    // --- CodeMetadata Class (for storing data for decompression tree) ---
    // This replaces the 'Tree' struct from C, holding char, length, decimal code
    static class CodeMetadata {
        char character;
        int length;
        int decimalCode; // Stored as an int

        public CodeMetadata(char character, int length, int decimalCode) {
            this.character = character;
            this.length = length;
            this.decimalCode = decimalCode;
        }
    }

    // --- Huffman Tree Building ---

    /**
     * Builds the Huffman tree from character frequencies.
     * @param frequencies Map of character frequencies.
     * @return The root node of the Huffman tree.
     */
    public static Node buildHuffmanTree(Map<Character, Integer> frequencies) {
        PriorityQueue<Node> pq = new PriorityQueue<>(new NodeComparator());

        // Add leaf nodes for each character with its frequency
        for (Map.Entry<Character, Integer> entry : frequencies.entrySet()) {
            pq.add(new Node(entry.getKey(), entry.getValue()));
        }

        // Build the tree by repeatedly combining the two lowest frequency nodes
        while (pq.size() > 1) {
            Node left = pq.poll();
            Node right = pq.poll();
            Node parent = new Node(left.frequency + right.frequency, left, right);
            pq.add(parent);
        }

        return pq.poll(); // The last remaining node is the root
    }

    /**
     * Generates Huffman codes by traversing the Huffman tree.
     * Stores codes in the HuffmanContext.huffmanCodes map.
     * @param node Current node in the traversal.
     * @param code Current binary code string.
     * @param context HuffmanContext to store codes.
     */
    private static void generateHuffmanCodes(Node node, String code, HuffmanContext context) {
        if (node.isLeaf()) {
            context.huffmanCodes.put(node.character, code);
            // Prepare metadata for decompression tree reconstruction
            context.decompressionMetadata.put(node.character,
                    new CodeMetadata(node.character, code.length(), binaryStringToDecimal(code)));
        } else {
            generateHuffmanCodes(node.left, code + "0", context);
            generateHuffmanCodes(node.right, code + "1", context);
        }
    }

    // --- Compression ---

    /**
     * Compresses an input file using Huffman coding.
     * @param inputFilePath Path to the input file.
     * @param outputFilePath Path to the compressed output file.
     * @throws IOException If an I/O error occurs.
     */
    public static void compressFile(String inputFilePath, String outputFilePath) throws IOException {
        HuffmanContext context = new HuffmanContext();

        // 1. Frequency Analysis
        Map<Character, Integer> frequencies = new HashMap<>();
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath))) {
            int byteRead;
            while ((byteRead = bis.read()) != -1) {
                char c = (char) byteRead;
                frequencies.put(c, frequencies.getOrDefault(c, 0) + 1);
                context.totalOriginalChars++;
            }
        }
        System.out.println("-----------------------------------------------------------------------------");
        frequencies.forEach((key, value) -> {
            System.out.println("key: " + key + ", value: " + value);
        });
        System.out.println("-----------------------------------------------------------------------------");
        // Handle empty file case
        if (context.totalOriginalChars == 0) {
            System.out.println("Input file is empty. Creating an empty compressed file.");
            new FileOutputStream(outputFilePath).close(); // Create empty file
            return;
        }

        // 2. Build Huffman Tree
        context.huffmanTreeRoot = buildHuffmanTree(frequencies);

        // 3. Generate Huffman Codes and prepare metadata for decompression
        generateHuffmanCodes(context.huffmanTreeRoot, "", context);

        // 4. Write to Compressed File
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath));
             DataOutputStream dos = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(outputFilePath)))) {

            // --- Write Header ---
            // Write total original characters (for stopping decompression)
            dos.writeInt(context.totalOriginalChars);
            // Write number of unique characters (for rebuilding tree)
            dos.writeInt(context.decompressionMetadata.size());
            // Write tree metadata (character, code length, decimal code)
            for (CodeMetadata meta : context.decompressionMetadata.values()) {
                dos.writeChar(meta.character);
                dos.writeInt(meta.length);
                dos.writeInt(meta.decimalCode);
            }

            // --- Write Compressed Data ---
            BitSet bitSet = new BitSet();
            int bitIndex = 0;

            int byteRead;
            while ((byteRead = bis.read()) != -1) {
                char c = (char) byteRead;
                String code = context.huffmanCodes.get(c);
                if (code == null) {
                    throw new IllegalStateException("No Huffman code found for character: " + c);
                }
                for (char bitChar : code.toCharArray()) {
                    if (bitChar == '1') {
                        bitSet.set(bitIndex);
                    }
                    bitIndex++;
                }
            }

            // Write the BitSet content to the file
            // BitSet.toByteArray() pads to the next full byte
            dos.write(bitSet.toByteArray());
        }
        System.out.println("File compressed successfully: " + outputFilePath);
    }

    // --- Decompression ---

    /**
     * Decompresses a Huffman-coded file.
     * @param inputFilePath Path to the compressed input file.
     * @param outputFilePath Path to the decompressed output file.
     * @throws IOException If an I/O error occurs.
     */
    public static void decompressFile(String inputFilePath, String outputFilePath) throws IOException {
        HuffmanContext context = new HuffmanContext();
        Node decompressionTreeRoot = null; // Rebuilt tree for decompression

        try (DataInputStream dis = new DataInputStream(new BufferedInputStream(new FileInputStream(inputFilePath)));
             BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream(outputFilePath))) {

            // 1. Read Header
            context.totalOriginalChars = dis.readInt();
            int uniqueCharsCount = dis.readInt();

            if (context.totalOriginalChars == 0) {
                System.out.println("Compressed file indicates original file was empty. Creating empty decompressed file.");
                return;
            }

            // 2. Rebuild Decompression Tree
            // Create a temporary root for rebuilding the tree
            decompressionTreeRoot = new Node('\0', 0); // Root of our custom decompression tree
            Node currentRebuildNode;

            for (int i = 0; i < uniqueCharsCount; i++) {
                char character = dis.readChar();
                int length = dis.readInt();
                int decimalCode = dis.readInt();

                String binaryCode = decimalToBinaryString(decimalCode, length);

                currentRebuildNode = decompressionTreeRoot;
                for (char bitChar : binaryCode.toCharArray()) {
                    if (bitChar == '0') {
                        if (currentRebuildNode.left == null) {
                            currentRebuildNode.left = new Node('\0', 0); // Create internal node
                        }
                        currentRebuildNode = currentRebuildNode.left;
                    } else { // '1'
                        if (currentRebuildNode.right == null) {
                            currentRebuildNode.right = new Node('\0', 0); // Create internal node
                        }
                        currentRebuildNode = currentRebuildNode.right;
                    }
                }
                currentRebuildNode.character = character; // Assign character to leaf
            }

            // 3. Decompress Data
            Node currentNode = decompressionTreeRoot;
            int charactersDecompressed = 0;
            byte[] buffer = new byte[1024]; // Read in chunks
            int bytesRead;

            while (charactersDecompressed < context.totalOriginalChars && (bytesRead = dis.read(buffer)) != -1) {
                // Convert the buffer into a BitSet for easy bit access
                BitSet receivedBitSet = BitSet.valueOf(buffer);

                for (int i = 0; i < bytesRead * 8; i++) { // Iterate through each bit in the buffer
                    if (charactersDecompressed >= context.totalOriginalChars) {
                        break; // Stop if we've decompressed all original characters
                    }

                    boolean bit = receivedBitSet.get(i);
                    if (!bit) { // Bit is 0, go left
                        currentNode = currentNode.left;
                    } else { // Bit is 1, go right
                        currentNode = currentNode.right;
                    }

                    if (currentNode == null) {
                        throw new IllegalStateException("Invalid Huffman code encountered during decompression.");
                    }

                    if (currentNode.isLeaf()) {
                        bos.write(currentNode.character);
                        charactersDecompressed++;
                        currentNode = decompressionTreeRoot; // Reset to root for next code
                    }
                }
            }
        } finally {
            // No explicit close needed for try-with-resources
        }
        System.out.println("The choosed file was "+inputFilePath);
        System.out.println("File decompressed successfully as: " + outputFilePath);
    }

    // --- Utility Methods ---

    /**
     * Converts a binary string to its decimal integer representation.
     * @param binaryString The binary string (e.g., "101").
     * @return The decimal integer.
     */
    private static int binaryStringToDecimal(String binaryString) {
        if (binaryString == null || binaryString.isEmpty()) {
            return 0;
        }
        // Using Integer.parseInt with base 2
        return Integer.parseInt(binaryString, 2);
    }

    /**
     * Converts a decimal integer to its binary string representation with a specific length.
     * @param decimalValue The decimal integer.
     * @param length The desired length of the binary string (will be padded with leading zeros).
     * @return The binary string.
     */
    private static String decimalToBinaryString(int decimalValue, int length) {
        // Using Integer.toBinaryString and padding with leading zeros
        String binaryString = Integer.toBinaryString(decimalValue);
        return String.format("%" + length + "s", binaryString).replace(' ', '0');
    }

    
    public static void processing(){
        String inputFilename = "sample.txt";
        String compressedFilename = "sample_compressed.huff";
        String decompressedFilename = "sample_decompressed.txt";

        // Create a dummy input file for demonstration
        try (FileWriter writer = new FileWriter(inputFilename)) {
            writer.write("this is a test string for huffman coding and compression. this is another test.");
            System.out.println("Created dummy input file: " + inputFilename);
        } catch (IOException e) {
            System.err.println("Error creating dummy input file: " + e.getMessage());
            return;
        }
        compressProcess(inputFilename,compressedFilename);
        decompressProcess(inputFilename,compressedFilename,decompressedFilename);
    }
    public static void compressProcess(String inputFilename,
        String compressedFilename){
        // Compression
        
        String[] description=compressedFilename.split("\\.");

        int counterHuffman = 0;
        File folder = new File("."); // Current directory
        File[] listOfFiles = folder.listFiles();

        if (listOfFiles != null) {
            for (File file : listOfFiles) {
                if (file.isFile() && file.getName().startsWith(description[0]) && file.getName().endsWith("."+description[1])) {
                    counterHuffman++;
                }
            }
        }

        if (counterHuffman == 0) {
            counterHuffman = 1;
        } else {
            counterHuffman++;
        }

        // Construct the new compressed filename with the counter
        compressedFilename = compressedFilename.replace("."+description[1], "_" + counterHuffman + "."+description[1]);

        // Compression
        try {
            long tempoInicial = System.currentTimeMillis();
            compressFile(inputFilename, compressedFilename);
            long tempoFinal=System.currentTimeMillis();
            System.out.println("Huffman compression was performed in " + ((tempoFinal - tempoInicial)/1000.0)+"s");
            long sizeOriginal=getSize(inputFilename); // This assumes the original file exists and is correctly passed
            long sizeCompress=getSize(compressedFilename); // Use the size of the actually compressed file
            float percentHuffman=((float)sizeCompress/(float)sizeOriginal)*100;
            System.out.println("Size of ("+inputFilename+"): " +sizeOriginal + " bytes");
            System.out.println("Size of ("+compressedFilename+"): " +sizeCompress + " bytes");
            System.out.println("Compression porcentage: " +String.format("%.2f",percentHuffman)+ "% of original file.");
            

        } catch (IOException e) {
            System.err.println("Compression failed: " + e.getMessage());
            e.printStackTrace();
        }
    }
    public static void decompressProcess(String inputFilename, String compressedFilename, String decompressedFilename) {
        
        List<File> huffmanFiles = new ArrayList<>();

        String[] description=compressedFilename.split("\\.");

        File folder = new File("."); // Current directory
        File[] listOfFiles = folder.listFiles();

        if (listOfFiles != null) {
            for (File file : listOfFiles) {
                if (file.isFile() && file.getName().startsWith(description[0]) && file.getName().endsWith("."+description[1])) {
                    huffmanFiles.add(file);
                }
            }
        }

        if (huffmanFiles.isEmpty()) {
            System.out.println("No compressed Huffman files found matching '" + description[0] + "*."+ description[1]+"'.");
            System.out.println("Please run compression first to create some files.");
            return;
        }

        // Sort files for consistent display order (optional, but good practice)
        huffmanFiles.sort(Comparator.comparing(File::getName));

        System.out.println("\n--- Available Compressed Huffman Files for Decompression ---");
        for (int i = 0; i < huffmanFiles.size(); i++) {
            System.out.println((i + 1) + ". " + huffmanFiles.get(i).getName());
        }

        int choice = -1;
        String selectedCompressedFilePath = null;
        while (selectedCompressedFilePath == null) {
            System.out.print("Enter the number of the file to decompress: ");
            try {
            	 choice = Functions.only_Int();
                if (choice > 0 && choice <= huffmanFiles.size()) {
                    selectedCompressedFilePath = huffmanFiles.get(choice - 1).getName();
                } else {
                    System.out.println("Invalid choice. Please enter a number between 1 and " + huffmanFiles.size() + ".");
                }
            } catch (NumberFormatException e) {
                System.out.println("Invalid input. Please enter a number.");
            }
        }
        System.out.println();
        // Decompression
        try {
            long tempoInicial = System.currentTimeMillis();
            // Use the chosen file's path for decompression
            decompressFile(selectedCompressedFilePath, decompressedFilename);
            long tempoFinal=System.currentTimeMillis();
            
            System.out.println("Huffman decompression was performed in " + ((tempoFinal - tempoInicial)/1000.0)+"s");
        } catch (IOException e) {
            System.err.println("Decompression failed: " + e.getMessage());
            e.printStackTrace();
        } finally {
            // No explicit close needed for try-with-resources in decompressFile,
            // but scanner should be closed here if it's opened in this method.
            // However, it's generally better to pass Scanner or create it in main.
            // For simplicity here, we'll keep it as is, but be mindful in larger applications.
        }

        System.out.println("\n--- Verification ---");
        System.out.println("You can now compare '" + inputFilename + "' and '" + decompressedFilename + "' for integrity.");
        System.out.println();
        long sizeOriginal=getSize(inputFilename); // This assumes the original file exists and is correctly passed
        long sizeCompress=getSize(selectedCompressedFilePath); // Use the size of the actually compressed file
        long sizeDecompress=getSize(decompressedFilename); // Use the size of the actually compressed file
        float percentHuffman=((float)sizeDecompress/(float)sizeOriginal)*100;
        
        System.out.println("Size of ("+inputFilename+"): " +sizeOriginal + " bytes");  
        System.out.println("Size of ("+selectedCompressedFilePath+"): " + sizeCompress+ " bytes");
        System.out.println("Size of ("+decompressedFilename+"): " + sizeDecompress + " bytes");
        System.out.println();
        System.out.println("Decompression recovery porcentage of original file is: " +String.format("%.2f",percentHuffman)+ "%.");

        //scanner.close();
    }
    public static long getSize(String filename) {
        File file = new File(filename);
        return file.length();
        
    }
}
