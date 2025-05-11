package TP_AED_3_2023.start;


import TP_AED_3_2023.file.Procedures_2_A_2;
import TP_AED_3_2023.file.*;

import TP_AED_3_2023.functions.*;//tratamento de exceções

public class Part_2A {

    public static void main(String[]args){
        //Menu Trabalho Pratico
        int op;//Variavel de escolha
        do{
            System.out.println(Changes.set_Locale("\nTrabalho Prático - Parte 2-a"));
            System.out.println(Changes.set_Locale("\nMenu de Opções:\n"));
            System.out.println("1 - 1) Adicionar apenas um registro==========");
            System.out.println("2 - 2) Adicionar registros do csv============");
            System.out.println("3 - 3) Ler todos os registros================");
            System.out.println("4 - 4) Buscar registro por ID================");
            System.out.println("5 - 5) Atualizar registro por ID=============");
            System.out.println("6 - 6) Apagar registro por ID================");
            System.out.println("7 - 7) Apagar Indice e registros=============");
            System.out.println("8 - 8) Restaurar indice e registros do backup");
            System.out.println("9 - 9) Testes================================");
            System.out.println("10 - 10) Testes==============================");
            System.out.println("\n0 - Encerrar\n");
            System.out.println(Changes.set_Locale("Por escolha uma opção:"));
            op=Functions.only_Int();//Tratamento de entrada
            //Procedimentos
            switch(op){
                //Procedimentos
                case 1:
                    //Procedimento #1
                    System.out.println("\n1) Procedimento #1===========================");
                    
                    Procedures_2_A_1.create_one();
                    System.out.println("=============================================\n");
                    break;
                case 2:
                    //Procedimento #2
                    System.out.println("\n2) Procedimento #2===========================");
                    
                    Procedures_2_A_1.create_from_file();
                    System.out.println("=============================================\n");
                    break;
                case 3:
                    //Procedimento #3
                    System.out.println("\n3) Procedimento #3===========================");
                    System.out.println(Changes.set_Locale("Leitura de todos os registros"));
                    Procedures_2_A_2.readIndex(1);
                    System.out.println("\n=============================================\n");
                    break;
                case 4:
                    //Procedimento #4
                    System.out.println("\n4) Procedimento #4===========================");
                    System.out.println(Changes.set_Locale("Busca de registro por ID"));
                    Procedures_2_A_2.readIndex(2);
                    System.out.println("\n=============================================\n");
                    break;
                case 5:
                    //Procedimento #5
                    System.out.println("\n5) Procedimento #5===========================");
                    System.out.println(Changes.set_Locale("Atualização de registro por ID"));
                    Procedures_2_A_2.readIndex(3);
                    System.out.println("\n=============================================\n");
                    break;
                case 6:
                    //Procedimento #6
                    System.out.println("\n6) Procedimento #6===========================");
                    System.out.println(Changes.set_Locale("Exclusão de registro por ID"));
                    Procedures_2_A_2.readIndex(4);
                    System.out.println("\n=============================================\n");
                    break;
                
                case 7:
                    //Procedimento #7
                    System.out.println("\n7) Procedimento #7===========================");
                    System.out.println(Changes.set_Locale("Exclusão de todos os registros"));
                    Procedures_2_A_1.delete_Registry();
                    Procedures_2_A_2.delete_Index();
                    System.out.println("\n=============================================\n");
                    break;
                case 8:
                    //Procedimento #8
                    System.out.println("\n8) Procedimento #8===========================");
                    System.out.println("=Restaurar indice e registros do backup======\n");
                    Procedures_2_A_1.read_csv("backup/data/tour.csv");
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
