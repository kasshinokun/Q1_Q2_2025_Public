import java.io.*;

public class Person{
	private int id;
	private String name;
	private String email;
	private String address;
	private String phone;
	private int age;
	
	public Person() {
		super();
		this.id = -1;
		this.name = "";
		this.email = "";
		this.address = "";
		this.phone = "";
		this.age = -1;
	}
	public Person(int id, String name, String email, String address, String phone, int age) {
		super();
		this.id = id;
		this.name = name;
		this.email = email;
		this.address = address;
		this.phone = phone;
		this.age = age;
	}
	public Person(String[] list) {
		try {
			this.id = Integer.parseInt(list[0]);
			this.name = list[1];
			this.email =list[2];
			this.address =list[3];
			this.phone = list[4];
			this.age = Integer.parseInt(list[5]);
			
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	//Setters
	public void setId(int id) {
		this.id = id;
	}
	public void setName(String name) {
		this.name = name;
	}
	public void setEmail(String email) {
		this.email = email;
	}
	public void setAddress(String address) {
		this.address = address;
	}
	public void setPhone(String phone) {
		this.phone = phone;
	}
	public void setAge(int age) {
		this.age = age;
	}
	//Getters
	public int getId() {
		return this.id;
	}
	public String getName() {
		return this.name;
	}
	public String getEmail() {
		return this.email;
	}
	public String getAddress() {
		return this.address;
	}
	public String getPhone() {
		return this.phone;
	}
	public int getAge() {
		return this.age;
	}
	//toString
	@Override
	public String toString() {
		return "Person [id=" + this.getId() + 
				", name=" + this.getName() + 
				", email=" + this.getEmail() + 
				", address=" + this.getAddress() + 
				", phone=" + this.getPhone() + 
				", age=" + this.getAge() + "]";
	}
	public byte[] toByteArray() throws IOException {
		
		//Instanciando Stream e configurando
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        
        DataOutputStream dos = new DataOutputStream(baos);
        
        //Adicionando atributos no stream a partir do objeto
        
        dos.writeInt(this.getId());
        dos.writeUTF(this.getName());
        dos.writeUTF(this.getEmail());
        dos.writeUTF(this.getAddress());
        dos.writeUTF(this.getPhone());
		dos.writeInt(this.getAge());
	    return baos.toByteArray();//retornando como vetor de bytes
	
	}
	public void fromByteArray(byte[] data) throws IOException {
        
		ByteArrayInputStream bais = new ByteArrayInputStream(data);
        DataInputStream dis = new DataInputStream(bais);
		
        this.setId(dis.readInt());
        this.setName(dis.readUTF());
        this.setEmail(dis.readUTF());
        this.setAddress(dis.readUTF());
        this.setPhone(dis.readUTF());
        this.setAge(dis.readInt());

    }
}