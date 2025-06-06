package estagio1.leitura;

import java.io.*;
import java.util.*;

import estagio1.DataObject;

public class LeitorArquivo {
	
	public static void main(String[] args) {
		
		String userP=System.getProperty("user.home");//Pasta do Usuario do PC
		String folder="Documents";//Local padrão
        String sep = File.separator;// Separador do sistema operacional em uso
		String folder_file="TP_AEDS_III";
		
		String name_file="traffic_accidents_pt_br_rev2.csv";
		
		String Path=userP.concat(sep+folder).concat(sep+folder_file).concat(sep+name_file);
		
		String pathDb="data/traffic_accidents.db";
	    
		ReadProcess.readAll(pathDb,4,7);
	}
	public static void optionsMain(String pathDb,String pathIndex) {
		int op=0;
		int Id=0;
		
  		do {
  			System.out.println("\n==================================================");
  			System.out.println("\nProcessos de leitura\n");
  			System.out.println("1) Ler todos os registros");
  			System.out.println("2) Ler apenas um registro");
  			System.out.println("3) Atualizar um registro");
  			System.out.println("4) Apagar registro");
			System.out.println("\n0) Sair\n\nEscolha um valor-------> :");
			op=Functions.only_Int();
			switch(op) {
				case 1:
					ReadProcess.readAll(pathDb,1,0);//Todos
					break;
				case 2:
					System.out.println("Digite a ID desejada :");
					Id=Functions.only_Int();
					ReadProcess.readAll(pathDb,2,Id);//Um
				    break;
				case 3:	
					System.out.println("Digite a ID desejada :");
					Id=Functions.only_Int();
					ReadProcess.readAll(pathDb,3,Id);
					break;
				case 4:
					System.out.println("Digite a ID desejada :");
					Id=Functions.only_Int();
					ReadProcess.readAll(pathDb,4,Id);//Um
					break;
				
				default:
					if(op==0) {
						System.out.println("\nVoltando ao Menu da Parte I.");
					}else {
						System.out.println("\nTente novamente, escolha fora do escopo.");
					}
			}
		}while(op!=0);
			
	}

	//===============================================================================Funções Internas
  	public static int getLastID(RandomAccessFile randomAccessFile) throws IOException{
  	//Identificação do valor no cabeçalho para o leitor de arquivo
		
		int ID=randomAccessFile.readInt();
		
		return ID;
	}
  	
  	//Identificação do valor no cabeçalho para o escritor de arquivo
    public static int getHeader(String path)throws IOException{
        
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
    //obtendo o fim do arquivo
    public static long find_end(RandomAccessFile raf) throws IOException{
        
    	long tail=0;
        
    	tail=(long)raf.length();
    	
    	return tail;//retorna o valor do fim do arquivo(EOF)
    }
    public static byte[] buildArray(RandomAccessFile randomAccessFile, long posicao) throws IOException{
	    
    	randomAccessFile.seek(posicao);
    	
    	int tamanho=randomAccessFile.readInt();//leitura do tamanho do vetor
	       
	    byte[] bytearray=new byte[tamanho];//Instancia um novo vetor de bytes 
		
		randomAccessFile.read(bytearray);//leitura do vetor
		
		return bytearray;
    }
    public static String showIndex(int ID,boolean lapide,int tamanho, long posicao) {
		if (posicao!=-1) {
			return "\nID lida: -----------------------------> "+ID
					+"\nValidade------------------------------> "+lapide
					+"\nTamanho do registro-------------------> "+tamanho+
					"\nPosição do registro-------------------> "+posicao;
		}else{
			return "\nID lida: -----------------------------> "+ID
				+"\nValidade------------------------------> "+lapide
				+"\nTamanho do registro-------------------> "+tamanho;
				
		}
	}
}
