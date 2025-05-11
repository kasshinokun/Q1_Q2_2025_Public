package TP_AED_II_2023_1.List;//Nome do Subprojeto

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

import TP_AED_II_2023_1.AVL.*;
import java.util.*;//Simplificação de bibliotecas necessarias 

public class Celula{
    
    private Palavra p;//Palavra;//variavel para inserção de Generrics
     
    //Ponteiros
    public Celula prox;//variavel para Proximo
    public Celula ant;//variavel para Anterior
    public Celula(){//Construtor Default 
        
        this.p=new Palavra();
        //Ponteiros              
        this.prox=null;
        this.ant=null;
    }
    //Sobrecarga 
    public Celula(String s){//Cria um novo objeto
        this.p=new Palavra(s);
        //Ponteiros              
        this.prox=null;
        this.ant=null;
    }
    public Celula(Palavra p){//Copia o objeto
        this.p=new Palavra();
        this.p.setPalavra(p.getPalavra(), p.getContador());
        //Ponteiros
        this.prox=null;
        this.ant=null;
    }
    public Celula(Celula x){//Adaptação
        this.p=new Palavra();
        this.p.setPalavra(x.getPalavra(),x.getContador());//Copia o objeto
        this.prox=x.prox;
        this.ant=x.ant; 
    }
    //Getters e Setters com sobrecarga
    //Palavra
    public void setPalavra(String s){
        this.p=new Palavra();//Cria a Palavra 
    }
    public void setPalavra(Palavra p){
        this.p.setPalavra(p);//Copia a Palavra com os atributos
    }
    public void setPalavra(String s,int x){//Adaptação
        this.p.setPalavra(s, x);
    }
    public String getPalavra(){
        return this.p.getPalavra();//retorna a palavra
    }
    public String mostrarPalavra(){
        return this.p.mostrarPalavra();//exibe o objeto
    }
    //Contador
    public void setContador(){
        this.p.setContador();//Incrementa o contador
    }
    public int getContador(){ 
        return this.p.getContador();//retorna o contador
    }
}
