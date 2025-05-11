package estagio1.leitura;

/*Correção do erro de Ponteiro  24-03-2025*/

import java.io.*;

import estagio1.EscritorUpdateArquivo;
import object.DataObject;

public class ReadProcess {
	
	public static void readAll(String pathDb,int choice,int idSeek) {
		
		RandomAccessFile randomAccessFile= null;
		
		DataObject obj;
		
        try {

        	randomAccessFile = new RandomAccessFile(pathDb,"rw");
            
        	System.out.println("Cabeçalho do arquivo sequencial= " +LeitorArquivo.getLastID(randomAccessFile));
        	
        	long position=randomAccessFile.getFilePointer();//Posição inicial para ler os atributos externos ao registro

            while (true) {
                try {
                	
    	        	obj=new DataObject();
    	        	
    	        	int ID=randomAccessFile.readInt();//
    	              
    	            boolean lapide=randomAccessFile.readBoolean();
    	            
    	            if(lapide!=false){
	    	           
						long posicao=randomAccessFile.getFilePointer();//Posição para ler o tamanho
						
						obj.fromByteArray(LeitorArquivo.buildArray(randomAccessFile,posicao));//recebe o retorno a partir da função
						if(choice==1) {
							System.out.println("Validade: ----------------------------> "+lapide); 
							System.out.println("\n"+obj.toStringObject()+"\n");
						}else {
							if(ID==idSeek) {
								//Read One
								System.out.println("\nA ID "+idSeek+" foi encontrada no índice.");
								System.out.println("\nLendo registro no arquivo");
								System.out.println("\nValidade: ----------------------------> "+lapide); 
								System.out.println("\n"+obj.toStringObject()+"\n");
								if(choice==3) {
									//Update
									byte[] array=EscritorUpdateArquivo.newObject(obj).toByteArray();
									randomAccessFile.seek(posicao);//Posição para ler o tamanho
									int tamanho=randomAccessFile.readInt();
									if(array.length>tamanho) {
										EscritorUpdateArquivo.updateOnDeleteRegistry(position, array,ID,pathDb);
									}else {
										EscritorUpdateArquivo.updateRegistry(position, array, pathDb);
									}
								}
								else if(choice==4){
									//Delete
									DeleteProcess.deleteFile(randomAccessFile,position);
									
								}break;
								
							}if (ID>idSeek) {
								System.out.println("\n\nA ID "+idSeek+" foi apagada do índice.");
								break;
							}
							
						}
	    				
    	            }else {
    	            	
    	            	randomAccessFile.skipBytes(randomAccessFile.readInt());
    	            	
    	            }
    	            position=randomAccessFile.getFilePointer();
    	            
    	            
    				
                } catch (EOFException eofe) {
                    System.out.println("Fim do arquivo atingido.");
                    break;
                } catch (IOException ioe) {
                    ioe.printStackTrace();
                }
            }
        } catch (IOException ioe) {
            ioe.printStackTrace();
        } finally {
            try {
            	randomAccessFile.close();
            } catch (IOException ioe) {
                ioe.printStackTrace();
            }
        }
    }
	
}
