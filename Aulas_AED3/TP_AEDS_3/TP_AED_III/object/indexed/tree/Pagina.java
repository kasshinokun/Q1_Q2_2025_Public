package object.indexed.tree;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;

public class Pagina {
	private short ordemPag;
	private byte[] bytearray;
	private ByteArrayInputStream bais;
	private DataInputStream dis;
	private ByteArrayOutputStream baos;
	private DataOutputStream dos;
	public Pagina(){
		
	}
	public Pagina(byte[] bytearray, short ordemPag) throws Exception {
		this.bytearray = bytearray;
		this.ordemPag = ordemPag;
	}
	public byte[] getByteArray() {
		return bytearray;
	}
	public void setByteArray(byte[] bytearray) {
		this.bytearray = bytearray;
	}
	public short getN() throws Exception {
		bais = new ByteArrayInputStream(this.getByteArray());
        dis = new DataInputStream(bais);
		return dis.readShort();
	}
	public void setN(short n) throws IOException {
		baos = new ByteArrayOutputStream();
		dos = new DataOutputStream(baos);
		dos.writeShort(n);
		for(int i=2; i<this.getByteArray().length; i++) {
			dos.writeByte(this.getByteArray()[i]);
		}
		bytearray = baos.toByteArray();
	}
	public boolean isLeaf() throws Exception {
		if(this.getSonAtIndexOf(0) == -1) {
			return true;
		}
		else {
			return false;
		}
	}
	public ByteArrayInputStream getBais() {
		return bais;
	}
	public void setBais(ByteArrayInputStream bais) {
		this.bais = bais;
	}
	public DataInputStream getDis() {
		return dis;
	}
	public void setDis(DataInputStream dis) {
		this.dis = dis;
	}
	public KeyAddressPair getPairAtIndexOf(int index) throws Exception {
		if(index < 0 || index > this.ordemPag - 1) {
			throw new Exception("Indice invalido");
		}
		this.bais = new ByteArrayInputStream(this.getByteArray());
        this.dis = new DataInputStream(bais);
		this.dis.skipNBytes((20*index) + 2);
		byte[] baPair = new byte[26];
		this.dis.read(baPair);
		return new KeyAddressPair(baPair);
	}
	public void setPairAtIndexOf(KeyAddressPair pair, int index) throws Exception {
		if(index < 0 || index > this.ordemPag - 1) {
			throw new Exception("Indice invalido");
		}
		this.baos = new ByteArrayOutputStream();
		this.dos = new DataOutputStream(this.baos);
		for(int i=0; i<(20*index) + 2 && i<this.getByteArray().length; i++) {
			this.dos.writeByte(this.getByteArray()[i]);
		}
		this.dos.write(pair.toByteArray());
		for(int i = (20*index) + 30; i<bytearray.length; i++) {
			this.dos.writeByte(bytearray[i]);
		}
		this.setByteArray(this.baos.toByteArray());
	}
	public void setSonAtIndexOf(long sonAddress, int index) throws Exception{
		if(index < 0 || index > this.ordemPag) {
			throw new Exception("Indice invalido");
		}
		this.baos = new ByteArrayOutputStream();
		this.dos = new DataOutputStream(baos);
		for(int i=0; i < (20*index) + 2; i++) {
			this.dos.writeByte(this.getByteArray()[i]);
		}
		this.dos.writeLong(sonAddress);
		for(int i = (20*index) + 10; i<this.getByteArray().length; i++) {
			this.dos.writeByte(this.getByteArray()[i]);
		}
		this.setByteArray(this.baos.toByteArray());
	}
	public long getSonAtIndexOf(int index) throws Exception{
		this.bais = new ByteArrayInputStream(this.getByteArray());
        this.dis = new DataInputStream(this.bais);
		this.dis.skipNBytes((20*index) + 2);
		return this.dis.readLong();
	}
	
}
