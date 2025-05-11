package TP_AED_3_2023.data.huffman;

import java.io.*;
import java.nio.file.*;
import java.util.*;

public class Encoder implements Serializable{
    private static final long serialVersionUID = 1L;
    public static void callHuffman(){
        System.out.println("Iniciando Processos........");
        String path="src/data/tour.csv";
        String data="";
        System.out.println("Lendo arquivo........");  
        try{
            RandomAccessFile file = new RandomAccessFile(path, "r");
	    int i=1;
            while (true) {
                data=data.concat(file.readLine().concat("\n"));              
                
                System.out.println("Leitura "+(i*100.0F/111)+"%........");
                i+=1;
            }
            
            
	   
        }catch(EOFException | NullPointerException e){
            System.out.println("\nLeitura finalizada do arquivo.");
            String data2="";
            int[] charFreqs = new int[256];
            System.out.println("Computando frequencias........");   
            int w =data.length();
            
             
            for (char c : data.toCharArray()){
                charFreqs[c]++;
            }

            System.out.println("Iniciando criação de arvore........");  
            // Criar a arvore dos codigos para a Compactação
            Tree tree = Encoder.buildTree(charFreqs);

            // Resultados das quantidade e o codigo da Compactação
            System.out.println("TABELA DE CÓDIGOS");
            System.out.println("SÍMBOLO\tQUANTIDADE\tHUFFMAN CÓDIGO");
            Encoder.mostrarHuffman(tree, new StringBuffer(),1);
            
            // Compactar o texto
            data2 = Encoder.encode(tree,data);
            int x =data2.length();
            int y=x%8;
            int z=x/8;
            System.out.println("\nTamanho Original: "+w);
            System.out.println("Tamanho Final: "+x+
                                "\no que sobra do modulo por---> 7:"+x%7+"       15:"+x%15+"       31:"+x%31+"       63:"+x%63+"      127:"+x%127+                                       
                                "\ncaracteres gerados por Split> 7:"+x/7+"    15:"+x/15+"    31:"+x/31+"     63:"+x/63+"     127:"+x/127+
                                "\no que sobra do modulo por---> 8:"+x%8+"       16:"+x%16+"       32:"+x%32+"       64:"+x%64+"      128:"+x%128+                                       
                                "\ncaracteres gerados por Split> 8:"+x/8+"    16:"+x/16+"    32:"+x/32+"     64:"+x/64+"     128:"+x/128+"\n");
            
            String []Split128=data2.split("(?<=\\G.{" + 127 + "})");
            //binario_String(Split128);



            //Descompactar o texto
            //Decoder.decoder(data2, tree);
            
            
            
            
        }catch (NoSuchFileException f) {
            System.out.println("\nArquivo/Pasta nao encontrado(a).");
        }catch(IOException e){
            System.out.println("\nErro na leitura do arquivo.");
        }
        
        
    
    }
    public static void binario_String(String[] data){
        //conversao para escrever em arquivo
        
        for(String x:data){
            System.out.println("\nOriginal     : "+x);
            System.out.println("\nEm caracteres: "+x);
            System.out.println("\nOriginal     : "+x);
        }
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    }
    private static void writeTree(int frequency, int charc){
        String HPath="src/data/indexed/Huffman_Tree.db";
        RandomAccessFile HTree=null;
        
    
    }
    private static void readTree(int frequency, int charc){}
    private static void mostrarHuffman(Tree tree, StringBuffer prefix,int condition) {
        assert tree != null;
        
        if (tree instanceof Leaf) {
            if(condition==1){
                Leaf leaf = (Leaf)tree;

                // Imprime na tela a Lista
                System.out.println(leaf.value + "\t" + leaf.frequency + "\t\t" + prefix);
            }else{
                Leaf leaf = (Leaf)tree;
                int c=(int)leaf.value;
                int frequency=leaf.frequency;
                //A inserção na arvore é (frequencia,char)
                System.out.println(frequency+ "\t" +c  );
                
            }
        } else if (tree instanceof Node) {
            Node node = (Node)tree;
 
            // traverse left
            prefix.append('0');
            mostrarHuffman(node.left, prefix,condition);
            prefix.deleteCharAt(prefix.length()-1);
 
            // traverse right
            prefix.append('1');
            mostrarHuffman(node.right, prefix,condition);
            prefix.deleteCharAt(prefix.length()-1);
        }
    }
    
    private static Tree buildTree(int[] charFreqs) {
    	// Cria uma Fila de Prioridade 
    	// A Fila será criado pela ordem de frequencia da letra no texto
        PriorityQueue<Tree> trees = new PriorityQueue<Tree>();
        // Criar as Folhas da arvore para cada letra 
        for (int i = 0; i < charFreqs.length; i++){
            if (charFreqs[i] > 0)
                trees.offer(new Leaf(charFreqs[i], (char)i)); // Insere os elementos, na folha, na fila de prioridade
        }
        // Percorre todos os elementos da fila
        // Criando a arvore binaria de baixo para cima
        while (trees.size() > 1) {
            // Pega os dois nos com menor frequencia
            Tree a = trees.poll(); // poll - Retorna o proximo no da Fila ou NULL se nao tem mais
            Tree b = trees.poll(); // poll - Retorna o proximo no da Fila ou NULL se nao tem mais
 
            // Criar os nos da arvore binaria
            trees.offer(new Node(a, b)); 
        }
        // Retorna o primeiro no da arvore
        return trees.poll();
    }
    private static String encode(Tree tree, String encode){
    	assert tree != null;
    	
    	String encodeText = "";
        for (char c : encode.toCharArray()){
        	encodeText+=(getCodes(tree, new StringBuffer(),c));
        }
    	return encodeText; // Retorna o texto Compactado
    }
    private static String getCodes(Tree tree, StringBuffer prefix, char w) {
        assert tree != null;
        
        if (tree instanceof Leaf) {
            Leaf leaf = (Leaf)tree;
            
            // Retorna o texto compactado da letra
            if (leaf.value == w ){
            	return prefix.toString();
            }
            
        } else if (tree instanceof Node) {
            Node node = (Node)tree;
 
            // Percorre a esquerda
            prefix.append('0');
            String left = getCodes(node.left, prefix, w);
            prefix.deleteCharAt(prefix.length()-1);
 
            // Percorre a direita
            prefix.append('1');
            String right = getCodes(node.right, prefix,w);
            prefix.deleteCharAt(prefix.length()-1);
            
            if (left==null) return right; else return left;
        }
		return null;
    }
    
    
    
}
