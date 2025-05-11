package object;//nome do package

//importação de funções do package
import functions.*;
//importação de bibliotecas
import java.io.*;
import java.time.*;



public class Winner {
    
    private int tour_y;//Ano
    private String date;//Data do Evento
    private int tour_n;//Numero do Tour de France
    private String tour_w;//Nome do vencedor
    private String rider_c;//Pais do Vencedor
    private String rider_t;//Equipe vencedora
    private int tour_l;//Distancia do Tour de France(km)
    private int rider_a;//idade
    private float rider_b;//BMI	do ciclista
    private int rider_w;//Peso(Kg)
    private double rider_h;//Altura (meters)		
    private String rt_PPS;//Tipo do Atleta
    private String crt_PPS="";//Modalidade do Atleta			
    
    public Winner(){//construtor padrão para print(teste de algoritmo) 
        
        this.setTour_y(2023,1);//Ano
        this.set_Date("01/01/2023");//Data
        this.setTour_n(110);//Numero do Tour de France
        this.setTour_w("Jonas Vingegaard");//Nome do vencedor
        this.setRider_c("Denmark");//Nome do país
        this.setRider_t("Team Jumbo Visma");//Equipe Vencedora
        this.setTour_l(3406);//Distancia do Tour de France(km)
        this.setRider_a(25);//Idade
        this.setRider_b(19.6F);//BMI	
        this.setRider_w(60);//Peso(Kg)
        this.setRider_h(1.749635531D);//Altura (metros)		
        this.setRt_PPS("climber");//Tipo do Ciclista
        this.setCrt_PPS("");//Modalidade do Atleta
    }
    public Winner(int tour_y,int condition,String date,int tour_n,String tour_w,String rider_c,String rider_t,int tour_l,int rider_a,float rider_b,int rider_w,double rider_h,String rt_PPS,String crt_PPS){//Constructor from setters
        
        setTour_y(tour_y,condition);//Ano
        set_Date(date);//Data
        setTour_n(tour_n);//Numero do Tour de France
        setTour_w(tour_w);//Nome do vencedor
        setRider_c(rider_c);//Nome do país
        setRider_t(rider_t);//Equipe Vencedora
        setTour_l(tour_l);//Distancia do Tour de France(km)
        setRider_a(rider_a);//Idade
        setRider_b(rider_b);//BMI	 
        setRider_w(rider_w);//Peso(Kg)
        setRider_h(rider_h);//Altura (metros)            
        setRt_PPS(rt_PPS);//Tipo do Ciclista              
        setCrt_PPS(crt_PPS);//Modalidade do Atleta
    }
    public void setWinner(int tour_y,int condition,String date,int tour_n,String tour_w,String rider_c,String rider_t,int tour_l,int rider_a,float rider_b,int rider_w,double rider_h,String rt_PPS,String crt_PPS){//Constructor from setters
        
        setTour_y(tour_y,condition);//Ano
        set_Date(date);//Data
        setTour_n(tour_n);//Numero do Tour de France
        setTour_w(tour_w);//Nome do vencedor
        setRider_c(rider_c);//Nome do país
        setRider_t(rider_t);//Equipe Vencedora
        setTour_l(tour_l);//Distancia do Tour de France(km)
        setRider_a(rider_a);//Idade
        setRider_b(rider_b);//BMI	 
        setRider_w(rider_w);//Peso(Kg)
        setRider_h(rider_h);//Altura (metros)            
        setRt_PPS(rt_PPS);//Tipo do Ciclista              
        setCrt_PPS(crt_PPS);//Modalidade do Atleta
    }
    //Setters    
    public void setTour_y(int tour_y,int condition){   
        if(condition==1){
            this.tour_y=tour_y;
        }else{
            this.tour_y=Functions.set_Year(tour_y);
        }
        
    }
    public void set_Date(String date){
        
        String newdate=Functions.read_data(date,this.getTour_y());//valida a data
        
        
        this.date=newdate;//Atribui a variavel
    }
    public void setTour_n(int tour_n){   
        this.tour_n=tour_n;
    }
    public void setTour_w(String tour_w){   
        this.tour_w=tour_w;
    }
    public void setRider_c(String rider_c){   
        this.rider_c=rider_c;
    }
    public void setRider_t(String rider_t){   
        this.rider_t=rider_t;
    }
    public void setTour_l(int tour_l){   
        this.tour_l=tour_l;
    }
    public void setRider_a(int rider_a){   
        this.rider_a=rider_a;
    }public void setRider_b(float rider_b){   
        this.rider_b=rider_b;
    }
    public void setRider_w(int rider_w){   
        this.rider_w=rider_w;
    }
    public void setRider_h(double rider_h){   
        this.rider_h=rider_h;
    }
    public void setRt_PPS(String rt_PPS){   
        this.rt_PPS=rt_PPS;
    }
    public void setCrt_PPS(String crt_PPS){   
        this.crt_PPS=crt_PPS;
    }
    //Getters
    public int getTour_y(){   
        return this.tour_y;    
    }
    public String get_Date(){
        return this.date;
    }
    public int getTour_n(){   
        return this.tour_n;    
    }
    public String getTour_w(){   
        return this.tour_w;    
    }
    public String getRider_c(){   
        return this.rider_c;    
    }
    public String getRider_t(){      
        return this.rider_t;    
    }
    public int getTour_l(){   
        return this.tour_l;   
    }
    public int getRider_a(){      
        return this.rider_a;    
    }
    public float getRider_b(){      
        return this.rider_b;    
    }
    public int getRider_w(){      
        return this.rider_w;    
    }
    public double getRider_h(){      
        return this.rider_h;    
    }
    public String getRt_PPS(){      
        return this.rt_PPS;    
    }
    public String getCrt_PPS(){      
        return this.crt_PPS;    
    }
    public String toString(){//toString Padrão  
        return  "\nAno: "+getTour_y()
               +"\nData: "+get_Date()
               + Changes.set_Locale("\nNúmero do Tour de France: "+getTour_n())
               + "\nNome do Vencedor: "+getTour_w()
               + "\nPais do Vencedor: "+getRider_c()
               + "\nEquipe do Vencedor: "+getRider_t()
               + Changes.set_Locale("\nDistância do Tour de France(km): "+getTour_l()+" km")
               + "\nIdade: "+getRider_a()+" anos"
               + "\nBMI do Ciclista: "+getRider_b()
               + "\nPeso(Kg): "+getRider_w()+" Kg"
               + "\nAltura (metros): "+getRider_h()+" m"
               + "\nTipo do Atleta: "+getRt_PPS()
               + "\nModalidade do Atleta: "+getCrt_PPS();

    }
    //procedimentos e funções para o ByteArray Stream
    public byte[] tba() throws IOException {
        
        //Instanciando Stream e configurando
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        DataOutputStream entry = new DataOutputStream(output);
        
        //Adicionando atributos no stream a partir do objeto
        entry.writeInt(this.getTour_y());
        entry.writeUTF(this.get_Date());
        entry.writeInt(this.getTour_n());
        entry.writeUTF(this.getTour_w());
        entry.writeUTF(this.getRider_c());
        entry.writeUTF(this.getRider_t());
        entry.writeInt(this.getTour_l());
        entry.writeInt(this.getRider_a());
        entry.writeFloat(this.getRider_b());
        entry.writeInt(this.getRider_w());
        entry.writeDouble(this.getRider_h());
        entry.writeUTF(this.getRt_PPS());
        entry.writeUTF(this.getCrt_PPS());
        
        byte[] arr=output.toByteArray();//Instancia e atribui valor a vetor
        
        return arr;//retornando como vetor de bytes
    }
    public void fba(byte[] array) throws IOException {
        
        //Instanciando Stream e configurando
        ByteArrayInputStream input = new ByteArrayInputStream(array);
        DataInputStream exit = new DataInputStream(input);
        
        //atribuir valores ao objeto proveniente da leitura do stream
        this.setTour_y(exit.readInt(),1);
        this.set_Date(exit.readUTF());
        this.setTour_n(exit.readInt());
        this.setTour_w(exit.readUTF());
        this.setRider_c(exit.readUTF());
        this.setRider_t(exit.readUTF());
        this.setTour_l(exit.readInt());
        this.setRider_a(exit.readInt());
        this.setRider_b(exit.readFloat()); 
        this.setRider_w(exit.readInt());
        this.setRider_h(exit.readDouble());            
        this.setRt_PPS(exit.readUTF());
        this.setCrt_PPS(exit.readUTF());

    }

}
