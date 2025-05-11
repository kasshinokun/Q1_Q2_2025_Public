package estagio1;

import java.io.*;
import java.nio.charset.*;
import java.util.*;

import estagio1.leitura.DeleteProcess;
import estagio1.leitura.Functions;
import estagio1.leitura.LeitorArquivo;
import object.DataObject;
import object.*;


public class EscritorUpdateArquivo {
	
	public static void main(String[] args){
		
		String userP=System.getProperty("user.home");//Pasta do Usuario do PC
		String folder="Documents";//Local padrão
        String sep = File.separator;// Separador do sistema operacional em uso
		String folder_file="TP_AEDS_III";
		String name_file="traffic_accidents_pt_br_rev2.csv";
		String Path=userP.concat(sep+folder).concat(sep+folder_file).concat(sep+name_file);
		String Path_db="data/traffic_accidents.db";
		System.out.println("Caminho recbido: "+Path);
		
		RandomAccessFile randomAccessFile=null;
		
		DataObject obj;
		if(Functions.findFile(Path_db)){ 
			try {
	        	
				randomAccessFile = new RandomAccessFile(Path_db, "rw");
				
	        	obj=new DataObject();
	        	
	        	System.out.println(randomAccessFile.readInt());//
	        	
	        	long posicao=randomAccessFile.getFilePointer();
	        	
	        	int ID=randomAccessFile.readInt();//
	              
	            boolean lapide=randomAccessFile.readBoolean();
	            
	            int tamanho=randomAccessFile.readInt();//ler o tamanho do vetor    
	            
	            byte[] array =new byte[tamanho];
	            
	            System.out.println(LeitorArquivo.showIndex(ID,lapide,tamanho,posicao));
	            
	            randomAccessFile.read(array);
	            
	            obj.fromByteArray(array);
	            
	            System.out.println(obj.toStringObject());
	            
			}catch(Exception e) {
				
			}
		}else {
			System.out.println("Não localizei o arquivo.");
		}
		
    }
	public static void updateRegistry(long posicao, byte[] bytearray,String pathDb)
		throws IOException{
			
		RandomAccessFile randomAccessFile=new RandomAccessFile(pathDb,"rw");
		randomAccessFile.seek(posicao);
		//Processos apenas por causa do reuso
		int ID =randomAccessFile.readInt();
		boolean lapide=randomAccessFile.readBoolean();
		int tamanho=randomAccessFile.readInt();
		
		EscritorArquivo.writeRandomAccessFile(posicao,bytearray,lapide,tamanho, randomAccessFile,ID);
		
	}
        public static void updateOnDeleteRegistry(long posicao, byte[] bytearray,int ID,String pathDb)throws IOException{

		RandomAccessFile randomAccessFile=new RandomAccessFile(pathDb,"rw");
		randomAccessFile.seek(posicao+4);
		//randomAccessFile.readInt();//4 bytes
		randomAccessFile.writeBoolean(false);
		EscritorArquivo.writeRandomAccessFile(LeitorArquivo.find_end(randomAccessFile), bytearray,true, bytearray.length, randomAccessFile,ID);
			
	}
        

	public static DataObject newObject(DataObject obj)throws IOException{
		
		
		
		boolean condition=false;
		int countList=0;
		int operation=0;//Condicionador interno
		
		if(obj.getID_registro()==0) {
			//System.out.println("aqui 0A");
			//recebe o valor presente no cabeçalho+1 se for novo registro
			int ID=LeitorArquivo.getHeader("data/traffic_accidents.db");
			//System.out.println("aqui 0B");
			obj.setID_registro(++ID);
			//System.out.println("aqui 0C");
			operation=1;
		}
		do {
			if(operation==1) {
				System.out.println("\nID Registro---------------------------> "+obj.getID_registro());
				
				System.out.println("\nData do Acidente\n(Exemplo 1: 12/01/2025 00:00:00 AM)\n(Exemplo 2: 12/01/2025 00:00:00 PM)\n----------------------> ");
				String timestamp=Functions.reading();
				try {
					//System.out.println("aqui 1A");
					obj.setCrash_dateFromTimestamp(timestamp);
					//System.out.println("aqui 1B");
				}catch(Exception e) {
					System.out.println("erro");
					return null;
					
				}
				
				//System.out.println("aqui 2");
				
				System.out.println("\nDispositivo de controle de tráfego----> ");
				obj.setTraffic_control_device(Functions.reading());
				
				//System.out.println("aqui 3");
				System.out.println("\nCondição climática--------------------> ");
				obj.setWeather_condition(Functions.reading());
				
				//System.out.println("aqui 4 ");
				countList=Functions.getCountList();
				obj.setLighting_condition(Functions.generateStringList("Condição de iluminação----------------> ",countList));
				//obj.setLighting_condition(Functions.generateStringArray("Condição de iluminação----------------> ",countList));
				
				//System.out.println("aqui 5 ");
				System.out.println("\nTipo de primeira colisão--------------> ");
				//System.out.println("aqui 6");
				obj.setFirst_crash_type(Functions.reading());
							
				System.out.println("\nTipo de via de tráfego----------------> ");
				obj.setTrafficway_type(Functions.reading());
				
				System.out.println("\nAlinhamento---------------------------> ");
				obj.setAlignment(Functions.reading());
				
				System.out.println("\nCondição da superfície da via---------> ");
				obj.setRoadway_surface_cond(Functions.reading());
				
				System.out.println("\nDefeito na estrada--------------------> ");
				obj.setRoad_defect(Functions.reading());
				
				countList=Functions.getCountList();
				obj.setCrash_type(Functions.generateStringList("Tipo de acidente----------------------> ",countList));
					
				System.out.println("\nInterseção relacionada i--------------> (USE S para Sim e N para Não)");
				obj.setIntersection_related_i(Functions.getBooleanFromString(Functions.reading()));
				
				do {
					System.out.println("\nDanos(Faixa de Dano Financeiro--------> ");
					System.out.println("1) - $500 OU MENOS");
					System.out.println("2) - $501 - $1,500");
					System.out.println("3) - ACIMA $1,500");
					countList=Functions.only_Int();
				}while(countList>3||countList<1);
				String[] options={"$500 OU MENOS","$501 - $1,500","ACIMA $1,500"};
				obj.setDamage(options[countList-1]);
				
				System.out.println("\nCausa contributiva primária-----------> ");
				obj.setPrim_contributory_cause(Functions.reading());
				
				System.out.println("\nNumero de Unidades--------------------> ");
				obj.setNum_units(Functions.only_Int());
				
				countList=Functions.getCountList();
				obj.setMost_severe_injury(Functions.generateStringList("Ferimento mais grave------------------> ",countList));
					
				System.out.println("\nTotal de ferimentos-------------------> ");
				obj.setInjuries_total(Functions.only_Float());
				
				System.out.println("\nFerimentos fatais---------------------> ");
				obj.setInjuries_fatal(Functions.only_Float());
				
				System.out.println("\nLesões incapacitantes-----------------> ");
				obj.setInjuries_incapacitating(Functions.only_Float());
				
				System.out.println("\nLesões não incapacitantes-------------> ");
				obj.setInjuries_non_incapacitating(Functions.only_Float());
				
				System.out.println("\nLesões relatadas não evidentes--------> ");
				obj.setInjuries_reported_not_evident(Functions.only_Float());
				
				System.out.println("\nLesões sem indicação------------------> ");
				obj.setInjuries_no_indication(Functions.only_Float());
				
				System.out.println("\nHora do acidente----------------------> ");
				obj.setCrash_hour(Functions.only_Int());
				
				System.out.println("\nDia da Semana do acidente-------------> "+obj.getCrash_day_of_week());
				
				System.out.println("\nMês do acidente-----------------------> "+obj.getCrash_month());
				
			}else {
				System.out.println("\nID Registro---------------------------> "+obj.getID_registro());
				
				System.out.println("\nData do Acidente----------------------> "+obj.getData());
				System.out.println("Timestamp da Data do Acidente---------> "+obj.getCrash_date());
				System.out.println("Digite o novo Timestamp do Acidente---> ");
				String timestamp=Functions.reading();
				try {
					//System.out.println("aqui 1A");
					obj.setCrash_dateFromTimestamp(timestamp);
					//System.out.println("aqui 1B");
				}catch(Exception e) {
					System.out.println("erro");
					return null;
					
				}
				
				//System.out.println("aqui 2");
				
				System.out.println("\nDispositivo de controle de tráfego----> \n"+obj.getTraffic_control_device());
				obj.setTraffic_control_device(Functions.reading());
				
				//System.out.println("aqui 3");
				System.out.println("\nCondição climática--------------------> "+obj.getWeather_condition());
				obj.setWeather_condition(Functions.reading());
				
				//System.out.println("aqui 4 ");
				System.out.println("Condição de iluminação----------------> \n"+obj.getLighting_condition_toString());
				countList=Functions.getCountList();
				obj.setLighting_condition(Functions.generateStringList("Condição de iluminação----------------> ",countList));
				//obj.setLighting_condition(Functions.generateStringArray("Condição de iluminação----------------> ",countList));
				
				//System.out.println("aqui 5 ");
				System.out.println("\nTipo de primeira colisão--------------> \n"+obj.getFirst_crash_type());
				obj.setFirst_crash_type(Functions.reading());
				
				System.out.println("\nTipo de via de tráfego----------------> \n"+obj.getTrafficway_type());
				obj.setTrafficway_type(Functions.reading());
				
				System.out.println("\nAlinhamento---------------------------> \n"+obj.getAlignment());
				obj.setAlignment(Functions.reading());
				
				System.out.println("\nCondição da superfície da via---------> \n"+obj.getRoadway_surface_cond());
				obj.setRoadway_surface_cond(Functions.reading());
				
				System.out.println("\nDefeito na estrada--------------------> \n"+obj.getRoad_defect());
				obj.setRoad_defect(Functions.reading());
				
				System.out.println("Tipo de acidente----------------------> \n"+obj.getLighting_condition_toString());
				countList=Functions.getCountList();	
				obj.setCrash_type(Functions.generateStringList("Tipo de acidente----------------------> ",countList));
					
				System.out.println("\nInterseção relacionada i--------------> "+obj.getString_Intersection_related_i()+"\n(USE S para Sim e N para Não)");
				obj.setIntersection_related_i(Functions.getBooleanFromString(Functions.reading()));
				
				System.out.println("\nDanos(Faixa de Dano Financeiro--------> "+obj.getDamage());
				do {
					System.out.println("Danos(Faixa de Dano Financeiro--------> ");
					System.out.println("1) - $500 OU MENOS");
					System.out.println("2) - $501 - $1,500");
					System.out.println("3) - ACIMA $1,500");
					countList=Functions.only_Int();
				}while(countList>3||countList<1);
				String[] options={"$500 OU MENOS","$501 - $1,500","ACIMA $1,500"};
				obj.setDamage(options[countList-1]);
				
				System.out.println("\nCausa contributiva primária-----------> \n"+obj.getPrim_contributory_cause());
				obj.setPrim_contributory_cause(Functions.reading());
				
				System.out.println("\nNumero de Unidades--------------------> ");
				obj.setNum_units(Functions.only_Int());
				
				System.out.println("\nFerimento mais grave------------------> "+obj.getMost_severe_injury_toString());
				countList=Functions.getCountList();
				obj.setMost_severe_injury(Functions.generateStringList("Ferimento mais grave------------------> ",countList));
					
				System.out.println("\nTotal de ferimentos-------------------> "+obj.getInjuries_total());
				obj.setInjuries_total(Functions.only_Float());
				
				System.out.println("\nFerimentos fatais---------------------> "+obj.getInjuries_fatal());
				obj.setInjuries_fatal(Functions.only_Float());
				
				System.out.println("\nLesões incapacitantes-----------------> "+obj.getInjuries_incapacitating());
				obj.setInjuries_incapacitating(Functions.only_Float());
				
				System.out.println("\nLesões não incapacitantes-------------> "+obj.getInjuries_non_incapacitating());
				obj.setInjuries_non_incapacitating(Functions.only_Float());
				
				System.out.println("\nLesões relatadas não evidentes--------> "+obj.getInjuries_reported_not_evident());
				obj.setInjuries_reported_not_evident(Functions.only_Float());
				
				System.out.println("\nLesões sem indicação------------------> "+obj.getInjuries_no_indication());
				obj.setInjuries_no_indication(Functions.only_Float());
				
				System.out.println("\nHora do acidente----------------------> "+obj.getCrash_hour());
				obj.setCrash_hour(Functions.only_Int());
				
				System.out.println("\nDia da Semana do acidente-------------> "+obj.getCrash_day_of_week());
				
				System.out.println("\nMês do acidente-----------------------> "+obj.getCrash_month());
				
				
			}
			
			
			System.out.println(obj.toStringObject());	 
			
			condition=true;
			
		}while(condition==false);
		
		return obj;
		
		
	}
}