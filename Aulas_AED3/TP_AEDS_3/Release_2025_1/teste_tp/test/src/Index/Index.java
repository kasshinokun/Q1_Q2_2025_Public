
//JRE usando Java-SE 21

package Index;//Nome do Subprojeto



/**
 * @version 1_2025_02_07
 * @author Gabriel da Silva Cassino
 */

// Generalização de imports
import java.text.*;

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
        String sep = File.separator;// Separador do sistema operacional em uso
        String pathFile=System.getProperty("user.home")+sep+"Documents"+sep+"chinese_id.txt";

        Index File=new Index(FileReader.read_file2(pathFile,2));

        //Feedback apenas
        System.out.println("Exibindo Lista.\n");
        for(Object_X y:File.getList()) {
            FileReader.print(y.printObject());
        }
        //WriteToFileDOS(File, 1);
        WriteToFileDOS(File, 2);//DataOutputStream
        //WriteToFileDOS(File, 3);

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
    public static void WriteToFileDOS(Index File,int condition){//
        
    	//salva na pasta escolhida
    	//String outputPATH="C:\\Users\\Projeto Social Tiú\\Documents\\teste_tp\\list.txt"; 
    	String outputPATH="list.db";//Salva em target
        
    	for(Object_X y:File.getList()) {
            try {
                
                if (condition==1) {//Usando
                	
                	
                }	
                else if (condition==2) {//Usando byte array	e DataOutputStream
                	DataOutputStream stream;
                    if(!new File(outputPATH).exists()) {	
                    	stream= new DataOutputStream(new FileOutputStream(outputPATH));
                    }else {	
                    	stream= new DataOutputStream(new FileOutputStream(outputPATH,true));
                    	stream.write("\n".getBytes());
                    }
	                stream.write(y.getName().getBytes());
	                stream.write(y.getChinese_id().getBytes());
	                stream.write(y.getStringDate().getBytes());
	                stream.write(y.getRegisterDate().toString().getBytes());
	                stream.write(Integer.toString(y.getYear()).getBytes());
	                stream.close();
                } 
                else if (condition==3) {//Usando 
                	
                	
                }
                
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    //Arvore Processos-----------------------------------------------------------------------------------------------  






	    

}