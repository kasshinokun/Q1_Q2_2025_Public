package TP_AED_II_2023_1.AVL;//Nome do Subprojeto

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

import java.io.*;//Simplificação de bibliotecas necessarias para arquivos
import java.util.*;//Simplificação de bibliotecas necessarias 
import TP_AED_II_2023_1.AVL.*;//Package das classes

public class No {//Declaração da Classe Nó
    
    private Palavra p;//Palavra
    //Ponteiros
    private No esq,dir;
    //Altura
    private int altura;
    
    public No(){//Construtor default
        this.p=new Palavra();
        this.altura = 1;
        this.esq=null;
        this.dir=null;    
    }
    //Sobrecarga
    //Adaptação para Classe
    public No(String s){//Instancia o No
        this.setPalavra(s);
        this.altura = 1;
        this.esq=null;
        this.dir=null;    
    }
    public No(No no){//Copia o No
        this.setPalavra(no.getPalavra());
        this.altura = no.altura;
        this.esq=no.esq.getNo();
        this.dir=no.dir.getNo(); 
    }

    //Get e Set adaptados para manter Objeto privado
    //Retorna o no por completo
    public No getNo(){
        return this;
    }
    //Ponteiros
    //setters do ponteiros
    public void setDir(No dir){
        this.dir=dir;
    }
    public void setEsq(No esq){
        this.esq=esq;
    }
    //getters do ponteiros
    public No getDir(){
        return this.dir;
    }
    public No getEsq(){
        return this.esq;
    }
    //Altura
    public void setAltura() {
        this.altura = 1 + Math.max(getAltura(esq), getAltura(dir));
    }
    public static int getAltura(No no) {
        return (no == null) ? 0 : no.altura;
    }
    //Palavra
    //Setter
    public void setPalavra(String s){
        this.p=new Palavra(s);
    }
    //Getters
    public String getPalavra(){
        return this.p.getPalavra();
    }
    public Palavra sendPalavra(){//Adaptação para envia a lista encadeada
        Palavra x=new Palavra();
        x.setPalavra(this.p.getPalavra(),this.p.getContador());
        return x;//Retorna a palvra completa
    }
    //Contador
    public void setContador(){ 
        this.p.setContador();
    }
    public int getContador(){ 
        return this.p.getContador();
    }
    //Exibe o objeto
    public String mostrarPalavra(){
        return this.p.mostrarPalavra();
    }
}
