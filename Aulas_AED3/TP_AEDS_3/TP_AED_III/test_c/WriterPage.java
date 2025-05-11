package test_c;

import java.io.EOFException;
import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.util.Arrays;

import estagio1.leitura.LeitorArquivo;

public class WriterPage {

	public static void main(String[] args) {
		
		//PageTree p=new PageTree(256);
		
		String sep = File.separator;// Separador do sistema operacional em uso
		
		String sArquivo="index".concat(sep+"indexTrafficAccidents.db");
		
		String sArquivoTree="index".concat(sep+"indexTree.db");
		
		//storeIndexOnLeaf(sArquivo,sArquivoTree);
		
		readAllSequential(sArquivoTree);
		
	}public static void readAllSequential(String sArquivoTree) {	
		try {
			readTree(sArquivoTree);
        } catch (IOException ioe) {
            ioe.printStackTrace();
        }
        
	}
	public static void storeIndexOnLeaf(String pathFile,String pathDb) {
		
		RandomAccessFile randomAccessFile= null;

        try {
        	//Acessar Arquivo de Indices
        	randomAccessFile = new RandomAccessFile(pathFile,"r");
            //Ponteiro do Cabeçalho
        	int ID_Header=LeitorArquivo.getLastID(randomAccessFile);
        	System.out.println("\nCabeçalho do arquivo = " +ID_Header);
        	//Inicio do Loop
        	int i=1;
        	int numPage=getHeaderTree(pathDb);
        	
        	//while (true&&i<=127) {
        	while (true&&i<=ID_Header) {
        		
                try {
                	int sizePage=676;
                	Registro[] children=new Registro[31];
                	int order=children.length+1;
					long pointers[]=new long[order];
					Arrays.fill(pointers,-1);//nulos por enquanto
					
					int nextPage=2*numPage+1;
					
					pointers[0]=12+(sizePage*(nextPage));//32n
										
					//pointers[0]=8+(676*(2*numPage+1));//32n
					
					//pointers[0]=order*(nextPage);//32n
					
					//pointers[0]=(children.length+1)*(2*numPage+1);//32n
                	
					for(int j=0;j<children.length;j++,i++) { 
						//long pointerKey=randomAccessFile.getFilePointer();//coleta o ponteiro
						
						int Key=randomAccessFile.readInt();//
						    		
						long posKey=randomAccessFile.readLong();
						    		
						byte lapide=randomAccessFile.readByte();
						   
						//Gravar no objeto
						children[j]=new Registro(Key,lapide,posKey);
						
						//Ponteiros
						pointers[j+1]=pointers[0]+sizePage*(j+1);//n*32n
						
						//pointers[j+1]=(children.length+1)*(numPage+1)*(j+2);//n*32n
						
						//pointers[j+1]=12+(676*(numPage+1)*(j+2));//64n
						
						//pointers[1]=pointers[0]+order;//32n
						
						//pointers[1]=12+(676*(2*numPage+2));//64n
						
						//pointers[1]=12+(sizePage*(2*numPage+2));//64n
						
						if(j==children.length-1 ||i==ID_Header) {
							
							long parentPage;
							if(numPage==0)
								parentPage = -1;
								//long parentPage=numPage%order!=0?order:(order*numPage);
								//long parentPage=numPage==0?order:(order*numPage);
							else
								//long parentPage = numPage%2==0?(2*numPage-2)/2:(2*numPage-1)/2;
								parentPage =  numPage%2==0?12+(sizePage*((numPage-2)/2)):12+(sizePage*((numPage-1)/2));
								//parentPage = numPage%2==0?(numPage-2)/2:(numPage-1)/2;
							PageTree pageTree=new PageTree(order,numPage,parentPage,j+1,true,children,pointers);
							                 //int degree,   
							                       //int numPage,
							                               //long parentPage,
							                                          //int numChild, 
							                                               //boolean leaf, 
							                                                   //Registro[] children,
							                                                             //long[] pointers
							//Feedback
		                	System.out.println("\nposicao fim do arquivo = " +getEndTree(pathDb,pageTree,Key));
		                	
		                	//Feedback
							System.out.println(pageTree.degree+" "+pageTree.numChild+" "+children.length);
							/*
							//Feedback
							for(Registro x:children) {
								System.out.println(x!=null?x.printRegistry():"Vazio");
							}*/
						}
						
					}
                	numPage++;
                	
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
	public static long getEndTree(String pathTree,PageTree x,int lastID) throws IOException{
		RandomAccessFile writerTree = new RandomAccessFile(pathTree,"rw");
		int ordem=x.degree;
		//Header do Indice
		writerTree.writeInt(x.degree);//Grau da Arvore
		writerTree.writeInt(x.numPage+1);//Próxima Página
		writerTree.writeInt(lastID);//Ultima ID
		
		//Feedback
		System.out.println("\n----------------------------------> Header "+writerTree.getFilePointer());
		writerTree.seek(LeitorArquivo.find_end(writerTree));
		//Header da Página		
		writerTree.writeInt(x.numPage);
		writerTree.writeInt(x.numChild);
		writerTree.writeBoolean(x.leaf);
		writerTree.writeLong(x.parentPage);
		//Feedback
		System.out.println("\n----------------------------------> P0 "+writerTree.getFilePointer());		
		writerTree.writeLong(x.pointers[0]);
		
		//Filhos da Página
		for(int i=0;i<x.getChildren().length;i++) {
			if(x.children[i]!=null) {
				writerTree.writeInt(x.children[i].getKey());
				writerTree.writeByte(x.children[i].isValidation()==true?(byte)1:(byte)0);
				writerTree.writeLong(x.children[i].getAddress());
				writerTree.writeLong(x.pointers[i+1]);
				//Feedback
				System.out.println("\n---------------------------------"+i+">"+x.children[i].getKey());
				System.out.println("-----------------Address-Node-End"+i+">"+writerTree.getFilePointer());
			}else {
				writerTree.writeInt(0);
				writerTree.writeByte(0);
				writerTree.writeLong(0);
				writerTree.writeLong(-1);
				//Feedback
				System.out.println("\n---------------------------------"+i+">"+" Vazio");
			}
			
		}
		
		System.out.println("\n----------------------------------> Gravado");
		return writerTree.getFilePointer();
	}
	//Identificação do valor no cabeçalho para o escritor de arquivo
    public static int getHeaderTree(String path)throws IOException{
        
    	RandomAccessFile writerTree = new RandomAccessFile(path, "rw");//instancia o RandomAccessFile para ler e escrever 
		
		int nextPage;//Instancia a variavel para guardar a ultima id ao fazer um novo registro
		
		if (writerTree.length()!=0) {//Verifica se o arquivo está vazio(ou null)
			
			writerTree.readInt();//Grau da Arvore
			nextPage=writerTree.readInt();//Próxima Página
			
		
		}else {
		
			nextPage=0;//Caso esteja vasio(null), atribui 1 a variavel
		
		}
		writerTree.close();
		
        return nextPage;//retorna o valor encontrado no cabeçalho
    }
	public static void readTree(String pathTree) throws IOException{
		RandomAccessFile writerTree = new RandomAccessFile(pathTree,"r");
		//Header do Indice
		int ordem=writerTree.readInt();//Grau da Arvore
		int nextPage=writerTree.readInt();//Próxima Página
		int lastID=writerTree.readInt();//Ultima ID
		//Feedback
		System.out.println("\n----------------------------------> Header PageTree Index ------>"+writerTree.getFilePointer());
		System.out.println("Grau =======> "+ordem);
		System.out.println("Next PageTree ==> "+nextPage);
		System.out.println("Ultima ID ==> "+lastID);
		while (true) {
            try {
            	//Loop
            	int numberPage=writerTree.readInt();
        		int numChildren=writerTree.readInt();
        		boolean validateLeaf=writerTree.readBoolean();
        		long parent=writerTree.readLong();
        		long p0=writerTree.readLong();
            	//Feedback
            	System.out.println("\n----------------------------------> Header PageTree After ------>"+writerTree.getFilePointer());
            	System.out.println("Num PageTree ===> "+numberPage);
        		System.out.println("Filhos =====> "+numChildren);
        		System.out.println("Folha ======> "+validateLeaf);
        		System.out.println("Pai ========> "+parent);
        		System.out.println("Ponteiro 0 => "+p0);
        		//Feedback
        		System.out.println("----------------------------------> Children's PageTree <--------------");
				for(int i=1;i<ordem;i++) {
					int key=writerTree.readInt();
					byte lapide=writerTree.readByte();
					long address=writerTree.readLong();
					long pointer=writerTree.readLong();
					//Feedback
					System.out.println("----------------------------------> Child "+i+" After ---------->"+writerTree.getFilePointer());
					//System.out.println("Ponteiro "+i+" = "+pointer);
					
					System.out.println(showIndex(i,key,lapide,address,pointer));
					
				}
				//Feedback
				System.out.println("----------------------------------> Posição Final da Pagina-> "+writerTree.getFilePointer());
                //break;
            } catch (EOFException eofe) {
                System.out.println("Fim do arquivo atingido.");
                break;
            } catch (IOException ioe) {
                ioe.printStackTrace();
            }
	    }    
	}
	
	public static String showIndex(int i, int key,byte lapide, long address, long pointer){
		
		if(key!=0) {
			
			return ("\nID do registro:---------> "+key+
			"\nValidade:---------------> "+(boolean)(lapide==1?true:false)+
			"\nPosição do indice:------> "+address+
			"\nPosição Ponteiro "+i+"------> "+pointer);
			
		}else {
			
			return ("\nID do registro:---------> Vazia "+key+
					"\nValidade:---------------> Vazia "+lapide+
					"\nPosição do indice:------> Vazia "+address+
					"\nPosição Ponteiro "+i+"------> Nula "+pointer);
			
		}
	}
}



