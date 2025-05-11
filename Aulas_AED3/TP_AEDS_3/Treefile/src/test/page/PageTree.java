package test.page;

import java.io.EOFException;
import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.util.*;

import test.estagio1.LeitorArquivo;


public class PageTree {
	int degree;
	int numPage;
	int numChild;
	boolean leaf;
	long parentPage;
	Registro[] children;
	long[] pointers;
	
	public PageTree(int degree){
		this.degree=degree;
		this.numPage=0;
		this.numChild=0;
		this.parentPage=-1;
		this.leaf=true;
		this.children=new Registro[degree-1];
		this.pointers=new long[degree];
		Arrays.fill(this.pointers,-1);
	}
	
	public PageTree(int degree, int numPage,long parentPage, int numChild, boolean leaf, Registro[] children,long[] pointers) {
		super();
		this.degree = degree;
		this.numPage=numPage;
		this.numChild = numChild;
		this.leaf = leaf;
		this.parentPage=parentPage;
		//if(numPage==0)
			//this.parentPage = -1;
		//else
			//this.parentPage = numPage%2==0?(numPage-2)/2:(numPage-1)/2;
		    //Header Index Tree= 12b
		    //PageTree Size= 676b (
		    //Header Pager = 17b 
		    //31 registros ==> cada = 29b
		    //)
			//numPage%2==0?12+(676*((numPage-2)/2)):8+(676*((numPage-1)/2));
			//this.parentPage = numPage%2==0?(numPage-2)/2:(numPage-1)/2;
		this.children = children;
		this.pointers=pointers;
	}
	
	public void setChildren(Registro[] children) {
		this.children = children;
	}
	
	public void setPointers(long[] pointers) {
		this.pointers = pointers;
	}
	
	public Registro[] getChildren() {
		return this.children;
	}

	String pagePrint() {
		String print=("\nGrau = "
			  +this.degree).concat("\nNumero Página = "
	          +this.numPage).concat("\nFilhos = "
		      +this.numChild).concat("\nFolha = "
	          +this.leaf).concat("\nPai = "
		      +this.parentPage).concat("\nPonteiro 0 = "
	          +this.pointers[0]);
		
		for(int i=1;i<this.degree;i++) {
	
			print=print.concat("\n"+this.getChildren()[i-1].printRegistry()).concat("\nPosição Ponteiro "+i+"------> "+this.pointers[i]);
		}
		return print;
	}
}
/*
 PageTree p=new PageTree(256);
                	for(int i=1;;) {
 */




/*
System.out.println(p.degree);
p.setChildren(children);
//page.setPointers(pointers);   

System.out.println("\nposicao fim do arquivo = " +getEndTree("index/indexTree.db",p));

System.out.println(p.pagePrint());

if(i==ID_Header) {
	break;
}
 */







/*
public static void readTree(String pathTree) throws IOException{
		RandomAccessFile writerTree = new RandomAccessFile(pathTree,"rw");
		System.out.println("\nGrau = "+writerTree.readInt());
		System.out.println("\nFilhos = "+writerTree.readInt());
		System.out.println("\nFolha = "+writerTree.readBoolean());
		System.out.println("\nPai = "+writerTree.readLong());
		System.out.println("\nPonteiro 0 = "+writerTree.readLong());
		
		for(int i=1;i<256;i++) {
	
			System.out.println("\nID do registro:---------> "+writerTree.readInt());
			System.out.println("Validade:---------------> "+writerTree.readBoolean());
			System.out.println("Posição do indice:------> "+writerTree.readLong());
			System.out.println("Posição Ponteiro "+i+"------> "+writerTree.readLong());
		}
		System.out.println("Posição Ponteiro Final--> "+writerTree.getFilePointer());
	}
}
/*
 long position=writerTree.getFilePointer();
		if(check!=1) {
			int numChild=writerTree.readInt();
			writerTree.writeBoolean(false);
			long parent=writerTree.readLong();
			long leftPointer=writerTree.readLong();
			
			for(int i=0;i<numChild;i++) {
				int key=writerTree.readInt();
				
				if(x.children[x.children.length-1].getKey()<key&&leftPointer==-1) {
					writerTree.seek(position+5);
					writerTree.writeLong(writerTree.length());
					x.parentPage=position;
					writerTree.seek(writerTree.length());
					break;
				}
				if(x.children[x.children.length-1].getKey()>key&&leftPointer==-1) {
					long rightpos=position+13;
					writerTree.seek(rightpos);
					long rightPointer=writerTree.readLong();
					key=writerTree.readInt();
					if(x.children[x.children.length-1].getKey()<key&&rightPointer==-1) {
						writerTree.seek(rightpos);
						writerTree.writeBoolean(false);
						writerTree.seek(position+5);
						writerTree.writeLong(writerTree.length());
						x.parentPage=position;
						writerTree.seek(writerTree.length());
						break;
					}
				}
			}
		}
		
		try {
			readTree("index/indexTree.db");
		} catch (EOFException eofe) {
            System.out.println("Fim do arquivo atingido B.");
        } catch (IOException ioe) {
            ioe.printStackTrace();
        }
		
		
		
		//long[] pointers= new long[8+1];
                	for(int i=0;i<=ID_Header;) {
            		
	                	for(int j=0;j<(page.degree-1);j++,i++) {
		                	//Ler valores e atribuir as variaveis
		                	long pointerKey=randomAccessFile.getFilePointer();//escreve o tamanho do vetor
		                    
		            		int Key=randomAccessFile.readInt();//
		            		
		            		randomAccessFile.readLong();
		            		
		            		boolean lapide=randomAccessFile.readBoolean();
		           
		                    //Gravar no objeto
		                    Registro x= new Registro(Key,lapide,pointerKey);
		                    
		                    //System.out.println(x.printRegistry()+"\n"+(i%8));
		                     
		                    childreen[j]=x;
		                    if(i==ID_Header) {
		                    	break;
		                    }
	                	}
	                	
	                	System.out.println(page.degree);
	                	page.setChildren(childreen);
	                	//page.setPointers(pointers);   
	                	System.out.println(page.pagePrint());
	                	System.out.println("\nposicao fim do arquivo = " +getEndTree("index/indexTree.db",page));
                	
 */
