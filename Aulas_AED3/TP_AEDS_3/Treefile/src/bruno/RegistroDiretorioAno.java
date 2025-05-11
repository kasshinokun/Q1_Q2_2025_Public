package bruno;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;

public class RegistroDiretorioAno {
	private int year;
	private int amount;
	private long iniPos;
	public RegistroDiretorioAno() {
		
	}
	public RegistroDiretorioAno(int year, int amount, long iniPos) {
		this.year = year;
		this.amount = amount;
		this.iniPos = iniPos;
	}
	public RegistroDiretorioAno(byte[] ba) throws IOException {
		ByteArrayInputStream bais = new ByteArrayInputStream(ba);
        DataInputStream dis = new DataInputStream(bais);
        this.year = dis.readInt();
        this.amount = dis.readInt();
        this.iniPos = dis.readLong();
	}
	public byte[] getBa() throws IOException {
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		DataOutputStream dos = new DataOutputStream(baos);
		dos.writeInt(this.year);
		dos.writeInt(this.amount);
		dos.writeLong(iniPos);
		return baos.toByteArray();
	}
	public int getYear() {
		return year;
	}
	public void setYear(int year) {
		this.year = year;
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
