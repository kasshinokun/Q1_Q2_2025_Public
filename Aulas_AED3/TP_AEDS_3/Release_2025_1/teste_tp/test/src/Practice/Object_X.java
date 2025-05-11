
//JRE usando Java-SE 21

package Practice;//Nome do Subprojeto

/**
 * @version 1_2025_02_06
 * @author Gabriel da Silva Cassino
 */


import java.text.*;
import java.util.*;
//import java.sql.*;
import java.time.*;//Testar viabilidade
import java.time.format.*;

public class Object_X {
    
    //Class attributes
    private String name;
    private String chinese_id;
    private String date;//Temporario
    private LocalDate register; //analisar viabilidade 
    private int year;

    //Constructor
    public Object_X(String name, String chinese_id, LocalDate register) {
        this.name = name;
        this.chinese_id = chinese_id;
        this.register=register;
        this.year = register.getYear();
    }
    public Object_X(String name, String chinese_id) {
        this.name = name;
        this.chinese_id = chinese_id;
        this.setRegisterDate(setdatefromstr(chinese_id));
    }
    
    //Setters
    public void setName(String name) {
        this.name = name;
    }

    public void setChinese_id(String chinese_id) {
        this.chinese_id = chinese_id;
    }
    
    private void setStringDate(String date) {
    	this.date=date;
	}
    
    public void setRegisterDate(LocalDate register) {
	    this.register=register; 
    }
    
    public void setYear(int year) {
        this.year = year;
    }
    
   //analisar viabilidade, ver site abaixo 
    //https://stackoverflow.com/questions/8746084/string-to-localdate
    private LocalDate setdatefromstr(String id_chinese){
    	
    	String pattern = "yyyyMMdd";//Pattern Date
    	DateTimeFormatter FORMATTER_LDATE = new DateTimeFormatterBuilder().parseCaseInsensitive()
    	        .append(DateTimeFormatter.ofPattern(pattern)).toFormatter();
    	try {
    		//330922 19940724 001X
			//Area    data    verificador   	
			String stringdate=id_chinese.substring( 6,  14);
			
			this.setStringDate(stringdate);//data temporária 19940704
			
    		LocalDate setDate = LocalDate.parse(stringdate, FORMATTER_LDATE);
    	    System.out.println(setDate); //data 1994-07-04
    	    
    	    this.setYear(setDate.getYear());//Ano 1994
    	    
    	    return setDate;
    	    
    	} catch (DateTimeParseException e) {
    	     // Exception handling message/mechanism/logging as per company standard
    		//retorna vazio
    		return null;
    	}
    	
    
    }
    
    //Getters
    public String getName() {
        return this.name;
    }

    public String getChinese_id() {
        return this.chinese_id;
    }
    
    public String getStringDate() {
    	return this.date;
    }
    
    public LocalDate getRegisterDate() {
		
    	return  this.register;
	
    }
    public int getYear() {
        return this.year;
    }
    
    //ToString       
    public String printObject() {
    	return "\nNome ----: "+this.getName()+
    		 "\nID_ZH ---: "+this.getChinese_id()+
    		 "\ndate ----: "+this.getStringDate()+ //Temporario
    		 "\nCal -----: "+this.getRegisterDate()+
    		 "\nYear ----: "+this.getYear();
    }
    
    
}
