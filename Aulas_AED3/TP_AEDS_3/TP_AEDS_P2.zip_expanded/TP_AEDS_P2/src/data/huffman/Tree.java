package data.huffman;

import java.io.*;
import java.util.*;
import java.nio.*;

public abstract class Tree implements Comparable<Tree> {
    public final int frequency; // Frequência da árvore
    //
    public Tree(int freq) { 
    	frequency = freq; 
    }
    
    // Compara as frequências - Implementação da Interface Comparable para a ordenação na fila
    public int compareTo(Tree tree) {
        return frequency - tree.frequency;
    }
}