package estagio2;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;

public class Index {
	private int Key;
	private long Pointer;
	private boolean lapide;
	
	public Index(int Key,long Pointer,boolean lapide) {
		this.Key=Key;
		this.Pointer=Pointer;
		this.lapide=lapide;
	}
	public Index() {
		this.Key=0;
		this.Pointer=-1;
		this.lapide=false;
	}
	//Setters
	public void setKey(int Key) {
		this.Key = Key;
	}

	public void setPointer(long Pointer) {
		this.Pointer = Pointer;
	}

	public void setLapide(boolean lapide) {
		this.lapide = lapide;
	}
	
	//Getters
	public int getKey() {
		return this.Key;
	}
	public long getPointer() {
		return this.Pointer;
	}
	public boolean isLapide() {
		return lapide;
	}
	
	//toString da Classe
	public String toStringIndex() {
		return
		"\nID Registro---------------------------> "+this.getKey()+
		"\nPosição-------------------------------> "+this.getPointer()+
		"\nValidade------------------------------> "+this.isLapide();
	}
	
	//======================================================> Byte Array
	public byte[] toByteArray() throws IOException {
		
		//Instanciando Stream e configurando
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        
        DataOutputStream dos = new DataOutputStream(baos);
        
        //Adicionando atributos no stream a partir do objeto
        dos.writeBoolean(this.isLapide());        
	    dos.writeInt(this.getKey());
	    dos.writeLong(this.getPointer());
	    
	    
	    return baos.toByteArray();//retornando como vetor de bytes
	}
	public void fromByteArray(byte[] data) throws IOException {
        
		ByteArrayInputStream bais = new ByteArrayInputStream(data);
        DataInputStream dis = new DataInputStream(bais);
        this.setLapide(dis.readBoolean());
        this.setKey(dis.readInt());
        this.setPointer(dis.readLong());
        
        
	}
		
	public static void main(String[] args) {
		// TODO Auto-generated method stub

	}

}
