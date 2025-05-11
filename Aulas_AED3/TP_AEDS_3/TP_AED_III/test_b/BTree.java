package test_b;

import java.io.EOFException;
import java.io.IOException;
import java.io.RandomAccessFile;

import estagio1.leitura.LeitorArquivo;
import object.indexed.Index;

public class BTree {
    BTreeNode root;
    int t;

    public BTree(int t) {
        this.root = null;
        this.t = t;
    }

    public void traverse() {
        if (root != null) {
            root.traverse();
        }
    }

    public BTreeNode search(Index k) {
        return (root == null) ? null : root.search(k);
    }

    public void insert(Index k) {
        if (root == null) {
            root = new BTreeNode(t, true);
            root.keys[0] = k;
            root.n = 1;
        } else {
            if (root.n == 2 * t - 1) {
                BTreeNode s = new BTreeNode(t, false);
                s.children[0] = root;
                s.splitChild(0, root);
                int i = 0;
                if (s.keys[0].getKey() < k.getKey()) {
                    i++;
                }
                s.children[i].insertNonFull(k);
                root = s;
            } else {
                root.insertNonFull(k);
            }
        }
    }
    public static void storeIndexOnTree(String Path_db) {
  		
    	BTree bTree = new BTree(16);
    	
		RandomAccessFile randomAccessFile= null;

		Index k=new Index();
        try {
        	//Acessar Arquivo de Indices
        	randomAccessFile = new RandomAccessFile(Path_db,"r");
            //Ponteiro do Cabeçalho
        	System.out.println("\nCabeçalho do arquivo = " +LeitorArquivo.getLastID(randomAccessFile));
        	//Inicio do Loop
            while (true) {
                try {
            		
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
                	Index Registro = new Index(Key,pointerKey,lapide);
                	
                	//teste
                	if (Key==6) {
                		k=Registro;
                	}
                	
                	//Salvar na Arvore
                	bTree.insert(Registro);
                	
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
        System.out.println("A travessia da árvore B construída é:");
        bTree.traverse();
        
        System.out.println();
        
        System.out.println(bTree.search(k) != null ? k.toStringIndex() : "Não está presente na árvore");

        k = new Index(15,k.getPointer(),k.isLapide());
        
        System.out.println(bTree.search(k) != null ? k.toStringIndex() : "Não está presente na árvore");
        
        System.out.println(bTree.root.n);
    }
    public static void main(String[] args) {
    	storeIndexOnTree("index/indexTrafficAccidents.db");
    }
    
    
}
