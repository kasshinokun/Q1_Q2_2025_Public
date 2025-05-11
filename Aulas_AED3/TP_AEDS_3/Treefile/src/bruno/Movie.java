package bruno;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.util.Arrays;

public class Movie {
	private int id;
	private String name;
	private byte day;
	private byte month;
	private int year;
	private float score;
	private String[] genres;
	private String overview;
	private String[] crew;
	private String origTitle;
	private char status;
	private String origLang;
	private double budget;
	private double revenue;
	private String country;
	public Movie() {
		
	}
	public Movie(int id, String name, byte day, byte month, int year, float score, String[] genres,
			String overview, String[] crew, String origTitle, char status, String origLang, double budget,
			double revenue, String country) {
		this.id = id;
		this.name = name;
		this.day = day;
		this.month = month;
		this.year = year;
		this.score = score;
		this.genres = genres;
		this.overview = overview;
		this.crew = crew;
		this.origTitle = origTitle;
		this.status = status;
		this.origLang = origLang;
		this.budget = budget;
		this.revenue = revenue;
		this.country = country;
	}
	public int getId() {
		return id;
	}
	public void setId(int id) {
		this.id = id;
	}
	public String getName() {
		return name;
	}
	public void setName(String name) {
		this.name = name;
	}
	public byte getDay() {
		return day;
	}
	public void setDay(byte day) {
		this.day = day;
	}
	public byte getMonth() {
		return month;
	}
	public void setMonth(byte month) {
		this.month = month;
	}
	public int getYear() {
		return year;
	}
	public void setYear(int year) {
		this.year = year;
	}
	public float getScore() {
		return score;
	}
	public void setScore(float score) {
		this.score = score;
	}
	public String[] getGenres() {
		return genres;
	}
	public void setGenres(String[] genres) {
		this.genres = genres;
	}
	public String getOverview() {
		return overview;
	}
	public void setOverview(String overview) {
		this.overview = overview;
	}
	public String[] getCrew() {
		return crew;
	}
	public void setCrew(String[] crew) {
		this.crew = crew;
	}
	public String getOrigTitle() {
		return origTitle;
	}
	public void setOrigTitle(String origTitle) {
		this.origTitle = origTitle;
	}
	public char getStatus() {
		return status;
	}
	public void setStatus(char status) {
		this.status = status;
	}
	public String getOrigLang() {
		return origLang;
	}
	public void setOrigLang(String origLang) {
		this.origLang = origLang;
	}
	public double getBudget() {
		return budget;
	}
	public void setBudget(double budget) {
		this.budget = budget;
	}
	public double getRevenue() {
		return revenue;
	}
	public void setRevenue(double revenue) {
		this.revenue = revenue;
	}
	public String getCountry() {
		return country;
	}
	public void setCountry(String country) {
		this.country = country;
	}
	@Override
	public String toString() {
		return "Movie [id=" + id + ", name=" + name + ", day=" + day + ", month=" + month + ", year="
				+ year + ", score=" + score + ", genres=" + Arrays.toString(genres) + ", overview="
				+ overview + ", crew=" + Arrays.toString(crew) + ", origTitle=" + origTitle
				+ ", status=" + status + ", origLang=" + origLang + ", budget=" + budget + ", revenue="
				+ revenue + ", country=" + country + "]";
	}
	public void exibir() {
		System.out.println("Id: " + this.id);
		System.out.println("Titulo: " + this.name);
		System.out.println("Data de lancamento: " + this.day + "/" + this.month + "/" + this.year);
		System.out.println("Nota: " + this.score);
		System.out.print("Generos: ");
		for(int i=0; i<this.genres.length - 1; i++) {
			System.out.print(genres[i] + ", ");
		}
		System.out.println(genres[genres.length-1]);
		System.out.println("Resumo: " + this.overview);
		System.out.println("Elenco(ator, personagem): ");
		for(int i=0; i<this.crew.length - 1; i++) {
			System.out.println(crew[i] + "; ");
		}
		if(crew.length > 0) {
			System.out.println(crew[crew.length - 1]);
		}
		System.out.println("Titulo original: " + this.origTitle);
		System.out.print("Status: ");
		if(this.status == 'r') {
			System.out.println("lancado");
		}
		else if(this.status == 'p') {
			System.out.println("Em pos-producao");
		}
		else {
			System.out.println("Em producao");
		}
		System.out.println("Lingua original: " + this.origLang);
		System.out.println("Orcamento: " + this.budget);
		System.out.println("Receita: " + this.revenue);
		System.out.println("Pais: " + this.country);
		
	}
	public byte[] toByteArray() throws IOException{
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		DataOutputStream dos = new DataOutputStream(baos);
		dos.writeBoolean(true);
		dos.writeInt(this.id);
		dos.writeUTF(this.name);
		dos.writeByte(this.day);
		dos.writeByte(this.month);
		dos.writeInt(this.year);
		dos.writeFloat(this.score);
		dos.writeByte(this.genres.length);
		for(int i=0; i<genres.length; i++) {
			dos.writeUTF(genres[i]);
		}
		dos.writeUTF(this.overview);
		dos.writeByte(this.crew.length);
		for(int i=0; i<crew.length; i++) {
			dos.writeUTF(crew[i]);
		}
		dos.writeUTF(this.origTitle);
		dos.writeChar(this.status);
		dos.writeUTF(this.origLang);
		dos.writeDouble(this.budget);
		dos.writeDouble(this.revenue);
		dos.writeUTF(this.country);
		return baos.toByteArray();
	}
	public void fromByteArray(byte[] b) throws IOException {
        ByteArrayInputStream bais = new ByteArrayInputStream(b);
        DataInputStream dis = new DataInputStream(bais);
        dis.read(); //Pula a lápide
        this.id = dis.readInt();
        this.name = dis.readUTF();
        this.day = dis.readByte();
        this.month = dis.readByte();
        this.year = dis.readInt();
        this.score = dis.readFloat();
        byte length = dis.readByte();
        this.genres = new String[length];
        for(byte i = 0; i<length; i++) {
        	this.genres[i] = dis.readUTF();
        }
        this.overview = dis.readUTF();
        length = dis.readByte();
        this.crew = new String[length];
        for(byte i = 0; i<length; i++) {
        	this.crew[i] = dis.readUTF();
        }
        this.origTitle = dis.readUTF();
        this.status = dis.readChar();
        this.origLang = dis.readUTF();
        this.budget = dis.readDouble();
        this.revenue = dis.readDouble();
        this.country = dis.readUTF();

    }
}
