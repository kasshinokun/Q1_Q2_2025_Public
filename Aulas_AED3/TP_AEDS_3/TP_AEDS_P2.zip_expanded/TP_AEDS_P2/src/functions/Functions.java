package functions;//nome do package

//importação de funções do package 
import functions.*;
//importação de bibliotecas
import java.text.*;
import java.util.*;
import java.time.*;
import java.io.*;
import java.nio.*;

public class Functions {
    public static int only_Int(){////Validação da entrada de Int
        Scanner reader=new Scanner(System.in);
        if(reader.hasNextInt()){//se for uma entrada int....
            return reader.nextInt();//retorna a entrada
        }else{
            return -1;//senao retorna -1
        }
        
        
    }
    public static float only_Float(){//Validação da entrada de Float
        Scanner reader=new Scanner(System.in);
        if(reader.hasNextFloat()){//se for uma entrada float....
            return reader.nextFloat();//retorna a entrada
        }else{
            return -1;//senao retorna -1
        }
        
        
    }
    public static double only_Double(){//Validação da entrada de Double
        Scanner reader=new Scanner(System.in);
        if(reader.hasNextDouble()){//se for uma entrada double....
            return reader.nextDouble();//retorna a entrada
        }else{
            return -1;//senao retorna -1
        }
        
        
    }
    public static long only_Long(){//Validação da entrada de Double
        Scanner reader=new Scanner(System.in);
        if(reader.hasNextLong()){//se for uma entrada double....
            return reader.nextLong();//retorna a entrada
        }else{
            return -1;//senao retorna -1
        }
        
        
    }
    public static String reading(){//entrada para strings
        Scanner reader=new Scanner(System.in);
        return reader.nextLine();
        
    }
    public static String read_data(String date, int year){//Validação da data digitada
        
        //substituição dos 4 ultimos caracteres para evitar divergencias
        //entre a data e o ano
        if(date.length()==10){//se tamanho total da string
            date=date.substring(0, 6).concat(String.valueOf(year));
        }else{//senao.....
            date=date.concat(String.valueOf(year));
        }
        
        boolean resp=false;
        if(Changes.set_Format(date)==false){//conferindo a data
            do{
                
                System.out.print("Insira o dia:------------");
                String day=Functions.reading();
                System.out.print(Changes.set_Locale("Insira o mês:------------"));
                String month=Functions.reading();
                
                date=day+"/"+month+"/"+String.valueOf(year);//monta a data
                                
                resp=Changes.set_Format(date);//valida a data

            }while(resp==false);
        }
        return date;
    }
    public static int set_Year(int year){//Validação do ano digitado   
        
        while((year<1903&&year>getYearNow())||
                (year>1914&&year<1919)||
                (year>1939&&year<1947)){
            System.out.print(Changes.set_Locale("Insira um Ano Válido:........"));
            year=Functions.only_Int();
        }
        return year;
    }
    public static String format_id(int id){//mascara para ID's
        if (id<10){
            return String.format("00%d",id);
        }
        else if(id>=10&&id<100){
            return String.format("0%d",id);
        }
        else{
            return String.format("%d",id);
        }
    }
    private static int getYearNow(){
        int year =(int)LocalDate.now().getYear();
        
        return year;
    }
}
