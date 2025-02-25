/*
 Criado em 15-02-2025 (Created on 15-02-2025)
 
PT-BR: Ele foi criado para me treinar depois que uma ideia surgiu apos um desafio para mim. 
	   Bons estudos, espero que o ajude em sua jornada
	   
EN-US: It's created to train myself after an idea came after a challenge to me.
	   Happy studying, I hope it helps you on your journey.
 */

import java.nio.*;
import java.lang.*;
import java.math.*;
import java.nio.charset.*;
import java.util.*;
import java.util.stream.*;

public class Convert_Input {

	public static void main(String[] args) {//Main
		
		String Phrase ="";//Empty String (String vazia)
		
		//To get data input from user (Para obter dados de entrada do usuário)
		Scanner Reader = new Scanner(System.in);
		
		//Se o idioma do sistema for Português(If the system language is Portuguese)
		if (System.getProperty("user.language")=="pt"){
			System.out.println("Por favor insira o texto desejado:");//Pergunta ao usuário
			Phrase = Reader.nextLine();//Coleta a entrada de dados do Teclado
			
		}else {//If the system language is different from Portuguese
			System.out.println("Please enter the desired text:");//Ask the user(Pergunta ao usuário)
			//Getting values from keyboard data input(Coleta a entrada de dados do Teclado)
			Phrase = Reader.nextLine();
		}
	
		System.out.println(Phrase);//Print Input to FeedBack(Exibe para Feedback)
		
		//Transform String on Byte Array(Transformar String em Byte Array)
		System.out.println(Phrase.getBytes(StandardCharsets.UTF_8));
		
		//get Binary String From Byte Array(obter string binária de vetor de bytes)
		System.out.println(getStringByByte(Phrase.getBytes(StandardCharsets.UTF_8)));
		
		//Recovery String from Byte Array(Recuperação de String de Byte Array)
		System.out.println(new String(Phrase.getBytes(StandardCharsets.UTF_8)));
	}
	
	//Recovery String from Byte Array(Recuperação de String de Byte Array)
	public static String getStringByByte(byte[] bytes){
	    StringBuilder ret  = new StringBuilder();
	    if(bytes != null){
	        for (byte b : bytes) {
	            ret.append(Integer.toBinaryString(b & 255 | 256).substring(1));
	        }
	    }
	  //Return the Restored String(Retorna a String Restaurada)
	    return ret.toString();
	}    
		
}
