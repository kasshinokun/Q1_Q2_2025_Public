package data.huffman;
/*
 * Classe de um nó da árvore 
 */
public class Node extends Tree {
    public final Tree left, right; // sub-árvores
 
    public Node(Tree l, Tree r) {
        super(l.frequency + r.frequency);
        left = l;
        right = r;
    }
}