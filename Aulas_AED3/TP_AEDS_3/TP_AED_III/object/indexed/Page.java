package object.indexed;

import java.io.EOFException;
import java.io.IOException;
import java.io.RandomAccessFile;

import estagio1.leitura.LeitorArquivo;
import object.indexed.Index;
import test_b.BTree;

public class Page {
	//int degree;
	int numChild;
	//boolean leaf;
	//long parentPage;
	Registro[] children;
	long[] pointers;
	public class Registro {
		int key;
		boolean validation;
		long address;
		//long leftNode;
		//long rightNode;
		public Registro() {
			this.key=0;
			this.validation=false;
			this.address=-1;
			//this.leftNode=-1;
			//this.rightNode=-1;
			
		}
		public void setKey(int key) {
			this.key = key;
		}
		public void setValidation(boolean validation) {
			this.validation = validation;
		}
		public void setAddress(long address) {
			this.address = address;
		}
		/*
		public void setLeftNode(long leftNode) {
			this.leftNode = leftNode;
		}
		public void setRightNode(long rightNode) {
			this.rightNode = rightNode;
		}
		public int getKey() {
			return key;
		}
		*/
		public boolean isValidation() {
			return validation;
		}
		public long getAddress() {
			return address;
		}
		/*
		public long getLeftNode() {
			return leftNode;
		}
		public long getRightNode() {
			return rightNode;
		}
		*/
	}
	public Page(int degree){
		//this.degree=degree;
		this.numChild=0;
		//this.leaf=true;
		//this.parentPage=-1;
		this.children=new Registro[degree];
		this.pointers=new long[degree+1];
	}
	
	public Page(/*int degree, */int numChild/*, boolean leaf, long parentPage*/, Registro[] children,long[] pointers) {
		super();
		//this.degree = degree;
		this.numChild = numChild;
		//this.leaf = leaf;
		//this.parentPage = parentPage;
		this.children = children;
		this.pointers=pointers;
	}
	
	public static void main(String[] args) {
		Page p=new Page(256);
		//storeIndexOnTree("index/indexTrafficAccidents.db");
		
		
	}
	public static void storeIndexOnTree(String Path_db) {
  		
		RandomAccessFile randomAccessFile= null;

        try {
        	//Acessar Arquivo de Indices
        	randomAccessFile = new RandomAccessFile(Path_db,"r");
            //Ponteiro do Cabeçalho
        	System.out.println("\nCabeçalho do arquivo = " +LeitorArquivo.getLastID(randomAccessFile));
        	//Inicio do Loop
            while (true) {
                try {
            		
                	//Ler valores e atribuir as variaveis
                	//Ler valores e atribuir as variaveis
                	long pointerIndex=randomAccessFile.getFilePointer();//escreve o tamanho do vetor
                    
            		int Key=randomAccessFile.readInt();//
            		
            		long pointerKey=randomAccessFile.readLong();
            		
            		boolean lapide=randomAccessFile.readBoolean();
                    
            		System.out.println("Posição no indice:------> "+pointerIndex);
            		
                    System.out.println("ID do registro:---------> "+Key);
                    
                    System.out.println("Posição no arquivo:-----> "+pointerKey);
                    
                    System.out.println("Validade:---------------> "+lapide);
                    
                    //Gravar no objeto

                	
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
