package connection;

import java.util.*;

/**
 * @version 1_2025_01_06
 * @author Gabriel da Silva Cassino
 */
public class functions_op {
    public static void state_connection(int state,int lang){
        if (state==0){//JDBC Driver wasn't installed
            if(lang==1){//message in English-US
                System.out.println("JDBC Driver wasn't installed");
                System.out.println("Please install required JDBC Driver.");
            }
            else{//Mensagem em Portugues-BR
                System.out.println("English-USA");
                System.out.println("English-USA");
            }
        }else if (state==1){//connection wasn't establised with database
            if(lang==1){//message in English-US
                System.out.println("The connection wasn't establised with database");
                System.out.println("Please, try again.");
            }
            else{//Mensagem em Portugues-BR
                System.out.println("English-USA");
                System.out.println("English-USA");
            }
        }else if (state==2){// Fail if it have problems on execution process
            if(lang==1){//message in English-US
                System.out.println("Error was found on execution.");
                System.out.println("Please, try again.");
            }
            else{//Mensagem em Portugues-BR
                System.out.println("English-USA");
                System.out.println("English-USA");
            }
        }
        else if (state==3){//Feedback if opened connection with sucess
            if(lang==1){//message in English-US
                System.out.println("The connection was opened successfully");
                System.out.println("Starting services...");
            }
            else{//Mensagem em Portugues-BR
                System.out.println("English-USA");
                System.out.println("English-USA");
            }
        }else if (state==4){//Feedback if closed connection with sucess
            if(lang==1){//message in English-US
                System.out.println("The connection was closed successfully");
                System.out.println("Process Done.");
            }
            else{//Mensagem em Portugues-BR
                System.out.println("English-USA");
                System.out.println("English-USA");
            }
        }
        else{ //condition out range operation
            if(lang==1){//message in English-US
                System.out.println("Condition Out of Range Operation.");
                System.out.println("Please, try again.");
            }
            else{//Mensagem em Portugues-BR
                System.out.println("English-USA");
                System.out.println("English-USA");
            }
        }
    
    }
    public static String invalid_argument(int lang){
        if(lang==1){//message in English-US
            return "The argument isn't valid to create object.";
        }
        else{//Mensagem em Portugues-BR
            return "O argumento nao e valido para criar objeto.";
        }
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
