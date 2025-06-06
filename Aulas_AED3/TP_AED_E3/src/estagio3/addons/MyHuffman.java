package estagio3.addons;
//Java Program to Implement
//Huffman Coding

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.PriorityQueue;
import java.util.HashMap;

//Driver Class
public class MyHuffman{
	// Main Function
	public static void main(String[] args) {
	     String csvFilePath = "traffic_accidents_pt_br_rev2.csv"; // Name of your CSV file containing the text
	
	     // 1. Read the entire CSV file content as a single string
	     String fileContent = readCsvAsString(csvFilePath);
	
	     if (fileContent == null || fileContent.isEmpty()) {
	         System.out.println("No content read from CSV or an error occurred. Exiting.");
	         return;
	     }else{
	         // The message to be encoded
	    	 executeHuffman(fileContent);
	
	     }
	     
	}
	public static String readCsvAsString(String filePath) {
	     StringBuilder contentBuilder = new StringBuilder();
	     try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
	         String line;
	         while ((line = br.readLine()) != null) {
	             contentBuilder.append(line);
	             // Optionally add a newline character if you want to preserve line breaks
	             contentBuilder.append("\\");
	             contentBuilder.append("n");
	         }
	     } catch (IOException e) {
	         System.err.println("Error reading CSV file: " + e.getMessage());
	         return null;
	     }
	     return contentBuilder.toString();
	 }
	 // Method to print the Huffman codes
	 public static void printCodes(HuffmanNode root, StringBuilder code) {
	     if (root == null) return;
	
	     // If this is a leaf node, print the character and its code
	     if (root.data != '$') {
	         System.out.println(root.data + ": " + code);
	     }
	     
	     // Traverse the left subtree
	     if (root.left != null) {
	         printCodes(root.left, code.append('0'));
	         code.deleteCharAt(code.length() - 1);
	     }
	     
	     // Traverse the right subtree
	     if (root.right != null) {
	         printCodes(root.right, code.append('1'));
	         code.deleteCharAt(code.length() - 1);
	     }
	 }
	 public static void executeHuffman(String message) { 
	     
		 // Create a frequency map to count the frequency of each character
	     HashMap<Character, Integer> frequencyMap = new HashMap<>();
	 
	     for (char c : message.toCharArray()) {
	         frequencyMap.put(c, frequencyMap.getOrDefault(c, 0) + 1);
	     }
	
	     // Create a priority queue to build the Huffman Tree
		 PriorityQueue<HuffmanNode> priorityQueue =
		 new PriorityQueue<>((a, b) -> a.frequency - b.frequency);
		
		 // Create a Huffman node for each character and add it to the priority queue
		 for (char c : frequencyMap.keySet()) {
		     priorityQueue.add(new HuffmanNode(c, frequencyMap.get(c)));
		 }
		
		 // Build the Huffman Tree
		 while (priorityQueue.size() > 1) {
		     // Remove the two nodes with the lowest frequency
			 HuffmanNode left = priorityQueue.poll();
			 HuffmanNode right = priorityQueue.poll();
			
			 // Create a new internal node with these two nodes
			 // as children and add it back to the queue
			 HuffmanNode newNode =
			 new HuffmanNode('$', left.frequency + right.frequency);
		 
		     newNode.left = left;
		     newNode.right = right;
		     priorityQueue.add(newNode);
		 }
		
		 // The remaining node is the root of the Huffman Tree
		 HuffmanNode root = priorityQueue.poll();
		
		 // Print the Huffman codes for each character
		 System.out.println("Huffman codes:");
		 printCodes(root, new StringBuilder());
	
	 }
 

}
// Class representing a node in the Huffman Tree
class HuffmanNode {
  	// Character data
    char data;           
  	
  	// Frequency of the character
    int frequency;       
  
  	// Left and right child nodes
    HuffmanNode left, right; 

    // Constructor to initialize the node
    HuffmanNode(char data, int frequency) {
        this.data = data;
        this.frequency = frequency;
        left = right = null;
    }
}

