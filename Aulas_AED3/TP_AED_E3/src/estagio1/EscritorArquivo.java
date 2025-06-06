package estagio1;

import java.io.*;
import java.nio.charset.*;
import java.util.*;

import estagio1.leitura.Functions;
import estagio1.leitura.LeitorArquivo;
import estagio1.leitura.ReadProcess;

public class EscritorArquivo {
	
	public static void main(String[] args){
		
		String userP=System.getProperty("user.home");//Pasta do Usuario do PC
		String folder="Documents";//Local padrão
        String sep = File.separator;// Separador do sistema operacional em uso
		String folder_file="TP_AEDS_III";
		String archive="traffic_accidents_pt_br_rev2.csv";
		//String archive="traffic_accidents_rev2.csv";
		String Path=userP.concat(sep+folder).concat(sep+folder_file).concat(sep+archive);
		
		//writeAllFile(1,archive,"traffic_accidents.db");
		
		//writeAllFile(2,"\"Definido em Processo Padrão\"","traffic_accidents.db");
		
		Start();
		
	}public static void Start(){	
		int op=0;
			
		//String pathFile="traffic_accidents_rev2.csv";
		String pathFile="data/traffic_accidents_pt_br_rev2.csv";
		String pathDb="data/traffic_accidents.db";
		
		do {
			System.out.println("\n===================Padrão=========================");
			System.out.println("\nProcessos de escrita\n");
			System.out.println("1) escrever todos os registros");
			System.out.println("2) escrever apenas um registro");
			System.out.println("\n==================Apendice========================");
			System.out.println("\nAnalise a criterio:\nCódigo reaproveitado para adicionar funcionalidade\n");
			System.out.println("3) explorador de arquivo");
			System.out.println("\n0) Sair\n\nEscolha um valor-------> :");
			op=Functions.only_Int();
			switch(op) {
				case 1:
					writeAllFile(op,pathFile,pathDb);
					break;
				case 2:
					writeAllFile(op,"\"Definido em Processo Padrão\"",pathDb);
				    break;
				case 3:
					//Envia o tipo de processo de escrita (int typeWrite)
					//TP parte 1=1
					//TP parte 2=2
					estagio1.FileExplorer.FileExplorer.seek(1);
					break;
				default:
					if(op==0) {
						System.out.println("\nVoltando ao ao Menu da Parte I.");
					}else {
						System.out.println("\nTente novamente, escolha fora do escopo.");
					}
			}
		}while(op!=0);
			
	}
	public static void writeAllFile(int condition,String pathFile,String pathDb){
		
		System.out.println("Caminho recebido: "+pathFile);
		
		RandomAccessFile randomAccessFile=null;
		
		DataObject obj;
		if (condition==2) {
			try {
				
				writerFile(EscritorUpdateArquivo.newObject(new DataObject()), pathDb);//Inicia o Processo de escrita
				
			}catch(IOException e) {
				e.printStackTrace();
			}
		}else {
		
			
			if(findFile(pathFile)){
				try {
						
					randomAccessFile = new RandomAccessFile(pathFile,"r");
		            
		            System.out.println(randomAccessFile.readLine());//leitura para ignora o cabeçalho do arquivo .csv, mas exibe(FeedBack apenas)
		            
		            System.out.println("================================================================================================");
		            
		            while (true||randomAccessFile.readLine()!=null) {
		            	
		                String[] line=randomAccessFile.readLine().split(";");
		                
		                int id=LeitorArquivo.getHeader(pathDb);//recebe o valor presente no cabeçalho
		                
		                obj=new DataObject(line,++id);//Instancia objeto incrementando a ID
		                
		                System.out.println(obj.toStringObject());//Exibe o objeto
		                
		                writerFile(obj, pathDb);//Inicia o Processo de escrita
		                
		                System.out.println("================================================================================================");
		                
		            }
				} catch (NullPointerException n) {
		             System.out.println("Fim da leitura e escrita do arquivo .db.");            
				} catch (IOException ioe) {
		            ioe.printStackTrace();
		        } finally {
		            try {
		            	randomAccessFile.close();
		            } catch (IOException ioe) {
		                ioe.printStackTrace();
		            }
		        }
			}else {
				System.out.println("Não localizei o arquivo.");
			}
		}
    }
  
	public static boolean findFile(String Path) {
		File diretorio = new File(Path);
		if (!diretorio.exists())
			return false;
		else
			return true;
	}
	public static void writerFile(DataObject object, String pathDb) throws IOException {
	    //se houver erro retorna a Exception para interromper o processo 
        //que chamou o procedimento (por isto não existe o try-catch)
		
		RandomAccessFile randomAccessFile = new RandomAccessFile(pathDb, "rw");//instancia o RandomAccessFile para ler e escrever 
		
		//Não há tratativa para registro duplicado com ID diferente
		randomAccessFile.writeInt(object.getID_registro());//Atualiza o cabeçalho
		
		byte[] bytearray=object.toByteArray();
        int tamanho=bytearray.length;
        long fimdoarquivo=LeitorArquivo.find_end(randomAccessFile);
        
        writeRandomAccessFile(fimdoarquivo, bytearray,true,tamanho,randomAccessFile,object.getID_registro());
        
        randomAccessFile.close();
			
	}
	
	//processo de escrita
    public static void writeRandomAccessFile(long posicao, byte[]bytearray,
    		
    		boolean lapide,int tamanho, RandomAccessFile raf,int ID)throws IOException{
        
            raf.seek(posicao);//busca a posição designada no arquivo

            raf.writeInt(ID);//Grava a ID fora do registro
            
            raf.writeBoolean(lapide);//escreve o boolean lapide
            
            raf.writeInt(tamanho);//escreve o tamanho do vetor

            raf.write(bytearray);//escreve o vetor no arquivo
            
            
            
    }
    
    
    
	
    
}
