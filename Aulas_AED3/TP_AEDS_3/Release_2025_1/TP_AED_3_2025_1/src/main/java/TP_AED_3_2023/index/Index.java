package TP_AED_3_2023.index;//nome do package

//importação de funções do package
import TP_AED_3_2023.functions.*;
//importação de bibliotecas
import java.io.*;

public class Index implements Serializable {
        
    private static final long serialVersionUID =1L;

    private int id;
    
    private long position;
    
    public Index(){
       setIndexId(-1);
       setIndexPos(-1); 

    }
    public Index(int id, long position){
        setIndexId(id);
        
        setIndexPos(position);
    }
    public void setIndexId(int id){
        this.id=id;
    }
    public void setIndexPos(long position){
        this.position=position;
    }
    public int getIndexId(){
        return this.id;
    }
    public long getIndexPos(){
        return this.position;
    }
    public String toString(){
        return Changes.set_Locale("\nId: "+getIndexId()+
                
                "\nPosição: "+getIndexPos());
    }
    
    //procedimentos e funções para o ByteArray Stream
    public byte[] tba(){
        try{
            //Instanciando Stream e configurando
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            DataOutputStream entry = new DataOutputStream(output);

            //Adicionando atributos no stream a partir do objeto
            entry.writeInt(this.getIndexId());
            entry.writeLong(this.getIndexPos());
            return output.toByteArray();//retornando como vetor de bytes
        
        }catch(IOException e){
            return null;
        }
    }
    public void fba(byte[] array) throws IOException {
       
        //Instanciando Stream e configurando
        ByteArrayInputStream input = new ByteArrayInputStream(array);
        DataInputStream exit = new DataInputStream(input);

        //atribuir valores ao objeto proveniente da leitura do stream
        this.setIndexId(exit.readInt());
        this.setIndexPos(exit.readLong());
    
    }
    
}
