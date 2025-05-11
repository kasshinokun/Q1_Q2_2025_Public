package estagio2.Escrita;

import java.io.IOException;
import java.io.RandomAccessFile;

import estagio1.EscritorArquivo;
import estagio1.leitura.Functions;
import estagio1.leitura.LeitorArquivo;
import object.DataIndex;

public class EscritorUpdateIndex {
	public static DataIndex newObject(int Key,DataIndex obj,String pathIndex,String pathDb) throws IOException {
		boolean condition=false;
		int countList=0;
		int operation=0;//Condicionador interno
		
		if(Key==0) {
			 
			//recebe o valor presente no cabeçalho
			int ID=LeitorArquivo.getHeader(pathIndex);
			//ID é incrementada em 1 por ser novo registro 
			Key=(++ID);

			operation=1;//Configura a operação
		}
		do {
			if(operation==1) {
				System.out.println("\nID Registro---------------------------> "+Key);
				
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
				obj.setLighting_condition(Functions.generateStringArray("Condição de iluminação----------------> ",countList));
				
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
				obj.setCrash_type(Functions.generateStringArray("Tipo de acidente----------------------> ",countList));
					
				System.out.println("\nInterseção relacionada i--------------> (USE S para Sim e N para Não)");
				obj.setIntersection_related_i(Functions.getBooleanFromString(Functions.reading()));
				
				do {
					System.out.println("Danos(Faixa de Dano Financeiro--------> ");
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
				obj.setMost_severe_injury(Functions.generateStringArray("Ferimento mais grave------------------> ",countList));
					
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
				System.out.println("\nID Registro---------------------------> "+Key);
				
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
				obj.setLighting_condition(Functions.generateStringArray("Condição de iluminação----------------> ",countList));
				
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
				obj.setCrash_type(Functions.generateStringArray("Tipo de acidente----------------------> ",countList));
					
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
				obj.setMost_severe_injury(Functions.generateStringArray("Ferimento mais grave------------------> ",countList));
					
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
			
			System.out.println("\nID Registro---------------------------> "+Key);
			System.out.println(obj.toStringObject());	 
			
			condition=true;
			
		}while(condition==false);
		
		return obj;
		
		
	}
	//========================================Testar logica assim que possivel
	public static void updateRegistry(int ID,long pointerKey, byte[] bytearray,String pathDb)
			throws IOException{
				
		RandomAccessFile rafIndexedData=new RandomAccessFile(pathDb,"rw");
		
		rafIndexedData.seek(pointerKey);
		//Processos apenas por causa do reuso
		boolean lapide=rafIndexedData.readBoolean();
		
		int tamanho=rafIndexedData.readInt();
		
		EscritorIndex.writeRafIndexedData(pointerKey, bytearray,lapide,tamanho,rafIndexedData);
		
		
	}
	//========================================Testar logica assim que possivel
    public static void updateOnDeleteRegistry(long pointerKey,long pointerIndex, byte[] bytearray,int ID,String pathDb,String pathIndex)throws IOException{

    	RandomAccessFile rafIndexedData=new RandomAccessFile(pathDb,"rw");
    	
    	rafIndexedData.seek(pointerKey);
    	
    	rafIndexedData.writeBoolean(false);
    	
    	long fimdearquivo=LeitorArquivo.find_end(rafIndexedData);
		
		int tamanho =bytearray.length;
		
		EscritorIndex.writeRafIndexedData(fimdearquivo, bytearray,true,tamanho,rafIndexedData);
		
		updateIndex(true,new RandomAccessFile(pathIndex,"rw"),fimdearquivo,pointerIndex);
		
		
	}
    //========================================Testar logica assim que possivel
    public static void updateIndex(boolean lapide,RandomAccessFile rafIndex,long pointerRegistry,long pointerIndex)throws IOException{
		
		rafIndex.seek(pointerIndex);//busca a posição designada no arquivo
		
		int ID_Registro=rafIndex.readInt();//Grava a ID do registro
		
		rafIndex.writeLong(pointerRegistry);//Grava a posição do registro
		
		rafIndex.writeBoolean(lapide);//escreve o boolean lapide
	}
}
