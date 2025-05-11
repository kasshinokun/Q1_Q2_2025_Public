package functions;//nome do package

//importação de funções do package 
import functions.*;
//importação de bibliotecas
import java.io.*;
import java.nio.charset.*;
import java.nio.file.*;

public class Restore {
    //procedimentos e funções para o ByteArray Stream
    private static byte[] tba(String line) throws IOException {//criação do vetor de bytes
        
        //Instanciando Stream e configurando
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        DataOutputStream entry = new DataOutputStream(output);
        
        //Adicionando atributos no stream a partir do objeto
        entry.writeUTF(line);
        
        byte[] arr=output.toByteArray();//Instanciando vetor
        
        return arr;//retornando como vetor de bytes
    }
    //criação da String a partir do vetor de bytes
    private static String fba(byte[] array) throws IOException {
        
        //Instanciando Stream e configurando
        ByteArrayInputStream input = new ByteArrayInputStream(array);
        DataInputStream exit = new DataInputStream(input);
        
        //atribuir valores ao objeto proveniente da leitura do stream
        String line=exit.readUTF();
        
        return line;//retornando String

    }
//================================================================================================
    //Adaptações para criar e carregar o backup
    public static void restoreCSV(String path){
        String path2="backup/data/tour.db";//arquivo binario
        read_backup(path, path2);
    }
    private static void read_backup(String path,String path2){//leitura do backup
        
        try (FileOutputStream fos = new FileOutputStream(path);
             RandomAccessFile raf=new RandomAccessFile(path2,"rw");//instancia pelo caminho recebido
             //especificações para leitura em UTF-8
             Writer writer = new OutputStreamWriter(fos, StandardCharsets.UTF_8)
                
                
            ) {
            raf.seek(0);//segue para o início do arquivo
            while(raf.getFilePointer()<raf.length()){
                try{
                    int size=raf.readInt();//Leita para definir o tamanho do vetor de bytes

                    byte[] arr=new byte[size];//Instancia um novo vetor de bytes 

                    raf.read(arr);//leitura do vetor

                    String line=fba(arr);//Instancia a String a partir do vetor de bytes
                    
                    writer.write(line);
                    
                    writer.write(raf.readUTF());
            
                    //writer.flush();
                //Tratamento de exceções       
                }catch (EOFException eof) {
                    System.out.println(Changes.set_Locale("\nFim do arquivo alcançado."));
                    break;
                } catch (IOException g) {
                    System.out.println(Changes.set_Locale("\nErro durante a leitura."));
                    break;
                } 
            }
        //Tratamento de exceções        
        } catch (IOException e) {
            //e.printStackTrace();
            System.out.println(Changes.set_Locale("\nArquivo não existe."));
        }
    }
    public static void create_backup(String path,String path2){//leitura do arquivo base e criação do backup
        
        try{
            
            RandomAccessFile file = new RandomAccessFile(path,"r");
            RandomAccessFile file2 = new RandomAccessFile(path2,"rw");    
            while (true) {
                //Instanciando String a partir da leitura de arquivo
                String line=file.readLine();
                //Instanciando demais objetos
                byte[] arr=tba(line);//vetor de bytes
                int size=arr.length;//inteiro para tamanho do vetor
                long tail=(long)file2.length();//long para posição no arquivo
                
                file2.seek(tail);//busca a posição designada no arquivo

                file2.writeInt(size);//escreve o tamanho do vetor

                file2.write(arr);//escreve o vetor no arquivo
                
                file2.writeUTF("\n");//salta linha
            }
	//Tratamento de exceções      
        }catch(EOFException | NullPointerException e){
            System.out.println("\nLeitura finalizada do arquivo.");
           
        }catch(IOException e){
            System.out.println("\nErro na leitura do arquivo.");
        }
        
    }
    public static void delete_db(String path){
        
        try{
            Files.delete(Paths.get(path));
            System.out.println("Arquivo Deletado com Sucesso");
        }
	catch (NoSuchFileException e) {
	    System.out.println(Changes.set_Locale("\nArquivo não existe."));
	}
        catch (IOException e) {
	    System.out.println("Erro durante o processo.");
        }
        
    }
//================================================================================================
    //teste interno do código
    public static void create_backup(){//leitura do arquivo base e criação do backup
        String path="backup/data/tour.csv";//arquivo csv original
        String path2="backup/data/tour.db";//arquivo binario
        try{
            
            RandomAccessFile file = new RandomAccessFile(path,"r");
            RandomAccessFile file2 = new RandomAccessFile(path2,"rw");    
            while (true) {
                //Instanciando String a partir da leitura de arquivo
                String line=file.readLine();
                //Instanciando demais objetos
                byte[] arr=tba(line);//vetor de bytes
                int size=arr.length;//inteiro para tamanho do vetor
                long tail=(long)file2.length();//long para posição no arquivo
                
                file2.seek(tail);//busca a posição designada no arquivo

                file2.writeInt(size);//escreve o tamanho do vetor

                file2.write(arr);//escreve o vetor no arquivo
                
                file2.writeUTF("\n");//salta linha
            }
	//Tratamento de exceções      
        }catch(EOFException | NullPointerException e){
            System.out.println("\nLeitura finalizada do arquivo.");
           
        }catch(IOException e){
            System.out.println("\nErro na leitura do arquivo.");
        }
        
    }
    public static void read_backup(){//leitura do backup
        
        String path = "backup/data/tour_2.csv";//arquivo a ser restaurado
        
        String path2="backup/data/tour.db";//arquivo binario
        
        try (FileOutputStream fos = new FileOutputStream(path);
             RandomAccessFile raf=new RandomAccessFile(path2,"rw");//instancia pelo caminho recebido
             //especificações para leitura em UTF-8
             Writer writer = new OutputStreamWriter(fos, StandardCharsets.UTF_8)
                
                
            ) {
            raf.seek(0);//segue para o início do arquivo
            while(raf.getFilePointer()<raf.length()){
                try{
                    int size=raf.readInt();//Leita para definir o tamanho do vetor de bytes

                    byte[] arr=new byte[size];//Instancia um novo vetor de bytes 

                    raf.read(arr);//leitura do vetor

                    String line=fba(arr);//Instancia a String a partir do vetor de bytes
                    
                    writer.write(line);
                    
                    writer.write(raf.readUTF());
            
                    //writer.flush();
                //Tratamento de exceções       
                }catch (EOFException eof) {
                    System.out.println(Changes.set_Locale("\nFim do arquivo alcançado."));
                    break;
                } catch (IOException g) {
                    System.out.println(Changes.set_Locale("\nErro durante a leitura."));
                    break;
                } 
            }
        //Tratamento de exceções        
        } catch (IOException e) {
            //e.printStackTrace();
            System.out.println(Changes.set_Locale("\nArquivo não existe."));
        }
    }
    public static void delete_db(){
        String path="backup/data/tour.db";
        try{
            Files.delete(Paths.get(path));
            System.out.println("Arquivo Deletado com Sucesso");
        }
	catch (NoSuchFileException e) {
	    System.out.println(Changes.set_Locale("\nArquivo não existe."));
	}
        catch (IOException e) {
	    System.out.println("Erro durante o processo.");
        }
        
    }
}
