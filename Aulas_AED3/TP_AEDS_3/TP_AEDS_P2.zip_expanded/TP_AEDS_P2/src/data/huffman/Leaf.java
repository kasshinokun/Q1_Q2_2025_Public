package data.huffman;



/*
 * Classe do nó folha da árvore 
 */
public class Leaf extends Tree {
    public final char value; // A letra x atribuida a um nó folha 
 
    public Leaf(int freq, char val) {
        super(freq);
        value = val;
    }
}