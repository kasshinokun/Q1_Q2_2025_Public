package TP_AED_3_2025;//Nome do Subprojeto

/**
 * @version 1_2025_02_06
 * @author Gabriel da Silva Cassino
 */


import Functions.*;
import FileExplorer.*;
import Practice.*;
import Practice.Process;

import java.util.*;

import TP_AED_II_2023_1.CallerTP;
import TP_AED_3_2023.start.Main;

public class Main_TP {

    public static void main(String[] args) {
        System.out.println("Hello World!");
        
        Menu_Processos(args);
        
        System.exit(0);//Encerra o programa
        
    }
    public static void Menu_Processos(String[] args){
        
        System.out.println("==Treino para Trabalho de Arvore B e Arquvo==\n");//Enunciado
        int op;//Variavel de escolha
        do{
        System.out.println("===01) Trabalho Pratico AED II de 2023-1=====");//Enunciado
        System.out.println("===02) Trabalho Pratico AED III de 2023-2====");//Enunciado
        System.out.println("===03) Preludio 2025-1 TP     ===============");//Enunciado
        System.out.println("===04) Trabalho de 2025-1     ===============");//Enunciado
        System.out.println("===05) Listar Caminho - Classe===============");//Enunciado
        op=functions_op.template();//error handling
            switch(op){
                //Modo Padrão e Demostrativo
                case 1://Chama o procedimento
                    CallerTP.main(args);//App;//Inicia os Processos do TP 2023-1
                    break;//Condição de parada
                case 2://Chama o procedimento
                    Main.main(args);//App;//Inicia os Processos do TP 2023-2
                    break;//Condição de parada
                case 3://Chama o procedimento
                    //Opção de Inicio e Inicio da Busca de Pastas
                	FileExplorer.main(args);//Vinculando Main's(Prelúdio do TP 2025-1)
                    break;//Condição de parada
                case 4://Chama o procedimento
                    //Escolha de extensão de arquivo-Modo Demostrativo
                	//A ser definido futuramente
                    break;//Condição de parada
                case 5://Chama o procedimento
                    new Process().search_folder_to_path();//teste de adaptação
                    break;//Condição de parada
                default:
                    if(op==0){//despedida do usuario e agradecimento
                        System.out.println("\n===============Muito obrigado================");
                        System.out.println("==Treino para Trabalho de Arvore B e Arquvo==\n");//Enunciado
                        
                    }
                    else{//Se não estiver no intervalo, informa ao usuario
                        //e reapresenta o menu
                        System.out.println("\n============Opcao Invalida.==================");
                        System.out.println("======Tente novamente por gentileza!=========\n");
                    } 
            }      
        }while( op!=0);//Se repetira enquanto não for zero
    }
            
    
}
