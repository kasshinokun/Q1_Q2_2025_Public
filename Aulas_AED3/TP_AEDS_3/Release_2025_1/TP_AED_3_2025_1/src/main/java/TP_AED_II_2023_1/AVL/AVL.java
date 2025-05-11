package TP_AED_II_2023_1.AVL;//Nome do Subprojeto

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

import java.io.*;//Simplificação de bibliotecas necessarias para arquivos
import java.util.*;//Simplificação de bibliotecas necessarias 
import TP_AED_II_2023_1.AVL.*;//Package das classes
import TP_AED_II_2023_1.List.*;

//Adaptação de código

public class AVL {//Declaração da AVL
    
    private No raiz;//Raiz da AVL
    
    public AVL(){//Construtor default
        this.raiz=null;
    }
    public void setRaiz(No A){//Recebe raiz
        this.raiz=A.getNo();
    }
    public No getRaiz(){//Retorna Raiz
        return this.raiz.getNo();
    }
    //Inicio da insercão na AVL
    public void add_Palavra(String x){
        raiz = inserir(x, raiz);
    }
    //Inserção na AVL
    private No inserir(String x, No n){
        if (n == null) {
            n = new No(x);
        } else if (x.compareTo( n.getPalavra())<0) {
            n.setEsq(inserir(x, n.getEsq()));
        } else if (x.compareTo( n.getPalavra()) > 0) {
            n.setDir(inserir(x, n.getDir()));
        } else if(x.compareTo( n.getPalavra())==0){
            n.setContador();
        }else{
            System.out.println("Erro!");
        }
        return balancear(n);//retorno de acordo com procedimento
    }
//Rotação para BST Padrão(Adaptação)
    private No balancear(No no){//Balanceamento da AVL
        if (no != null) {//se não for vazio....
            int fator = No.getAltura(no.getDir()) - No.getAltura(no.getEsq());
            // Se balanceada
            if (Math.abs(fator) <= 1) {
                no.setAltura();
            // Se desbalanceada para a direita
            } else if (fator == 2) {
                int fatorFilhoDir = No.getAltura(no.getDir().getDir()) - No.getAltura(no.getDir().getEsq());
                // Se o filho a direita tambem estiver desbalanceado
                if (fatorFilhoDir == -1) {
                        no.setDir(rotacionarDir(no.getDir()));
                }
                no=rotacionarEsq(no);
            // Se desbalanceada para a esquerda
            } else if (fator == -2) {
                int fatorFilhoEsq = No.getAltura(no.getEsq().getDir()) - No.getAltura(no.getEsq().getEsq());
                // Se o filho a esquerda tambem estiver desbalanceado
                if (fatorFilhoEsq == 1) {
                    no.setEsq(rotacionarEsq(no.getEsq()));
                }
                no=rotacionarDir(no);
            } else {
                System.out.println("Erro no No( " + no.getPalavra()+ " ) com fator de balanceamento (" + fator + ") invalido!");
            }
        }
        return no;//retorno ao procedimento
    }
    private No rotacionarDir(No no) {//Rotação a direita
        
        No noEsq = no.getEsq();
        No noEsqDir = noEsq.getDir();
        
        
        noEsq.setDir(no);
        no.setEsq(noEsqDir);
        no.setAltura(); // Atualizar o nivel do no
        noEsq.setAltura(); // Atualizar o nivel do noEsq

        return noEsq;//retorno ao procedimento
    }

    private No rotacionarEsq(No no) {//Rotação a esquerda
        
        No noDir = no.getDir();
        No noDirEsq = noDir.getEsq();

        noDir.setEsq(no);
        no.setDir(noDirEsq);

        no.setAltura(); // Atualizar o nivel do no
        noDir.setAltura(); // Atualizar o nivel do noDir
        return noDir;//retorno ao procedimento
    }

//Inicio da busca baseado na Arvore Binaria padrão
    public boolean pesquisar(String x) {
        System.out.println("\nPesquisando pela Palavra: "+x+".......");//Enunciado
        No n=raiz;
        boolean resp=pesquisar(x, n);//Envia ao procedimento
        if(resp==false){//Se não encontrar....
            System.out.println("\nA palavra: "+x+" nao foi encontrada");//Enunciado
        }
        return resp;//retorno ao procedimento
    }
//Busca na AVL
    private boolean pesquisar(String x, No n) {
        boolean resp;//instancia objeto booleano
        if (n == null) {//Se vazio...
            resp = false;
        } else if(x.compareTo(n.getPalavra())==0) {//Se igual
            resp = true;//resp recebe true
            System.out.println("\nA palavra: "+n.getPalavra()+" foi encontrada.");//Exibe em tela
            System.out.println(n.mostrarPalavra());
        
        } else if(x.compareTo(n.getPalavra())<0) {//Se menor...
            resp = pesquisar(x, n.getEsq());
        } else {
            resp = pesquisar(x, n.getDir());//Se maior....
        }
        
        return resp;//retorno ao procedimento
    }
//Remoção na AVL
    public void remover(String x){
       System.out.println("\nPesquisando pela Palavra: "+x+".......");//Enunciado
       raiz = remover(x, raiz);
    }
    private No remover(String x, No i){
        if (i == null) {
            System.out.println("\nErro!");
            System.out.println("\nA palavra "+x+" nao foi encontrada.");
        } else if (x.compareTo(i.getPalavra())< 0) {
            i.setEsq(remover(x, i.getEsq()));
        } else if (x.compareTo(i.getPalavra()) > 0) {
            i.setDir(remover(x, i.getDir()));
        // Sem no a direita.
        } else if (i.getDir() == null) {
            System.out.println("\nA palavra "+i.getPalavra()+" foi encontrada.");
            System.out.println("Removendo.......");
            i = i.getEsq();
        // Sem no a esquerda.
        } else if (i.getEsq() == null) {
            System.out.println("\nA palavra "+i.getPalavra()+" foi encontrada.");
            System.out.println("Removendo.......");
            i = i.getDir();
        // No a esquerda e no a direita.
        } else {
            i.setEsq(maiorEsq(i, i.getEsq()));
        }
        return balancear(i);
    }
    private No maiorEsq(No i, No j) {
        // Encontrou o maximo da subarvore esquerda.
        if (j.getDir() == null) {
            System.out.println("\nA palavra "+i.getPalavra()+" foi encontrada.");
            System.out.println("Removendo.......");
            i.setPalavra(j.getPalavra()); // Substitui i por j.
            j = j.getEsq(); // Substitui j por j.ESQ.
        // Existe no a direita.
        } else {
            // Caminha para direita.
            j.setDir(maiorEsq(i, j.getDir()));
        }
        return j;
    }

//Caminhamentos na AVL
    private void preOrder(No no) {//Pré=Ordem
        if (no != null) {
            System.out.println(no.mostrarPalavra());
            preOrder(no.getEsq());
            preOrder(no.getDir());
        }
    }
    private void inOrder(No no) {//Caminhamento Central
        if (no != null) {
            inOrder(no.getEsq());
            System.out.println(no.mostrarPalavra());
            inOrder(no.getDir());
        }
    }
    private void posOrder(No no) {//Pós-Ordem
        if (no != null) {
            posOrder(no.getEsq());
            posOrder(no.getDir());
            System.out.println(no.mostrarPalavra());
        }
    }
    public void imprimir(int op){//Impressão baseado na escolha do usuario
        
        if(op==1){//Pré-Ordem
            System.out.println("\nPre-Order\n");
            preOrder(this.raiz);
        }else if(op==2){//Caminhamento Central
            System.out.println("\nIn-Order\n");
            inOrder(this.raiz);
        }else{//Pós-Ordem
            System.out.println("\nPos-Order\n");
            posOrder(this.raiz);
        }
    }
    public void inserirOrdenado(Lista lista){//Inserçao de Palavra
        inserirOrdenado(raiz,lista);//Envia aoProcedimento
        lista.sortItens();//ordena
        lista.print();//Exibe a Lista ao final
    }
    private void inserirOrdenado(No no,Lista lista){
    //Procedimento de inserção baseado no caminhamento in Order
        if (no != null) {
            inserirOrdenado(no.getEsq(),lista);
            //Envia a palavra ao procedimento da lista
            lista.inserirPalavra(no.sendPalavra());
            inserirOrdenado(no.getDir(),lista);
        }
    }
    //Adaptação para feedback----Fonte Programiz
    public void feedBack(){//Apresenta a AVL de forma grafica
        System.out.println("\n===Exibindo a AVL em Modo Grafico=============\n");
        feedBack(this.getRaiz(), "", true);
        System.out.println("\n=============================================");
    }
    private void feedBack(No atual, String indent, boolean ultimo) {
        if (atual != null) {//Metodo utilizará o Caminhamento Pré-Order para Exibir a AVL
            System.out.print(indent);
            //variavel booleana para tabulação e definição correta de No
            if (ultimo) {
                System.out.print("Dir----");
                indent += "   ";
            } else {
                System.out.print("Esq----");
                indent += "|  ";
            }
            System.out.println(atual.mostrarPalavra());//Exibe o Objeto
            feedBack(atual.getEsq(), indent, false);//No a  Esquerda
            feedBack(atual.getDir(), indent, true);//No a Direita
        }
    }
}
