package bruno;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.Scanner;
import java.io.File;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Paths;
import static java.nio.file.StandardCopyOption.*;

public class Main {
	
	static Scanner scanner = new Scanner(System.in);
	static File file_aux; //Objeto utilizado para controlar o arquivo de dados
	static RandomAccessFile file; //Objeto usado para fazer acesso aleatório no arquivo de dados
	static ArvoreB btree;
	static Multilista multilista;

    public static void main(String[] args) throws Exception {
    	
        String arquivoCSV = "csv/imdb_movies.csv";
        
        //Localização da base de dados no formato csv no diretório do projeto
        
        File dbDir = new File("db");
        dbDir.mkdir();
        file_aux = new File("db/banco.db");
		file = new RandomAccessFile(file_aux, "rw");
		
		//O arquivo de dados é criado na pasta "db" e é aberto para o acesso aleatório
		
		btree = new ArvoreB("btree.index", 10);
		multilista = new Multilista();
		//São instanciados os objetos dos arquivos de índice
				
		if(file.length() == 0) {
			System.out.print("Deseja fazer a carga da base de dados? (s ou S para confirmar) ");
			String aux = scanner.nextLine();
			if(aux.equalsIgnoreCase("s")) {
				System.out.print("Digite a quantidade de registros a serem carregados (até 10178): ");
				int qtdReg = scanner.nextInt();
				while(qtdReg < 0 || qtdReg > 10178) {
					System.out.print("Quantidade inválida, digite novamente: ");
					qtdReg = scanner.nextInt();
				}
				scanner.nextLine();
				System.out.println("Carregando........");
				
				cargaBase(arquivoCSV, qtdReg); 
				//Se o arquivo de dados estiver vazio, é feita a carga da base
				
				crud(); 
				//Depois de o arquivo ser carregado com os registros da base, a interface do crud é executada
			}

		}
		else {
			crud();
			//Se o arquivo já estiver preenchido, a interface do crud é imediatamente executada
		}
		
		scanner.close();
		file.close();
		
		//Por fim, fecha-se o acesso aleatório ao arquivo de dados
        
    }

	private static void crud() throws Exception {
		Movie movie;
		int contComp = 1;
		String msg = "Digite FIM para finalizar a execução do programa." + "\n" + "Create, Read, Update, Delete, Sort, Compress, Decompress ou Casamento? ";
		System.out.print(msg);
		String aux = scanner.nextLine();
		
		while(!aux.equalsIgnoreCase("FIM")) {
			
			movie = new Movie(); //Para cada opção escolhida pelo usuário, instancia-se um novo objeto do tipo filme
			
			if(aux.equalsIgnoreCase("create")) {
				entrada(movie); //Para criar um registro, primeiramente ele deve ter seus dados preenchidos pelo usuário
				int id = create(movie);
				if(id != -1) {
					System.out.println("Filme registrado com SUCESSO com id " + id);
				}
				else {
					System.out.println("Ocorreu um erro ao criar o registro");
				}
			}
			else if(aux.equalsIgnoreCase("read")) {
				System.out.print("Deseja pesquisar por id(1), país(2), ano(3) ou país e ano(4)? ");
				int answer = scanner.nextInt();
				if(answer == 1) {
					System.out.print("ID: ");
					movie = read(scanner.nextInt());
					if(movie != null) {
						movie.exibir();
					}
					else {
						System.out.println("ERRO: Registro nao encontrado!");
					}
					
					scanner.nextLine();
					//Limpando o buffer para que a próxima entrada não seja descartada
				}
				else if(answer == 2) {
					System.out.print("Digite o país: ");
					scanner.nextLine();
					String country = scanner.nextLine();
					
					ArrayList<Integer> array = multilista.search(country); 
					int i;
					for(i=0; i<array.size(); i++) {
						movie = read(array.get(i));
						if(movie != null) {
							movie.exibir();
							System.out.println("\n------------------------------------------------------------\n");
						}
						else {
							System.out.println("ERRO: Registro nao encontrado!");
						}
					}
					//A pesquisa na multilista retorna um array de ids, que são usados para busca no arquivo de índices
					if(i == 0) {
						System.out.println("Nenhum registro com o país " + country + " foi encontrado");
					}
				}
				else if(answer == 3) {
					System.out.print("Digite o ano: ");
					int year = scanner.nextInt();
					ArrayList<Integer> array = multilista.search(year);
					int i;
					for(i=0; i<array.size(); i++) {
						movie = read(array.get(i));
						if(movie != null) {
							movie.exibir();
							System.out.println("\n------------------------------------------------------------\n");
						}
						else {
							System.out.println("ERRO: Registro nao encontrado!");
						}
					}
					if(i == 0) {
						System.out.println("Nenhum registro com o ano " + year + " foi encontrado");
					}
					
					scanner.nextLine();
				}
				else if(answer == 4) {
					System.out.print("Digite o ano: ");
					int year = scanner.nextInt();
					System.out.print("Digite o país: ");
					scanner.nextLine();
					String country = scanner.nextLine();
					ArrayList<Integer> arrayYear = multilista.search(year);
					ArrayList<Integer> arrayCountry = multilista.search(country); 
					ArrayList<Integer> array = intercessao(arrayYear, arrayCountry);
					
					int i;
					for(i=0; i<array.size(); i++) {
						movie = read(array.get(i));
						if(movie != null) {
							movie.exibir();
							System.out.println("\n------------------------------------------------------------\n");
						}
						else {
							System.out.println("ERRO: Registro nao encontrado!");
						}
					}
					if(i == 0) {
						System.out.println("Nenhum registro com o ano " + year + " e com o país " + country + " foi encontrado");
					}
				}
				
			}
			
			else if(aux.equalsIgnoreCase("delete")) {
				System.out.print("ID: ");
				movie = delete(scanner.nextInt());
				if(movie != null) {
					multilista.remover(movie.getId(), movie.getCountry(), movie.getYear());
					System.out.println("O seguinte registro foi excluído com SUCESSO");
					movie.exibir();
				}
				else {
					System.out.println("ERRO: Registro nao encontrado");
				}
				
				scanner.nextLine();
			}
			else if(aux.equalsIgnoreCase("update")) {
				System.out.print("ID: ");
				movie.setId(scanner.nextInt()); //Como se trata de uma atualização, o id do registro é definido pelo usuário, já que ele se trata do id do filme que será substituído
				scanner.nextLine(); //Limpando o buffer
				entrada(movie);
				Movie tmp = update(movie);
				//O método retorna o filme que foi substituído, para que as informações não sejam perdidas
				if(tmp != null) {
					
					if(!tmp.getCountry().equalsIgnoreCase(movie.getCountry()) || tmp.getYear() != movie.getYear()) {
						multilista.remover(movie.getId(), movie.getCountry(), movie.getYear());
						multilista.inserir(tmp.getId(), tmp.getCountry(), tmp.getYear());
						//As informações são atualizadas no índice secundário
					}
					
					System.out.println("O filme foi atualizado com SUCESSO!");
					System.out.println("As informações antigas eram as seguintes");
					tmp.exibir();
				}
				else {
					System.out.println("ERRO: Registro não encontrado");
				}

			}
			else if(aux.equalsIgnoreCase("sort")) {
				try {
					sort();
					System.out.println("Registros ordenados com sucesso!");
		            //Caso o processo tenha ocorrido normalmente, é sinalizado para o usuário
					
				} catch(IOException e) {
					e.printStackTrace();
				}
				
			}
			else if(aux.equalsIgnoreCase("compress")) {
				String nomeAux = "bancoCompressao" + contComp;
				compress(nomeAux);
				System.out.println("O arquivo compactado gerado tem nome " + nomeAux);
			}
			else if(aux.equalsIgnoreCase("decompress")) {
				System.out.print("Digite a versão do arquivo a ser descompactado: ");
				int verAux = scanner.nextInt();
				while(verAux < 1 || verAux > contComp) {
					System.out.println("Versão inválida, digite novamente:");
					verAux = scanner.nextInt();
				}
				decompress("bancoCompressao" + verAux);
				scanner.nextLine();
			}
			else if(aux.equalsIgnoreCase("casamento")) {
				System.out.print("Digite o padrão a ser procurado: ");
				String pattern = scanner.nextLine();
				casamento(pattern);
			}
			else {
				System.out.println("Opção inválida!");
			}
			System.out.print(msg);
			aux = scanner.nextLine();
		}
		
	}
	
	private static ArrayList<Integer> intercessao(ArrayList<Integer> arrayYear, ArrayList<Integer> arrayCountry) {
		ArrayList<Integer> resp = new ArrayList<Integer>();
		for(int i=0; i<arrayYear.size(); i++) {
			for(int j=0; j<arrayCountry.size(); j++) {
				if(arrayYear.get(i).equals(arrayCountry.get(j))) {
					resp.add(arrayYear.get(i));
					break;
				}
			}
		}
		return resp;
	}

	private static void entrada(Movie movie) {
		String aux;
		byte auxByte;
		int auxint;
		float auxFloat;
		double auxDouble;
		
		System.out.print("Nome: ");
		movie.setName(scanner.nextLine());
		
		System.out.print("Dia: ");
		auxByte = scanner.nextByte();
		while(auxByte < 1 || auxByte > 31) {
			System.out.print("Dia inválido, digite um dia de 1 a 31: ");
			auxByte = scanner.nextByte();
		}
		movie.setDay(auxByte);
		//Os valores válidos para dia vão de 1 a 31
		
		System.out.print("Mês: ");
		auxByte = scanner.nextByte();
		while(auxByte < 1 || auxByte > 12) {
			System.out.print("Mês inválido, digite um mês de 1 a 12: ");
			auxByte = scanner.nextByte();
		}
		movie.setMonth(auxByte);
		//Os valores válidos para mês vão de 1 a 12
		
		System.out.print("Ano: ");
		auxint = scanner.nextInt();
		while(auxint < 0) {
			System.out.print("Ano inválido, digite um ano positivo: ");
			auxint = scanner.nextInt();
		}
		movie.setYear(auxint);
		
		System.out.print("Pontuação: ");
		auxFloat = scanner.nextFloat();
		while(auxFloat < 0 || auxFloat > 100) {
			System.out.print("Pontuação inválida, digite uma pontuação de 0 a 100: ");
			auxFloat = scanner.nextFloat();
		}
		movie.setScore(auxFloat);
		//A pontuação é de 0 a 100
		
		scanner.nextLine(); //Limpando o "\n" do buffer
		
		System.out.print("Generos(digite FIM para terminar a entrada): ");
		String[] str_array = new String[256]; //Como o indicador de tamanho para gêneros é de 1 Byte, são aceitos no máximo 256 gêneros
		byte i = 0;
		aux = scanner.nextLine();
		while(!aux.equalsIgnoreCase("fim") && i < str_array.length) {
			str_array[i] = aux;
			aux = scanner.nextLine();
			i++;
		}
		
		String[] genres = new String[i];
		for(byte j = 0; j < i; j++) {
			genres[j] = str_array[j];
		}
		movie.setGenres(genres);
		//Os gêneros digitados pelo usuário são armazenados no objeto
		
		System.out.print("Resumo: ");
		movie.setOverview(scanner.nextLine());
		
		System.out.print("Elenco (digite FIM para terminar a entrada): ");
		str_array = new String[256];
		aux = scanner.nextLine();
		i = 0;
		while(!aux.equalsIgnoreCase("fim") && i < str_array.length) {
			str_array[i] = aux;
			aux = scanner.nextLine();
			i++;
		}
		String[] crew = new String[i];
		for(byte j=0; j<i; j++) {
			crew[j] = str_array[j];
		}
		movie.setCrew(crew);
		//Segue a mesma lógica da entrada dos gêneros 
		
		System.out.print("Titulo original: ");
		movie.setOrigTitle(scanner.nextLine());
		
		System.out.print("Status(r para released, p para post-released, i para in production): ");
		movie.setStatus(scanner.next().charAt(0));
		
		scanner.nextLine(); //Eliminando o \n do buffer
		
		System.out.print("Lingua original: ");
		movie.setOrigLang(scanner.nextLine());
		
		System.out.print("Orçamento: ");
		auxDouble = scanner.nextDouble();
		while(auxDouble < 0) {
			System.out.print("Digite um orçamento positivo: ");
			auxDouble = scanner.nextDouble();
		}
		movie.setBudget(auxDouble);
		
		System.out.print("Receita: ");
		movie.setRevenue(scanner.nextDouble());
		
		scanner.nextLine(); //Limpando o "\n" do buffer
		
		System.out.print("País: ");
		movie.setCountry(scanner.nextLine());
	}

	private static void cargaBase(String arquivoCSV, int qtdReg) throws Exception {
		
        Movie movie;
        try (BufferedReader br = new BufferedReader(new FileReader(arquivoCSV))) {
            br.readLine();            
            //Pula a primeira linha, já que ela só apresenta o nome das variáveis
            int cont = 0;
            String linha = br.readLine();
            while (linha != null && cont < qtdReg) {
            	movie = new Movie();
            	lineToObject(linha, movie); //Para cada linha, é preenchido o filme com as informações descritas em csv
            	create(movie); //Cada um dos filmes da base de dados é adicionado ao arquivo de dados
            	cont++;
            	linha = br.readLine();
            }
            System.out.println(cont + " registros foram gravados na base de dados com sucesso!");
        } catch (IOException e) {
            e.printStackTrace();
        }
	}

	private static Movie read(int id) throws Exception {
		try {
			Movie aux;
			long adress = btree.search(id);
			if(adress != -1) {
				file.seek(adress);
				int length = file.readInt();
				byte[] b = new byte[length];
				file.read(b);
				aux = new Movie();
				aux.fromByteArray(b);
				
				String overview = aux.getOverview();
				overview = cesarDecrypt(overview, 61);
				overview = vigenereDecrypt(overview, "algoritmos");
				aux.setOverview(overview);
				//Antes de ser retornado, o objeto lido tem seu resumo descriptografado
				
				return aux;
			}
			else {
				//Se o registro não for encontrado, retorna-se nulo
				return null;
			}
			
		} catch (IOException e) {
			e.printStackTrace();
			return null;
		}
		
	}

	private static int create(Movie movie) throws Exception {
		byte[] b;
		String overview = movie.getOverview();
		overview = vigenereEncrypt(overview, "algoritmos");
		overview = cesarEncrypt(overview, 61);
		movie.setOverview(overview);
		//Antes do registro ser escrito no arquivo de dados, seu resumo é criptografado duas vezes
		System.out.println("aqui create");//
		try {
			file.seek(0);
			
			if(file.length() == 0) {
				file.writeInt(0);
				file.seek(0);
			}
			
			//O ponteiro é levado para o ínicio do arquivo, caso o arquivo esteja vazio, é escrito o número 0
			
			System.out.println("aqui create");//
			movie.setId((file.readInt() + 1));
			file.seek(0);
			file.writeInt(movie.getId());
			
			//O Livro a ser registrado recebe o último id mais um e o último id é atualizado no inicio do arquivo
			
			b = movie.toByteArray();
			
			// É criado um registro em formato de vetor de bytes para o objeto
			
			file.seek(file.length());
			
			//O ponteiro é levado até o fim do arquivo
			
			btree.inserir(movie.getId(), file.length());
			System.out.println("aqui create");//
			multilista.inserir(movie.getId(), movie.getCountry(), movie.getYear());
			
			//O par chave/endereço é inserido nos arquivos de índice
			
			file.writeInt(b.length);
			file.write(b);
			
			//O tamanho do registro e o registro propriamente dito são escritos no arquivo
			System.out.println(movie.getId());//
			
			return movie.getId();
			
		} catch (IOException e) {
			e.printStackTrace();
			return -1;
		}
		
	}
	
	private static Movie update(Movie newMovie) throws Exception {
		  try {
			  String overview = newMovie.getOverview();
			  overview = vigenereEncrypt(overview, "Algoritmos");
			  overview = cesarEncrypt(overview, 61);
			  newMovie.setOverview(overview);
			  //Antes do registro ser escrito no arquivo de dados, seu resumo é criptografado duas vezes
				
			  
			  long adress = btree.search(newMovie.getId());
			  //O id do novo filme é usado para procurar o par chave/endereço no arquivo de índice
			  
			  if(adress != -1) {
				  //Nesse caso, a chave existe no índice
				  
				  file.seek(adress);
				  int length = file.readInt();
				  byte[] ba = new byte[length];
				  file.read(ba);
				  //O registro antigo é armazenado em ba
				  
				  byte[] bNew = newMovie.toByteArray();

				  if(bNew.length <= ba.length) {
					  //Se o endereço do registro no arquivo de dados for preservado, basta sobrescrever as informações
					  file.seek(adress + 4);
					  file.write(bNew);
				  }
				  else {
					  //Caso contrário, é necessário atualizar o endereço do registro no arquivo de índices
					  btree.updateAddress(newMovie.getId(), file.length());
					  file.seek(adress + 4);
					  file.writeBoolean(false);
					  file.seek(file.length());
					  file.writeInt(bNew.length);
					  file.write(bNew);
				  }
				  newMovie = new Movie();
				  newMovie.fromByteArray(ba);
				  return newMovie;
			  }

			  
		  } catch (IOException e) {
			  e.printStackTrace();
		  }
		  
		  return null;
		  //Se a chave não existir no arquivo de índice, é retornado nulo
		  
	}
	
	private static Movie delete(int id) throws Exception {
		  
		  try{
			  long adress = btree.remove(id);
			  if(adress == -1) {
				  //Nesse caso, nenhum par chave/endereço com a chave passada por parâmetro foi encontrada no arquivo de índice
				  return null;
			  }
			  else {
				  //Caso a chave seja encontrada no arquivo de índice, ainda é necessário sinalizar a lápide no arquivo de dados
				  file.seek(adress);
				  int length = file.readInt();
				  byte[] ba = new byte[length];
				  file.read(ba);
				  Movie movie = new Movie();
				  movie.fromByteArray(ba);
				  file.seek(adress + 4);
				  file.writeBoolean(false);
				  return movie;
			  }
//			  file.seek(2);
//			  Movie aux;
//			  while(file.getFilePointer() < file.length()) {
//				  int length = file.readInt();
//				  long pos = file.getFilePointer();
//				  byte[] b = new byte[length];
//				  file.read(b);
//				  //O registro é lido e o array de bytes é preenchido
//				  if(b[0] == 1) {
//					  aux = new Movie();
//					  aux.fromByteArray(b);
//					  //Se o registro for válido, um objeto auxlixar é preenchido
//					  if(aux.getId() == id) {
//						  file.seek(pos);
//						  file.writeBoolean(false);
//						  return aux;
//						  //Se o registro tiver o id procurado, ele é desvalidado no arquivo de dados
//					  }
//				  }
//			  }
			  
		  }
		  catch(IOException e) {
			  e.printStackTrace();
		  }
		  return null;
	  }
	
	private static void sort() throws Exception{
		
		File tmpDir = new File("tmp");
		tmpDir.mkdir();
		
		File aux1 = new File("tmp/tempFile1.db");
        File aux2 = new File("tmp/tempFile2.db");
        File aux3 = new File("tmp/tempFile3.db");
        File aux4 = new File("tmp/tempFile4.db");

        RandomAccessFile tempFile1 = new RandomAccessFile(aux1, "rw");
        RandomAccessFile tempFile2 = new RandomAccessFile(aux2, "rw");
        RandomAccessFile tempFile3 = new RandomAccessFile(aux3, "rw");
        RandomAccessFile tempFile4 = new RandomAccessFile(aux4, "rw");
        
        //São definidos os arquivos temporários usados para ordenação (2n = 2*2 = 4)
        
        escreverBlocosOrdenados(tempFile1, tempFile2);
      
        // Os primeiros 2 arquivos são preenchidos com os blocos ordenados
        
        int i=0, blocosArq1, blocosArq2, tamanho_grupo;             
        tempFile1.seek(0);
        tempFile2.seek(0);
        blocosArq1 = tempFile1.readInt();
        blocosArq2 = tempFile2.readInt();
        //Os arquivos temporários tem como cabeçalho a quantidade de blocos ordenados existentes na fita, sendo assim, essa informação é lida para controle do algoritmo
        
        tamanho_grupo = 40;
        //O primeiro grupo de registros a ser intercalado contém um bloco do arq1 e 1 bloco do arq 2, portanto tem tamanho 40
        
        RandomAccessFile entrada1, entrada2, destino1, destino2;
        
        while(blocosArq1 > 1 || blocosArq2 > 1) { //A intercalação é feita até que só exista um bloco nos dois arquivos
        	
        	if(i % 2 == 0) {
        		entrada1 = tempFile1;
        		entrada2 = tempFile2;
        		destino1 = tempFile3;
        		destino2 = tempFile4;
        	}
        	else {
        		entrada1 = tempFile3;
        		entrada2 = tempFile4;
        		destino1 = tempFile1;
        		destino2 = tempFile2;
        	}
        	//Primeiramente, decide-se qual grupo de arquivos temporários será usado como destino para a intercalação dos outros dois
        	
        	destino1.setLength(0);
        	destino2.setLength(0);
        	//Para evitar que blocos ordenados escritos nas intercalações anteriores sejam reconsiderados, os arquivos de destino da intercalação atual tem seus registros apagados
        	
        	destino1.seek(0);
        	destino2.seek(0);
        	
        	destino1.writeInt(0);
        	destino2.writeInt(0);
        	//A quantidade inicial de blocos ordenados nos arquivos de destino da intercalação atual é 0
        	
        	Movie movie1, movie2;
    		byte[] ba1, ba2;
    		int length1, length2, pointer1, pointer2;
    		        		
    		entrada1.seek(2);
    		entrada2.seek(2);
    		//Pula-se o cabeçalho dos arquivos temporários a serem intercalados
    		
    		RandomAccessFile destino_grupo;
        	
        	for(int k=0; k<blocosArq1; k++) {
        		//A quantidade de grupos intercalados é igual a quantidade de blocos ordenados existentes no arq entrada 1
        		            		
        		if(k % 2 == 0) {
        			destino_grupo = destino1;
        		}
        		else {
        			destino_grupo = destino2;
        		}
        		//Para cada grupo a ser intercalado, é definido qual dos arquivos de destino será o destino desse grupo
        		
        		pointer1 = pointer2 = 0;
        		
        		if(entrada1.getFilePointer() < entrada1.length()) {
        			
        			length1 = entrada1.readInt();
        			ba1 = new byte[length1];
        			entrada1.read(ba1);
        			movie1 = new Movie();
        			movie1.fromByteArray(ba1);
        			
        		}
        		else {
        			movie1 = null;
        			ba1 = null;
        		}
        		
        		if(entrada2.getFilePointer() < entrada2.length()) {
        			
        			length2 = entrada2.readInt();
            		ba2 = new byte[length2];	
            		entrada2.read(ba2);	
            		movie2 = new Movie();
            		movie2.fromByteArray(ba2);
        			
        		}
        		else {
        			movie2 = null;
        			ba2 = null;
        		}
        		//Os primeiros registros pertencentes ao grupo nos arquivos 1 e 2 são lidos

            	while(movie1 != null || movie2 != null) { //Enquanto algum dos registros não for nulo
            		
            		if((movie1 != null && movie2 != null && movie1.getId() < movie2.getId()) || (movie1 != null && movie2 == null)) {
            			
            			destino_grupo.seek(destino_grupo.length());
            			
            			destino_grupo.writeInt(ba1.length);
            			destino_grupo.write(ba1);
            			//Se o objeto do arquivo 1 tiver id menor ou for o único não nulo dentre os dois, ele deve ser escrito no arquivo de destino do grupo
            			
            			if(pointer1 < ((tamanho_grupo/2) - 1) && entrada1.getFilePointer() < entrada1.length()) {
            				
            				length1 = entrada1.readInt();
                			
                			ba1 = new byte[length1];
                			
                			entrada1.read(ba1);
                			
                			movie1.fromByteArray(ba1);
                			
                			pointer1++;
                			
                			//Se o próximo registro do arquivo 1 pertencer ao grupo e o arquivo não estiver no fim, lê-se o próximo registro
                			
            			}
            			else {
            				
            				movie1 = null;
            				
            			}
            			                			
            		}
            		else{
            			
            			destino_grupo.seek(destino_grupo.length());
            			
            			destino_grupo.writeInt(ba2.length);
            			destino_grupo.write(ba2);
            			
            			if(pointer2 < (tamanho_grupo/2) - 1 && entrada2.getFilePointer() < entrada2.length()) {
            				
            				length2 = entrada2.readInt();
                			
                			ba2 = new byte[length2];
                			
                			entrada2.read(ba2);
                			
                			movie2.fromByteArray(ba2);
                			
                			pointer2++;
            			}
            			else {
            				
            				movie2 = null;
            				
            			}
            			
            		}
            		
            		
            	}
            	
            	destino_grupo.seek(0);
            	int aux = destino_grupo.readInt();
            	destino_grupo.seek(0);
            	destino_grupo.writeInt(aux + 1);
            	
            	//Para cada grupo intercalado, o indicador de quantidade de blocos ordenados é incrementado no arquivo de destino dese grupo
        		
        	}
        	
        	destino1.seek(0);
        	destino2.seek(0);
        	blocosArq1 = destino1.readInt();
        	blocosArq2 = destino2.readInt();
        	tamanho_grupo *= 2;
        	//Ao final de cada intercalação, a quantidade de blocos ordenados nos arquivos de entrada da próxima iteração e o tamanho do grupo são atualizados
        	
        	i++;
        	
        }
        
        File arq_final;

        if(i % 2 == 0) {
        	
        	entrada1 = tempFile1;
        	entrada2 = tempFile2;
        	destino1 = tempFile3;
        	arq_final = aux3;
        	tempFile4.close();
        	aux4.delete();
        	
        }
        else {
        	
        	entrada1 = tempFile3;
        	entrada2 = tempFile4;
        	destino1 = tempFile1;
        	arq_final = aux1;
        	tempFile2.close();
        	aux2.delete();
        	
        }
        //Decide-se quem serão os últimos dois arquivos a serem intercalados e quem será usado como destino da última intercalação
        
        entrada1.seek(0);
        entrada2.seek(0);
        
        file.seek(0);
        int ultimo_id = file.readInt();            
        
        destino1.setLength(0); //Os blocos ordenados usados anteriormente são excluidos do arquivo
        destino1.seek(0);
        destino1.writeInt(ultimo_id);
        //Uma vez definido o arquivo de saida (destino1), é escrito nele o último id do cabeçalho do arquivo de dados original
        
        intercalarFinal(entrada1, entrada2, destino1);
        //Finalmente, é feita a última intercalação no arquivo de saída final 
        
        
        tempFile1.close();
        tempFile2.close();
        tempFile3.close();
        tempFile4.close();             
        file.close();
        file.close();
        
               
        file_aux = (Files.move(Paths.get(arq_final.toURI()), Paths.get(file_aux.toURI()), REPLACE_EXISTING)).toFile(); 
                          
        //O arquivo de dados antigo é removido e subtituído pelo novo arquivo ordenado
                    
        if(i % 2 == 0) {
        	
        	aux1.delete();
        	aux2.delete();
        	//Nesse caso, os arquivos temporários 1 e 2 devem ser apagados, já que não serão mais usados
        	
        }
        else {
        	aux3.delete();
        	aux4.delete();
        	//Nesse caso, os arquivos temporários 3 e 4 devem ser apagados, já que não serão mais usados

        }
        
        file = new RandomAccessFile(file_aux, "rw");
        // O objeto de acesso aleatório ao arquivo de dados é atualizado
        
        file.seek(2);
        long pos = 2;
        
        while(pos < file.length()) {
        	
        	int length = file.readInt();
        	byte[] ba = new byte[length];
        	file.read(ba);
        	Movie movie = new Movie();
        	movie.fromByteArray(ba);
        	btree.updateAddress(movie.getId(), pos);
        	
        	pos = file.getFilePointer();
        }
        //Depois da ordenação, é necessário atualizar o endereço dos registros no arquivo de índices
        
	}
	
	private static void intercalarFinal(RandomAccessFile entrada1, RandomAccessFile entrada2,
			RandomAccessFile destino) {
		
		try {
						
			Movie movie1, movie2;
			byte[] ba1, ba2;
			int length1, length2;
			
			movie1 = new Movie();
			movie2 = new Movie();
			
			entrada1.seek(2);
			entrada2.seek(2);
			
			if(entrada1.getFilePointer() < entrada1.length()) {
    			
    			length1 = entrada1.readInt();
    			ba1 = new byte[length1];
    			entrada1.read(ba1);
    			movie1 = new Movie();
    			movie1.fromByteArray(ba1);
    			
    		}
    		else {
    			movie1 = null;
    			ba1 = null;
    		}
    		
    		if(entrada2.getFilePointer() < entrada2.length()) {
    			
    			length2 = entrada2.readInt();
        		ba2 = new byte[length2];	
        		entrada2.read(ba2);	
        		movie2 = new Movie();
        		movie2.fromByteArray(ba2);
    			
    		}
    		else {
    			movie2 = null;
    			ba2 = null;
    		}
    		//Os primeiros registros pertencentes aos arquivos 1 e 2 são lidos
			
			while(movie1 != null || movie2 != null) {
				
				if((movie1 != null && movie2 != null && movie1.getId() < movie2.getId()) || (movie1 != null && movie2 == null)) {
					
					destino.seek(destino.length());
					destino.writeInt(ba1.length);
					destino.write(ba1);
					
					if(entrada1.getFilePointer() < entrada1.length()) {
						
						length1 = entrada1.readInt();
						ba1 = new byte[length1];
						entrada1.read(ba1);
						movie1.fromByteArray(ba1);
						
					}
					else {
						
						movie1 = null;
						
					}
				}
				else {
					
					destino.seek(destino.length());
					destino.writeInt(ba2.length);
					destino.write(ba2);
					
					if(entrada2.getFilePointer() < entrada2.length()) {
						
						length2 = entrada2.readInt();
						ba2 = new byte[length2];
						entrada2.read(ba2);
						movie2.fromByteArray(ba2);
						
					}
					else {
						
						movie2 = null;
						
					}
					
				}
				//A intercalação segue a mesma lógica da anterior, entretanto não existe um controle do tamanho do grupo a ser intercalado, já que todo o arquivo deve ser percorrido nessa intercalação
			}
			
		} catch(IOException e) {
			e.printStackTrace();
		}
		
		
	}

	private static void escreverBlocosOrdenados(RandomAccessFile tempFile1, RandomAccessFile tempFile2){
		
	
		try {
			
			Movie[] array;
			
			tempFile1.seek(0);
			tempFile2.seek(0);
			tempFile1.writeInt(0);
			tempFile2.writeInt(0);
			//Primeiramente, é escrito nos primeiros n arquivos temporários a quantidade de blocos ordenados existentes
			
			file.seek(2); // Pulando o cabeçalho do arquivo de dados
            Movie aux;
            int i = 0, length;
            int blocos;
            byte[] b;
            
            while(file.getFilePointer() < file.length()) {
            	
            	array = new Movie[20]; 
            	//Para cada bloco de 20 registros lido do arquivo de dados, instancia-se um novo array usado para armazenar o bloco
            	
            	int cont = 0;
            	
            	while(cont < array.length && file.getFilePointer() < file.length()) {
            		
            		length = file.readInt();
            		b = new byte[length];
            		file.read(b);
            		if(b[0] == 1) {
            			aux = new Movie();
            			aux.fromByteArray(b);
            			array[cont] = aux;
            			cont++;
            		}
            	}
            	//O array de objetos é preenchido com 20 (ou menos) registros válidos
            	
            	quickSort(array);
            	//O array é ordenado em memória principal
            	
            	RandomAccessFile destino;
            	
            	if(i % 2 == 0) {
            		destino = tempFile1;
            	} //Se i for par, o bloco é escrito no arq temp 1, caso contrário é escrito no arq temp 2
            	else {
            		destino = tempFile2;
            	}
            	
            	destino.seek(0);
    			blocos = destino.readInt();
    			destino.seek(0);
    			destino.writeInt(blocos + 1);
    			
    			//Para cada bloco que será escrito, é incrementado o indicador da quantidade de blocos existentes no arquivo temporário
    			
    			destino.seek(destino.length()); //O ponteiro do arq temp de destino atual é movido para o final
    			
        		for(int j=0; j<array.length && array[j] != null; j++) {
        			
        			b = array[j].toByteArray();
        			destino.writeInt(b.length);
        			destino.write(b);
        		}
            	
            	i++;
            }
			
		} catch(IOException e) {
			e.printStackTrace();
		}
		
	}
		
	
	
	private static void quickSort(Movie[] array) {
		int i;
		for(i=0; i < array.length && array[i] != null; i++);
		//Primeiro armazena-se a última posição válida do array, já que ele pode não estar completamente cheio
		quickSort(array, 0, i-1);
	}
	
	private static void quickSort(Movie[] array, int esq, int dir) {
		int i = esq, j = dir, pivo = array[(esq+dir)/2].getId();
		while (i <= j) {
		while (array[i].getId() < pivo)
			i++;
		while (array[j].getId() > pivo)
			j--;
			if (i <= j){ 
				swap(array, i, j); 
				i++; 
				j--; 
			}
		}
		if (esq < j)
			quickSort(array, esq, j);
		if (i < dir)
			quickSort(array, i, dir);
	}
	
	private static void swap(Movie[] array, int i, int j) {
		Movie tmp = array[i];
		array[i] = array[j];
		array[j] = tmp;
	}

	private static void lineToObject(String linha, Movie movie) {
		String[] campos = new String[12];
        for(int i=0; i<campos.length; i++) {
        	campos[i] = new String();
        } //É criado um vetor de strings que será usado para armazenar cada um dos campos dos filmes
        
        int i = 0;
        if(linha.charAt(i) == '"') {
        	i++;
        	while(linha.charAt(i) != '"' || linha.charAt(i+1) == '"' || linha.charAt(i-1) == '"') {
        		campos[0] += linha.charAt(i);
        		i++;
        	}
        	movie.setName(campos[0]);
        	i += 2;
        }
        else {
        	while(linha.charAt(i) != ',') {
            	campos[0] += linha.charAt(i);
            	i++;
            }
        	movie.setName(campos[0]);
            i++;
        }
        // Para cada atributo do filme que tem valor textual(String), existem duas possibilidades: o texto estar limitado por vírgula ou por aspas
       
        
        while(linha.charAt(i) != ',') {
        	campos[1] += linha.charAt(i);
        	i++;
        }
        
        String[] data = campos[1].split("/");
		movie.setMonth(Byte.parseByte(data[0]));
		movie.setDay(Byte.parseByte(data[1]));
		movie.setYear(Integer.parseInt(data[2].stripIndent()));
		
		i++;
		while(linha.charAt(i) != ',') {
			campos[2] += linha.charAt(i);
			i++;
		}
		movie.setScore(Float.parseFloat(campos[2]));
		
		i++;
		if(linha.charAt(i) == '"') {
			i++;
			while(linha.charAt(i) != '"' || linha.charAt(i+1) == '"' || (linha.charAt(i-1) == '"' && linha.charAt(i-2) != '"') || (linha.charAt(i) == '"' && linha.charAt(i-1) == '"' && linha.charAt(i-2) == '"' && linha.charAt(i-3) == ',')) {
				campos[3] += linha.charAt(i);
				i++;
			}
			
			String[] genres = campos[3].split(",");
			movie.setGenres(genres);
			
			i += 2;
		}
		else {
			while(linha.charAt(i) != ',') {
				campos[3] += linha.charAt(i);
				i++;
			}
			
			String[] genres = new String[1];
			genres[0] = campos[3];
			movie.setGenres(genres);
			
			i++;
		}
		
		if(linha.charAt(i) == '"') {
			i++;
			while(linha.charAt(i) != '"' || linha.charAt(i+1) == '"' || (linha.charAt(i-1) == '"' && linha.charAt(i-2) != '"') || (linha.charAt(i) == '"' && linha.charAt(i-1) == '"' && linha.charAt(i-2) == '"' && linha.charAt(i-3) == ',')) {
				campos[4] += linha.charAt(i);
				i++;
			}
			
			i += 2;
		}
		else {
			while(linha.charAt(i) != ',') {
				campos[4] += linha.charAt(i);
				i++;
			}
			i++;
		}
		movie.setOverview(campos[4]);
		
		if(linha.charAt(i) == '"') {
			i++;
			while(linha.charAt(i) != '"' || linha.charAt(i+1) == '"' || (linha.charAt(i-1) == '"' && linha.charAt(i-2) != '"') || (linha.charAt(i) == '"' && linha.charAt(i-1) == '"' && linha.charAt(i-2) == '"' && linha.charAt(i-3) == ',')) {
				campos[5] += linha.charAt(i);
				i++;
			}
			i += 2;
		}
		else {
			while(linha.charAt(i) != ',') {
				campos[5] += linha.charAt(i);
				i++;
			}
			i++;
		}
		
		String[] crewAux = campos[5].split(",");
		String[] crew = new String[crewAux.length / 2];
		for(int j=0; j<crew.length; j++) {
			crew[j] = new String();
			crew[j]  = crewAux[2*j] + ", " + crewAux[(2*j) + 1];
		}
		movie.setCrew(crew);
		
		// Como a base de dados dá primeiro o nome do personagem interpretado e depois o ator que o interpreta, é necessário fazer um tratamento para juntar ambos na mesma string
		
		if(linha.charAt(i) == '"') {
			i++;
			while(linha.charAt(i) != '"' || linha.charAt(i+1) == '"' || (linha.charAt(i-1) == '"' && linha.charAt(i-2) != '"') || (linha.charAt(i) == '"' && linha.charAt(i-1) == '"' && linha.charAt(i-2) == '"' && linha.charAt(i-3) == ',')) {
				campos[6] += linha.charAt(i);
				i++;
			}
			movie.setOrigTitle(campos[6]);
			i += 3;
		}
		else {
			while(linha.charAt(i) != ',') {
				campos[6] += linha.charAt(i);
				i++;
			}
			movie.setOrigTitle(campos[6]);
			
			i += 2;
		}
		
		while(linha.charAt(i) != ',') {
			campos[7] += linha.charAt(i);
			i++;
		}
		if(campos[7].equals("Released")) {
			movie.setStatus('r');
		}
		else if(campos[7].equals("Post Production")) {
			movie.setStatus('p');
		}
		else {
			movie.setStatus('i');
		}
		
		i++;
		if(linha.charAt(i) == '"') {
			i += 2;
			while(linha.charAt(i) != '"') {
				campos[8] += linha.charAt(i);
				i++;
			}
			movie.setOrigLang(campos[8]);
			i += 2;
		}
		else {
			i++;
			while(linha.charAt(i) != ',') {
				campos[8] += linha.charAt(i);
				i++;
			}
			movie.setOrigLang(campos[8]);
			
			i++;
		}
		
		while(linha.charAt(i) != ',') {
			campos[9] += linha.charAt(i);
			i++;
		}
		movie.setBudget(Double.parseDouble(campos[9]));
		
		i++;
		while(linha.charAt(i) != ',') {
			campos[10] += linha.charAt(i);
			i++;
		}
		movie.setRevenue(Double.parseDouble(campos[10]));
		
		i++;
		while(i < linha.length() ) {
			campos[11] += linha.charAt(i);
			i++;
		}
		movie.setCountry(campos[11]);
	}
	
	/*private static void exibirIds(RandomAccessFile arquivo) {
		try {
			Movie aux;
			byte[] b;
			int length, i = 0;
			arquivo.seek(2);
			while(arquivo.getFilePointer() < arquivo.length()) {
				length = arquivo.readInt();
				b = new byte[length];
				arquivo.read(b);
				if(b[0] == 1) {
					aux = new Movie();
					aux.fromByteArray(b);
					System.out.println(aux.getId());
					i++;
				}
			}
			System.out.println("Existem " + i + " registros validos no arquivo");
		} catch (IOException e) {
			e.printStackTrace();
		}

	} */
	
	//Esse é um método auxiliar que foi utilizado para conferir o resultado da ordenação, deixei no projeto se por ventura for necessário realizar novos testes
	
	private static void compress(String fileName) throws IOException {
		
		File lzwDir = new File("lzw");
        lzwDir.mkdir();
		File compFileAux = new File("lzw/" + fileName + ".lzw");
		RandomAccessFile compFile = new RandomAccessFile(compFileAux, "rw");
		//É criado o arquivo de saída da compactação
		
		int maxValue = Integer.MAX_VALUE;
		ArrayList<ArrayList<Byte>> dicionario = new ArrayList<ArrayList<Byte>>(maxValue);
		for(int i=0; i<256; i++) {
			ArrayList<Byte> aux = new ArrayList<Byte>(1);
			aux.add((byte)(i - 128));
			dicionario.add(aux);
		}
		//O dicionário é inicializado com todos os valores que um byte pode assumir
		
		int fileLength = (int) file.length();
		byte[] fileBa = new byte[fileLength];
		file.seek(0);
		file.read(fileBa);
		//O arquivo de dados é carregado para a memória principal
		
		int cont = 0, dicN = 256; 
		int wordIndex = 0;
		ArrayList<Byte> byteSeq;
		ArrayList<Integer> outAL = new ArrayList<Integer>();
		
		while(cont < fileLength) {
			System.out.println((String.format("%.2f", ((float)cont/fileLength)*100)) + "%");
			
			byteSeq = new ArrayList<Byte>();
			byteSeq.add(fileBa[cont]);
			//A sequência de bytes a ser procurada no dicionário é inicializada com o primeiro byte
			
			for(int i=0; i<256; i++) {
				if(dicionario.get(i).equals(byteSeq)) {
					wordIndex = i;
					break;
				}
			}
			//Primeiramente, o índice salvo é o índice do primeiro byte no dicionário
			
			boolean found;
			cont++;
			
			while(cont < fileLength) {
				byteSeq.add(fileBa[cont]);
				found = false;
				for(int i=0; i<dicionario.size(); i++) {
					if(dicionario.get(i).equals(byteSeq)) {
						found = true;
						wordIndex = i;
						break;
					}
				}
				if(found) {
					cont++;
				}
				else {
					break;
				}
			}
			//É feita uma pesquisa pelo maior padrão existente no dicionário
			//A próxima sequência de bytes a ser processada tem ínicio no byte que causou o erro na busca
			
			if(byteSeq.size() > 1 && dicionario.size() < maxValue) {
				dicionario.add(byteSeq);
			}
			//Se for necessário, a sequência é inserida no dicionário

			outAL.add(wordIndex);
			//o índice da última busca com sucesso é escrito no array que armazena a saída
		}
		
		
		byte[] outArray = new byte[outAL.size() * 2];
		for(int i=0; i<outAL.size(); i++) {
			int num = outAL.get(i);
			byte[] baAux = ByteBuffer.allocate(2).putInt(num).array();
			for(int j = i*2, k = 0; k<2; j++, k++) {
				outArray[j] = baAux[k];
			}
		}
		//Os índices correspondentes à saída da compactação são copiados para um array de bytes
		
		compFile.seek(0);
		compFile.write(outArray);
				
		System.out.println("O arquivo de dados foi compactado com sucesso no arquivo de nome " + fileName);
		System.out.println("Tamanho do arquivo original: " + file.length() + "B");
		System.out.println("Tamanho do arquivo compactado: " + compFile.length() + "B");
		System.out.println("Taxa de compressão: " + (((float)compFile.length()/file.length()) * 100) + "%");
	}
	
	private static void decompress(String fileName) throws Exception {
		
		File compFileAux = new File("lzw/" + fileName + ".lzw");
		RandomAccessFile compFile = new RandomAccessFile(compFileAux, "rw");
		
		if(compFile.length() > 0) {
			
			int maxValue = Integer.MAX_VALUE;
			
			ArrayList<ArrayList<Byte>> dicionario = new ArrayList<ArrayList<Byte>>();
			for(int i=0; i<256; i++) {
				ArrayList<Byte> aux = new ArrayList<Byte>(1);
				aux.add((byte)(i - 128));
				dicionario.add(aux);
			}
			//O dicionário é inicializado com todos os valores que um byte pode assumir
			
			int fileLength = (int) compFile.length();
			byte[] fileBa = new byte[fileLength];
			compFile.seek(0);
			compFile.read(fileBa);
			//O arquivo compactado é carregado para a memória principal
			
			int[] fileArray = new int[fileLength/2];
			for(int i=0; i<fileArray.length; i++) {
				byte[] baAux = new byte[2];
				for(int j=0; j<2; j++) {
					baAux[j] = fileBa[(2*i) + j];
				}
				fileArray[i] = ByteBuffer.wrap(baAux).getInt();
			}
			//O arquivo compactado é convertido em um array de índices do tipo int
			
			ArrayList<Byte> byteSeqAux, byteSeq;
			ArrayList<Byte> outAL = new ArrayList<Byte>();
			
			for(int cont = 0; cont < fileArray.length; cont++) {
				
				int curIndex = fileArray[cont];
				byteSeqAux = dicionario.get(curIndex);
				byteSeq = new ArrayList<Byte>();
				for(int i=0; i<byteSeqAux.size(); i++) {
					byteSeq.add(byteSeqAux.get(i).byteValue());
				}
				
				for(int i=0; i<byteSeq.size(); i++) {
					outAL.add(byteSeq.get(i));
				}
				//A sequência de bytes correspondente ao índice lido é adicionada ao array da saída da descompactação
				
				if((cont + 1) < fileArray.length && dicionario.size() < maxValue) {
					int nextIndex = fileArray[cont + 1];
					//System.out.println("nextIndex: " + nextIndex + "\tdic.size: " + dicionario.size());
					dicionario.add(byteSeq);
					byteSeq.add(dicionario.get(nextIndex).get(0).byteValue());
					dicionario.set(dicionario.size()-1, byteSeq);
				}
				//Se for necessário, a sequência de bytes processada mais o primeiro byte indicado pelo próximo índice são adicionados ao dicionário
			}
			
			byte[] outBa = new byte[outAL.size()];
			for(int i=0; i<outBa.length; i++) {
				outBa[i] = outAL.get(i).byteValue();
			}
			
			file.setLength(0);
			file.write(outBa);
			//Por fim, o arquivo de dados recebe a descompactação 
			
			System.out.println("O arquivo de dados foi substituído pela descompactação de " + fileName);
			file.seek(0);
			System.out.println("Último id: " + file.readInt());
		}
		else {
			System.out.println("Erro: o arquivo de nome " + fileName + " não existe");
		}
		
	}
	
	private static void casamento(String pattern) throws Exception {
		
		ArrayList<String> texts = new ArrayList<String>();
		file.seek(0);
		int lastId = file.readInt();
		if(lastId > 0) {
			for(int i=1; i<=lastId; i++) {
				Movie aux = read(i);
				if(aux != null) {
					texts.add(aux.getOverview());
				}
			}
			//Para cada id que pode existir no arquivo de dados, é feita uma busca pelo registro correspondente usando a Árvore B
			//Os resumos dos filmes encontrados são adicionados ao vetor de Strings
			System.out.println("KMP:");
			kmp(texts, pattern);
			System.out.println("--------------------------------------\n");
			System.out.println("Rabin-Karp: ");
			rabinKarp(texts, pattern);
			System.out.println("--------------------------------------\n");
			System.out.println("Força Bruta: ");
			forcaBruta(texts, pattern);
			System.out.println("--------------------------------------\n");
		}
		//Caso o último id armazenado seja maior do que um, é possível que exista algum registro no arquivo de dados
		//Portanto, apenas nesse caso a busca pelo padrão é realizada
		else {
			System.out.println("Erro: não existem registros no arquivo de dados!");
		}
	}
	
	private static void forcaBruta(ArrayList<String> texts, String pattern) {
		int op = 0, ocorrencias = 0;
		
		long beginTime, endTime;
		beginTime = System.currentTimeMillis();
		
		for(int i=0; i<texts.size(); i++) {
			String text = texts.get(i);
			for(int j=0; j <= text.length() - pattern.length(); j++) {
				int k = 0;
				for(; k<pattern.length() && text.charAt(j + k) == pattern.charAt(k); k++);
				if(k == pattern.length()) {
					ocorrencias++;
				}
				op += k + 1;
			}
		}
		
		endTime = System.currentTimeMillis();
		System.out.println("Foram encontradas " + ocorrencias + " ocorrências do padrão " + pattern + " nos resumos dos filmes da base de dados.");
		System.out.println("Foram feitas " + op + " operações.");
		System.out.println("O tempo de execução foi de " + (endTime - beginTime) + " ms.");
	}

	private static void rabinKarp(ArrayList<String> texts, String pattern) {
		int patternHash = 0, ocorrencias = 0, op = 0, base = 256, h = 1;
		for (int i = 0; i < pattern.length() - 1; i++) {
			h = (h * base) % 101;
		}
		for(int i=0; i<pattern.length(); i++) {
			patternHash = (base * patternHash + pattern.charAt(i)) % 101;
		}
		//Primeiramente, é encontrado o hash do padrão
		
		long beginTime, endTime;
		beginTime = System.currentTimeMillis();
		
		for(int i=0; i<texts.size(); i++) {
			String text = texts.get(i);
			int textHash = 0;
			for(int j=0; j<pattern.length(); j++) {
				textHash = (base * textHash + text.charAt(j)) % 101;
			}
			//Primeiramente, calcula-se o hash para a primeira substring do texto com o tamanho do padrão
			
			if(textHash < 0) {
				textHash = textHash + 101;
			}
			
			if(textHash == patternHash) {
				int j = 0;
				for(; j<pattern.length() && text.charAt(j) == pattern.charAt(j); j++);
				if(j == pattern.length()) {
					ocorrencias++;
				}
				op += j + 1;
			}
			//De início, obtém-se o hash do primeiro grupo do texto com o mesmo tamanho do padrão
			//Além disso, se o hash for o mesmo do padrão, já é realizada a primeira comparação
			
			for(int j=1; j <= text.length() - pattern.length(); j++) {
				
				textHash = (base * (textHash - text.charAt(j - 1) * h) + text.charAt(j + pattern.length() - 1)) % 101;
				//O hash composto pelos algarismos formados pelas letras do grupo do texto com tamanho do padrão é atualizado a partir do hash do grupo anterior
				
				if(textHash < 0) {
					textHash = textHash + 101;
				}
				
				if(textHash == patternHash) {
					int k = 0;
					for(; k<pattern.length() && text.charAt(j + k) == pattern.charAt(k); k++);
					if(k == pattern.length()) {
						ocorrencias++;
					}
					op += k + 1;
				}
			}
			//Em seguida, executa-se o algoritmo para os demais grupos do texto com o mesmo tamanho do padrão
		}
		
		endTime = System.currentTimeMillis();
		System.out.println("Foram encontradas " + ocorrencias + " ocorrências do padrão " + pattern + " nos resumos dos filmes da base de dados.");
		System.out.println("Foram feitas " + op + " operações.");
		System.out.println("O tempo de execução foi de " + (endTime - beginTime) + " ms.");
	}

	private static void kmp(ArrayList <String> texts, String pattern) {
		
		int[] pref = new int[pattern.length() + 1];
		pref[0] = -1;
		pref[1] = 0;
		//O vetor prefixo básico tem uma posição a mais do que o padrão e seus dois primeiros valores são -1 e 0
		for(int i=2, j=0, k=1; i<pref.length; i++, k++) {
			
			if(pattern.charAt(j) == pattern.charAt(k)) {
				pref[i] = pref[k] + 1;
				j++;
			}
			//Se os elementos forem iguais, a posição a ser preenchida recebe a anterior mais um
			//Além disso, a posição de ínicio da comparação é incrementada
			else {
				j=0;
				if(pattern.charAt(0) == pattern.charAt(k)) {
					pref[i] = 1;
					j++;
				}
				else {
					pref[i] = 0;
				}
			}
			//Caso contrário, a comparação é feita com a posição de início sendo 0
		}
		for(int i=1; i<pref.length - 1; i++) {
			if(pattern.charAt(i) == pattern.charAt(pref[i])){
				pref[i] = pref[pref[i]];
			}
		}
		//Por fim, é obtido o vetor prefixo melhorado
		
		int ocorrencias = 0, op = 0;
		long beginTime, endTime;
		beginTime = System.currentTimeMillis();
		
		for(int i=0; i<texts.size(); i++) {
			String text = texts.get(i);
			int j = 0, k = 0;
			//A variável j se refere ao índice do texto, já a k o índice do padrão
			while(j < text.length()) {
				if(k < pattern.length() && text.charAt(j) == pattern.charAt(k)) {
					j++;
					k++;
				}
				//Em caso de sucesso, ocorre avanço no texto e no padrão
				else {
					if(k == pattern.length()) {
						ocorrencias++;
					}
					//Caso o índice do padrão alcançe o tamanho do mesmo, significa que o padrão foi encontrado
					k = pref[k];
					if(k == -1) {
						j++;
						k = 0;
					}
					//Se o valor do vetor de prefixo indicar -1, deve ocorrer avanço de 1 no texto e o índice do padrão deve ser 0
				}
				//Caso ocorra uma falha, é feito o deslocamento no padrão de acordo com o vetor de prefixo melhorado
				op++;
			}
		}
		
		endTime = System.currentTimeMillis();
		System.out.println("Foram encontradas " + ocorrencias + " ocorrências do padrão " + pattern + " nos resumos dos filmes da base de dados.");
		System.out.println("Foram feitas " + op + " operações.");
		System.out.println("O tempo de execução foi de " + (endTime - beginTime) + " ms.");
	}
	public static String vigenereEncrypt(String text, String key) {
		String encryptedTxt = "";
		key = getKey(text.length(), key);
		//A chave passada como parâmetro é transformada em uma string com repetições da chave original, para que tenha o mesmo tamanho do texto.
		for(int i=0; i < text.length(); i++) {
			encryptedTxt += (char)((text.charAt(i) + key.charAt(i) + 256) % 256);
			//Cada caracter do texto é transformado no conteúdo da matriz da cifra de Vigenére, na linha do caracter do texto e na coluna do caracter da chave
		}
		return encryptedTxt;
		//Ao final, o texto criptografado é retornado 
	}
	public static String vigenereDecrypt(String text, String key) {
		String decryptedTxt = "";
		key = getKey(text.length(), key);
		//A chave passada como parâmetro é transformada em uma string com repetições da chave original, para que tenha o mesmo tamanho do texto.
		for(int i=0; i < text.length(); i++) {
			decryptedTxt += (char)((text.charAt(i) - key.charAt(i) + 256) % 256);
			//Cada caracter do texto criptografado é transformado no conteúdo da matriz da cifra de Vigenére, na linha do caracter da chave e na coluna do caracter do texto criptografado
		}
		return decryptedTxt;
		//Ao final, o texto descriptografado é retornado 
	}
	public static String getKey(int textLength, String key) {
		String returnKey = key;
		int diff = textLength - key.length();
		for(int i=0; i<diff; i++) {
			returnKey += key.charAt(i % key.length());
		}
		return returnKey;
		//Esse método retorna a chave passada como parâmetro com repetições, para que tenha o mesmo tamanho do texto a ser criptografado
	}
	
	public static String cesarEncrypt(String text, int key) {
		String encryptedTxt = "";
		for(int i=0; i < text.length(); i++) {
			encryptedTxt += (char)((text.charAt(i) + key) % 256);
		}
		return encryptedTxt;
		//O texto tem seus caracteres deslocados e é retornado
	}
	public static String cesarDecrypt(String text, int key) {
		String decryptedTxt = "";
		for(int i=0; i < text.length(); i++) {
			decryptedTxt += (char)((text.charAt(i) - key) % 256);
		}
		return decryptedTxt;
	}
	
}