package Practice;//Nome do Subprojeto

/**
 * @version 1_2025_02_06
 * @author Gabriel da Silva Cassino
 */


import Practice.Object_X;

import java.text.*;
import java.util.*;
import java.sql.*;
import java.time.*;
import java.time.format.*;

//Herança para facilitar gerencia na arvore e index
public class Object_X_ID extends Object_X{
	
	private int id_object;
	
	//Constructors
	public Object_X_ID(String name, String chinese_id, LocalDate register, int id_object/*, Object_X object*/) {
		
		super(name, chinese_id, register);//Aproveitando a classe-mae
		
		this.id_object = id_object;
		
	}
	public Object_X_ID(String name, String chinese_id, int id_object/*, Object_X object*/) {
		
		super(name, chinese_id);//Aproveitando a classe-mae
		
		this.id_object = id_object;
		
	}
	public Object_X_ID(Object_X X, int id_object/*, Object_X object*/) {
		
		super(X.getName(), X.getChinese_id());//Aproveitando a classe-mae
		
		this.id_object = id_object;
		
	}
	
	//Settter
	public void setID(int id_object) {
		this.id_object = id_object;
	}
	
	//Getters
	public int getID() {
		return id_object;
	}
	
	public Object_X getObject_X() {
		
		return new Object_X(super.getName(),super.getChinese_id());//Aproveitando a classe-mae
	
	}
	
	//ToString       
    public String printObject() {
    	return "\nID ------: "+this.getID()+
    			super.printObject(); //Aproveitando a classe-mae
    }
	
}
