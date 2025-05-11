package object;




	import java.io.ByteArrayInputStream;
	import java.io.ByteArrayOutputStream;
	import java.io.DataInputStream;
	import java.io.DataOutputStream;
	import java.io.IOException;
	import java.text.SimpleDateFormat;
	import java.time.LocalDate;
	import java.time.format.DateTimeFormatter;
	import java.util.ArrayList;
	import java.util.List;
	import java.util.Locale;

	import estagio1.leitura.Functions;

	public class DataTreeObject {
		private SimpleDateFormat LOCALDATEFORMATTER=new SimpleDateFormat("dd/MM/yyyy hh:mm:ss aa",Locale.getDefault());
		private DateTimeFormatter DATEFORMATTER =DateTimeFormatter.ofPattern("dd/MM/yyyy");
		private SimpleDateFormat HOURFORMATER = new SimpleDateFormat("HH:mm:ss",Locale.getDefault());
		
		private int ID_registro;
		private String crash_date;
		private LocalDate data;
		private String traffic_control_device;	
		private String weather_condition;
		private String[] lighting_condition;
		private String first_crash_type;
		private String trafficway_type;	
		private String alignment;	
		private String roadway_surface_cond;	
		private String road_defect;	
		private String[] crash_type;
		private boolean intersection_related_i;
		private String damage;
		private String prim_contributory_cause;
		private int  num_units;
		private String[] most_severe_injury;
		private float injuries_total;
		private float injuries_fatal;
		private float injuries_incapacitating;
		private float injuries_non_incapacitating;
		private float injuries_reported_not_evident;
		private float injuries_no_indication;
		private int crash_hour;
		private int crash_day_of_week;
		private int crash_month;
		
		public DataTreeObject() {
			this.ID_registro = 0;
			this.crash_date="";
			this.data=LocalDate.parse("01/01/1900",DATEFORMATTER);
			this.traffic_control_device = "";
			this.weather_condition = "";
			this.first_crash_type = "";
			this.trafficway_type = "";
			this.alignment = "";
			this.roadway_surface_cond = "";
			this.road_defect = "";
			this.crash_type = crash_type;
			this.intersection_related_i=false;
			this.damage = "";
			this.prim_contributory_cause = "";
			this.num_units = 0;
			this.injuries_total = 0;
			this.injuries_fatal = 0;
			this.injuries_incapacitating = 0;
			this.injuries_non_incapacitating = 0;
			this.injuries_reported_not_evident = 0;
			this.injuries_no_indication = 0;
			this.crash_hour = 0;
			this.crash_day_of_week = 0;
			this.crash_month = 0;
		}
		public DataTreeObject(int id,String crash_date,LocalDate data, String traffic_control_device,
				String weather_condition, String[] lighting_condition, String first_crash_type, String trafficway_type,
				String alignment, String roadway_surface_cond, String road_defect, String[] crash_type,
				boolean intersection_related_i, String damage, String prim_contributory_cause, int num_units,
				String[] most_severe_injury, float injuries_total, float injuries_fatal, float injuries_incapacitating,
				float injuries_non_incapacitating, float injuries_reported_not_evident, float injuries_no_indication,
				int crash_hour, int crash_day_of_week, int crash_month) {
			this.ID_registro = id;
			this.crash_date=crash_date;
			this.data=data;
			this.traffic_control_device = traffic_control_device;
			this.weather_condition = weather_condition;
			this.lighting_condition =lighting_condition;
			this.first_crash_type = first_crash_type;
			this.trafficway_type = trafficway_type;
			this.alignment = alignment;
			this.roadway_surface_cond = roadway_surface_cond;
			this.road_defect = road_defect;
			this.crash_type = crash_type;
			this.intersection_related_i=intersection_related_i;
			this.damage = damage;
			this.prim_contributory_cause = prim_contributory_cause;
			this.num_units = num_units;
			this.most_severe_injury = most_severe_injury;
			this.injuries_total = injuries_total;
			this.injuries_fatal = injuries_fatal;
			this.injuries_incapacitating = injuries_incapacitating;
			this.injuries_non_incapacitating = injuries_non_incapacitating;
			this.injuries_reported_not_evident = injuries_reported_not_evident;
			this.injuries_no_indication = injuries_no_indication;
			this.crash_hour = crash_hour;
			this.crash_day_of_week = crash_day_of_week;
			this.crash_month = crash_month;
		}
		//Construtor baseado em Int,Float,String e Boolean (e Metodos Internos Fase 1)
		public DataTreeObject(int id,String crash_date, String traffic_control_device,
				String weather_condition, String lighting_condition, String first_crash_type, String trafficway_type,
				String alignment, String roadway_surface_cond, String road_defect, String crash_type,
				boolean intersection_related_i, String damage, String prim_contributory_cause, int num_units,
				String most_severe_injury, float injuries_total, float injuries_fatal, float injuries_incapacitating,
				float injuries_non_incapacitating, float injuries_reported_not_evident, float injuries_no_indication,
				int crash_hour, int crash_day_of_week, int crash_month) {
			super();
			try {
				this.ID_registro = id;
				this.setCrash_dateFromTimestamp(crash_date);
				this.traffic_control_device = traffic_control_device;
				this.weather_condition = weather_condition;
				this.lighting_condition = Functions.generateArrayString(lighting_condition,",");// String[]  lighting_condition
				this.first_crash_type = first_crash_type;
				this.trafficway_type = trafficway_type;
				this.alignment = alignment;
				this.roadway_surface_cond = roadway_surface_cond;
				this.road_defect = road_defect;
				this.crash_type = Functions.generateArrayString(crash_type,"/");//String[] crash_type,
				this.intersection_related_i=intersection_related_i;
				this.damage = damage;
				this.prim_contributory_cause = prim_contributory_cause;
				this.num_units = num_units;
				this.setMost_severe_injury(Functions.generateArrayString(most_severe_injury,","));
				this.injuries_total = injuries_total;
				this.injuries_fatal = injuries_fatal;
				this.injuries_incapacitating = injuries_incapacitating;
				this.injuries_non_incapacitating = injuries_non_incapacitating;
				this.injuries_reported_not_evident = injuries_reported_not_evident;
				this.injuries_no_indication = injuries_no_indication;
				this.crash_hour = crash_hour;
				this.crash_day_of_week = crash_day_of_week;
				this.crash_month = crash_month;
			}catch(Exception e) {
				e.printStackTrace();
			}
			
		}
		//Construtor para o Arquivo e id - Fase 2
		public DataTreeObject(String[] list,int i) {
			try {
				this.ID_registro = i;
				this.setCrash_dateFromTimestamp(list[0].substring(3, 5)+"/"+list[0].substring(0, 2)+"/"+list[0].substring(6,10)+" "+list[0].substring(11));
				this.traffic_control_device = list[1];
				this.weather_condition = list[2];
				this.lighting_condition = Functions.generateArrayString(list[3],",");// String[] lighting_condition
				this.first_crash_type = list[4];
				this.trafficway_type = list[5];
				this.alignment = list[6];
				this.roadway_surface_cond = list[7];
				this.road_defect = list[8];
				this.crash_type = Functions.generateArrayString(list[9],"/");//String[] crash_type,
				this.setString_Intersection_related_i(list[10]);//intersection_related_i 
				this.damage = list[11];
				this.prim_contributory_cause = list[12];
				this.num_units = Integer.parseInt(list[13]);
				this.setMost_severe_injury(Functions.generateArrayString(list[14],","));
				this.injuries_total = Float.parseFloat(list[15]);
				this.injuries_fatal = Float.parseFloat(list[16]);
				this.injuries_incapacitating = Float.parseFloat(list[17]);
				this.injuries_non_incapacitating = Float.parseFloat(list[18]);
				this.injuries_reported_not_evident = Float.parseFloat(list[19]);
				this.injuries_no_indication = Float.parseFloat(list[20]);
				this.crash_hour = Integer.parseInt(list[21]);
				//this.crash_day_of_week = Integer.parseInt(list[22]);
				//this.crash_month = Integer.parseInt(list[23]);
				
			}catch(Exception e) {
				e.printStackTrace();
			}
		}
		
		//Setters auxiliados por Classe externa
		public void setCrash_dateFromTimestamp(String crash_date)throws Exception{
			//System.out.println("aqui 1D");
			LocalDate date=LocalDate.parse(crash_date.substring(0,10),DATEFORMATTER);
			//System.out.println("aqui 1E1");
			this.setData(date);
			//System.out.println("aqui 1E2");
			//System.out.println(date);
			//System.out.println("aqui 1E4");
			this.setCrash_day_of_week(Functions.getDayWeek(date));
			//System.out.println("aqui 1E5");
			this.setCrash_month(Functions.getNumMonth(date));
			//System.out.println("aqui 1E6");
			
			this.crash_date = crash_date;
			//System.out.println("aqui 1F");
		}
		public void setString_Intersection_related_i(String root) {
			this.setIntersection_related_i(Functions.getBooleanFromString(root));
		}
		
		//Setters Internos
		public void setID_registro(int iD_registro) {
			ID_registro = iD_registro;
		}
		public void setCrash_date(String crash_date) {
			this.crash_date = crash_date;
		}
		public void setData(LocalDate data) {
			this.data = data;
		}
		public void setTraffic_control_device(String traffic_control_device) {
			this.traffic_control_device = traffic_control_device;
		}
		public void setWeather_condition(String weather_condition) {
			this.weather_condition = weather_condition;
		}
		public void setLighting_condition(String[] lighting_condition) {
			this.lighting_condition = lighting_condition;
		}
		public void setFirst_crash_type(String first_crash_type) {
			this.first_crash_type = first_crash_type;
		}
		public void setTrafficway_type(String trafficway_type) {
			this.trafficway_type = trafficway_type;
		}
		public void setAlignment(String alignment) {
			this.alignment = alignment;
		}
		public void setRoadway_surface_cond(String roadway_surface_cond) {
			this.roadway_surface_cond = roadway_surface_cond;
		}
		public void setRoad_defect(String road_defect) {
			this.road_defect = road_defect;
		}
		public void setCrash_type(String[] crash_type) {
			this.crash_type = crash_type;
		}
		public void setIntersection_related_i(boolean intersection_related_i) {
			this.intersection_related_i = intersection_related_i;
		}
		public void setDamage(String damage) {
			this.damage = damage;
		}
		public void setPrim_contributory_cause(String prim_contributory_cause) {
			this.prim_contributory_cause = prim_contributory_cause;
		}
		public void setNum_units(int num_units) {
			this.num_units = num_units;
		}
		public void setMost_severe_injury(String[] most_severe_injury) {
			this.most_severe_injury = most_severe_injury;
		}
		public void setInjuries_total(float injuries_total) {
			this.injuries_total = injuries_total;
		}
		public void setInjuries_fatal(float injuries_fatal) {
			this.injuries_fatal = injuries_fatal;
		}
		public void setInjuries_incapacitating(float injuries_incapacitating) {
			this.injuries_incapacitating = injuries_incapacitating;
		}
		public void setInjuries_non_incapacitating(float injuries_non_incapacitating) {
			this.injuries_non_incapacitating = injuries_non_incapacitating;
		}
		public void setInjuries_reported_not_evident(float injuries_reported_not_evident) {
			this.injuries_reported_not_evident = injuries_reported_not_evident;
		}
		public void setInjuries_no_indication(float injuries_no_indication) {
			this.injuries_no_indication = injuries_no_indication;
		}
		public void setCrash_hour(int crash_hour) {
			this.crash_hour = crash_hour;
		}
		public void setCrash_day_of_week(int crash_day_of_week) {
			this.crash_day_of_week = crash_day_of_week;
		}
		public void setCrash_month(int crash_month) {
			this.crash_month = crash_month;
		}
		
		//Getters auxiliados por Classe externa
		public String getLighting_condition_toString() {
			return Functions.ArrayToString(this.getLighting_condition());
		}
		public String getCrash_type_toString() {
			return Functions.ArrayToString(this.getCrash_type());
		}
		public String getString_Intersection_related_i() {
			return Functions.getStringFromBoolean(this.isIntersection_related_i());
		}
		public String getMost_severe_injury_toString() {
			return Functions.ArrayToString(this.getMost_severe_injury());
		}
		//Getters Internos
		public int getID_registro() {
			return ID_registro;
		}
		public String getCrash_date() {
			return crash_date;
		}
		public LocalDate getData() {
			return data;
		}
		public String getTraffic_control_device() {
			return traffic_control_device;
		}
		public String getWeather_condition() {
			return weather_condition;
		}
		public String[] getLighting_condition() {
			return lighting_condition;
		}
		public String getFirst_crash_type() {
			return first_crash_type;
		}
		public String getTrafficway_type() {
			return trafficway_type;
		}
		public String getAlignment() {
			return alignment;
		}
		public String getRoadway_surface_cond() {
			return roadway_surface_cond;
		}
		public String getRoad_defect() {
			return road_defect;
		}
		public String[] getCrash_type() {
			return crash_type;
		}
		public boolean isIntersection_related_i() {
			return intersection_related_i;
		}
		public String getDamage() {
			return damage;
		}
		public String getPrim_contributory_cause() {
			return prim_contributory_cause;
		}
		public int getNum_units() {
			return num_units;
		}
		public String[] getMost_severe_injury() {
			return most_severe_injury;
		}
		public float getInjuries_total() {
			return injuries_total;
		}
		public float getInjuries_fatal() {
			return injuries_fatal;
		}
		public float getInjuries_incapacitating() {
			return injuries_incapacitating;
		}
		public float getInjuries_non_incapacitating() {
			return injuries_non_incapacitating;
		}
		public float getInjuries_reported_not_evident() {
			return injuries_reported_not_evident;
		}
		public float getInjuries_no_indication() {
			return injuries_no_indication;
		}
		public int getCrash_hour() {
			return crash_hour;
		}
		public int getCrash_day_of_week() {
			return crash_day_of_week;
		}
		public int getCrash_month() {
			return crash_month;
		}
		
		//toString da Classe
		//ToString
		public String toStringObject() {
			return
			"\nID Registro---------------------------> "+this.getID_registro()+
			"\nData do Acidente----------------------> "+this.getCrash_date()+
			"\nData por LocalDate--------------------> "+this.getData()+
			"\nDispositivo de controle de tráfego----> "+this.getTraffic_control_device()+
			"\nCondição climática--------------------> "+this.getWeather_condition()+
			"\nCondição de iluminação----------------> "+Functions.ArrayToString(this.getLighting_condition())+
			"\nTipo de primeira colisão--------------> "+this.getFirst_crash_type()+
			"\nTipo de via de tráfego----------------> "+this.getTrafficway_type()+
			"\nAlinhamento---------------------------> "+this.getAlignment()+
			"\nCondição da superfície da via---------> "+this.getRoadway_surface_cond()+
			"\nDefeito na estrada--------------------> "+this.getRoad_defect()+
			"\nTipo de acidente----------------------> "+Functions.ArrayToString(this.getCrash_type())+
			"\nInterseção relacionada i--------------> "+this.getString_Intersection_related_i()+
			"\nDanos---------------------------------> "+this.getDamage()+
			"\nCausa contributiva primária-----------> "+this.getPrim_contributory_cause()+
			"\nNumero de Unidades--------------------> "+this.getNum_units()+
			"\nFerimento mais grave------------------> "+Functions.ArrayToString(this.getMost_severe_injury())+
			"\nTotal de ferimentos-------------------> "+this.getInjuries_total()+
			"\nFerimentos fatais---------------------> "+this.getInjuries_fatal()+
			"\nLesões incapacitantes-----------------> "+this.getInjuries_incapacitating()+
			"\nLesões não incapacitantes-------------> "+this.getInjuries_non_incapacitating()+
			"\nLesões relatadas não evidentes--------> "+this.getInjuries_reported_not_evident()+
			"\nLesões sem indicação------------------> "+this.getInjuries_no_indication()+
			"\nHora do acidente----------------------> "+this.getCrash_hour()+
			"\nDia da Semana do acidente-------------> "+this.getCrash_day_of_week()+
			"\nMês do acidente-----------------------> "+this.getCrash_month();
			
		}
		
		//======================================================> Byte Array
		public byte[] toByteArray() throws IOException {
			
			//Instanciando Stream e configurando
	        ByteArrayOutputStream baos = new ByteArrayOutputStream();
	        
	        DataOutputStream dos = new DataOutputStream(baos);
	        
	        //Adicionando atributos no stream a partir do objeto
		    
	        dos.writeInt(this.getID_registro());
	        
		    dos.writeUTF(this.getCrash_date());
		    
		    dos.writeLong(this.getData().toEpochDay());
		    
		    dos.writeUTF(this.getTraffic_control_device());
				
		    dos.writeUTF(this.getWeather_condition());
		    
		    dos.writeInt(this.getLighting_condition().length);//tamanho do array
		    		    
			dos.writeUTF(this.getLighting_condition_toString());
			
			dos.writeUTF(this.getFirst_crash_type());
			
			dos.writeUTF(this.getTrafficway_type());
			
			dos.writeUTF(this.getAlignment());	
			
			dos.writeUTF(this.getRoadway_surface_cond());
			
			dos.writeUTF(this.getRoad_defect());
			
			dos.writeInt(this.getCrash_type().length);//tamanho do array
						
			dos.writeUTF(this.getCrash_type_toString());
			
			dos.writeUTF(this.getString_Intersection_related_i());
			
			dos.writeUTF(this.getDamage());
			
			dos.writeUTF(this.getPrim_contributory_cause());
			
			dos.writeInt(this.getNum_units());
			
			dos.writeInt(this.getMost_severe_injury().length);//Tamanho do array
			
			dos.writeUTF(this.getMost_severe_injury_toString());
			
			dos.writeFloat(this.getInjuries_total());
			
			dos.writeFloat(this.getInjuries_fatal());
			
			dos.writeFloat(this.getInjuries_incapacitating());
			
			dos.writeFloat(this.getInjuries_non_incapacitating());
			
			dos.writeFloat(this.getInjuries_reported_not_evident());
			
			dos.writeFloat(this.getInjuries_no_indication());
			
			dos.writeInt(this.getCrash_hour());
			
			dos.writeInt(this.getCrash_day_of_week());
			
			dos.writeInt(this.getCrash_month());
			
			return baos.toByteArray();//retornando como vetor de bytes
		
		}
		public void fromByteArray(byte[] data) throws IOException {
	        
			ByteArrayInputStream bais = new ByteArrayInputStream(data);
	        DataInputStream dis = new DataInputStream(bais);
			
	        this.setID_registro(dis.readInt());
	        this.setCrash_date(dis.readUTF());
	        this.setData(LocalDate.ofEpochDay(dis.readLong()));
	        this.setTraffic_control_device(dis.readUTF());
	        this.setWeather_condition(dis.readUTF());
			int value1=dis.readInt();//Tamanho lista ou array
	        this.setLighting_condition(Functions.generateArrayString(dis.readUTF(),",")); 
			this.setFirst_crash_type(dis.readUTF()); 
			this.setTrafficway_type(dis.readUTF()); 
			this.setAlignment(dis.readUTF()); 
			this.setRoadway_surface_cond(dis.readUTF()); 
			this.setRoad_defect(dis.readUTF()); 
			int value2=dis.readInt();//Tamanho lista ou array
			this.setCrash_type(Functions.generateArrayString(dis.readUTF(),",")); 
			this.setIntersection_related_i(Functions.getBooleanFromString(dis.readUTF()));
			this.setDamage(dis.readUTF()); 
			this.setPrim_contributory_cause(dis.readUTF()); 
			this.setNum_units(dis.readInt());
			int value3=dis.readInt();//Tamanho lista ou array
			this.setMost_severe_injury(Functions.generateArrayString(dis.readUTF(),","));
	        this.setInjuries_total(dis.readFloat());
	        this.setInjuries_fatal(dis.readFloat()); 
			this.setInjuries_incapacitating(dis.readFloat());
			this.setInjuries_non_incapacitating(dis.readFloat());
			this.setInjuries_reported_not_evident(dis.readFloat());
			this.setInjuries_no_indication(dis.readFloat());
	        this.setCrash_hour(dis.readInt()); 
	        this.setCrash_day_of_week(dis.readInt()); 
	        this.setCrash_month(dis.readInt()); 	

	    }
	}