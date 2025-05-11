package bruno;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;

public class ListNode {
	private int id;
	private String country;
	private long nextCountry;
	private int year;
	private long nextYear;
	
	public ListNode(){
		
	}
	
	public ListNode(int id, String country, long nextCountry, int year, long nextYear) throws IOException{
		this.id = id;
		this.country = country;
		this.nextCountry = nextCountry;
		this.year = year;
		this.nextYear = nextYear;
	}
	
	public ListNode(byte[] ba) throws IOException {
		ByteArrayInputStream bais = new ByteArrayInputStream(ba);
        DataInputStream dis = new DataInputStream(bais);
        this.id = dis.readInt();
        this.nextCountry = dis.readLong();
        this.nextYear = dis.readLong();
	}
	public byte[] getBa() throws IOException {
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		DataOutputStream dos = new DataOutputStream(baos);
		dos.writeInt(this.id);
		dos.writeLong(this.nextCountry);
		dos.writeLong(this.nextYear);
		return baos.toByteArray();
	}

	public int getId() {
		return id;
	}

	public void setId(int id) {
		this.id = id;
	}

	public String getCountry() {
		return country;
	}

	public void setCountry(String country) {
		this.country = country;
	}

	public long getNextCountry() {
		return nextCountry;
	}

	public void setNextCountry(long nextCountry) {
		this.nextCountry = nextCountry;
	}

	public int getYear() {
		return year;
	}

	public void setYear(int year) {
		this.year = year;
	}

	public long getNextYear() {
		return nextYear;
	}

	public void setNextYear(long nextYear) {
		this.nextYear = nextYear;
	}
}
