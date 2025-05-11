package object.indexed.tree;
//https://chatgpt.com/canvas/shared/681e82e457048191afea23fcc5c01bd4
import java.io.EOFException;
import java.io.IOException;
import java.io.RandomAccessFile;

import estagio1.leitura.Functions;
import estagio1.leitura.LeitorArquivo;
import object.DataTreeObject;

public class EscritorTree {
	
	public static void cargaBase(ArvoreB btree, int condition,String pathFile,String pathDb){
		
    	System.out.println("Caminho recebido: "+pathFile);
    	
    	RandomAccessFile rafTreeReader=null;
    	
    	DataTreeObject object;
    	
    	if (condition==2) {
			//Criação de registro
    		try {
				
    			object=LeitorTree.newObject(new DataTreeObject(),pathDb);//Novo Objeto
				
    			System.out.println("Registro gravado com SUCESSO na id "+create(btree,object, pathDb));
			
    		}catch(IOException e) {
    			System.out.println("Ocorreu um erro na analise do arquivo de dados");
    		} catch (Exception e) {
				System.out.println("Ocorreu um erro ao criar o registro");
			}//----------------------------------//Inicia o Processo de escrita do objeto
            
		}else {
		
			
			if(Functions.findFile(pathFile)){
				try {
					
					rafTreeReader = new RandomAccessFile(pathFile,"r");
		    		
					System.out.println(rafTreeReader.readLine());//leitura para ignora o cabeçalho do arquivo .csv, mas exibe(FeedBack apenas)
		            
		            System.out.println("================================================================================================");
		            
		            
		            while (true||rafTreeReader.readLine()!=null) {
		            	
		            	String[] line=rafTreeReader.readLine().split(";");
		                
		                int id=LeitorArquivo.getHeader(pathDb);//recebe o valor presente no cabeçalho
		                
		            	object = new DataTreeObject(line,++id);//Instancia objeto incrementando a ID
		            	
		            	try {
							
		            		System.out.println("Registro gravado com SUCESSO na id "+create(btree,object,pathDb));
		            		
		            		System.out.println(object.toStringObject());
						
		            	} catch (Exception e) {
						
		            		System.out.println("Ocorreu um erro ao criar o registro");
						
		            	}//----------------------------------//Inicia o Processo de escrita do objeto
		                
		                System.out.println("================================================================================================");
		
		            }
				} catch (NullPointerException n) {
		             System.out.println("Fim da leitura e escrita do arquivo .db.");            
				} catch (IOException ioe) {
		            ioe.printStackTrace();
		        } finally {
		            try {
		            	rafTreeReader.close();
		            } catch (IOException ioe) {
		                ioe.printStackTrace();
		            }
		        }
			}else {
				System.out.println("Não localizei o arquivo.");
			}
		}
	}
    
    public static int create(ArvoreB btree,DataTreeObject obj,String pathDb) throws Exception {
		
    	RandomAccessFile file; //Objeto usado para fazer acesso aleatório no arquivo de dados
    	
    	byte[] bytearray;
		int tamanho=0;
		//Encriptação
		
		
		//Gravação
		try {
			//Inicia o RandomAccessFile
			//criando o arquivo de dados no Diretorio da Arvore B
			file = new RandomAccessFile(pathDb, "rw");
					
			//O ponteiro é levado para o ínicio do arquivo, caso o arquivo esteja vazio, é escrito a ID
			file.writeInt(obj.getID_registro());
			
			//O Livro a ser registrado recebe o último id mais um e o último id é atualizado no inicio do arquivo
			
			bytearray = obj.toByteArray();
			
			tamanho=bytearray.length;
			
			// É criado um registro em formato de vetor de bytes para o objeto
			
			
			long pointerRegistry=LeitorArquivo.find_end(new RandomAccessFile(pathDb, "rw"));
			
			//O par chave/endereço é inserido nos arquivos de índice
			writeRafTreeData(pointerRegistry, bytearray,true,tamanho,new RandomAccessFile(pathDb, "rw"));
			
			insertOnTree(obj.getID_registro(),pointerRegistry, btree);
			//O tamanho do registro e o registro propriamente dito são escritos no arquivo
			
			return obj.getID_registro();
			
		} catch (EOFException e) {
			System.out.println("fim de arquivo");
			return obj.getID_registro();	
		} catch (IOException e) {
			e.printStackTrace();
			return -1;
		}
		
	}
    public static void writeRafTreeData(long pointerRegistry, 
    									byte[]bytearray,
    									boolean lapide,
    									int tamanho, 
    									RandomAccessFile rafTree)throws IOException{
    	rafTree.seek(pointerRegistry);//busca a posição designada no arquivo
        
    	rafTree.writeBoolean(lapide);//escreve o boolean lapide
        
    	rafTree.writeInt(tamanho);//escreve o tamanho do vetor

    	rafTree.write(bytearray);//escreve o vetor no arquivo
		
	}
	
    public static void insertOnTree(int ID_Registro,long pointerRegistry,ArvoreB btree)throws IOException, Exception{
		//O ponteiro é levado até o fim do arquivo
		btree.inserir(ID_Registro, pointerRegistry);//Inserção na arvore ID e posição
		//-------------------------------------------------//Escrita no Bucket(Lista Invertida)
	}
    
    
    
    //Leitura
    public static DataTreeObject read(ArvoreB btree, int id, String pathDb) throws Exception {
    	RandomAccessFile file; //Objeto usado para fazer acesso aleatório no arquivo de dados
    	
    	DataTreeObject aux=null;
    	try {
    		file = new RandomAccessFile(pathDb, "r");
			
			long address = btree.search(id);
			if(address != -1) {
				file.seek(address);
				boolean lapide=file.readBoolean();
				
				if(lapide==true) {
					int length = file.readInt();
					byte[] b = new byte[length];
					file.read(b);
					aux = new DataTreeObject();
					aux.fromByteArray(b);
					
					//Decriptação
					
					return aux;
				}else {
					//Chama o processo de exclusão na arvore
					btree.remove(id);
					
					//Se o registro foi encontrado mas estava marcado como excluido, retorna-se nulo
					return null;
				}	
			}
			else {
				//Se o registro não for encontrado, retorna-se nulo
				return null;
			}
		} catch (EOFException e) {
			System.out.println("fim de arquivo");
			return aux;
			
		} catch (IOException e) {
			e.printStackTrace();
			return null;
		}
		
	}
    //Update
    
	//Delete

}
