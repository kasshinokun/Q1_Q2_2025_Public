package TP_AED_3_2023.functions;//nome do package

//importação de bibliotecas
import java.io.*; 
import java.util.*;
import java.time.*;
import java.text.*; 
import java.time.format.*;

public class Changes{
    
    static Locale lpt_BR = Locale.of("pt", "BR");//Padrão do Brasil 
       
    private static final DateTimeFormatter dtf = DateTimeFormatter.ofPattern("dd/MM/yyyy", lpt_BR);
    
    public static String set_Locale(String x){
        return String.format(lpt_BR, x);
    }
    public static boolean set_Format(String date){

        try {
            LocalDate ld = LocalDate.parse(date, dtf);
            date=dtf.format(ld);
            //System.out.println("OK "+date);//feedback apenas
            return true;
        }catch (DateTimeParseException e) {
            System.err.println(set_Locale("Data Inválida, tente novamente."));
            return false;
        }
    
    }
    
}