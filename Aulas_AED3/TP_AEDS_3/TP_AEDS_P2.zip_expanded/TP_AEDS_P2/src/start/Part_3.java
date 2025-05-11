package start;

import file.*;
import functions.*;


public class Part_3 {
    public static void main(String[]args){
        //Menu Trabalho Pratico
        int op;//Variavel de escolha
        do{
            System.out.println(Changes.set_Locale("\nTrabalho Prático - Parte 3"));
            System.out.println("=================Criptografia===================");
            System.out.println(Changes.set_Locale("\nMenu de Opções:\n"));
            System.out.println("1 - 1) Testes: Cifra de Cesar ASCII 32-256======");
            System.out.println("2 - 2) Testes: Cifra de Vigenere ASCII 32-256===");
            /*Pode vir a ser usado futuramente
            System.out.println("3 - 3) Testes===================================");
            System.out.println("4 - 4) Testes===================================");
            System.out.println("5 - 5) Testes===================================");
            System.out.println("6 - 6) Testes===================================");
            System.out.println("7 - 7) Testes===================================");
            System.out.println("8 - 8) Testes===================================");
            System.out.println("9 - 9) Testes===================================");
            System.out.println("10 - 10) Testes=================================");
            System.out.println("11 - 11) Testes=================================");
            System.out.println("12 - 12) Testes=================================");
            System.out.println("13 - 13) Testes=================================");
            System.out.println("14 - 14) Testes=================================");
            System.out.println("15 - 15) Testes=================================");
            System.out.println("16 - 16) Testes=================================");
            System.out.println("17 - 17) Testes=================================");
            System.out.println("18 - 18) Testes=================================");
            System.out.println("19 - 19) Testes=================================");
            System.out.println("20 - 20) Testes=================================");
            */
            System.out.println("\n0 - Encerrar\n");
            System.out.println(Changes.set_Locale("Por escolha uma opção:"));
            op=Functions.only_Int();//Tratamento de entrada
            //Procedimentos
            switch(op){
                //Procedimentos
                case 1:
                    //Procedimento #1
                    System.out.println("\n1) Procedimento #1==============================");
                    System.out.println("\nEm Desenvolvimento");
                    //Cifra de Cesar 
                    Procedures_3_A.callCaesar();
                    System.out.println("\n================================================\n");
                    break;
                case 2:
                    //Procedimento #2
                    System.out.println("\n2) Procedimento #2==============================");
                    System.out.println("\nEm Desenvolvimento");
                    //Cifra de Vigenere
                    Procedures_3_A.callVigenere();
                    System.out.println("\n================================================\n");
                    break;
                /*Pode vir a ser usado futuramente
                case 3:
                    //Procedimento #3
                    System.out.println("\n3) Procedimento #3==============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 4:
                    //Procedimento #4
                    System.out.println("\n4) Procedimento #4==============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 5:
                    //Procedimento #5
                    System.out.println("\n5) Procedimento #5==============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 6:
                    //Procedimento #6
                    System.out.println("\n6) Procedimento #6==============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                
                case 7:
                    //Procedimento #7
                    System.out.println("\n7) Procedimento #7==============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 8:
                    //Procedimento #8
                    System.out.println("\n8) Procedimento #8==============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 9:
                    //Procedimento #9
                    System.out.println("\n9) Procedimento #9==============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 10:
                    //Procedimento #10
                    System.out.println("\n10) Procedimento #10=========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 11:
                    //Procedimento #11
                    System.out.println("\n11) Procedimento #11=========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 12:
                    //Procedimento #12
                    System.out.println("\n12) Procedimento #12=========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 13:
                    //Procedimento #13
                    System.out.println("\n13) Procedimento #13=========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 14:
                    //Procedimento #14
                    System.out.println("\n14) Procedimento #14=========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 15:
                    //Procedimento #15
                    System.out.println("\n15) Procedimento #15=========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                case 16:
                    //Procedimento #16
                    System.out.println("\n16) Procedimento #16============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                
                case 17:
                    //Procedimento #17
                    System.out.println("\n17) Procedimento #17============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 18:
                    //Procedimento #18
                    System.out.println("\n18) Procedimento #18============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 19:
                    //Procedimento #19
                    System.out.println("\n19) Procedimento #19============================");
                    
                    System.out.println("\n================================================\n");
                    break;
                case 20:
                    //Procedimento #20
                    System.out.println("\n20) Procedimento #20=========================");
                    
                    System.out.println("\n=============================================\n");
                    break;
                */
                default:   
                    if(op==0){
                        System.out.println("\nProcesso finalizado");
                        System.out.println("Retornando ao Menu\n");
                        
                    }else{
                        System.out.println(Changes.set_Locale("\nOpção inválida."));
                        System.out.println("Por favor, tente novamente.\n");
                    }
            }
        }while(op!=0);//Condição de parada do programa
    }
}
