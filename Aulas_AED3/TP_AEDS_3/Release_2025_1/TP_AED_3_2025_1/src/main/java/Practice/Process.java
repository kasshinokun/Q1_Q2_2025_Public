package Practice;

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
import Functions.*;
public class Process {
    
    //Class attributes
    private File file_p;
    private Path path_file_p;

//------------------------------Settings----------------------------------------    
    //Constructor
    public Process(File file_p, Path path_file_p) {
        this.file_p = file_p;
        this.path_file_p = path_file_p;
    }
    public Process() {
        
    }
    //Setters
    public void setFile_p(File file_p) {
        this.file_p = file_p;
    }

    public void setPath_file_p(Path path_file_p) {
        this.path_file_p = path_file_p;
    }
    
    //Getters
    public File getFile_p() {
        return file_p;
    }
    public Path getPath_file_p() {
        return path_file_p;
    }
    
//-----------------------------------Folder Manager-----------------------------    
    //get file folder path
    public String search_folder_to_path(){
        String path_File="";
        int input=1; //to stay on loop
        do{
            System.out.println("Choose a Path Folder");
            System.out.println("1) Documents");
            System.out.println("2) Custom Folder");
            input=functions_op.template();//error handling
            switch(input){
                case 1:
                    // code block
                    path_File=this.custom_folder_path(1);
                    break;
                case 2:
                    // code block
                    path_File=this.custom_folder_path(2);
                    break;
                default:   
                    if(input==0){
                        System.out.println("\nProcess finished");
                        System.out.println("Program ended.");
                    }else{
                        System.out.println("\nInvalid option.");
                        System.out.println("Please, try again.");  
                    }
            }    
        }while(input!=0);
        
        return path_File;
    }
    
    //custom path folder
    private String custom_folder_path(int condition){
        
        //base string to generate path folder
        String path_File="";

        //Default
        if (condition==1){
            
            //code block to generate Documents Folder Path
            path_File=(System.getProperty("user.home").concat("\\"+"Documents"));//Default Documents Folder Path
                                         //mudar para separador do sistema via programação java
        }else{
        //Custom generation of Custom Folder Path
            
            System.out.println("Listando Diretorios..........\n");
            
            path_File=System.getProperty("user.home");
            
            File[] directoriesUser=ListDirectories(path_File);//Instacia vetor do tipo File e recebe vetor da função

            int op2=1;//Qualificador para manter o processo de busca
            
            boolean resp=false;
            
            while(resp==true||op2==1) {

                for(int i=0;i<directoriesUser.length;i++){//Laço de repetição para analise de pastas
                    //se for pasta exibira o nome em tela
                    System.out.println("Pasta Encontrada 0"+(i)+"): "+directoriesUser[i].getName());//Nome do arquivo encontrado
                }
                System.out.println("\n");//Salta linha
                System.out.println("Escolha  uma pasta:..........");//Solicita ao usuario
                int op=functions_op.template();//aguarda escolha

                if(op>=0&&op<directoriesUser.length){//analise da opção em relação ao vetor
                    if(directoriesUser[op].isDirectory()==true){
                        //Concatena Path em String
                        path_File=(path_File.concat("\\"+directoriesUser[op].getName()));
                                                  //mudar para separador do sistema via programação java
                        System.out.println("Posso listar pastas dentro de: "+directoriesUser[op].getName());
                        System.out.println("1 - Continuar \n-Digite um valor qualquer para prosseguir");
                        op2=functions_op.template();//aguarda escolha

                        if(op2==1){

                            directoriesUser=ListDirectories(path_File);//Recebe vetor da função
                            resp=ListDirectories(path_File).length==0?false:true;//se vazio, encerra
                        }
                    }
                }                
            }
        }    
        System.out.println(path_File);
        return path_File;// retorna o caminho
    }
    
    private File[] ListDirectories(String nome){//lista pasta e retorna//Escolha do usuario
        File[] directoriesUser= new File(nome).listFiles(File::isDirectory);//lista somente diretorios
        return directoriesUser;//retorna vetor
    }
    
    
//-----------------------------------File Manager-------------------------------    
    //read file based on path
    public void Read_File(String path_File){
    
    
    }
    
    


}
