package estagio3;

import java.io.*;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

import estagio1.leitura.Functions;
public class LZWC {

    // --- Main Method for Demonstration ---
    public static void main(String[] args) {
        processing();
        //compressProcess("fruits_data.csv","fruits_data.huff");
        //decompressProcess("fruits_data.csv","fruits_data.huff","fruits_data_2.csv");
        compressProcess("traffic_accidents_pt_br_rev2.csv","traffic_accidents_pt_br_rev2_huffman.lzw");
        decompressProcess("traffic_accidents_pt_br_rev2.csv","traffic_accidents_pt_br_rev2_huffman.lzw","traffic_accidents_pt_br_rev2_2.csv");
    }

    // Maximum dictionary size (e.g., for 16-bit codes, it's 65536)
    // For "more than 1 million combinations", you'd need larger codes.
    // Let's target up to 24-bit codes for 16 million entries, or 32-bit for 4 billion.
    // We'll use int for codes, allowing up to 2^31-1.
    private static final int MAX_DICTIONARY_SIZE = 1 << 24; // ~16 million entries (24-bit codes)

    public void compress(String inputFilePath, String outputFilePath) throws IOException {
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath));
             DataOutputStream dos = new DataOutputStream(new FileOutputStream(outputFilePath))) {

            Map<String, Integer> dictionary = new HashMap<>();
            int dictionarySize = 256; // ASCII characters

            // Initialize dictionary with single ASCII characters
            for (int i = 0; i < dictionarySize; i++) {
                dictionary.put("" + (char) i, i);
            }

            String currentSequence = "";
            int nextCode = dictionarySize; // Next available code

            int character;
            while ((character = bis.read()) != -1) {
                String newSequence = currentSequence + (char) character;

                if (dictionary.containsKey(newSequence)) {
                    currentSequence = newSequence;
                } else {
                    // Output the code for currentSequence
                    dos.writeInt(dictionary.get(currentSequence));

                    // Add newSequence to dictionary if not full
                    if (nextCode < MAX_DICTIONARY_SIZE) {
                        dictionary.put(newSequence, nextCode++);
                    }
                    currentSequence = "" + (char) character; // Reset currentSequence
                }
            }

            // Output the code for the last currentSequence
            if (!currentSequence.isEmpty()) {
                dos.writeInt(dictionary.get(currentSequence));
            }

            System.out.println("Compression complete. Dictionary size: " + dictionary.size());
        }
    }
    public static void processing(){
        String inputFilename = "sample.txt";
        String compressedFilename = "sample_compressed.lzw";
        String decompressedFilename = "sample_decompressed.txt";

        // Create a dummy input file for demonstration
        try (FileWriter writer = new FileWriter(inputFilename)) {
            writer.write("this is a test string for LZW coding and compression. this is another test.");
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
        LZWC compressor = new LZWC();
        
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
            compressor.compress(inputFilename, compressedFilename);
            long tempoFinal = System.currentTimeMillis();
            System.out.println("LZW compression was performed in " + ((tempoFinal - tempoInicial)/1000.0)+"s");
            long sizeOriginal=getSize(inputFilename); // This assumes the original file exists and is correctly passed
            long sizeCompress=getSize(compressedFilename); // Use the size of the actually compressed file
            float percentLZW=((float)sizeCompress/(float)sizeOriginal)*100;
            System.out.println("Size of ("+inputFilename+"): " +sizeOriginal + " bytes");
            System.out.println("Size of ("+compressedFilename+"): " +sizeCompress + " bytes");
            System.out.println("Compression porcentage: " +String.format("%.2f",percentLZW)+ "% of original file.");
            
       } catch (IOException e) {
            System.err.println("Compression failed: " + e.getMessage());
            e.printStackTrace();
        }
    }
    public static void decompressProcess(String inputFilename, String compressedFilename, String decompressedFilename) {
        
        List<File> lzwFiles = new ArrayList<>();
        LZWD decompressor = new LZWD();
        
        String[] description=compressedFilename.split("\\.");

        File folder = new File("."); // Current directory
        File[] listOfFiles = folder.listFiles();

        if (listOfFiles != null) {
            for (File file : listOfFiles) {
                if (file.isFile() && file.getName().startsWith(description[0]) && file.getName().endsWith("."+description[1])) {
                    lzwFiles.add(file);
                }
            }
        }

        if (lzwFiles.isEmpty()) {
            System.out.println("No compressed LZW files found matching '" + description[0] + "*."+ description[1]+"'.");
            System.out.println("Please run compression first to create some files.");
            return;
        }

        // Sort files for consistent display order (optional, but good practice)
        lzwFiles.sort(Comparator.comparing(File::getName));
        
        System.out.println("\n--- Available Compressed LZW Files for Decompression ---");
        for (int i = 0; i < lzwFiles.size(); i++) {
            System.out.println((i + 1) + ". " + lzwFiles.get(i).getName());
        }
        
        int choice = -1;
        String selectedCompressedFilePath = null;
        while (selectedCompressedFilePath == null) {
            System.out.print("Enter the number of the file to decompress: ");
            try {
                choice = Functions.only_Int();
                if (choice > 0 && choice <= lzwFiles.size()) {
                    selectedCompressedFilePath = lzwFiles.get(choice - 1).getName();
                } else {
                    System.out.println("Invalid choice. Please enter a number between 1 and " + lzwFiles.size() + ".");
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
            decompressor.decompress(selectedCompressedFilePath, decompressedFilename);
            long tempoFinal=System.currentTimeMillis();
            
            System.out.println("LZW decompression was performed in " + ((tempoFinal - tempoInicial)/1000.0)+"s");
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


    
        
