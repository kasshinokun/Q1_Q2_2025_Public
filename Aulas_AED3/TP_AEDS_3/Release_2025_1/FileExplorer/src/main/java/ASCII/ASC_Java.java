package ASCII;

import java.nio.*;
import java.nio.charset.*;
import java.util.*;
import java.util.stream.*;

//It's created to train myself after an idea came from a challenge to me.
//It's will be changed to my own code to meet my goals.

public class ASC_Java{
  public static void main(String[] args)
  {
      //Geeks for Geeks Example
      strToBinary("geeks");  

      // Mkyong Example
      StringToBinaryExample1("Hello");
      StringToBinaryExample2("a");
      StringToBinaryExample3("01001000 01100101 01101100 01101100 01101111");
      System.out.println("String Base is 你.");
      UnicodeToBinary1("你".getBytes(StandardCharsets.UTF_8));
      UnicodeToBinary2("111001001011110110100000");   
      
      //Tutorial Point Example 
      HexadecimalToString(StringToHexadecimal("Tutorialspoint")); 
    
    }
    public static void Mkyong4_5(){
           
      System.out.println("String Base is 你.");
      UnicodeToBinary1("你".getBytes(StandardCharsets.UTF_8));
      UnicodeToBinary2("111001001011110110100000");// 你, Chinese character
      
    }
	
//=======================Geeks for Geeks Example 
/*
Source-base developed by 29AjayKumar
Source-url: https://www.geeksforgeeks.org/convert-string-binary-sequence/
*/
// Java program to convert
// string into binary string
	// utility function
	static void strToBinary(String s)
	{
		int n = s.length();
		System.out.println("String Base is "+s+"\nConverting to Binary: ");
		for (int i = 0; i < n; i++) 
		{
			// convert each char to
			// ASCII value
			int val = Integer.valueOf(s.charAt(i));

			// Convert ASCII value to binary
			String bin = "";
			while (val > 0) 
			{
				if (val % 2 == 1)
				{
					bin += '1';
				}
				else
					bin += '0';
				val /= 2;
			}
			bin = reverse(bin);

			System.out.print(bin + " ");
		}
	}

	static String reverse(String input) 
	{
		char[] a = input.toCharArray();
		int l, r = 0;
		r = a.length - 1;

		for (l = 0; l < r; l++, r--)
		{
			// Swap values of l and r 
			char temp = a[l];
			a[l] = a[r];
			a[r] = temp;
		}
		return String.valueOf(a);
	}

//================Mkyong Example 1
/*
Source-base developed by Mkyong
Source-url: https://mkyong.com/java/java-convert-string-to-binary/
*/

    public static void StringToBinaryExample1(String input) {
      
        String result = convertStringToBinary(input);
        System.out.println("\n\nString Base is "+input);
        System.out.println("Converted String is "+result);

        // pretty print the binary format
        System.out.println("Annother convertion is "+prettyBinary(result, 8, " "));

    }

    public static String convertStringToBinary(String input) {

        StringBuilder result = new StringBuilder();
        char[] chars = input.toCharArray();
        for (char aChar : chars) {
            result.append(
                    String.format("%8s", Integer.toBinaryString(aChar))   // char -> int, auto-cast
                            .replaceAll(" ", "0")                         // zero pads
            );
        }
        return result.toString();

    }
    //Mkyong Example 2
    public static void StringToBinaryExample2(String input) {

        String result = convertByteArraysToBinary(input.getBytes(StandardCharsets.UTF_8));
        System.out.println("\nString Base is "+input);
        System.out.println("Converted String is "+prettyBinary(result, 8, " ")+"\n");
        

    }

    public static String convertByteArraysToBinary(byte[] input) {

        StringBuilder result = new StringBuilder();
        for (byte b : input) {
            int val = b;
            for (int i = 0; i < 8; i++) {
                result.append((val & 128) == 0 ? 0 : 1);      // 128 = 1000 0000
                val <<= 1;
            }
        }
        return result.toString();

    }

    //Mkyong Example 3
    public static void StringToBinaryExample3(String input) {

        
        // Java 8 makes life easier
        String raw = getString(input); 

        System.out.println("Binary String is "+input+"\nthe converted String is "+raw+"\n");
        

    }
    static String getString(String input) {

        // Java 8 makes life easier
        return Arrays.stream(input.split(" "))
                .map(binary -> Integer.parseInt(binary, 2))
                .map(Character::toString)
                .collect(Collectors.joining()); // cut the space
    	
    }

    //Mkyong Example 4
    public static void UnicodeToBinary1(byte[] input) {
        
        String binary = convertByteArraysToBinary4(input);
        
        System.out.println("Size of byte array is "+input.length);                       // 3, 1 Chinese character = 3 bytes
        System.out.println("Binary is "+binary);
        System.out.println("Another version Binary is "+prettyBinary(binary, 8, " "));

    }

    public static String convertByteArraysToBinary4(byte[] input) {

        StringBuilder result = new StringBuilder();
        for (byte b : input) {
            int val = b;
            for (int i = 0; i < 8; i++) {
                result.append((val & 128) == 0 ? 0 : 1);      // 128 = 1000 0000
                val <<= 1;
            }
        }
        return result.toString();

    }
    //Mkyong Example 5
    public static void UnicodeToBinary2(String binary) {

        String result = binaryUnicodeToString(binary);
        System.out.println();
        System.out.print("Binary String Base is "+binary+"\nReconverting to String: ");
        System.out.println(result.trim()+"\n");
    }

    // <= 32bits = 4 bytes, int needs 4 bytes
    public static String binaryUnicodeToString(String binary) {

        byte[] array = ByteBuffer.allocate(4).putInt(   // 4 bytes byte[]
                Integer.parseInt(binary, 2)
        ).array();

        return new String(array, StandardCharsets.UTF_8);
    }
	
    
    //It's same to example 1,2 and 4
    public static String prettyBinary(String binary, int blockSize, String separator) {

        List<String> result = new ArrayList<>();
        int index = 0;
        while (index < binary.length()) {
            result.add(binary.substring(index, Math.min(index + blockSize, binary.length())));
            index += blockSize;
        }

        return result.stream().collect(Collectors.joining(separator));
    }
    
//================Tutorialspoint Example
/*
Source-base developed by Tutorialspoint
https://www.tutorialspoint.com/how-to-convert-a-string-to-hexadecimal-and-vice-versa-format-in-java
*/
 
  public static String StringToHexadecimal(String str) {
      
    System.out.println("The choiced String value is \n"+str);
    StringBuffer sb = new StringBuffer();
    //Converting string to character array
    char ch[] = str.toCharArray();
    for(int i = 0; i < ch.length; i++) {
      String hexString = Integer.toHexString(ch[i]);
      sb.append(hexString);
    }
    String result = sb.toString();
    System.out.println("\nHex String: "+result+"\n");
    
    return result;
  }
 
  public static void HexadecimalToString(String str) {
    
    System.out.println("The Received Hexadecimal \nString value is\n"+str);
    String result = new String();
    char[] charArray = str.toCharArray();
    for(int i = 0; i < charArray.length; i=i+2) {
      String st = ""+charArray[i]+""+charArray[i+1];
      char ch = (char)Integer.parseInt(st, 16);
      result = result + ch;
    }
    System.out.println("\nThe rebuilded String is "+result);
  }

}
