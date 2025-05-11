package bruno;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;

public class RegistroDiretorioPais{
	private String country;
	private int amount;
	private long iniPos;
	public RegistroDiretorioPais() {
		
	}
	public RegistroDiretorioPais(String country, int amount, long iniPos) {
		this.country  = country;
		this.amount = amount;
		this.iniPos = iniPos;
	}
	public RegistroDiretorioPais(byte[] ba) throws IOException {
		ByteArrayInputStream bais = new ByteArrayInputStream(ba);
        DataInputStream dis = new DataInputStream(bais);
        this.country = dis.readUTF();
        this.amount = dis.readInt();
        this.iniPos = dis.readLong();
	}
	public byte[] getBa() throws IOException {
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		DataOutputStream dos = new DataOutputStream(baos);
		dos.writeUTF(this.country);
		dos.writeInt(this.amount);
		dos.writeLong(this.iniPos);
		return baos.toByteArray();
	}
	public String getCountry() {
		return country;
	}
	public void setCountry(String country) {
		this.country = country;
	}
	public int getAmount() {
		return amount;
	}
	public void setAmount(int amount) {
		this.amount = amount;
	}
	public long getIniPos() {
		return iniPos;
	}
	public void setIniPos(long iniPos) {
		this.iniPos = iniPos;
	}
	
}

