package object.professor;
import java.io.*;
import java.text.DecimalFormat;

class Jogador {
    
    protected int idJogador;
    protected String nome;
    protected float pontos;

    public Jogador(int i, String n, float p) {
        idJogador = i;
        nome = n;
        pontos = p;  
    }

    public Jogador() {
        idJogador = -1;
        nome = "";
        pontos = 0F;  
    }

    public String toString() {
        DecimalFormat df = new DecimalFormat("#,##0.00"); 
        return "\nID: " + idJogador +
               "\nNome: " + nome +
               "\nPontos: " + df.format(pontos);
    }

    public byte[] toByteArray() throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DataOutputStream dos = new DataOutputStream(baos);
        dos.writeInt(idJogador);
        dos.writeUTF(nome);
        dos.writeFloat(pontos);
        return baos.toByteArray();
    }

    public static Jogador JfromByteArray(byte[] data) throws IOException {
        ByteArrayInputStream bais = new ByteArrayInputStream(data);
        DataInputStream dis = new DataInputStream(bais);
        int id = dis.readInt();
        String nome = dis.readUTF();
        float pontos = dis.readFloat();
        return new Jogador(id, nome, pontos);
    }
    public void fromByteArray(byte ba[]) throws IOException{

        ByteArrayInputStream bais = new ByteArrayInputStream(ba);
        DataInputStream dis = new DataInputStream(bais);

        idJogador=dis.readInt();
        nome=dis.readUTF();
        pontos=dis.readFloat();

    }
    public static void main(String[] args) throws IOException {
        
    	main0(args);
    	
    	main1(args);
        
        main2(args);
    }
    public static void main0(String[] args) throws IOException {
		
		ByteArrayOutputStream baos = new ByteArrayOutputStream();

        DataOutputStream dos = new DataOutputStream(baos);

        dos.writeInt(25);    
        dos.writeUTF("Conceição");  
        dos.writeFloat(49.90f);   

         byte[] dados = baos.toByteArray();

        
        ByteArrayInputStream bais = new ByteArrayInputStream(dados);
        DataInputStream dis = new DataInputStream(bais);
        
        int id = dis.readInt();     
        String nome = dis.readUTF(); 
        float salario = dis.readFloat(); 
        

        System.out.println("\nDados lidos do array de bytes:");
        System.out.println("ID: " + id);
        System.out.println("Nome: " + nome);
        System.out.println("Salário: " + salario);
    }
    public static void main1(String[] args) throws IOException {
    	
    	Jogador jogador1 = new Jogador(25, "Conceição", 49.90F);
        Jogador jogador2 = new Jogador(37, "José Carlos", 62.50F);
        Jogador jogador3 = new Jogador(291, "Pedro", 53.45F);


        byte[] bytes1 = jogador1.toByteArray();
        byte[] bytes2 = jogador2.toByteArray();
        byte[] bytes3 = jogador3.toByteArray();

        Jogador jogador1Reconstruido = Jogador.JfromByteArray(bytes1);
        Jogador jogador2Reconstruido = Jogador.JfromByteArray(bytes2);
        Jogador jogador3Reconstruido = Jogador.JfromByteArray(bytes3);

        System.out.println(jogador1Reconstruido);
        System.out.println(jogador2Reconstruido);
        System.out.println(jogador3Reconstruido);
        
    }
    public static void main2(String[] args){

        Jogador j1= new Jogador(25, "Conceição", 49.90F);
        Jogador j2= new Jogador(37, "José Carlos", 62.50F);
        Jogador j3= new Jogador(291, "Pedro", 53.45F);
        Jogador j_temp= new Jogador();

        FileOutputStream arq;
        DataOutputStream dos;

        FileInputStream arq2;
        DataInputStream dis;

        byte[] ba;
        int len;


        try {

            arq = new FileOutputStream("jogadores_ds_ba.db");
            dos = new DataOutputStream(arq);

            ba = j1.toByteArray();
            dos.writeInt(ba.length); //Tamano do registro em bytes
            dos.write(ba);
            
            ba = j2.toByteArray();
            dos.writeInt(ba.length);
            dos.write(ba);
            
            ba = j3.toByteArray();
            dos.writeInt(ba.length);
            dos.write(ba);
            
            dos.close();

            arq2 =  new FileInputStream("jogadores_ds_ba.db");
            dis = new DataInputStream(arq2);
  
            len = dis.readInt(); //Tamano do registro em bytes
            ba = new byte[len];
            dis.read(ba);
            j_temp.fromByteArray(ba);
            System.out.println(j_temp);

            len = dis.readInt();
            ba = new byte[len];
            dis.read(ba);
            j_temp.fromByteArray(ba);
            System.out.println(j_temp);

            len = dis.readInt();
            ba = new byte[len];
            dis.read(ba);
            j_temp.fromByteArray(ba);
            System.out.println(j_temp);


            

        } catch (Exception e) {
            System.out.println(e.getMessage());
        }
    }
}