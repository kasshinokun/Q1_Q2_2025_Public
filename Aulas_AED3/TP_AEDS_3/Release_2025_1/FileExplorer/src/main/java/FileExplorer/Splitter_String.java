package FileExplorer;//Nome do Subprojeto

/**
 * @version 2_2025_01_31
 * @author Gabriel da Silva Cassino
 */

import java.util.*;

public class Splitter_String {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Splitter_String("Hello,World",1); 
	}
	//Splitter de String
    public static void Splitter_String(String target,int i) {//target é apenas placebo
    	//Serão 12446 vezes
    	//String target2="蒋寓琨 330902199403040015";//alvo do processo
    	//Objetivo:    <蒋寓琨> <330902199403040015>  <1994-03-04>   --->send to ObjectX class Object
    	String[] result=target.split(","); 
    	if (result.length==2){
    		System.out.println("Linha 0"+i+": "+result[0]+" "+result[1]);//Exibe "Linha 012444: ???        33092219940724001X"
    	}
    }

}
