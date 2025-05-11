package index;

import java.io.*;

public class Page {
    C_Index[] pagina;
    
    int size;
    public Page(){}
    public Page(int size){
        setPage(size);
    }
    public void setPage(int size){
        this.pagina=new C_Index[size];
        this.size=size;
    }
    public void setPage(C_Index[] page){
        int t=page.length;
        this.pagina=new C_Index[t];
        this.pagina=page;
        this.size=t;
    }
    public void insertIndex(C_Index i){
        boolean resp=false;
        for(int j=0;j<this.pagina.length;j++){
            if(this.pagina[j]==null){
                this.pagina[j]=i;
                resp=true;
                break;
            }
        }if(resp==false){
            System.out.println("Não foi possível adicionar");
        }
    }
    public C_Index[] getPage(){
        return this.pagina;
    }
    public int getSize(){
        return this.size;
    }
    public void ToString(){
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
            entry.writeInt(this.getSize());
            entry.writeObject(this.getPage());
            
            return output.toByteArray();//retornando como vetor de bytes
        
        }catch(IOException e){
            return null;
        }
    }
    public Page fba(byte[] array){
        try{
            //Instanciando Stream e configurando
            ByteArrayInputStream input = new ByteArrayInputStream(array);
            ObjectInputStream exit = new ObjectInputStream(input);

            //atribuir valores ao objeto proveniente da leitura do stream
            this.setPage(exit.readInt());
            C_Index[] e=new C_Index[this.getSize()];
            e = (C_Index[])exit.readObject();
            this.setPage(e);
            return this;
            
        }catch(IOException | ClassNotFoundException | NullPointerException e){
            return new Page();
        }
        
    }
}
