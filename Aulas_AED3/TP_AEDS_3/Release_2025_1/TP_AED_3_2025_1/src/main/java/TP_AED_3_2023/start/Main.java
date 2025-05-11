package TP_AED_3_2023.start;

import TP_AED_3_2023.file.Procedures_3_A;
import TP_AED_3_2023.functions.Changes;
import TP_AED_3_2023.functions.Functions;

public class Main {
    public static void main(String[]args){
        //Menu Trabalho Pratico
        int op;//Variavel de escolha
        do{
            System.out.println(Changes.set_Locale("\nTrabalho Prático - AEDS 3"));
            System.out.println(Changes.set_Locale("\nMenu Inicial"));
            System.out.println(Changes.set_Locale("\nMenu de Opções:\n"));
            System.out.println("1 - 1) Parte 1==Arquivo em Memória Secundária");
            System.out.println("2 - 2) Parte 2-A=Arquivos Indexados Parte 1==");
            System.out.println("3 - 3) Parte 2-B=Arquivos Indexados Parte 2==");
            System.out.println("4 - 4) Parte 3-Criptografia==================");
            /*Pode vir a ser usada futuramente
            System.out.println("5 - 5) Testes================================");
            System.out.println("6 - 6) Testes================================");
            System.out.println("7 - 7) Testes================================");
            System.out.println("8 - 8) Testes================================");
            System.out.println("9 - 9) Testes================================");
            System.out.println("10 - 10) Testes==============================");
            */
            System.out.println("\n0 - Encerrar\n");
            System.out.println(Changes.set_Locale("Por escolha uma opção:"));
            op=Functions.only_Int();//Tratamento de entrada
            //Procedimentos
            switch(op){
                //Procedimentos
                case 1:
                    //Procedimento #1
                    System.out.println("\n1) Parte 1===================================");
                    Part_1.main(args);//Parte 1 do Trabalho Prático
                    
                    break;
                case 2:
                    //Procedimento #2
                    System.out.println("\n2) Parte 2===================================");
                    Part_2A.main(args);//Parte 2-A) do Trabalho Prático
                    break;
                case 3:
                    //Procedimento #3
                    System.out.println("\n3) Procedimento #3===========================");
                    Part_2B.main(args);//Parte 2-B) do Trabalho Prático
                    System.out.println("\n=============================================\n");
                    break;
                
                case 4:
                    //Procedimento #4
                    System.out.println("\n4) Procedimento #4===========================");
                    System.out.println("\nEm Desenvolvimento");
                    Part_3.main(args);//Parte 3 do Trabalho Prático
                    System.out.println("\n=============================================\n");
                    break;
                /*Pode vir a ser usado futuramente    
                case 5:
                    //Procedimento #5
                    System.out.println("\n5) Procedimento #5===========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 6:
                    //Procedimento #6
                    System.out.println("\n6) Procedimento #6===========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                
                case 7:
                    //Procedimento #7
                    System.out.println("\n7) Procedimento #7===========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 8:
                    //Procedimento #8
                    System.out.println("\n8) Procedimento #8===========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 9:
                    //Procedimento #9
                    System.out.println("\n9) Procedimento #9===========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 10:
                    //Procedimento #10
                    System.out.println("\n10) Procedimento #10=========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                */
                default:   
                    if(op==0){
                        System.out.println("\nProcesso finalizado");
                        System.out.println("Retornando ao Menu\n");
                        //System.exit(0);
                    }else{
                        System.out.println(Changes.set_Locale("\nOpção inválida."));
                        System.out.println("Por favor, tente novamente.\n");
                    }
            }
        }while(op!=0);//Condição de parada do programa
    }
}
