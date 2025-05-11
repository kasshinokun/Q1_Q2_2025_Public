
//JRE usando Java-SE 21

package FileExplorer;//Nome do Subprojeto

/**
 * @version 2_2025_02_06
 * @author Gabriel da Silva Cassino
 */


import java.util.*;//Simplificação de bibliotecas necessarias 
import java.util.regex.*;//Simplificação de bibliotecas especificas e necessarias 
import java.util.stream.*;//Simplificação de bibliotecas especificas e necessárias

import java.io.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.file.*;//Simplificação de bibliotecas especificas e necessárias
import FileExplorer.*;//Simplificação de bibliotecas especificas para escrita e leitura

public class FileExplorer {//Explorador de Arquivos
	
//Chamada principal e de testes    
    public static void main(String[] args) {
        
        System.out.println("Hello World!");//Feedback apenas
        String userP=System.getProperty("user.home");//Pasta do Usuario do PC
        get_FolderPath(userP, args);//Inicia os processos a partir 
                              //da Pasta do Usuario do OS em uso
    
    }  
//Caminho, Arquivos e Pastas-Gerenciamento-----------------------------------------------------------------------  
    public static void get_FolderPath(String userP, String[] args){//Obter caminho para inicar buscar de arquivo    
        
        //Opções do procedimento
        System.out.println("\nTipo de Busca:");
        System.out.println("1)Listar arquivos --->Documentos");
        System.out.println("2)Listar pastas dentro da pasta Documentos");
        System.out.println("3)Escolha do Usuario");
        System.out.println("4)UTF-8");
        System.out.println("5)Listar pastas dentro da pasta Documentos\nGravar em Arquivo"); 
        System.out.println("Qualquer outro valor ---> Sair\n");
        
        //Instancia String base para gerar o PATH da pasta Documentos
        String folder="Documents";//Local padrão
        String sep = File.separator;// Separador do sistema operacional em uso
        String folderPath;//Instancia String base para guardar o PATH da pasta escolhida
        int op=functions_op.template();//escolha do usuario
        switch(op){
            case 1:
                
                //Concatena String com PATH default da pasta Documentos 
                //e busca arquivos .txt
                chooseFiles(userP.concat(sep+folder),".txt",1);
            
                break;
            case 2: 
                
                //Concatena String com PATH default da pasta Documentos           
                //Busca na pasta Users/<Nome_Usuario>/Documents   
                folderPath=chooseDirectory((userP.concat(sep+folder)));
                //busca arquivos .txt no PATH informado
                System.out.println(folderPath);
                chooseFiles(folderPath,".txt",1);
            
                break;
            case 3: 
                       
                //Busca na pasta Users
                folderPath=chooseDirectory(userP);
                //busca arquivos .txt no PATH informado
                System.out.println(folderPath);
                chooseFiles(folderPath,".txt",1);
                
                break;
            case 4:
                
                read_utf8.main(args);
                
                break;
            default:
                
                //se fora do escopo interrompe o processo
                System.out.println("\n==Opcao Invalida....Finalizando Processo.....");//Encerra
                System.out.println("==Retornando ao Menu Principal===============\n");//Enunciado
        }
    }
    
//Caminho e Pastas-----------------------------------------------------------------------------------------------        
    private static File[] ListDirectories(String nome){//lista pasta e retorna//Escolha do usuario
        
        File[] directoriesUser= new File(nome).listFiles(File::isDirectory);//lista somente diretorios
        return directoriesUser;//retorna vetor
    }
    private static String chooseDirectory(String folderPath){
       
        boolean resp=false;//Qualificador de interrupção de Processo
        File[] directoriesUser=ListDirectories(folderPath);//Instacia vetor do tipo File 
        //e recebe vetor com os PATH's das pastas
        
        //While de busca 
        while(resp==false){
            
            if (directoriesUser.length!=0){
            //Se directoriesUser not null
                int tamanho=directoriesUser.length;//Referencia do tamanho do vetor
   
                for(int i=0;i<tamanho;i++){//Laço de repetição para analise de pastas
                    //se for pasta exibira o nome em tela(Feedback para escolha)
                    System.out.println("Pasta Encontrada 0"+(i)+"): "+directoriesUser[i].getName());
                }
                //Solicita a escolha
                System.out.println("\nPor favor escolha e digite o numero da pasta desejada:\n---> ");
                int choice=functions_op.template();//escolha do usuario
                
                
                if (choice>-1&&choice<tamanho){
                    folderPath=directoriesUser[choice].getPath();
                    System.out.print("Posso buscar o arquivo na pasta "+directoriesUser[choice].getName()+"?"
                    + "\n 1) Sim\n 2) Ver subpastas\nEscolha uma alternativa: --->");
                    choice=functions_op.template();//escolha do usuario
                    if(choice==2){
                        directoriesUser=ListDirectories(folderPath);//Recebe vetor da função
                        System.out.println(directoriesUser.length);
                        if (directoriesUser.length==0){
                            System.out.println("Sem subpastas, encaminhando para busca no caminho base");
                            resp=true;//se vazio, encerra
                        }
                    }else{
                        resp=true;//se a escolha for 1, encerra
                    }
                } 
            }else{//Senão retorna empty ou null object
                System.out.println("Sem subpastas, encaminhando para busca no caminho base");
                resp=true;//Altera o estado para encerrar  
            }
        }
        return folderPath;//Retorna o Path da pasta
    }
//Caminho e Arquivos---------------------------------------------------------------------------------------------
    private static File[] ListFiles(String folderPath,String extension){//lista arquivos e retorna
         
        //Escolha do usuario
        return new File(folderPath).listFiles((File pathname) -> pathname.getName().endsWith(extension));
        //retorna vetor                                          //lista somente arquivos com a extensão desejada
    }
    
    
    private static void chooseFiles(String folderPath,String extension,int condition){
        
        File[] files = ListFiles(folderPath, extension);//Instacia vetor do tipo File 
        //e recebe vetor com os PATH's dos arquivos baseado na extensão
        int tamanho=files.length;//Referencia do tamanho do vetor
        if(tamanho!=0){//Se não for empty ou null object
            for(int i=0;i<files.length;i++){//Laço de repetição para analise de arquivos
                //se for arquivo do tipo .txt exibira o nome em tela
                System.out.println("Arquivo Encontrado 0"+(i)+"): "+files[i].getName());//Nome do arquivo encontrado
            }
            //Solicita a escolha
            System.out.print("\nPor favor escolha e digite o numero do arquivo desejado:\n---> ");
            int choice=functions_op.template();//escolha do usuario
            if (choice>-1&&choice<tamanho){//se dentro do escopo inicia o processo
                
                //Processo de leitura do arquivo
                String pathFile=files[choice].getPath();
                if (condition >=1&&condition<=4) {//leitura, atribuição e escrita mediante escolha
            		//FileReader.read_file(pathFile);//Funcionou
            		FileReader.read_file2(pathFile,condition);//Erro corrigido 12442 registros
            	}else{//Preventivo Apenas
                    System.out.println("Fora do escopo interrompendo o processo.\n");
                }  	
                	
                
                
            }//se fora do escopo interrompe o processo
            else{
                System.out.println("Fora do escopo interrompendo o processo.\n");
            }
        }else{//se não houver arquivos interrompe o processo
            System.out.println("Pasta sem arquivos "+extension+".\n");
        }
    
    
    
    
    
    }

//Funções Handling-----------------------------------------------------------------------------------------------    
    public class functions_op {
        
        public static int template(){//input validate(on development)
            Scanner reader=new Scanner(System.in);
            if(reader.hasNextInt()){
                return reader.nextInt();
            }else{
                return -1;
            }
        }
    }
}
