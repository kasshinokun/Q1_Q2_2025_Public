package Index;//Nome do Subprojeto

/**
 * @version 4_06_02_2025
 * @author Gabriel da Silva Cassino
 */

import java.io.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.file.*;//Simplificação de bibliotecas especificas e necessárias
import java.util.ArrayList;

import FileExplorer.*;//Simplificação de bibliotecas especificas para escrita e leitura
import FileExplorer.FileReader;//Leitor de arquivos - parte A
import Practice.Object_X; //Objeto No-Index
import Practice.Object_X_ID; //Objeto Index


//Writer class
public class Writer{
    
	//Atributos Normais como uma classe normal
    //----------> Path of a file
    static String FILEPATH = "output.db";
    //----------> Getting the file via creating File class object
    static File file = new File(FILEPATH);
    //----------> Array de objetos para os 3 processos
    static ArrayList<Object_X> list_person;
    
//------------------------------------>    
    public static void main(String[] args) {
    	teste(args);
    	
    }
    
    
    
    
    
//------------------------------------> testes   
    //Fonte: https://sentry.io/answers/how-to-create-a-file-and-write-to-it-in-java/
    public static void stage_0(String[] args) {
        String stringToWrite = "Java files are easy";
        FILEPATH="Arroz.txt";
        System.out.println("path: "+FILEPATH);
        try {
            BufferedWriter writer = new BufferedWriter(new FileWriter(FILEPATH));
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
            if(!file.exists()) {
            	OutputStream os = new FileOutputStream(file);
            	setOutputStream(os,"\n".getBytes());
            	setOutputStream(os,byteInt);
            	os = new FileOutputStream(file,true);
            	setOutputStream(os, byteChar);
            	setOutputStream(os,byteDouble);
            	
            	os.close();
            }
            else {
            	OutputStream os = new FileOutputStream(file,true);
            	setOutputStream(os,"\n".getBytes());
            	setOutputStream(os,byteInt);
            	setOutputStream(os, byteChar);
            	setOutputStream(os,byteDouble);
            	
            	os.close();
            }
            
        }

        // Catch block to handle exceptions
        catch (Exception e) {

                // Display message when exceptions occurs
                System.out.println("Exception: " + e);
        }
    }
    public static void setOutputStream(OutputStream os,byte[] bytearray) throws Exception
    {
    	// Starting writing the bytes in it

        // Writing received byte array
        os.write(bytearray);
        
        System.out.println(
                "Successfully byte inserted");

        // Close the file connections
        // using close() method
        
    
    
    
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
    public static void stage_3()//RandomAccessFile
    {
    	//Checar se existe o arquivo
    	
    	
    	
    	
    	
    	
    }
    //----------------> Testes 
    public static void teste(String[] args){//Apenas Teste de escrita
        System.out.println("Stage 00");
    	stage_0(args);//criação do arquivo 
    	System.out.println("Stage 01");
    	stage_1(args);//adição de conteúdo ao arquivo 
    	System.out.println("Stage 02");
    	stage_2(args);//Geeks for Geeks
    }
}
