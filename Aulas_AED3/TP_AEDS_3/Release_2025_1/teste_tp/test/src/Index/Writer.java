
//JRE usando Java-SE 21

package Index;//Nome do Subprojeto

/**
 * @version 1_07_02_2025
 * @author Gabriel da Silva Cassino
 */

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;


//https://sentry.io/answers/how-to-create-a-file-and-write-to-it-in-java/

// Importing required classes(GeeksforGeeks Byte Array to File)
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

// Main class
public class Writer{

// Java Program to Convert Integer, Character and Double
// Types into Bytes and Writing it in a File

    //--------------------->Attributes

	// Path of a file
	static String FILEPATH = "output.db";

	// Getting the file via creating File class object
	static File file = new File(FILEPATH);
   
	//---------------------->Main
	
	public static void main(String[] args){//Apenas Teste de escrita
        
		//stage_0(args);//criação do arquivo 
        
		//stage_1(args);//adição de conteúdo ao arquivo
		
		stage_2(args);//criação do arquivo 
        
		//stage_3(args);//adição de conteúdo ao arquivo
	}
	
	//----------------------->Testes
	
	public static void stage_0(String[] args) {
        String stringToWrite = "Java files are easy";
        try {
            BufferedWriter writer = new BufferedWriter(new FileWriter("newfile.txt"));
            writer.write(stringToWrite);
            writer.close();
        } catch (IOException ioe) {
            System.out.println("Couldn't write to file");
        }
    }
    

    public static void stage_1(String[]args) {
        String stringToWrite = "\nJava files are easy";
        try {
            BufferedWriter writer = new BufferedWriter(new FileWriter("newfile.txt", true));
            writer.write(stringToWrite);

            writer.close();
        } catch (IOException ioe) {
            System.out.println("Couldn't write to file");
        }
    }
    


//---------------------------GeeksforGeeks Tutorial 
	// Method 1
	// Writing the bytes into a file
	static void writeByte(byte[] byteInt, byte[] byteChar,
						byte[] byteDouble)
	{

		// Try block to check for exceptions
		try {

			// Initialize a pointer in file
			// using OutputStream class object
			OutputStream os;
			if(!file.exists()) {
				os= new FileOutputStream(file);
			}else{
				os= new FileOutputStream(file,true);
				setOutputStream(os,"\n".getBytes());
			}	
			// Starting writing the bytes in it
			setOutputStream(os,byteInt);
			setOutputStream(os, byteChar);
			setOutputStream(os,byteDouble);
			

			// Close the file connections
			// using close() method
			os.close();
		}

		// Catch block to handle exceptions
		catch (Exception e) {

			// Display message when exceptions occurs
			System.out.println("Exception: " + e);
		}
	}
    public static void setOutputStream(OutputStream os,byte[] byteArray)throws Exception {
    	
    	// Writing value inside byte array
		os.write(byteArray);

		// Display message for successful execution of
		// program
		System.out.println(
			"Successfully byte inserted");
    	
    }
	// Method 2
	// Main driver method
	public static void stage_2(String args[])
	{

		// Declaring and initializing data types
		int num = 56;
		char ch = 's';
		double dec = 78.9;

		// Inserting integer value
		byte[] byteInt = Integer.toString(num).getBytes();

		// Inserting character value
		byte[] byteChar = Character.toString(ch).getBytes();

		// Inserting double value
		byte[] byteDouble = Double.toString(dec).getBytes();

		// Calling Method 1 to
		// write the bytes into a file
		writeByte(byteInt, byteChar, byteDouble);
	}
}