package TP_AED_II_2023_1.List;//Nome do Subprojeto

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

import java.util.*;
import TP_AED_II_2023_1.AVL.*;

public class Lista{
    private Celula primeiro;
    private Celula ultimo;
    int n=0;

    public Lista(){
        this.primeiro=new Celula();
        this.ultimo=this.primeiro;
    }
    public void inserirInicio(String x){
        
        Celula tmp=new Celula(x);
        tmp.ant=primeiro;
        tmp.prox=primeiro.prox;
        primeiro.prox=tmp;
        
        if(primeiro==ultimo){
            ultimo=tmp;
        }
        tmp=null;
        n++;
    
    }
    public void inserirFim(String x){
        if(primeiro==ultimo){
            inserirInicio(x);
        }
        else{
            
            ultimo.prox=new Celula(x);
            ultimo.prox.ant=ultimo;
            ultimo=ultimo.prox;
            n++;
            
        }
    
    }
    public void addStart(Celula tmp){
        
        tmp.ant=primeiro;
        tmp.prox=primeiro.prox;
        primeiro.prox=tmp;
        
        if(primeiro==ultimo){
            ultimo=tmp;
        }
        tmp=null;
        n++;
        
    
    }
    public void addEnd(Celula x){
        if(primeiro==ultimo){
            addStart(x);
        }
        else{
            
            ultimo.prox=x;
            ultimo.prox.ant=ultimo;
            ultimo=ultimo.prox;
            n++;
            
        }
        
    }
    public void addPos(Celula x, int pos){
        if(pos<=0){
            if(pos<0){
                System.out.println("===Parametro Invalido, adaptando ....=======\n");
            }
            System.out.println("==========Adicionando no Inicio ============\n");
            addStart(x);
        }else if(pos>=n){
            if(pos>n){
                System.out.println("===Parametro Invalido, adaptando ....=======\n");
            }
            System.out.println("==========Adicionando no Fim ===============\n");
            addEnd(x);
        }else{//senao....
            
            Celula i=this.primeiro;
            for(int j=0;j<pos;j++,i=i.prox);
            Celula tmp=new Celula(x);
            tmp.ant=i;
            tmp.prox=i.prox;
            tmp.ant.prox=tmp.prox.ant=tmp;
            tmp=i=null;
            n++;
            
        }
    
    }
    public void inserirPos(String x, int pos){
        if(pos<=0){
            if(pos<0){
                System.out.println("===Parametro Invalido, adaptando ....=======\n");
            }
            System.out.println("==========Adicionando no Inicio ============\n");
            inserirInicio(x);
        }else if(pos>=n){
            if(pos>n){
                System.out.println("===Parametro Invalido, adaptando ....=======\n");
            }
            System.out.println("==========Adicionando no Fim ===============\n");
            inserirFim(x);
        }else{//senao....
            
            Celula i=this.primeiro;
            for(int j=0;j<pos;j++,i=i.prox);
            Celula tmp=new Celula(x);
            tmp.ant=i;
            tmp.prox=i.prox;
            tmp.ant.prox=tmp.prox.ant=tmp;
            tmp=i=null;
            n++;
            
        }
    
    }
    public String removerInicio(){
        if(primeiro==ultimo){
            //Informa ao Usuario
            System.out.println("\n=============Nao e possivel ================");
            System.out.println("==============Inserir dados,================");
            System.out.println("============== Lista Vazia !!===========\n");
            return null;
        }else{
            Celula tmp=primeiro;
            primeiro=primeiro.prox;
            String y=primeiro.getPalavra();
            tmp.prox=primeiro.ant=null;
            tmp=null;
            n--;
            return y;
        }
    }
    
    public String removerFim(){
        if(primeiro==ultimo){
            //Informa ao Usuario
            System.out.println("\n=============Nao e possivel ================");
            System.out.println("==============Inserir dados,================");
            System.out.println("============== Lista Vazia !!===========\n");
            return null;
        }else{
            String y=ultimo.getPalavra();
            ultimo=ultimo.ant;
            ultimo.prox.ant=null;
            ultimo.prox=null;
            n--;
            return y;
        }
    }
    
    public String removerPos(int pos){
        if(primeiro==ultimo||pos<0||pos>=n){
            //Se n igual a 0....
            //Ou também se pos menor que 0.... 
            //Ou pos maior ou igual a n..... 

            //Informa ao Usuario
            System.out.println("\n=============Nao e possivel ================");
            System.out.println("==============Remover dados,================");
            System.out.println("==========Parametros Invalidos !!===========\n");
                                  
            return null;
        }else if(pos<=0){
            if(pos<0){
                System.out.println("===Parametro Invalido, adaptando ....=======\n");
            }
            System.out.println("==========Removendo no Inicio===============\n");
            return removerInicio();
        }else if(pos>=n){
            if(pos>n){
                System.out.println("===Parametro Invalido, adaptando ....=======\n");
            }
            System.out.println("==========Removendo no Fim==================\n");
            return removerFim();
        }else{//senao....
            Celula i=this.primeiro.prox;
            for(int j=0;j<pos;j++,i=i.prox);
            i.ant.prox=i.prox;
            i.prox.ant=i.ant;
            String y=i.getPalavra();
            i.prox=i.ant=null;
            i=null;
            n--;
            return y;
        }
    }
    public void buscar(String s){
        System.out.println("\nPesquisando pela Palavra: "+s+".......");//Enunciado
        Celula i = this.primeiro;
        boolean resp=false;
        for(i=i.prox;i!=null;i=i.prox){
           if(i.getPalavra().compareTo(s)==0){
               resp=true;
               System.out.println("\nA palavra: "+i.getPalavra()+" foi encontrada.");//Exibe em tela
               System.out.println(i.mostrarPalavra());
               break;
           }
        }if(resp==false){
            System.out.println("\nA palavra: "+s+" nao foi encontrada");//Enunciado
        }
    
    
    }
/*//===================================================================================================================
    //Analise de desenvolvimento de código-base
    
    public void inserirPalavra(Palavra x){//recebe a palavra e ordena
        Celula i=new Celula(x);
        this.addEnd(i);
    }
    public void sortItens(){//Ordena lista
        
        Celula i=this.primeiro.prox;
        Celula j=this.ultimo;
        Celula k;
        while(i!=null){
             k=i;//recebe de i
             while(k!=null){
                if(k.getContador()>j.getContador()&&j.getContador()!=0){
                   swap(k,j);
                }
                k=k.prox;
             }i=i.prox;//vai para a próxima celula
        }
        
    }*///Teste de Swap para lista encadeada
    public void swap(Celula a, Celula b) {//declaração do procedimento de troca de posições
        Palavra temp=new Palavra();
        temp.setPalavra(a.getPalavra(),a.getContador());
        a.setPalavra(b.getPalavra(),b.getContador());
        b.setPalavra(temp); 
        
    }
//===================================================================================================================*/
    public void sortItens(){//Chamada do MergeSort
        
        primeiro.prox = mergeSort(primeiro.prox);
        System.out.println();
        
    }
    private Celula mergeSort(Celula i) {//Executa inicializa as etapas do MergeSort
        if(i == null || i.prox == null) {
          return i;
        }
    
        Celula meio = middleCell(i);
        Celula meioProx = meio.prox;
        meio.prox=null;

        return merge(mergeSort(i), mergeSort(meioProx));
    }

    /*
     * Localizar a Celula no meio da Lista
     */
    private Celula middleCell(Celula i) {
        if(i== null) {
            return null;
        }

        Celula a = i;
        Celula b = i.prox;

        while(b != null && b.prox!= null) {
            a = a.prox;
            b = b.prox.prox;
        }

        return a;
    }
  
  /*
   * Executa o MergeSort  com duas Celulas
   */
  private Celula merge(Celula a, Celula b) {
    Celula temp = new Celula();
    Celula i = temp;
    
    while(a!= null && b!= null) {
        if(a.getContador() > b.getContador()) {
            temp.prox=a;
            a = a.prox;
        }else if(a.getContador() == b.getContador()&&a.getPalavra().compareTo(b.getPalavra())>0){
            temp.prox=a;
            a = a.prox;
        }else if(a.getContador() == b.getContador()&&a.getPalavra().compareTo(b.getPalavra())<0){
            temp.prox=b;
            b = b.prox;
        }else {
            temp.prox=b;
            b = b.prox;
        }
        temp = temp.prox;
    }
    temp.prox=(a == null) ? b : a;
    return i.prox;
  }
  
  /*
   * getNewCell() cria uma nova Celula
   */
    private Celula getNewCell(Palavra key) {
        Celula i = new Celula(key);
        return i;
    }

    /*
     * Inserção de objeto na Lista
     */
    public void inserirPalavra(Palavra p){//Palavra já instaciada
        
        primeiro.prox = inserirPalavra(p, primeiro.prox);   
        //sortItens();
    }
    public void inserirData(String x, int y){//Cria uma nova Palavra
        Palavra p=new Palavra();
        p.setPalavra(x,y);
        primeiro.prox = inserirPalavra(p, primeiro.prox);   

    }
    private Celula inserirPalavra(Palavra key, Celula i) {//Inseri a palavra

        if (i == null)
            return getNewCell(key);
        else
            i.prox=inserirPalavra(key, i.prox);

        return i;
    }
    public void print(){//metodo de impressão adaptado para o MergeSort
        printList(primeiro.prox);
    }
    private void printList(Celula i) {//Impressão recursiva da lista
        if (i== null) {
            return;
        }

        System.out.println(i.mostrarPalavra()+ " ");
        printList(i.prox);
    }
    public void mostrar(){//imprimir Padrão
        
        Celula i = this.primeiro;
        
        for(i=i.prox;i!=null;i=i.prox){
            System.out.println(i.mostrarPalavra());
        }
    }
}
