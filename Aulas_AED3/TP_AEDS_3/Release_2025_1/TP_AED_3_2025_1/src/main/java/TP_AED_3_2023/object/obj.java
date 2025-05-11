package TP_AED_3_2023.object;
import java.io.*;
import java.time.*;

import TP_AED_3_2023.functions.*;

public class obj extends Winner{
    
    private int id;//ID
    		
    
    public obj(){//construtor padrão para print(teste de algoritmo) 
        super();
        this.setId(-1);//ID
        
    }
    public obj(int id,int tour_y,int condition,String date,int tour_n,String tour_w,String rider_c,String rider_t,int tour_l,int rider_a,float rider_b,int rider_w,double rider_h,String rt_PPS,String crt_PPS){//Constructor from setters
        super(tour_y,condition, date, tour_n, tour_w, rider_c, rider_t, tour_l, rider_a, rider_b, rider_w, rider_h,rt_PPS,crt_PPS);
        setId(id);
    }
    public void setObj(int id,int tour_y,int condition,String date,int tour_n,String tour_w,String rider_c,String rider_t,int tour_l,int rider_a,float rider_b,int rider_w,double rider_h,String rt_PPS,String crt_PPS){//Constructor from setters
        super.setWinner(tour_y,condition, date, tour_n, tour_w, rider_c, rider_t, tour_l, rider_a, rider_b, rider_w, rider_h,rt_PPS,crt_PPS);
        setId(id);
    }
    //Setters    
    public void setId(int id){   
        this.id=id;
    }
    //Getters
    public int getId(){
        return this.id;
    }
    public String toString(){//toString Padrão com Herança
        return   "\nID: "+Functions.format_id(getId())
               + super.toString();
    }
    //procedimentos e funções para o ByteArray Stream
    public byte[] tba() throws IOException {
        
        //Instanciando Stream e configurando
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        DataOutputStream entry = new DataOutputStream(output);
        
        //Adicionando atributos no stream a partir do objeto
        entry.writeInt(this.getId());
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
        this.setId(exit.readInt());
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
