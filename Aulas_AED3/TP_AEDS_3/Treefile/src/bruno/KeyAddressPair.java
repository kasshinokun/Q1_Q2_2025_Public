package bruno;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;



public class KeyAddressPair {
	private int key;
	private long address, leftSon, rightSon;
	KeyAddressPair(){
		
	}
	KeyAddressPair(byte[] ba) throws IOException{
		ByteArrayInputStream bais = new ByteArrayInputStream(ba);
        DataInputStream dis = new DataInputStream(bais);
        this.leftSon = dis.readLong();
        this.key = dis.readInt();
        this.address = dis.readLong();
        this.rightSon = dis.readLong();
	}
	KeyAddressPair(int key, long address) throws IOException{
		this.key = key;
		this.address = address;
		this.rightSon = this.leftSon = -1;
	}
	KeyAddressPair(long leftSon, int key, long address, long rightSon) throws IOException{
		this.key = key;
		this.address = address;
		this.leftSon = leftSon;
		this.rightSon = rightSon;
	}
	public byte[] getBa() throws IOException {
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		DataOutputStream dos = new DataOutputStream(baos);
		dos.writeLong(leftSon);
		dos.writeInt(key);
		dos.writeLong(address);
		dos.writeLong(rightSon);
		return baos.toByteArray();
	}
	public int getKey() {
		return key;
	}
	public void setKey(int key) {
		this.key = key;
	}
	public long getAddress() {
		return address;
	}
	public void setAddress(long address) {
		this.address = address;
	}
	public long getLeftSon() {
		return leftSon;
	}
	public void setLeftSon(long leftSon) {
		this.leftSon = leftSon;
	}
	public long getRightSon() {
		return rightSon;
	}
	public void setRightSon(long rightSon) {
		this.rightSon = rightSon;
	}
}
