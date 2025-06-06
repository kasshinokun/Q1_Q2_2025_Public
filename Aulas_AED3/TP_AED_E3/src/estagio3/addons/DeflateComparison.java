package estagio3.addons;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.BufferedInputStream;
import java.util.Arrays;
import java.util.zip.Deflater;
import java.util.zip.Inflater;
import java.util.zip.DataFormatException;
import java.util.zip.ZipEntry; // Default Java ZIP library
import java.util.zip.ZipOutputStream; // Default Java ZIP library


/**
 * This class demonstrates the difference in compression size between
 * standard Deflate (using java.util.zip.Deflater) and
 * ZIP compression using Java's default java.util.zip package.
 *
 * NOTE: Java's default java.util.zip does NOT support ZIP64.
 * For files > 4GB or archives with > 65535 entries, use external libraries like
 * Apache Commons Compress or Zip4j, as they handle ZIP64 (and implicitly Deflate64).
 *
 * A full custom Deflate64 implementation is highly complex and not provided here.
 */
public class DeflateComparison {

    // --- Standard Deflate Compression/Decompression (using java.util.zip.Deflater/Inflater) ---

    /**
     * Compresses the given input data using the standard Deflate algorithm.
     *
     * @param inputData The byte array to compress.
     * @return The compressed byte array.
     */
    public static byte[] compressWithStandardDeflate(byte[] inputData) {
        // Create a new Deflater instance with default compression level
        Deflater deflater = new Deflater();
        // Set the input data for compression
        deflater.setInput(inputData);
        // Indicate that all input data has been provided
        deflater.finish();

        // Use a ByteArrayOutputStream to collect the compressed data
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream(inputData.length);
        // Buffer to hold compressed data chunks
        byte[] buffer = new byte[4096]; // Increased buffer size for efficiency

        // Loop until the deflater has finished compressing all data
        while (!deflater.finished()) {
            // Compress data into the buffer
            int count = deflater.deflate(buffer);
            // Write the compressed data from the buffer to the output stream
            outputStream.write(buffer, 0, count);
        }
        // Clean up native resources used by the deflater
        deflater.end();
        return outputStream.toByteArray();
    }

    /**
     * Decompresses the given compressed data using the standard Deflate algorithm.
     *
     * @param compressedData The byte array to decompress.
     * @return The decompressed byte array.
     * @throws DataFormatException If the compressed data format is invalid.
     */
    public static byte[] decompressWithStandardDeflate(byte[] compressedData) throws DataFormatException {
        // Create a new Inflater instance
        Inflater inflater = new Inflater();
        // Set the compressed input data
        inflater.setInput(compressedData);

        // Use a ByteArrayOutputStream to collect the decompressed data
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream(compressedData.length);
        // Buffer to hold decompressed data chunks
        byte[] buffer = new byte[4096]; // Increased buffer size for efficiency

        // Loop until the inflater has finished decompressing all data
        while (!inflater.finished()) {
            // Decompress data into the buffer
            int count = inflater.inflate(buffer);
            // Write the decompressed data from the buffer to the output stream
            outputStream.write(buffer, 0, count);
        }
        // Clean up native resources used by the inflater
        inflater.end();
        return outputStream.toByteArray();
    }

    // --- ZIP Compression using Java's default java.util.zip ---

    /**
     * Creates a ZIP file with a single entry using Java's built-in java.util.zip.
     *
     * IMPORTANT: This method does NOT support ZIP64.
     * If the source file is larger than 4GB, or the archive
     * contains too many entries, this will likely fail or produce an invalid ZIP.
     *
     * @param sourceFilePath The path to the file to be compressed and added to the ZIP.
     * @param zipFilePath    The path where the output ZIP file will be created.
     * @return The size of the created ZIP file, or -1 if an error occurred.
     */
    public static long compressWithJavaUtilZip(String sourceFilePath, String zipFilePath) {
        File sourceFile = new File(sourceFilePath);
        if (!sourceFile.exists()) {
            System.err.println("Source file not found for java.util.zip: " + sourceFilePath);
            return -1;
        }

        System.out.println("\nCompressing with Java's default java.util.zip...");
        try (FileOutputStream fos = new FileOutputStream(zipFilePath);
             ZipOutputStream zos = new ZipOutputStream(fos); // Use ZipOutputStream
             BufferedInputStream bis = new BufferedInputStream(new FileInputStream(sourceFile))) {

            // Create a new ZipEntry for the file
            ZipEntry zipEntry = new ZipEntry(sourceFile.getName());
            // Set the compression method to DEFLATED (which uses standard Deflate)
            zipEntry.setMethod(ZipEntry.DEFLATED);
            // Java's default ZipOutputStream does not expose options for Deflate64.

            zos.putNextEntry(zipEntry); // Add the entry to the ZIP

            byte[] buffer = new byte[8192]; // Buffer for copying data
            int bytesRead;
            while ((bytesRead = bis.read(buffer)) != -1) {
                zos.write(buffer, 0, bytesRead); // Write file content to the ZIP entry
            }

            zos.closeEntry(); // Close the current entry
            System.out.println("Successfully created ZIP file (using java.util.zip): " + zipFilePath);

            // Return the size of the created ZIP file
            return new File(zipFilePath).length();

        } catch (IOException e) {
            System.err.println("Error creating ZIP file with java.util.zip: " + e.getMessage());
            e.printStackTrace();
            return -1;
        }
    }

    public static void main(String[] args) {
        String largeFilePath = "LZW/testZIP/large_data_for_compression.txt";
        String standardDeflateOutput = "LZW/testZIP/output_standard_deflate.bin";
        String javaUtilZipOutput = "LZW/testZIP/output_javautilzip.zip"; // Changed output file name

        // --- Step 1: Create a large dummy file for testing ---
        // For actual Deflate64 benefits and ZIP64 testing, this file should be > 4GB.
        // For this demo, a 100MB file is used to show compression, but java.util.zip
        // will not use ZIP64 even if it were larger.
        long fileSizeMB = 100; // 100 MB file
        long fileSize = fileSizeMB * 1024 * 1024;
        System.out.println("Creating a large dummy file (" + fileSizeMB + "MB) at: " + largeFilePath + "...");
        try (FileOutputStream fos = new FileOutputStream(largeFilePath)) {
            byte[] dataChunk = new byte[1024 * 1024]; // 1MB chunk
            // Fill with repetitive data to ensure good compression ratio
            for (int i = 0; i < dataChunk.length; i++) {
                dataChunk[i] = (byte) ('A' + (i % 26));
            }

            for (long i = 0; i < fileSizeMB; i++) {
                fos.write(dataChunk);
            }
            System.out.println("Dummy file created successfully.");
        } catch (IOException e) {
            System.err.println("Failed to create large dummy file: " + e.getMessage());
            return;
        }

        // --- Step 2: Read the large file into memory for standard Deflate ---
        // Note: For very, very large files (> RAM), this approach won't work.
        // You'd need to stream the data directly to the Deflater/Compressor.
        byte[] fileBytes;
        try (FileInputStream fis = new FileInputStream(largeFilePath)) {
            fileBytes = fis.readAllBytes();
            System.out.println("\nOriginal file size: " + fileBytes.length + " bytes");
        } catch (IOException e) {
            System.err.println("Error reading large file into memory: " + e.getMessage());
            return;
        }

        // --- Step 3: Compress using standard Deflate (java.util.zip.Deflater) ---
        System.out.println("\nCompressing with standard Deflate (java.util.zip.Deflater)...");
        byte[] compressedStandardDeflate = compressWithStandardDeflate(fileBytes);
        System.out.println("Standard Deflate compressed size: " + compressedStandardDeflate.length + " bytes");

        // Save the standard Deflate output to a file (optional)
        try (FileOutputStream fos = new FileOutputStream(standardDeflateOutput)) {
            fos.write(compressedStandardDeflate);
        } catch (IOException e) {
            System.err.println("Error saving standard deflate output: " + e.getMessage());
        }

        // --- Step 4: Decompress and verify standard Deflate ---
        try {
            byte[] decompressedStandardDeflate = decompressWithStandardDeflate(compressedStandardDeflate);
            boolean matches = Arrays.equals(fileBytes, decompressedStandardDeflate);
            System.out.println("Standard Deflate decompression successful and matches original: " + matches);
        } catch (DataFormatException e) {
            System.err.println("Error decompressing standard Deflate: " + e.getMessage());
        }

        // --- Step 5: Compress using Java's default java.util.zip (for comparison) ---
        long javaUtilZipCompressedSize = compressWithJavaUtilZip(largeFilePath, javaUtilZipOutput); // Call new method
        if (javaUtilZipCompressedSize != -1) {
            System.out.println("Java.util.zip output file size: " + javaUtilZipCompressedSize + " bytes");
        }

        // --- Step 6: Compare Results ---
        System.out.println("\n--- Compression Comparison Summary ---");
        System.out.println("Original file size: " + fileBytes.length + " bytes");
        System.out.println("Standard Deflate output size: " + compressedStandardDeflate.length + " bytes");
        System.out.println("Java.util.zip output size: " + javaUtilZipCompressedSize + " bytes"); // Updated variable name

        // Clean up generated files
        System.out.println("\nCleaning up generated files...");
        new File(largeFilePath).delete();
        new File(standardDeflateOutput).delete();
        new File(javaUtilZipOutput).delete(); // Updated file name
        System.out.println("Cleanup complete.");
    }
}
