package Index;//Nome do Subprojeto

/**
 * @version 1_2025_02_08
 * @author Gabriel da Silva Cassino
 */

// Generalização de imports
import java.text.*;
import java.sql.*;
import java.time.*;//Testar viabilidade
import java.time.format.*;
import java.util.*;//Simplificação de bibliotecas necessarias 
import java.util.regex.*;//Simplificação de bibliotecas especificas e necessarias 
import java.util.stream.*;//Simplificação de bibliotecas especificas e necessárias

import java.io.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.file.*;//Simplificação de bibliotecas especificas e necessárias
import FileExplorer.*;//Simplificação de bibliotecas especificas para escrita e leitura
import FileExplorer.FileReader;
import Practice.Object_X;
import Practice.Object_X_ID;

import Index.*;

public class Index {
    
    private ArrayList<Object_X> list_person;
    
    //Constructors
    public Index(){
    
    
    } 
    public Index(ArrayList<Object_X> list_person){
        this.list_person=list_person;
    }
    
    //Setter
    public void setList(ArrayList<Object_X> list_person){
        this.list_person=list_person;
    }
    
    //Getter
    public ArrayList<Object_X> getList( ){
        return this.list_person;
    }
    
    public static void main(String[] args) {

        FileReader.print("Index Home");
        
        String pathFile="C:\\Users\\Projeto Social Tiú\\Documents\\teste_tp\\chinese_id.txt";

        Index File=new Index(FileReader.read_file2(pathFile,2));
		
        //Feedback apenas
        /*
        System.out.println("Exibindo Lista.\n");
        for(Object_X y:File.getList()) {
            FileReader.print(y.printObject());
        }*/
        /*
        FileReader.print("Start Write");
        try {
			Thread.sleep(5000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}*/
        
        WriteToFileDOS(File, 1);//DataOutputStream
        
        FileReader.print("Start Read");
        try {
			Thread.sleep(5000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
        ReadToFileBR("list.db");//BufferedReader
    }
    public static void SelectWriter(ArrayList<Object_X> list_person,int condition) {
    //O Seletor do escritor definirá se é para No-Indexed,Indexed ou Tree-Indexed	
        //---> 1 não faz nada


        //---> 2 <--No-Indexed Writer
        


        //---> 3 <--Indexed Writer



        //---> 4 <--Tree-Indexed Writer


    }
    //Indexed No-Indexed Processos-----------------------------------------------------------------------------------    
    public static void Writer_File(Index File,int condition){
        






    }
    //Preludio Escrita
    public static byte[] BAO(Object X) throws UnsupportedEncodingException {
    	
    	if(X.getClass()==(String.class)) {
    		return X.toString().getBytes("UTF-8");
    	}
    	
    	else if(X.getClass()==(Integer.class)) {
    		return Integer.toString((int)X).getBytes("UTF-8");
    	}

    	else if(X.getClass()==(Float.class)) {
    		return Float.toString((float)X).getBytes("UTF-8");
    	}

    	else if(X.getClass()==(Double.class)) {
    		return Double.toString((double)X).getBytes("UTF-8");
    	}
    	else {
    		return null;
    	}
    }
    
    
    
    
    public static void WriteToFileDOS(Index File,int condition){
        
    	//salva na pasta escolhida
    	//String outputPATH="C:\\Users\\Projeto Social Tiú\\Documents\\teste_tp\\list.txt"; 
    	String outputPATH="list.db";//Salva externo as pasta do programa
        
    	
    	
    	
    	if(condition==1) {//Write using DataOutputStream (Done with Sucess)
	    	for(Object_X y:File.getList()) {
	            try {
	            	DataOutputStream stream;
	                if(!new File(outputPATH).exists())
	                	stream = new DataOutputStream(new FileOutputStream(outputPATH));
	                else {
	                	stream = new DataOutputStream(new FileOutputStream(outputPATH,true));
	                }
	                
	                stream.write(y.getName().getBytes("UTF-8"));
	                
	                stream.write(y.getChinese_id().getBytes("UTF-8"));
	                
	                stream.write(y.getStringDate().getBytes("UTF-8"));
	                
	                stream.write(y.getRegisterDate().toString().getBytes("UTF-8"));
	                
	                stream.write(Integer.toString(y.getYear()).getBytes("UTF-8"));
	                
	                stream.write("\n".getBytes("UTF-8"));
	                
	                stream.close();
	            } catch (IOException e) {
	                e.printStackTrace();
	            }
	        }
    	}
    	if(condition==2) {//Another method on development
	    	for(Object_X y:File.getList()) {
	            
	    		
	    		
	    		
	    		
	    		
	    		
	    		
	        }
    	}
    	
    	
    	
    	
    	
    	
    }
    //Preludio Leitura
    public static void ReadToFileBR(String outputPATH){//(Done with Sucess)
        
    	//leitura na pasta escolhida
    	//String outputPATH="C:\\Users\\Projeto Social Tiú\\Documents\\teste_tp\\list.txt"; 
    	//String outputPATH="list.db";//leitura externo as pasta do programa
    	BufferedReader reader;

		try {
			reader = new BufferedReader(new java.io.FileReader(outputPATH));
			String line = reader.readLine();

			while (line != null) {
			// Name     Chinese ID     String Date     Date    Year	
			//卞钧益 330902199409090312 19940909      1994-09-09 1994
				System.out.println(new Object_X(line.substring(0, (line.length()-40)),//Name 
						line.substring((line.length()-40), (line.length()-22)))//Chinese ID 
						.printObject());//Print Data Object

				// read next line
				line = reader.readLine();
			}

			reader.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
    	
    	
    }
    //Arvore Processos-----------------------------------------------------------------------------------------------  






	    

}
