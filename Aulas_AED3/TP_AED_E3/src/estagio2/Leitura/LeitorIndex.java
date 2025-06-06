package estagio2.Leitura;
import java.io.EOFException;
import java.io.IOException;
import java.io.RandomAccessFile;

import estagio1.DataObject;
import estagio1.EscritorUpdateArquivo;
import estagio1.leitura.*;
import estagio2.DataIndex;
import estagio2.Escrita.EscritorUpdateIndex;
public class LeitorIndex {

	public static void main(String[] args) {
	
		Start();
		
	}
	public static void Start(){	
		int op=0;
			
		//String pathFile="traffic_accidents_rev2.csv";
		String pathFile="data/traffic_accidents_pt_br_rev2.csv";
		
		
		String pathDb="index/traffic_accidents.db";
		
		String pathIndex="index/indexTrafficAccidents.db";
		int Id=0;
		
  		do {
  			System.out.println("\n==================================================");
  			System.out.println("\nProcessos de leitura\n");
  			System.out.println("1) Ler todos os registros");
  			System.out.println("2) Ler apenas um registro");
  			System.out.println("3) Atualizar um registro");
  			System.out.println("4) Apagar registro");
			System.out.println("\n0) Sair\n\nEscolha um valor-------> :");
			op=Functions.only_Int();
			switch(op) {
				case 1:
					readAllIndex(pathDb,pathIndex,op,0);//Todos
					break;
				case 2:
					System.out.println("Digite a ID desejada :");
					Id=Functions.only_Int();
					readAllIndex(pathDb,pathIndex,op,Id);//Um
				    break;
				case 3:	
					System.out.println("Digite a ID desejada :");
					Id=Functions.only_Int();
					readAllIndex(pathDb,pathIndex,op,Id);//Um
					break;
				case 4:
					System.out.println("Digite a ID desejada :");
					Id=Functions.only_Int();
					readAllIndex(pathDb,pathIndex,op,Id);//Um
					break;
				
				default:
					if(op==0) {
						System.out.println("\nVoltando ao Menu da Parte II.");
					}else {
						System.out.println("\nTente novamente, escolha fora do escopo.");
					}
			}
		}while(op!=0);
			
	}

	//===============================================================================Funções Internas
	public static void readAllIndex(String pathDb,String pathIndex,int choice,int idSeek) {
  		
		RandomAccessFile rafReaderIndexedData= null;
		
		RandomAccessFile raf=null;
		
		DataIndex objIndex;
		
        try {

        	rafReaderIndexedData = new RandomAccessFile(pathIndex,"rw");
        	raf = new RandomAccessFile(pathDb,"rw");
        	int indexHeader=LeitorArquivo.getLastID(rafReaderIndexedData);
        	
        	System.out.println("Cabeçalho do arquivo de índice= " +indexHeader);
        	
        	if(idSeek<=indexHeader&idSeek>0||(idSeek==0&choice==1)) {
        		
        		long pointerIndex=rafReaderIndexedData.getFilePointer();

	            while (true) {
	                try {
	            		
	            		int ID=rafReaderIndexedData.readInt();//                                      
	                    
	                    long pointerKey=rafReaderIndexedData.readLong();//ler o posição do vetor
	                    
	                    boolean lapide=rafReaderIndexedData.readBoolean();                                    
	                    
	                    if(lapide!=false){
	                    	objIndex=new DataIndex();//Instancia objeto
							
	                    	objIndex.fromByteArray(getObject(pathDb,pointerKey));
	                    	if(choice==1) {
								//Leitura de todos os indices
								System.out.println(showIndex(ID, lapide,  pointerKey));
								
								//Leitura de um registro								
								System.out.println("\nLendo registro no arquivo");
								
								System.out.println(objIndex.toStringObject());
							}else {
								
								if (ID==idSeek) {
									System.out.println("\nA ID "+idSeek+" foi encontrada no índice.");
									//Leitura de um indice
									System.out.println(showIndex(ID, lapide, pointerKey));
			                    	
									//Leitura de um registro								
									System.out.println("\nLendo registro no arquivo");
									//ReadOne
									System.out.println(objIndex.toStringObject());
									if(choice==3) {
										//Update
										byte[] array=EscritorUpdateIndex.newObject(ID,objIndex,pathIndex,pathDb).toByteArray();
										raf.seek(pointerKey);//Posição para ler o tamanho
										int tamanho=raf.readInt();
										if(array.length>tamanho) {
											EscritorUpdateIndex.updateOnDeleteRegistry(pointerKey,pointerIndex, array,ID,pathDb,pathIndex);
										}else {
											EscritorUpdateIndex.updateRegistry(ID,pointerKey, array, pathDb);
										}
									}
									if(choice==4) {
										//Delete
										deleteIndex(rafReaderIndexedData,pointerIndex);
										deleteRegistry(ID, pathDb, pointerKey);
									}
			                    	break;
								}
								if (ID>idSeek) {
									System.out.println("\n\nA ID "+idSeek+" foi apagada do índice.");
									break;
								}
							}
		    				
	    	            }
	                    
	                    pointerIndex=rafReaderIndexedData.getFilePointer();
	                
	                } catch (EOFException eofe) {
	                    System.out.println("\nFim do arquivo atingido.");
	                    break;
	                } catch (IOException ioe) {
	                    ioe.printStackTrace();
	                }
	            }
        	}else {
        		System.out.println("\nA ID "+idSeek+" fora do escopo do indice.");
        	}
        } catch (IOException ioe) {
            ioe.printStackTrace();
        } finally {
            try {
            	rafReaderIndexedData.close();//Indice
            	if(raf!=null) {
            		raf.close();//Arquivo 
            	}       
            } catch (IOException ioe) {
                ioe.printStackTrace();
            }
        }
    }
	public static String showIndex(int ID,boolean lapide, long posicao){
		
			return "\nID lida: -----------------------------> "+ID
					+"\nValidade------------------------------> "+lapide
					+"\nPosição do registro-------------------> "+posicao;
	}
	public static byte[] getObject(String pathDb, long pointerObject) throws IOException{
		
		DataIndex obj=new DataIndex();
		
		RandomAccessFile rafIndexedData=new RandomAccessFile(pathDb,"rw");
		
		byte[] bytearray=LeitorArquivo.buildArray(rafIndexedData,pointerObject+1);
		
		rafIndexedData.close();//Fecha o RandomAccessFile    
        
		return bytearray;
	}
	public static void deleteIndex(RandomAccessFile rafIndex,long pointerIndex)throws IOException{
  		
		rafIndex.seek(pointerIndex); //busca a posição designada no arquivo de indice
	
		int Key=rafIndex.readInt();//Lê a chave
        
        long pointerKey=rafIndex.readLong();//Lê a posição do registro
        
        rafIndex.writeBoolean(false);//escreve o boolean lapide
        
        System.out.println("A ID "+Key+" foi apagada do indice.");
        
        //rafIndex.close();//Fecha o RandomAccessFile    
        
        //return pointerKey;//Envia a posição para ser apagada no arquivo de dados
        
  	}
	public static void deleteRegistry(int Key, String pathDb, long pointerKey)throws IOException{
  		
		RandomAccessFile rafIndexedData=new RandomAccessFile(pathDb,"rw");
		
		rafIndexedData.seek(pointerKey);
       
		rafIndexedData.writeBoolean(false);
        
		pointerKey=rafIndexedData.getFilePointer();
        
        DataIndex obj=new DataIndex();
        
        obj.fromByteArray(LeitorArquivo.buildArray(rafIndexedData,pointerKey));
        
        System.out.println("\n"+obj.toStringObject()+"\n");
        
        System.out.println("A ID "+Key+" foi apagada do registro.");
  	}
	/*
	public static void updateIndex(long pointerKey, //Ponteiro da localização do Registro
			long pointerIndex,//Ponteiro da localização do Indice do Registro
			boolean lapide, //Boolean para etapas futuras se necessário(placebo por hora)
			String pathIndex
			)throws IOException{//Trativa de erro para quem o chamou
		
		RandomAccessFile randomAccessFile=new RandomAccessFile(pathIndex,"rw");//instancia o RandomAccessFile para ler e escrever 
		
		randomAccessFile.seek(pointerIndex); //busca a posição designada no arquivo de indice
		
		randomAccessFile.readInt();//Le a chave
		
		randomAccessFile.writeLong(pointerKey);//Grava a posição do registro
		
		randomAccessFile.writeBoolean(lapide);//escreve o boolean lapide
		
		randomAccessFile.close();//Fecha o RandomAccessFile   
	}
		*/
}
