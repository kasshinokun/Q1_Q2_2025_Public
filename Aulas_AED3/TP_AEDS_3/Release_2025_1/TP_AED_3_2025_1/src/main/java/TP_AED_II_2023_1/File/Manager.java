package TP_AED_II_2023_1.File;//Nome do Subprojeto

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

import java.util.*;//Simplificação de bibliotecas necessarias 
import java.util.regex.*;//Simplificação de bibliotecas especificas e necessarias 
import java.io.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.*;//Simplificação de bibliotecas necessarias para arquivos

import TP_AED_II_2023_1.AVL.*;//Importa classe do package 
import TP_AED_II_2023_1.List.*;//Importa classe do package 
import TP_AED_II_2023_1.File.*;//Importa classe do package 
public class Manager {
    
    static AVL tree=new AVL();//Instancia lista para teste 
    public static void main(String[] args){
      
        Scanner reader=new Scanner(System.in);//coleta a entrada do teclado
        int opcao;//Variavel de escolha
        do{
            System.out.println("\n==Trabalho sobre Arvore AVL, Lista e Arquvo==\n");//Enunciado

            System.out.println("=============Menu de Operacoes===============");//Enunciado

            System.out.println("===01) Processos do Trabalho Pratico em Serie");//Enunciado
            System.out.println("===02) Listar Pastas=========================");//Enunciado
            System.out.println("===03) Listar Arquivo na Pasta===============");//Enunciado
            System.out.println("===04) Insercao na Arvore AVL================");//Enunciado
            System.out.println("===05) Pesquisa na Arvore AVL================");//Enunciado
            System.out.println("===06) Remover na Arvore AVL=================");//Enunciado
            System.out.println("===07) Exibe a Arvore AVL====================");//Enunciado
            System.out.println("===08) Processos em Lista Dupla Encadeada====");
            System.out.println("09)Processos em Lista Dupla Encadeada-Usuario");
            System.out.println("===10) Teste - Exibir a AVL em Modo Grafico==");//Enunciado
            System.out.println("===11) Teste - Lista=========================");//Enunciado
            System.out.println("===12) Teste - MergeSort=====================");//Enunciado
            System.out.println("\n==========Digite 0 para Encerrar=============");//Enunciado
            
            System.out.println("\n======Por favor escolha uma opcao: ==========");//Enunciado
            opcao = Integer.parseInt(reader.nextLine());//armazena o valor
            switch(opcao){//Analise do que foi digitado
//===============================================================================================================
                //Modo Padrão e Demostrativo
                case 1://Chama o procedimento
                    Procedures.executarTP();//Inicia os Processos do TP
                    break;//Condição de parada
                case 2://Chama o procedimento
                    Procedures.optionStart();//Opção de Inicio e Inicio da Busca de Pastas
                    break;//Condição de parada
                case 3://Chama o procedimento
                    Procedures.typeFiles();//Escolha de extensão de arquivo-Modo Demostrativo
                    break;//Condição de parada
                case 4://Chama o procedimento
                    Procedures.inserir();//Inserir na AVL-Modo Demostrativo
                    break;//Condição de parada2
//===============================================================================================================
                //Modo Demostrativo a partir da AVL instanciada na classe
                case 5://Chama o procedimento
                    Procedures.buscar(tree);//Busca na AVL
                    break;//Condição de parada
                case 6://Chama o procedimento
                    Procedures.remover(tree);//Exibe a AVL
                    break;//Condição de parada
                case 7://Chama o procedimento
                    Procedures.exibir(tree);//Exibe a AVL
                    break;//Condição de parada
//===============================================================================================================
                //Modo Demostrativo-Lista
                case 8://Chama o procedimento
                    Procedures.inserirLista();//Processos em Lista-Modo Demostrativo
                    break;//Condição de parada
                case 9://Chama o procedimento
                    Procedures.inserirLista(new Lista());//Processos em Lista de acordo com usuario
                    break;//Condição de parada
//===============================================================================================================
                //Modo Demostrativo - Testes de Código
                case 10://Chama o procedimento
                    Procedures.testeAVL();//teste AVL
                    break;//Condição de parada
                case 11://Chama o procedimento
                    Procedures.testeLista();//teste Lista
                    break;//Condição de parada
                case 12://Chama o procedimento
                    Procedures.MergeSort();//teste Merge Sort
                    break;//Condição de parada
                default:
                    if(opcao==0){//despedida do usuario e agradecimento
                        System.out.println("\n===============Muito obrigado================");
                        System.out.println("==Trabalho sobre Arvore AVL, Lista e Arquvo==\n");//Enunciado
                        
                    }
                    else{//Se não estiver no intervalo, informa ao usuario
                        //e reapresenta o menu
                        System.out.println("\n============Opcao Invalida.==================");
                        System.out.println("======Tente novamente por gentileza!=========\n");
                    } 
            }      
        }while( opcao!=0);//Se repetira enquanto não for zero
    }
    public static void AVL(AVL Arvore){//Recebe a AVL do procedimento buffer da classe Procedures
        //e finaliza os Processos do Trabalho Prático
        tree.setRaiz(Arvore.getRaiz());//recebe a raiz da AVL Arvore
        System.out.println("\n========Execucao de todos os Processos=======");
        System.out.println("============do Trabalho Pratico==============\n");
        Procedures.exibir(tree);//Exibe a AVL
        System.out.println("\n========Insercao de Itens da AVL na==========");
        System.out.println("==========Lista Dupla Encadeada==============\n");
        Procedures.inserirAVL_Lista(tree, new Lista());
        System.out.println();//Salta linha
        System.out.println("\n========Processos dentro da AVL =============");
        Procedures.buscar(tree);//Busca na AVL
        Procedures.remover(tree);//Remoção na AVL
        Procedures.exibir(tree);//Exibe a AVL
    }
    
}
