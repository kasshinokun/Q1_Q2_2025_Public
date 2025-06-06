package estagio2.Escrita;

import java.io.EOFException;
import java.io.IOException;
import java.io.RandomAccessFile;

import estagio1.EscritorArquivo;
import estagio1.leitura.DeleteProcess;
import estagio1.leitura.Functions;
import estagio1.leitura.LeitorArquivo;
import estagio2.DataIndex;
import estagio2.Index;

public class EscritorIndex {

	public static void main(String[] args) {
		/*
		//String pathFile="traffic_accidents_rev2.csv";
		String pathFile="traffic_accidents_pt_br_rev2.csv";
		
		String pathDb="index/traffic_accidents.db";
		
		String pathIndex="index/indexTrafficAccidents.db";
		
		writeAllIndex(1,pathFile,"index/traffic_accidents.db","index/indexTrafficAccidents.db");
		 */
		Start();
	}
	public static void Start(){	
		int op=0;
			
		//String pathFile="traffic_accidents_rev2.csv";
		String pathFile="data/traffic_accidents_pt_br_rev2.csv";

		String pathDb="index/traffic_accidents.db";
		
		String pathIndex="index/indexTrafficAccidents.db";
		
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
					writeAllIndex(op,pathFile,pathDb,pathIndex);
					break;
				case 2:
					writeAllIndex(op,"\"Definido em Processo Padrão\"",pathDb,pathIndex);
				    break;
				case 3:
					//Envia o tipo de processo de escrita (int typeWrite)
					//TP parte 1=1
					//TP parte 2-A=2
					estagio1.FileExplorer.FileExplorer.seek(2);
					break;
				default:
					if(op==0) {
						System.out.println("\nVoltando ao ao Menu da Parte II.");
					}else {
						System.out.println("\nTente novamente, escolha fora do escopo.");
					}
			}
		}while(op!=0);
			
	}	
	public static void writeAllIndex(int condition,String pathFile,String pathDb,String pathIndex){
		
		System.out.println("Caminho recebido: "+pathFile);
		
		RandomAccessFile rafReaderData= null;
		DataIndex objIndex;
		
		if (condition==2) {
			try {
				int ID_Registro=LeitorArquivo.getHeader(pathIndex);
				writerRegistryIndex(ID_Registro,EscritorUpdateIndex.newObject(0,new DataIndex(), pathIndex, pathIndex), pathDb,pathIndex);//Inicia o Processo de escrita
				
			}catch(IOException e) {
				e.printStackTrace();
			}
		}else {
		
		
			if(EscritorArquivo.findFile(pathFile)){
				try {
				
					rafReaderData = new RandomAccessFile(pathFile,"r");
		            
		            System.out.println(rafReaderData.readLine());//leitura para ignora o cabeçalho do arquivo .csv, mas exibe(FeedBack apenas)
		            
		            System.out.println("================================================================================================");
		            
		            
	            
		            while (true||rafReaderData.readLine()!=null) {
		            	
		            	String[] line=rafReaderData.readLine().split(";");
		                
		                int ID_Registro=LeitorArquivo.getHeader(pathIndex);//recebe o valor presente no cabeçalho
		                
		                objIndex=new DataIndex(line);//Instancia objeto
		                
		                System.out.println("\nID Registro---------------------------> "+(++ID_Registro));
		                
		                System.out.println(objIndex.toStringObject());//Exibe o objeto
		                
		                writerRegistryIndex(ID_Registro,objIndex, pathDb,pathIndex);//Inicia o Processo de escrita
		                
		                System.out.println("================================================================================================");
		                
		            }
				} catch (NullPointerException n) {
		             System.out.println("Fim da leitura e escrita do arquivo .db.");            
				} catch (IOException ioe) {
		            ioe.printStackTrace();
		        } finally {
		            try {
		            	rafReaderData.close();
		            } catch (IOException ioe) {
		                ioe.printStackTrace();
		            }
		        }
			}else {
				System.out.println("Não localizei o arquivo.");
			}
		}
    }
	public static void writerRegistryIndex(int ID_Registro,DataIndex object, String pathDb,String pathIndex) throws IOException {
	    //se houver erro retorna a Exception para interromper o processo 
        //que chamou o procedimento (por isto não existe o try-catch)
		
			
		byte[] bytearray=object.toByteArray();
        int tamanho=bytearray.length;
        long pointerRegistry=LeitorArquivo.find_end(new RandomAccessFile(pathDb, "rw"));
        
        writeRafIndexedData(pointerRegistry, bytearray,true,tamanho,new RandomAccessFile(pathDb, "rw"));
        
        createIndex(ID_Registro,true,new RandomAccessFile(pathIndex, "rw"),pointerRegistry);
       
			
	}
	public static void writeRafIndexedData(long pointerRegistry, byte[]bytearray,
    		
    		boolean lapide,int tamanho, RandomAccessFile rafIndexedData)throws IOException{
		rafIndexedData.seek(pointerRegistry);//busca a posição designada no arquivo
        
        rafIndexedData.writeBoolean(lapide);//escreve o boolean lapide
        
        rafIndexedData.writeInt(tamanho);//escreve o tamanho do vetor

        rafIndexedData.write(bytearray);//escreve o vetor no arquivo
		
	}
	public static void createIndex(int ID_Registro,boolean lapide,RandomAccessFile rafIndex,long pointerRegistry)throws IOException{
		
		rafIndex.writeInt(ID_Registro);
		rafIndex.seek(LeitorArquivo.find_end(rafIndex));//busca a posição designada no arquivo
		rafIndex.writeInt(ID_Registro);//Grava a ID do registro
		rafIndex.writeLong(pointerRegistry);//Grava a posição do registro
		rafIndex.writeBoolean(lapide);//escreve o boolean lapide
	}
	
	
}
