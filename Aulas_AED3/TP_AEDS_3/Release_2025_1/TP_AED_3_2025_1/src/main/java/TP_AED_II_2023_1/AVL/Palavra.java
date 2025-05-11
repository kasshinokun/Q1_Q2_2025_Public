package TP_AED_II_2023_1.AVL;//Nome do Subprojeto

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

import java.util.*;//Simplificação de bibliotecas necessarias 
public class Palavra {//Declaração da Classe
    
    private String palavra;
    private int contador=0;
    
    public Palavra(){//Construtor default
        this.palavra="";
        this.setContador(0);
    }
    public Palavra(String s){//Sobrecarga
        this.setPalavra(s);//Instancia já atribuindo valores 
    }
    //Get e Set
    //String Palavra
    //Setters
    public void setPalavra(String s){//Somente a String
        this.palavra=s;
        this.setContador();
    }
    public void setPalavra(String s,int x){//String e inteiro(Adaptação para Swap em Lista)
        this.setPalavra(s);
        this.setContador(x);
    }
    public void setPalavra(Palavra p){//Objeto Completo 
        this.setPalavra(p.getPalavra(),p.getContador());
    } 
    //Getter
    public String getPalavra(){
        return this.palavra; 
    }
    //Contador
    //Setter
    public void setContador(){//disponivel para demais classe
        this.contador++;
    }
    private void setContador(int x){//especifico para a classe
        this.contador=x;
    }
    //Getter
    public int getContador(){ 
       return this.contador; 
    }
    //Exibe a classe em tela
    public String mostrarPalavra(){
       return "Palavra: "+this.getPalavra()+" qtd: "+this.getContador();
    }
    
}
