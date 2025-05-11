package test.estagio1;

import java.io.File;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

public class Functions {//Classe Template e, para Trativa de erros e Conversões de entrada
    
	private static Scanner reader=new Scanner(System.in);//Scanner das classes    
	
    //=================================================> Tratativa de Erros de Entrada
    //Verificadores e Scanners
    public static int only_Int(){////Validação da entrada de Int
        
        if(reader.hasNextInt()){//se for uma entrada int....
            return reader.nextInt();//retorna a entrada
        }else{
            return -1;//senao retorna -1
        }
        
        
    }
    public static void closeBuffer() {
    	
    }
    public static float only_Float(){//Validação da entrada de Float
        
        if(reader.hasNextFloat()){//se for uma entrada float....
            return reader.nextFloat();//retorna a entrada
        }else{
            return -1;//senao retorna -1
        }
        
        
    }
    public static double only_Double(){//Validação da entrada de Double
        
        if(reader.hasNextDouble()){//se for uma entrada double....
            return reader.nextDouble();//retorna a entrada
        }else{
            return -1;//senao retorna -1
        }
        
        
    }
    public static long only_Long(){//Validação da entrada de Double
       
        if(reader.hasNextLong()){//se for uma entrada double....
            return reader.nextLong();//retorna a entrada
        }else{
            return -1;//senao retorna -1
        }
        
        
    }
    public static String reading(){//entrada para strings
    	Scanner reader2=new Scanner(System.in);//Scanner da função  
        return reader2.next();
    }
    //Funções de Data
    public static int getYearNow(){
        int year =(int)LocalDate.now().getYear();
        
        return year;
    }
    public static boolean findFile(String Path) {
		File diretorio = new File(Path);
		if (!diretorio.exists())
			return false;
		else
			return true;
	}

    //=================================================> Boolean
    //Conversores
    public static boolean getBooleanFromString(String root) {
  		
  		if (root.charAt(0)=='Y') {
  			//System.out.println(true);
  			return true;
  		}else {
  			//System.out.println(false);
  			return false;
  		}
  		
  	}

  	public static String getStringFromBoolean(boolean request) {
  		
  		if (request==true) {
  			//System.out.println(true);
  			return "Y";
  		}else {
  			//System.out.println(false);
  			return "N";
  		}
  		
  	}
  	
    //=================================================> Data e testes	
  	public static String dateToString(String datetime)/*throws ParseException*/ {
  			
  		SimpleDateFormat FORMATTER=new SimpleDateFormat("dd/MM/yyyy hh:mm:ss aa",Locale.getDefault());
          try {
          	return ("Data de Registro: "+getDay(FORMATTER,datetime)+
          			         "\nHorario --------: "+getHourFromDay(FORMATTER,datetime));

          } catch (ParseException e) {
              e.printStackTrace();
              return "Data Invalida";
          }
  	    
  	}
  	
  	public static String getDay(SimpleDateFormat FORMATTER,String datetime) throws  ParseException{
  		return new SimpleDateFormat("dd/MM/yyyy",Locale.getDefault()).format(FORMATTER.parse(datetime));
  	}
  	
  	public static String getHourFromDay(SimpleDateFormat FORMATTER,String datetime) throws  ParseException{
  		return new SimpleDateFormat("HH:mm:ss",Locale.getDefault()).format(FORMATTER.parse(datetime));
  	}
  	public static int getDayWeek(LocalDate date) {
  		return date.getDayOfWeek().getValue();
  	}
  	public static int getNumMonth(LocalDate date) {
  		return date.getMonthValue();
  	}
  	
    //=================================================> List<String> e String[]
  //Para novo registro e Update
  	public static int getCountList() {
    	int count=0;
    	while(count<1){
    		System.out.println("\nPor favor me diga a quantidade de itens a ser listada por favor:");
    		count=only_Int();
    	};
    	return count;
    }
  	
  	//Conversores
    //-------------------> Lista de Strings
  	public static String listToString(List<String> list) {
  		return String.join(" , ", list);
  	}
  	public static List<String> convertIntoList(String[] array) {
  		return Arrays.asList(array);
  	}
  	public static int getSizeList(List<String> Lista) {
  		return Lista.size();//Retornando o tamanho da List<String>
  	}
  	public static List<String> generateStringList(String enunciado, int count) {
    	List<String> result=new ArrayList<>();
    	for(int i=0;i<count;i++) {
    		System.out.println(enunciado);
    		result.add(reading());
    	}
    	return result;
    } 
  	//-------------------> Vetor de Strings
  	public static String ArrayToString(String[] array) {
  		return String.join(" , ", array);
  	}
  	public static String[] generateArrayString(String str,String Pattern) {
  		return str.split(Pattern);
  	}
  	public int getSizeArray(String[] array) {
  		return array.length;//Retornando o tamanho do Array
  	}
    public static String[] generateStringArray(String enunciado, int count) {
    	String[] result=new String[count];
    	
    	for(int i=0;i<count;i++) {
    		System.out.println(enunciado);
    		result[i]=reading();
    	}
    	return result;
    } 
    
  	
  	//=================================================> Teste Iniciais (Apenas para uso se necessário)
    public static int getSizeString(String data) {
  		return data.length();//Retornando o tamanho da String
  	}
  	
  	public static int transformDate(String date) {//Transforma a String Data em int para gravar 
  		return Integer.parseInt(date.replace("/",""));//Retorna com int
  	}
  	public String regenerateDate(int number) {//Recupera a String Data a partir de um int
  		StringBuilder sb = new StringBuilder();//Instancia um StringBuilder
  		sb.append("");
  				//Dia ---> DD/
  		sb.append(Integer.toString(number).substring(0, 2).concat("/").
  				//Mês ---> MM/
  				concat(Integer.toString(number).substring(2, 4).concat("/")).
  				//Ano ---> AAAA
  				concat(Integer.toString(number).substring(4)));
  		return sb.toString();//Retorna a String recuperada
  	}
  	
  	public static void teste() {
  		String datetime = "12/16/2022 01:10:00 PM";
  		char[] date= {(char)Integer.parseInt(datetime.replaceAll("[^0-9]", "").substring(0, 5)),
  				      (char)Integer.parseInt(datetime.replaceAll("[^0-9]", "").substring(6, 10)),
  				      (char)Integer.parseInt(datetime.replaceAll("[^0-9]", "").substring(10))};
  		for (char c: date) {
  			System.out.println((int)c);
  		}
  	}
  	public static void teste04() {
	  	String timestamp="12/16/2012 12:10:00 PM";
		System.out.println(timestamp);	
		String newtimestamp=timestamp.substring(3, 5)+"/"+timestamp.substring(0, 2)+"/"+timestamp.substring(6,10)+" "+timestamp.substring(11);
		System.out.println(dateToString(newtimestamp));
		LocalDate data=LocalDate.parse(newtimestamp.substring(0,10),DateTimeFormatter.ofPattern("dd/MM/yyyy"));
		System.out.println(data);
  	}
  	
}
