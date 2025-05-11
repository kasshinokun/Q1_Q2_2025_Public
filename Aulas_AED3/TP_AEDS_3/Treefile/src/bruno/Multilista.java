package bruno;
import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.util.ArrayList;

public class Multilista {
	
	private File dirYearFile;
	private RandomAccessFile dirYear;
	private File dirCountryFile;
	private RandomAccessFile dirCountry;
	private File listFile;
	private RandomAccessFile list;
	
	public Multilista() throws IOException {
		
		this.dirYearFile = new File("index/diretorio_ano");
		this.dirYear = new RandomAccessFile(dirYearFile, "rw");
		this.dirCountryFile = new File("index/diretorio_pais");
		this.dirCountry = new RandomAccessFile(dirCountryFile, "rw");
		this.listFile = new File("index/multilista");
		this.list = new RandomAccessFile(listFile, "rw");
	}
	
	public void inserir(int id, String country, int year) throws IOException {
		dirYear.seek(0);
		dirCountry.seek(0);
		RegistroDiretorioAno rda = new RegistroDiretorioAno();
		RegistroDiretorioPais rdp = new RegistroDiretorioPais();
		long posDir = 0;
		boolean found = false;
		
		//Primeiramente, é feita uma pesquisa sequencial no diretório das listas de ano, até que o ano do parâmetro seja encontrado
		while(posDir < dirYear.length()) {
			byte[] baYear = new byte[14];
			dirYear.read(baYear);
			rda = new RegistroDiretorioAno(baYear);
			//Os registros do diretório do ano sempre têm tamanho 12
			
			if(rda.getYear() == year) {
				found = true;
				if(rda.getAmount() == 0) {
					rda.setIniPos(list.length());
					//Se o registro tiver quantidade 0, é necessário alterar a posição inicial
				}
				else {
					long pos = 0;
					ListNode node = new ListNode();
					node.setNextYear(rda.getIniPos());
					//A primeira posição a ser procurada é a posição inicial
					byte[] baNode = new byte[20];
					//Os nós do arquivo de lista sempre tem tamanho 18
					
					while(node.getNextYear() != -1) {
						list.seek(node.getNextYear());
						pos = list.getFilePointer();
						list.read(baNode);
						node = new ListNode(baNode);
					}
					//É feita uma pesquisa sequencial sobre os nós da lista encadeada, até que o último elemento seja encontrado
					
					node.setNextYear(list.length());
					list.seek(pos);
					list.write(node.getBa());
					//O último elemento da lista encadeada do ano enviado como parâmetro tem o ponteiro atualizado para o final do arquivo
					
				}
				rda.setAmount((int)(rda.getAmount() + 1));
				dirYear.seek(posDir);
				dirYear.write(rda.getBa());
				//O registro do diretório tem suas informações atualizadas
				break;
			}
			posDir = dirYear.getFilePointer();
		}
		if(!found) {
			dirYear.seek(dirYear.length());
			dirYear.write(new RegistroDiretorioAno(year, (int)1, list.length()).getBa());
			//Se o registro de diretório com o ano do parâmetro não tiver sido encontrado, é criado um novo no final do diretório, com posição inicial sendo o fim do arquivo de listas
		}
		
		posDir = 0;
		found = false;
		
		//Posteriormente, é feita uma pesquisa sequencial no diretório do país
		
		while(posDir < dirCountry.length()) {
			
			int length = dirCountry.readInt();
			byte[] baCountry = new byte[length];
			dirCountry.read(baCountry);
			rdp = new RegistroDiretorioPais(baCountry);
			
			if(rdp.getCountry().equals(country)) {
				found = true;
				if(rdp.getAmount() == 0) {
					rdp.setIniPos(list.length());
				}
				else {
					long pos = 0;
					ListNode node = new ListNode();
					node.setNextCountry(rdp.getIniPos());
					byte[] baNode = new byte[18];
					while(node.getNextCountry() != -1) {
						list.seek(node.getNextCountry());
						pos = list.getFilePointer(); 
						list.read(baNode);
						node = new ListNode(baNode);
					}
					node.setNextCountry(list.length());
					list.seek(pos);
					list.write(node.getBa());
					//O último elemento da lista encadeada do país enviado como parâmetro tem o ponteiro atualizado para o final do arquivo
				}
				
				rdp.setAmount((int)(rdp.getAmount() + 1));
				dirCountry.seek(posDir + 4);
				byte[] aux = rdp.getBa();
				dirCountry.write(aux);
				break;
			}
			posDir = dirCountry.getFilePointer();
		}
		if(!found) {
			dirCountry.seek(dirCountry.length());
			byte[] aux = new RegistroDiretorioPais(country, (int)1, list.length()).getBa() ;
			dirCountry.writeInt(aux.length);
			dirCountry.write(aux);
		}

		list.seek(list.length());
		ListNode aux = new ListNode(id, country,-1, year,-1);
		list.write(aux.getBa());
		//Por fim, o nó da lista encadeada referente ao registro passado por parâmetro é escrito no final do arquivo das listas
	}
	
	public boolean remover(int id, String country, int year) throws Exception{
		
		dirYear.seek(0);
		dirCountry.seek(0);
		list.seek(0);
		RegistroDiretorioAno rda = new RegistroDiretorioAno();
		RegistroDiretorioPais rdp = new RegistroDiretorioPais();
		long posDir = 0;
		boolean found = false;
		//Procura de registro de diretório de ANO
		while(posDir < dirYear.length()) {
			byte[] baDirAno = new byte[12];
			dirYear.read(baDirAno);
			rda = new RegistroDiretorioAno(baDirAno);
			if(rda.getYear() == year && rda.getAmount() > 0) {
				if(rda.getAmount() > 1) {
					ListNode node = new ListNode();
					byte[] ba = new byte[18];
					long pos = rda.getIniPos();
					list.seek(pos);
					list.read(ba);
					node = new ListNode(ba);
					while(node.getNextYear() != -1 && getNextYear(node).getId() != id) {
						pos = node.getNextYear();
						node = getNextYear(node);
					}
					//Depois do while, a variável node contém o nó que aponta para o nó que tem o id procurado ou para -1(fim da lista)
					
					if(getNextYear(node).getYear() == year) {
						found = true;
						long next = getNextYear(node).getNextYear();
						node.setNextYear(next);
						list.seek(pos);
						list.write(node.getBa());
						//O ponteiro do penúltimo antes do procurado passa a apontar para o nó depois do procurado
					}
					else {
						found = false;
					}

				}
				if(found) {
					rda.setAmount((int)(rda.getAmount() - 1));
					dirYear.seek(posDir);
					dirYear.write(rda.getBa());
				}
				break;
			}
			posDir = dirYear.getFilePointer();
		}
		
		posDir = 0;
		while(posDir < dirCountry.length()) {
			dirCountry.seek(posDir);
			int length = dirCountry.readInt();
			byte[] ba = new byte[length];
			dirCountry.read(ba);
			rdp = new RegistroDiretorioPais(ba);
			if(rdp.getCountry().equals(country) && rdp.getAmount() > 0) {
				if(rdp.getAmount() > 1) {
					ListNode node;
					byte[] ba2 = new byte[18];
					long pos = rdp.getIniPos();
					list.seek(pos);
					list.read(ba2);
					node = new ListNode(ba2);
					while(node.getNextCountry() != -1 && getNextCountry(node).getId() != id) {
						pos = node.getNextCountry();
						node = getNextCountry(node);
					}
					//Depois do while, a variável node contém o nó que aponta para o nó que tem o id procurado ou para -1(fim da lista)
					long next = getNextCountry(node).getNextCountry();
					
					if(getNextCountry(node).getCountry() == country) {
						found = true;
						next = getNextCountry(node).getNextCountry();
						node.setNextCountry(next);
						list.seek(pos);
						list.write(node.getBa());
						//O ponteiro do penúltimo antes do procurado passa a apontar para o nó depois do procurado
					}
					else {
						found = false;
					}
				}
				
				if(found) {
					rdp.setAmount((int)(rdp.getAmount() - 1));
					dirCountry.seek(posDir);
					dirCountry.write(rdp.getBa());
				}
				break;
				
			}			
			posDir = dirCountry.getFilePointer();
		}
		return found;
	}
	private ListNode getNextYear(ListNode node) throws IOException {
		list.seek(node.getNextYear());
		byte[] ba = new byte[20];
		list.read(ba);
		return new ListNode(ba);
	}
	private ListNode getNextCountry(ListNode node) throws IOException {
		list.seek(node.getNextCountry());
		byte[] ba = new byte[20];
		list.read(ba);
		return new ListNode(ba);
	}

	public ArrayList<Integer> search(int year) throws IOException {
		ArrayList<Integer> array = new ArrayList<Integer>(0);
		//Já que é uma chave secundária, será retornado um conjunto de ids que contém o ano passado por parâmetro
		long pos;
		dirYear.seek(0);
		RegistroDiretorioAno rda = new RegistroDiretorioAno();
		while(dirYear.getFilePointer() < dirYear.length()) {
			
			byte[] ba = new byte[14];
			dirYear.read(ba);
			rda = new RegistroDiretorioAno(ba);
			
			if(rda.getYear() == year && rda.getAmount() > 0) {
				pos = rda.getIniPos();
				byte[] baList;
				while(pos != -1 && pos < list.length()) {
					list.seek(pos);
					baList = new byte[20];
					list.read(baList);
					ListNode ln = new ListNode(baList);
					array.add(ln.getId());
					pos = ln.getNextYear();
					//O nó da lista é lido e seu id é inserido no array que será retornado posteriormente
				}
				break;
			}
		}
		return array;
	}
	public ArrayList<Integer> search(String country) throws Exception{
		ArrayList<Integer> array = new ArrayList<Integer>(0);
		long pos;
		byte[] ba;
		int length;
		dirCountry.seek(0);
		RegistroDiretorioPais rdp = new RegistroDiretorioPais();
		while(dirCountry.getFilePointer() < dirCountry.length()) {
			
			length = dirCountry.readInt();
			ba = new byte[length];
			dirCountry.read(ba);
			rdp = new RegistroDiretorioPais(ba);
			
			if(rdp.getCountry().equals(country) && rdp.getAmount() > 0) {
				pos = rdp.getIniPos();
				byte[] baList = new byte[20];
				while(pos != -1 && pos < list.length()) {
					list.seek(pos);
					list.read(baList);
					ListNode ln = new ListNode(baList);
					array.add(ln.getId());
					pos = ln.getNextCountry();
				}
				break;
			}
		}
		return array;
	}
	
}
