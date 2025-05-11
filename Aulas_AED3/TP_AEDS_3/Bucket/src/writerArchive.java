


import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;


public class writerArchive{
		
	String pathFile;
	
	String pathDb;
	
	public writerArchive(String pathFile,String pathDb) {
		setPathFile(pathFile);
		setPathDb(pathDb);
	}
	
	public void setPathFile(String pathFile) {
		this.pathFile=pathFile;
	}
	public void setPathDb(String pathDb) {
		this.pathDb=pathDb;
	}
	
	public String getPathFile() {
		return this.pathFile;
	}
	public String getPathDb() {
		return this.pathDb;
	}
	public void writeAllFile(){
		
		System.out.println("Caminho recebido: "+this.getPathFile());
		
		RandomAccessFile randomAccessFile=null;
		
		Person obj;
		
		
			
		if(findFile(this.getPathFile())){
			try {
					
				randomAccessFile = new RandomAccessFile(this.getPathFile(),"r");
	            
	            System.out.println(randomAccessFile.readLine());//leitura para ignora o cabeçalho do arquivo .csv, mas exibe(FeedBack apenas)
	            
	            System.out.println("================================================================================================");
	            
	            while (true||randomAccessFile.readLine()!=null) {
	            	
	                String[] line=randomAccessFile.readLine().split(";");
	                
	                //int id=getHeader(pathDb);//recebe o valor presente no cabeçalho
	                
	                obj=new Person(line);//Instancia objeto incrementando a ID
	                
	                System.out.println(obj.toString());//Exibe o objeto
	                
	                writerFile(obj);//Inicia o Processo de escrita
	                
	                System.out.println("================================================================================================");
	                
	            }
			} catch (NullPointerException n) {
	             System.out.println("Fim da leitura e escrita do arquivo .db.");            
			} catch (IOException ioe) {
	            ioe.printStackTrace();
	        } finally {
	            try {
	            	randomAccessFile.close();
	            } catch (IOException ioe) {
	                ioe.printStackTrace();
	            }
	        }
		}else {
			System.out.println("Não localizei o arquivo.");
		}
		
    }
	public boolean findFile(String Path) {
		File diretorio = new File(Path);
		if (!diretorio.exists())
			return false;
		else
			return true;
	}
	public int getLastID(RandomAccessFile randomAccessFile) throws IOException{
  	//Identificação do valor no cabeçalho para o leitor de arquivo
		
		int ID=randomAccessFile.readInt();
		
		return ID;
	}
  	
  	//Identificação do valor no cabeçalho para o escritor de arquivo
    public int getHeader(String path)throws IOException{
        
    	RandomAccessFile randomAccessFile = new RandomAccessFile(path, "rw");//instancia o RandomAccessFile para ler e escrever 
		
		int NewID;//Instancia a variavel para guardar a ultima id ao fazer um novo registro
		
		if (randomAccessFile.length()!=0) {//Verifica se o arquivo está vazio(ou null)
			
			NewID=randomAccessFile.readInt();// gera uma ID incrementada igual ao MySQL AUTO_INCREMENT somente a cada novo registro 
		
		}else {
		
			NewID=0;//Caso esteja vasio(null), atribui 1 a variavel
		
		}
		randomAccessFile.close();
		
        return NewID;//retorna o valor encontrado no cabeçalho
    }
    public void writerFile(Person object) throws IOException {
	    //se houver erro retorna a Exception para interromper o processo 
        //que chamou o procedimento (por isto não existe o try-catch)
		
		RandomAccessFile randomAccessFile = new RandomAccessFile(this.getPathDb(), "rw");//instancia o RandomAccessFile para ler e escrever 
		
		//Não há tratativa para registro duplicado com ID diferente
		randomAccessFile.writeInt(object.getId());//Atualiza o cabeçalho
		
		byte[] bytearray=object.toByteArray();
        int tamanho=bytearray.length;
        long fimdoarquivo=find_end(randomAccessFile);
        
        writeRandomAccessFile(fimdoarquivo, bytearray,true,tamanho,randomAccessFile);
        
        randomAccessFile.close();
			
	}
    public long find_end(RandomAccessFile raf) throws IOException{
        
    	long tail=0;
        
    	tail=(long)raf.length();
    	
    	return tail;//retorna o valor do fim do arquivo(EOF)
    }
	//processo de escrita
    public void writeRandomAccessFile(long posicao, byte[]bytearray,
    		
    		boolean lapide,int tamanho, RandomAccessFile raf)throws IOException{
        
            raf.seek(posicao);//busca a posição designada no arquivo
            
            raf.writeBoolean(lapide);//escreve o boolean lapide
            
            raf.writeInt(tamanho);//escreve o tamanho do vetor

            raf.write(bytearray);//escreve o vetor no arquivo
            
            
            
    }
}