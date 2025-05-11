package index;//nome do package

//importação de funções do package
import functions.*;
//importação de bibliotecas
import java.io.*;

public class C_Index extends Index{
    
    private byte tomb;
        
    public C_Index(){
       super(-1,-1);
       setValidate((byte)0);
       

    }
    public C_Index(int id,byte tomb, long position){
        super(id,position);
        setValidate(tomb);
        
    }
    public void setValidate(byte c){
        this.tomb=c;
    }
    public byte getValidate(){
        return this.tomb;
    }
    public String toString(){
        String x="";
        if(this.getValidate()==0){
            x="Inválido";
        }else if(this.getValidate()==1){
            x="Válido";
        }else{
            x="Erro";
        }
        return Changes.set_Locale("\nId: "+getIndexId()+
                "\nValidate: "+x+
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
            entry.writeByte(this.getValidate());
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
        this.setValidate(exit.readByte());
        this.setIndexPos(exit.readLong());
    
    }
    
}
