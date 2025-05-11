package index;

import java.io.*;
//
public class C_Page extends Page{
    String palavra;
    
    public C_Page(){
        setPalavra("");
    }
    public C_Page(int size,String palavra){
        super.setPage(size);
        setPalavra(palavra);
    }
    public void setPalavra(String palavra){
        this.palavra=palavra;
    }
    public String getPalavra(){
        return this.palavra;    
    }
    public void ToString(){
        System.out.println("\nPalavra: "+getPalavra());
        for(int i=0;i<getSize();i++){
            System.out.println(this.pagina[i].toString());
        }    
    }
    //procedimentos e funções para o ByteArray Stream
    public byte[] tba(){
        try{
            //Instanciando Stream e configurando
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            ObjectOutputStream entry = new ObjectOutputStream(output);
            
            //Adicionando atributos no stream a partir do objeto
            entry.writeUTF(this.getPalavra());
            entry.writeInt(this.getSize());
            entry.writeObject(this.getPage());
            
            return output.toByteArray();//retornando como vetor de bytes
        
        }catch(IOException e){
            return null;
        }
    }
    public C_Page fba(byte[] array){
        try{
            //Instanciando Stream e configurando
            ByteArrayInputStream input = new ByteArrayInputStream(array);
            ObjectInputStream exit = new ObjectInputStream(input);

            //atribuir valores ao objeto proveniente da leitura do stream
            this.setPalavra(exit.readUTF());
            this.setPage(exit.readInt());
            C_Index[] e=new C_Index[this.getSize()];
            e = (C_Index[])exit.readObject();
            this.setPage(e);
            return this;
            
        }catch(IOException | ClassNotFoundException | NullPointerException e){
            return new C_Page();
        }
        
    }
}
