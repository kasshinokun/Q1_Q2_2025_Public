package TP_AED_3_2023.data.huffman;

public class Decoder {
    public static void decoder(String data, Tree tree){
        // Decodificar o texto
        System.out.println("\n\nTEXTO DECODIFICADO");
          
        System.out.println(decode(tree,data));
        
    
    
    }
    private static String decode(Tree tree, String encode) {
    	assert tree != null;
    	
    	String decodeText="";
    	Node node = (Node)tree;
    	for (char code : encode.toCharArray()){
    		if (code == '0'){ // Quando for igual a 0  o Lado Esquerdo
    		    if (node.left instanceof Leaf) { 
    		    	decodeText += ((Leaf)node.left).value; // Retorna o valor do no folha, pelo lado Esquerdo  
	                node = (Node)tree; // Retorna para a Raiz da arvore
	    		}else{
	    			node = (Node) node.left; // Continua percorrendo a arvore pelo lado Esquerdo 
	    		}
    		}else if (code == '1'){ // Quando for igual a 1  o Lado Direito
    		    if (node.right instanceof Leaf) {
    		    	decodeText += ((Leaf)node.right).value; //Retorna o valor do no folha, pelo lado Direito
	                node = (Node)tree; // Retorna para a Raiz da arvore
	    		}else{
	    			node = (Node) node.right; // Continua percorrendo a arvore pelo lado Direito
	    		}
    		}
    	} // End for
    	return decodeText; // Retorna o texto Decodificado
    }

    
}
