package com.test_db.main;
import com.test_db.connection.*; //All classes inside package (todas as calsses no pacote)

import java.util.Scanner;

/**
 * @version 1_2025_01_04
 * Netbeans IDE 24 - Java Maven application
 * 
 * PT-BR: 
 * Algumas observações:
 * criado em 04-01-2025
 * para testes e analises de java usando JDBC para conectar
 * com MySQL e PostgreSQL
 * 
 * Espero que o ajude em seus estudos e projetos.
 * 
 * EN-US: 
 * Some observations:
 * created on 04-01-2025
 * for testing and analyzing Java using JDBC to connect
 * with MySQL and PostgreSQL
 * 
 * I hope it helps you in your studies and projects.
 * 
 * @author Gabriel da Silva Cassino
 */
public class main {

    public static void main(String[] args) {
        
        int input=1; //to stay on loop
        do{//main of application
            System.out.println("Hello World!");
            System.out.println("Ola Mundo!");
            System.out.println("EN-US: Please select your language to start:");
            System.out.println("PT-BR: Por favor selecione seu idioma para iniciar:");
            System.out.println("1) English-US");
            System.out.println("2) Portugues-BR");
            System.out.println("0) Exit(Sair)\n\nPlease insert your CHOICE:\n(Por favor insira sua ESCOLHA:)");       
            input=template();//error handling
            switch(input){
                case 1:
                    // code block
                    main_us();
                    break;
                case 2:
                    main_pt();
                    // code block
                    break;
                default:   
                    if(input==0){
                        System.out.println("\nEN-US:");
                        System.out.println("Process finished");
                        System.out.println("Program ended\n");
                        System.out.println("\nPT-BR:");
                        System.out.println("Processo finalizado");
                        System.out.println("Programa encerrado\n");
                    }else{
                        System.out.println("\nEN-US:");
                        System.out.println("Invalid option.");
                        System.out.println("Please, try again.\n");
                        System.out.println("\nPT-BR:");
                        System.out.println("Entrada Invalida.");
                        System.out.println("Por favor, tente novamente.\n");
                    }
            }    
        }while(input!=0);
    }
    public static void main_us(){
        int input=1; //to stay on loop
        do{//main of application
            System.out.println("Hello World!");
            System.out.println("EN-US: Please select your database test to start:");
            System.out.println("PT-BR: Por favor selecione seu teste de banco de dados para iniciar:");
            System.out.println("1) MySQL");
            System.out.println("2) PostgreSQL");
            System.out.println("0) Exit\nPlease insert your CHOICE:"); 
            input=template();//error handling
            switch(input){
                case 1:
                    // code block
                    mysql.main(1);
                    break;
                case 2:
                    postgresql.main(1);
                    // code block
                    break;
                default:   
                    if(input==0){
                        System.out.println("\nProcess finished");
                        System.out.println("\nI'm back to main application\n");
                    }else{
                        System.out.println("\nInvalid option.");
                        System.out.println("Please, try again.\n");
                     }
            }    
        }while(input!=0);
    }
    public static void main_pt(){
        int input=1; //to stay on loop
        do{//main of application
            System.out.println("PT-BR: Ola Mundo!");
            System.out.println("Por favor selecione seu teste de banco de dados para iniciar:");
            System.out.println("1) MySQL");
            System.out.println("2) PostgreSQL");
            System.out.println("0) Sair\nPor favor insira sua ESCOLHA:"); 
            input=template();//error handling
            switch(input){
                case 1:
                    // code block
                    mysql.main(2);
                    break;
                case 2:
                    postgresql.main(2);
                    // code block
                    break;
                default:   
                    if(input==0){
                        System.out.println("\nProcesso finalizado");
                        System.out.println("\nEu estou voltando ao menu do programa\n");
                    }else{
                        System.out.println("\nEntrada Invalida.");
                        System.out.println("Por favor, tente novamente.\n");
                    }
            }    
        }while(input!=0);
    }
    public static int template(){//input validate(on development)
        Scanner reader=new Scanner(System.in);
        if(reader.hasNextInt()){
            return reader.nextInt();
        }else{
            return -1;
        }
    }
}