package test;

import java.io.*;
import java.util.*;
import java.util.Arrays.*;
import java.lang.*;
import javax.xml.*;

/*
//Procurar substituto
import javax.xml.bind.*;
import javax.xml.bind.DatatypeConverter.*;

public static String byteHex(byte[] b){
  DatatypeConverter byteHex;
  return byteHex.printHexBinary(b);
}
public static byte[] stringByte(String hex){
  DatatypeConverter stringByte;
  return stringByte.parseHexBinary(hex) ;
}
*/

public class Snippet {	
	
	public static String hexBit(String hex){
	  //usar regex para verificar se 
	  //a String é composta somente por
	  //caracteres de 0 a F
	  
	  hex = hex.replaceAll("0", "0000");
	  hex = hex.replaceAll("1", "0001");
	  hex = hex.replaceAll("2", "0010");
	  hex = hex.replaceAll("3", "0011");
	  hex = hex.replaceAll("4", "0100");
	  hex = hex.replaceAll("5", "0101");
	  hex = hex.replaceAll("6", "0110");
	  hex = hex.replaceAll("7", "0111");
	  hex = hex.replaceAll("8", "1000");
	  hex = hex.replaceAll("9", "1001");
	  hex = hex.replaceAll("A", "1010");
	  hex = hex.replaceAll("B", "1011");
	  hex = hex.replaceAll("C", "1100");
	  hex = hex.replaceAll("D", "1101");
	  hex = hex.replaceAll("E", "1110");
	  hex = hex.replaceAll("F", "1111");
	  
	  return hex;
	}
	
	public static String bitHex(String bit){
	  //usar regex para verificar se 
	  //a String é composta somente por
	  //0 e 1
	  
	  //replica reversa de hexBit não funciona
	
	  return bit;
	}
	public static void main(String[] args) {
		System.out.println(hexBit("AF34B8"));
		System.out.println(bitHex(hexBit("AF34B8")));
		
	}
}

