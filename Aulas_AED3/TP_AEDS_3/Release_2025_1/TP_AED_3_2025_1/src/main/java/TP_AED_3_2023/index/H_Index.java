package TP_AED_3_2023.index;//nome do package

//importação de funções do package
import TP_AED_3_2023.functions.*;
//importação de bibliotecas
import java.io.*;
//classe para o header do cabeçalho do indice
public class H_Index extends Index{
    
    private long find;
        
    public H_Index(){
       super(-1,-1);
       setFind(-1);
       

    }
    public H_Index(int id, long position,long find){
        super(id,position);
        setFind(find);
        
    }
    public void setFind(long find){
        this.find=find;
    }
    public long getFind(){
        return this.find;
    }
    public String toString(){
        return Changes.set_Locale("\nId: "+getIndexId()+
                "\nPosição Inicial: "+getIndexPos()+
                "\nPosição Real---: "+getFind());
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
            entry.writeLong(this.getFind());
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
        this.setFind(exit.readLong());
    
    }
    
}