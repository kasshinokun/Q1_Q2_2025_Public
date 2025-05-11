package bruno;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;

public class Pagina {
	private int ordemPag;
	private byte[] ba;
	private ByteArrayInputStream bais;
	private DataInputStream dis;
	private ByteArrayOutputStream baos;
	private DataOutputStream dos;
	public Pagina(){
		
	}
	public Pagina(byte[] ba, int ordemPag) throws Exception {
		this.ba = ba;
		this.ordemPag = ordemPag;
	}
	public byte[] getBa() {
		return ba;
	}
	public void setBa(byte[] ba) {
		this.ba = ba;
	}
	public int getN() throws Exception {
		bais = new ByteArrayInputStream(this.ba);
        dis = new DataInputStream(bais);
		return dis.readInt();
	}
	public void setN(int n) throws IOException {
		baos = new ByteArrayOutputStream();
		dos = new DataOutputStream(baos);
		dos.writeInt(n);
		for(int i=2; i<ba.length; i++) {
			dos.writeByte(ba[i]);
		}
		ba = baos.toByteArray();
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
		System.out.println(index);//
		if(index < 0 || index > ordemPag - 1) {
			throw new Exception("Indice invalido");
		}
		bais = new ByteArrayInputStream(this.ba);
        dis = new DataInputStream(bais);
		dis.skipNBytes((20*index) + 4);
		byte[] baPair = new byte[28];
		dis.read(baPair);
		return new KeyAddressPair(baPair);
	}
	public void setPairAtIndexOf(KeyAddressPair pair, int index) throws Exception {
		if(index < 0 || index > ordemPag - 1) {
			throw new Exception("Indice invalido");
		}
		baos = new ByteArrayOutputStream();
		dos = new DataOutputStream(baos);
		for(int i=0; i<(20*index) + 4 && i<ba.length; i++) {
			dos.writeByte(ba[i]);
		}
		dos.write(pair.getBa());
		for(int i = (20*index) + 30; i<ba.length; i++) {
			dos.writeByte(ba[i]);
		}
		ba = baos.toByteArray();
	}
	public void setSonAtIndexOf(long sonAddress, int index) throws Exception{
		if(index < 0 || index > ordemPag) {
			throw new Exception("Indice invalido");
		}
		baos = new ByteArrayOutputStream();
		dos = new DataOutputStream(baos);
		for(int i=0; i < (20*index) + 4; i++) {
			dos.writeByte(ba[i]);
		}
		dos.writeLong(sonAddress);
		for(int i = (20*index) + 12; i<ba.length; i++) {
			dos.writeByte(ba[i]);
		}
		ba = baos.toByteArray();
	}
	public long getSonAtIndexOf(int index) throws Exception{
		bais = new ByteArrayInputStream(this.ba);
        dis = new DataInputStream(bais);
		dis.skipNBytes((20*index) + 4);
		return dis.readLong();
	}
	
}
