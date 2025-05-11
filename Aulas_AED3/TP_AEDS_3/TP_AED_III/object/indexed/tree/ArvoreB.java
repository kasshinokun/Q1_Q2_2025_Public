package object.indexed.tree;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.RandomAccessFile;

import estagio1.leitura.Functions;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;



public class ArvoreB {
	
	private File file;
	private RandomAccessFile indexFile;
	private short ordem;
	
	public ArvoreB() throws IOException {
		this("btree.index", (short)31);
	}
	
	public ArvoreB(String fileName, short ordem) throws IOException {
		
		this.ordem = ordem;
		
		Functions.checkDirectory("index");//Verifica se existe, senão existir cria o caminho
		
		this.file = new File("index"+File.separator+"arvore_b" +File.separator+ fileName);// Separador do sistema operacional em uso
		
		this.indexFile = new RandomAccessFile(file, "rw");
		//A classe é instanciada com ordem e nome do arquivo de índices passado por parâmetro
		
		if(indexFile.length() == 0) {
			//indexFile.seek(0);
			indexFile.writeLong(8);//escreve 8, pois é o tamanho do long associado a posição da raiz
			indexFile.write(criarPagina());
			//No primeiro momento, o ponteiro para a raiz é criado e a raiz começa na posição 8
		}
		//Caso o arquivo já esteja preenchido, não é necessário criar a raiz
	}
	
	public byte[] criarPagina() throws IOException {
		
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		DataOutputStream dos = new DataOutputStream(baos);
		dos.writeShort(0);//Escreve N da página - equivale a 2 bytes antes da página
		// qtd de pares chaves/endereço da página
		for(int i=0; i<this.ordem-1; i++) {
			dos.writeLong(-1);
			dos.writeInt(0);
			dos.writeLong(-1);//Cada nó filho equivale a 20 bytes
		}
		dos.writeLong(-1);
		//Escreve uma página com 0 filhos e 0 pares chave/endereço válidos, com o tamanho adequado à ordem da árvore
		
		return baos.toByteArray();
	}
	
	public short getOrdem() {
		return ordem;
	}
	
	public void setOrdem(short ordem) {
		this.ordem = ordem;
	}

	public void inserir(int chave, long endereco) throws Exception {
		//indexFile.seek(0);
		KeyAddressPair aux = inserir(chave, endereco, indexFile.readLong());
		// Chama o método inserir passando como endereço da página a raiz
		
		if (aux != null) {
			//criar nova raiz
			long posNovaRaiz = indexFile.length();
			Pagina raiz = new Pagina(criarPagina(), this.ordem);
			raiz.setPairAtIndexOf(aux, 0);
			raiz.setN((short)1);
			//indexFile.seek(0);
			indexFile.writeLong(posNovaRaiz);
			indexFile.seek(posNovaRaiz);
			indexFile.write(raiz.getByteArray());
		}
	}

	private KeyAddressPair inserir(int chave, long endereco, long endPag) throws Exception {
		byte[] baPagAtual = new byte[(20 * ordem) - 8];
		//O tamanho dos vetores de bytes usados para armazenar as páginas de forma temporária é calculado de acordo com a ordem da árvore
		
		indexFile.seek(endPag);
		indexFile.read(baPagAtual);
		Pagina paginaAtual = new Pagina(baPagAtual, this.ordem);
		KeyAddressPair pair = new KeyAddressPair();
		
		if(!paginaAtual.isLeaf()) {
			// se não for folha, será feita chamada recursiva no endereço de algum dos filhos
			
			for(int i=0; i<paginaAtual.getN(); i++) {
				if(chave < paginaAtual.getPairAtIndexOf(i).getKey()) {
					pair = inserir(chave, endereco, paginaAtual.getSonAtIndexOf(i));
					break;
				}
			}
			if(chave > paginaAtual.getPairAtIndexOf(paginaAtual.getN()-1).getKey()) {
				//Nesse caso, significa que a chave a ser inserida é maior do que a última chave da página
				pair = inserir(chave, endereco, paginaAtual.getPairAtIndexOf(paginaAtual.getN() - 1).getRightSon());
			}
			if(pair == null) {
				return null;
			}
		}
		else {
			// se for folha, o par chave/endereço a ser inserido é o que veio como parâmetro
			pair = new KeyAddressPair(chave, endereco);
		}
		
		if(paginaAtual.getN() < this.ordem - 1) {
			//será feita a inserção do par chave/endereço nessa página
			inserirOrdenado(pair, paginaAtual);
			indexFile.seek(endPag);
			indexFile.write(paginaAtual.getByteArray());
			return null;
			//Como a inserção será concluida, ocorrerá a condição de parada
		}
		else {
			//será necessário split e promover o elemento intermediário
			long posPagIrma = indexFile.length();
			Pagina paginaIrma = new Pagina(criarPagina(), this.ordem);
			//A nova página é criada e será escrita posteriormente no final do arquivo de indice
			
			int i;
			for(i = paginaAtual.getN()/2; i<paginaAtual.getN(); i++) {
				paginaIrma.setPairAtIndexOf(paginaAtual.getPairAtIndexOf(i), i - paginaAtual.getN()/2);
			}
			paginaAtual.setN((short) (paginaAtual.getN()/2));
			//A segunda metade dos pares chave/endereço é copiada para a nova folha, que também tem seu indicador de qtd de chaves atualizado
			
			if(this.ordem % 2 == 0) {
				paginaIrma.setN((short) (paginaAtual.getN() + 1));
			}
			//Se a ordem for par, significa que a quantidade de chaves máxima é ímpar, então a página irmã armazenará uma chave a mais em relação a página onde ocorreu a tentativa de inserção
			else {
				paginaIrma.setN(paginaAtual.getN());
			}
			//Caso contrário, a quantidade de chaves vai ser igual nas duas páginas irmãs
			
			KeyAddressPair intermediario = new KeyAddressPair();
			
			if(pair.getKey() > paginaAtual.getPairAtIndexOf(paginaAtual.getN() - 1).getKey() && pair.getKey() < paginaIrma.getPairAtIndexOf(0).getKey()) {
				paginaIrma.setSonAtIndexOf(pair.getRightSon(), 0);
				intermediario.setKey(pair.getKey());
				intermediario.setAddress(pair.getAddress());
			}
			//Para esse caso, a chave a ser promovida é justamente a que queremos inserir, portanto ela é simplesmente retornada para ser promovida, sendo que o seu filho à direita será a nova página criada
			
			
			else if(pair.getKey() > paginaIrma.getPairAtIndexOf(0).getKey()) {
				//Se a chave tiver de ser inserida na pagina da direita
				
				intermediario = paginaIrma.getPairAtIndexOf(0);
				for(int j=0; j < paginaIrma.getN() - 1; j++) {
					paginaIrma.setPairAtIndexOf(paginaIrma.getPairAtIndexOf(j + 1), j);
				}
				paginaIrma.setN((short)(paginaIrma.getN() - 1));
				//Primeiramente, os pares chave/endereço são empurrados para o início da página, para que a inserção ocorra corretamente
				
				inserirOrdenado(pair, paginaIrma);
			}
			
			else {
				//Se a chave tiver de ser inserida na pagina da esquerda
				intermediario = paginaAtual.getPairAtIndexOf(paginaAtual.getN() - 1);
				paginaAtual.setN((short)(paginaAtual.getN() - 1));
				inserirOrdenado(pair, paginaAtual);
			}
			
			intermediario.setRightSon(posPagIrma);
			intermediario.setLeftSon(endPag);
			
			indexFile.seek(posPagIrma);
			indexFile.write(paginaIrma.getByteArray());
			//A página irmã é escrita na posição correspondente no arquivo de índices
			
			indexFile.seek(endPag);
			indexFile.write(paginaAtual.getByteArray());
			//A página atual é atualizada
			
			return intermediario;
			
		}
			
			
	}
	
	private void inserirOrdenado(KeyAddressPair pair, Pagina pagina) throws Exception {
		int i = 0;
		for(i = pagina.getN(); i > 0 &&  pagina.getPairAtIndexOf(i-1).getKey() > pair.getKey(); i--) {
			pagina.setPairAtIndexOf(pagina.getPairAtIndexOf(i-1), i);
		}
		pagina.setPairAtIndexOf(pair, i);
		pagina.setN((short)(pagina.getN() + 1));
	}
	
	public long search(int key) throws Exception {
		//chama o método recursivo passando como endereço a raiz
		//indexFile.seek(0);
		KeyAddressPair resp = search(key, indexFile.readLong());
		if(resp != null) {
			return resp.getAddress();
		}
		else {
			return -1;
		}
	}
	
	private KeyAddressPair search(int key, long endPag) throws Exception {
		byte[] baPagAtual = new byte[(20 * ordem) - 8];
		indexFile.seek(endPag);
		indexFile.read(baPagAtual);
		Pagina paginaAtual = new Pagina(baPagAtual, this.ordem);
		KeyAddressPair aux = new KeyAddressPair();
		
		if(!paginaAtual.isLeaf()) {
			//Se a página não for folha, é checado se a chave procurada é igual ou menor a cada uma das chaves da página 
			for(int i=0; i<paginaAtual.getN(); i++) {
				aux = paginaAtual.getPairAtIndexOf(i);
				if(key == aux.getKey()) {
					return aux;
				}
				else if(key < aux.getKey()) {
					return search(key, paginaAtual.getSonAtIndexOf(i));
				}
			}
			//Se nenhuma das verificações anteriores forem verdadeiras, a única possibilidade restante é que a chave procurada é maior que a última chave 
			return search(key, aux.getRightSon());
		}
		else {
			//Se for folha e a chave existir na página, o par chave/endereço procurado será retornado
			//Caso a chave não exista na página, é retornado nulo
			for(int i=0; i<paginaAtual.getN(); i++) {
				aux = paginaAtual.getPairAtIndexOf(i);
				if(key == aux.getKey()) {
					return aux;
				}
			}
			return null;
		}
	}
	
	public void updateAddress(int key, long newAddress) throws Exception {
		//chama o método recursivo passando como endereço a raiz
		//indexFile.seek(0);
		update(indexFile.readLong(), key, newAddress);
	}

	private void update(long endPag, int key, long newAddress) throws Exception {
		byte[] baPagAtual = new byte[(20 * ordem) - 8];
		indexFile.seek(endPag);
		indexFile.read(baPagAtual);
		Pagina paginaAtual = new Pagina(baPagAtual, this.ordem);
		KeyAddressPair aux = new KeyAddressPair();
		
		if(!paginaAtual.isLeaf()) {
			//Se a página não for folha, é checado se a chave procurada é igual ou menor a cada uma das chaves da página 
			for(int i=0; i<paginaAtual.getN(); i++) {
				aux = paginaAtual.getPairAtIndexOf(i);
				if(key == aux.getKey()) {
					//O endereço do par chave/endereço é atualizado e a página é reescrita 
					aux.setAddress(newAddress);
					paginaAtual.setPairAtIndexOf(aux, i);
					indexFile.seek(endPag);
					indexFile.write(paginaAtual.getByteArray());
				}
				else if(key < aux.getKey()) {
					update(paginaAtual.getSonAtIndexOf(i), key, newAddress);
				}
			}
			//Se nenhuma das verificações anteriores forem verdadeiras, a única possibilidade restante é que a chave procurada é maior que a última chave 
			update(aux.getRightSon(), key, newAddress);
		}
		else {
			//Se for folha, a chave terá seu endereço do arquivo de dados atualizado
			for(int i=0; i<paginaAtual.getN(); i++) {
				aux = paginaAtual.getPairAtIndexOf(i);
				if(key == aux.getKey()) {
					aux.setAddress(newAddress);
					paginaAtual.setPairAtIndexOf(aux, i);
					indexFile.seek(endPag);
					indexFile.write(paginaAtual.getByteArray());
				}
			}
		}
	}
	
	public long remove(int key) throws Exception {
		//indexFile.seek(0);
		return remove(key, indexFile.readLong(), -1);
		//Chamada para a função passando a raiz como endereço
	}

	private long remove(int key, long endPagAtual, long endPagPai) throws Exception {
		//É necessário mudar o método getEndAntecessor para retornar o antecessor do par e não da página, e o caso da remoção do elemento da raiz
		byte[] baPagAtual = new byte[(20 * ordem) - 8];
		indexFile.seek(endPagAtual);
		indexFile.read(baPagAtual);
		Pagina pagAtual = new Pagina(baPagAtual, this.ordem);
		long resp = -1;
		
		if(!pagAtual.isLeaf()) {
			//Se a página não for folha, verifica-se se a chave está nessa página
			//Se estiver, ela será substituída pelo antecessor
			//Caso contrário, ocorrerá chamada recursiva para algum filho da página
			KeyAddressPair aux = new KeyAddressPair();
			for(int i=0; i<pagAtual.getN(); i++) {
				aux = pagAtual.getPairAtIndexOf(i);
				if(key == aux.getKey()) {
					resp = aux.getAddress();
					KeyAddressPair antecessor = getAntecessor(pagAtual, (short)i);
					long[] adresses = new long[2];
					adresses = getEndAntecessor(pagAtual, endPagAtual, (short)i);
					//O array adresses recebe os endereços da página folha onde está o antecessor e do pai dessa, para que o antecessor seja removido da folha
					
					remove(antecessor.getKey(), adresses[0], adresses[1]);
					//O antecessor é removido da folha por chamada recursiva
					
					aux.setKey(antecessor.getKey());
					aux.setAddress(antecessor.getAddress());
					pagAtual.setPairAtIndexOf(aux, i);
					//O par chave/endereço é atualizado com as informações do antecessor, sem alterar seus filhos à esquerda e direita
					
					indexFile.seek(endPagAtual);
					indexFile.write(pagAtual.getByteArray());
					//A página é atualizada no arquivo de índices
					
					return resp;
					
				}
				else if(key < aux.getKey()) {
					return remove(key, pagAtual.getSonAtIndexOf(i), endPagAtual);
					//Se a chave a ser removida for menor do que a chave analisada, é feita chamada recursiva para o filho à esquerda
				}
			}
			return remove(key, aux.getRightSon(), endPagAtual);
			//A última possibilidade restante é que a chave a ser removida é maior que a última chave da página
		}
		else {
			//Se a página for folha, é necessário, primeiro, conferir se o par procurado se encontra na página
			boolean exists = false;
			int bottom = 0;
			int top = pagAtual.getN() - 1;
			int middle;
			while(bottom <= top) {
				middle = (bottom + top)/2;
				int midElement = pagAtual.getPairAtIndexOf(middle).getKey();
				if(midElement == key) {
					resp = pagAtual.getPairAtIndexOf(middle).getAddress();
					exists = true;
					break;
				}
				else if(key < midElement) {
					top = middle - 1;
				}
				else {
					bottom = middle + 1;
				}
			}
			if(!exists) {
				//Se o elemento não estiver na folha, é retornado -1 como código da condição de falha
				return -1;
			}
			else if(endPagPai != -1){
				//Nesse caso, a página é uma folha e não é raiz, portanto a remoção deve preservar a taxa mínima de ocupação
				if(pagAtual.getN() > this.ordem / 2) {
					//Se a remoção mantiver a ocupação mínima, basta remover de forma ordenada
					removerOrdenado(key, pagAtual);
					indexFile.seek(endPagAtual);
					indexFile.write(pagAtual.getByteArray());
				}
				else if(hasFilledSibling(baPagAtual, endPagAtual, endPagPai) != -1) {
					//Nesse caso, algum irmão pode ceder uma chave
					
					removerOrdenado(key, pagAtual);
					//O par chave/endereço já é removido da folha, e o processamento ocorrerá em seguida
					
					byte[] baPagPai = new byte[(20 * ordem) - 8];
					indexFile.seek(endPagPai);
					indexFile.read(baPagPai);
					Pagina pagPai = new Pagina(baPagPai, this.ordem);
					
					int siblingIndex = hasFilledSibling(baPagAtual, endPagAtual, endPagPai);
					
					if(siblingIndex == 1) {
						//O irmão que vai ceder uma chave é o da esquerda
						
						KeyAddressPair aux = pagPai.getPairAtIndexOf(siblingIndex);
						aux.setLeftSon(-1);
						aux.setRightSon(-1);
						//aux recebe o par chave/endereço que será inserido na pagAtual, e será substituido na pagPai
						
						inserirOrdenado(aux, pagAtual);
						//Esse par é inserido na página atual
						
						long siblingAdress = pagPai.getSonAtIndexOf(siblingIndex);
						aux = stealBiggest(siblingAdress);
						aux.setLeftSon(pagPai.getSonAtIndexOf(siblingIndex));
						aux.setRightSon(pagPai.getSonAtIndexOf(siblingIndex + 1));
						pagPai.setPairAtIndexOf(aux, siblingIndex);
						//O par chave/endereço que tem como filhos a pagAtual e a pagIrma é substituído pelo par de maior chave da página irmã, conservando seus ponteiros da esquerda e direita
						//A página irmã que cedeu sua maior chave já foi atualizada no arquivo por meio do método stealBiggest()
						
						indexFile.seek(endPagAtual);
						indexFile.write(pagAtual.getByteArray());
						indexFile.seek(endPagPai);
						indexFile.write(pagPai.getByteArray());
						//O arquivo de dados é atualizado
						
					}
					else {
						//O irmão que vai ceder uma chave é o da direita
						
						KeyAddressPair aux = pagPai.getPairAtIndexOf(siblingIndex - 1);
						aux.setLeftSon(-1);
						aux.setRightSon(-1);
						//aux recebe o par chave/endereço que será inserido na pagAtual, e será substituido na pagPai
						
						inserirOrdenado(aux, pagAtual);
						//Esse par é inserido na página atual
						
						long siblingAdress = pagPai.getSonAtIndexOf(siblingIndex);
						aux = stealShortest(siblingAdress);
						aux.setLeftSon(pagPai.getSonAtIndexOf(siblingIndex - 1));
						aux.setRightSon(pagPai.getSonAtIndexOf(siblingIndex));
						pagPai.setPairAtIndexOf(aux, siblingIndex - 1);
						//O par chave/endereço que tem como filhos a pagAtual e a pagIrma é substituído pelo par de menor chave da página irmã, conservando seus ponteiros da esquerda e direita
						//A página irmã que cedeu sua maior chave já foi atualizada no arquivo por meio do método stealShortest()
						
						indexFile.seek(endPagAtual);
						indexFile.write(pagAtual.getByteArray());
						indexFile.seek(endPagPai);
						indexFile.write(pagPai.getByteArray());
						//O arquivo de dados é atualizado
					}

				}
				else {
					//Nesse caso, como não existe nenhuma página irmã que pode ceder uma chave, deverá ocorrer a junção de duas páginas-folha
					
					removerOrdenado(key, pagAtual);
					//Antes de qualquer processamento, o elemento já é removido para que a junção de folhas possa ocorrer normalmente
					
					byte[] baPagPai = new byte[(20 * ordem) - 8];
					byte[] baPagIrma = new byte[(20 * ordem) - 8];
					indexFile.seek(endPagPai);
					indexFile.read(baPagPai);
					Pagina pagPai = new Pagina(baPagPai, this.ordem);
					Pagina pagIrma = new Pagina();
					
					int index = getSonIndex(endPagAtual, pagPai);
					
					if(index < pagPai.getN()) {
						//Para esse caso, serão copiados para a página atual um par da página pai e todos os pares da página irmã à direita, nessa ordem
						
						KeyAddressPair aux = pagPai.getPairAtIndexOf(index);
						aux.setLeftSon(-1);
						aux.setRightSon(-1);
						inserirOrdenado(aux, pagAtual);
						//Primeiramente, o par chave/endereço que tem a pagAtual como filho é inserido na pagAtual, desprezando ponteiros para filhos
						
						indexFile.seek(pagPai.getSonAtIndexOf(index + 1));
						indexFile.read(baPagIrma);
						pagIrma = new Pagina(baPagIrma, this.ordem);
						for(int i=0; i<pagIrma.getN(); i++) {
							inserirOrdenado(pagIrma.getPairAtIndexOf(i), pagAtual);
						}
						//Os pares da página irmã à direita são copiados de forma ordenada para a página atual
						
						
						pagPai.setSonAtIndexOf(endPagAtual, (index + 1));
						removerOrdenado(aux.getKey(), pagPai);
						//O par retirado da página pai é removido, com a correção do ponteiro do filho à direita, que passa a apontar para a página atual
						
						indexFile.seek(endPagAtual);
						indexFile.write(pagAtual.getByteArray());
						indexFile.seek(endPagPai);
						indexFile.write(pagPai.getByteArray());
						//As páginas são atualizadas no arquivo de índices
						
						
					}
					else {
						//Para esse caso, a página destino será o irmão à esquerda da pagAtual
						
						indexFile.seek(pagPai.getSonAtIndexOf(index - 1));
						indexFile.read(baPagIrma);
						pagIrma = new Pagina(baPagIrma, this.ordem);
						
						KeyAddressPair aux = pagPai.getPairAtIndexOf(index - 1);
						aux.setLeftSon(-1);
						aux.setRightSon(-1);
						inserirOrdenado(aux, pagIrma);
						//Primeiramente, o par chave/endereço que tem a pagAtual como filho é inserido na pagIrma, desprezando ponteiros para filhos
						
						for(int i=0; i<pagAtual.getN(); i++) {
							inserirOrdenado(pagAtual.getPairAtIndexOf(i), pagIrma);
						}
						//Os pares da página atual são copiados de forma ordenada para a página irmã á esquerda
						
						pagPai.setSonAtIndexOf(pagPai.getSonAtIndexOf(index - 1), index);
						removerOrdenado(aux.getKey(), pagPai);
						//O par retirado da página pai é removido, com a correção do ponteiro do filho à direita, que passa a apontar para a página irmã à esquerda da página atual
						
						indexFile.seek(pagPai.getSonAtIndexOf(index - 1));
						indexFile.write(pagIrma.getByteArray());
						indexFile.seek(endPagPai);
						indexFile.write(pagPai.getByteArray());
						//As páginas são atualizadas no arquivo de índices
					}
				}
			}
			else {
				//Nesse caso, página atual é folha mas também é raiz, portanto basta remover de forma ordenada
				removerOrdenado(key, pagAtual);
				indexFile.seek(endPagAtual);
				indexFile.write(pagAtual.getByteArray());
			}
			return resp;
		}
		
	}
		
	private int getSonIndex(long pagAdress, Pagina pagPai) throws Exception{
		int i;
		for(i=0; i<pagPai.getN() + 1 && pagPai.getSonAtIndexOf(i) != pagAdress ; i++);
		return i;
	}
	
	private KeyAddressPair stealShortest(long pagAdress) throws Exception{
		byte[] baPagAtual = new byte[(20 * ordem) - 8];
		indexFile.seek(pagAdress);
		indexFile.read(baPagAtual);
		Pagina pagAtual = new Pagina(baPagAtual, this.ordem);
		
		KeyAddressPair resp = pagAtual.getPairAtIndexOf(0);
		removerOrdenado(resp.getKey(), pagAtual);
		
		indexFile.seek(pagAdress);
		indexFile.write(pagAtual.getByteArray());
		
		return resp;
	}
	
	private KeyAddressPair stealBiggest(long pageAdress) throws Exception {
		//retira o par chave/endereço de maior chave
		
		byte[] baPag = new byte[(20 * ordem) - 8];
		indexFile.seek(pageAdress);
		indexFile.read(baPag);
		Pagina pagAtual = new Pagina(baPag, this.ordem);
		
		KeyAddressPair aux = pagAtual.getPairAtIndexOf(pagAtual.getN() - 1);
		pagAtual.setN((short)(pagAtual.getN() - 1));
		//O par chave/endereço de maior chave é removido e retornado posteriormente
		
		indexFile.seek(pageAdress);
		indexFile.write(pagAtual.getByteArray());
		
		return aux;
	}


	private int hasFilledSibling(byte[] baPagAtual, long endPagAtual, long endPagPai) throws Exception {
		byte[] baPai = new byte[(20 * ordem) - 8];
		byte[] baIrma1 = new byte[(20 * ordem) - 8];
		byte[] baIrma2 = new byte[(20 * ordem) - 8];
		Pagina paginaIrma;
		indexFile.seek(endPagPai);
		indexFile.read(baPai);
		Pagina pagPai = new Pagina(baPai, this.ordem);
		
		int i;
		
		for(i=0; i<pagPai.getN() + 1 && pagPai.getSonAtIndexOf(i) != endPagAtual ; i++);
		//A variável i para no índice do ponteiro para a página atual
		
		if(i == 0) {
			//Se esse índice for 0, o único irmão possível é o de índice 1
			long endPagIrma = pagPai.getSonAtIndexOf(1);
			indexFile.seek(endPagIrma);
			indexFile.read(baIrma1);
			paginaIrma = new Pagina(baIrma1, this.ordem);
			if(paginaIrma.getN() > this.ordem / 2) {
				return (i + 1);
			}
			else {
				return -1;
			}
		}
		else if(i == pagPai.getN()) {
			//Se o índice for n, o único irmão possível é n-1
			long endPagIrma = pagPai.getSonAtIndexOf(pagPai.getN() -  1);
			indexFile.seek(endPagIrma);
			indexFile.read(baIrma1);
			paginaIrma = new Pagina(baIrma1, this.ordem);
			if(paginaIrma.getN() > this.ordem / 2) {
				return (i - 1);
			}
			else {
				return -1;
			}
		}
		else {
			//Se não for nenhum dos extremos, é necessário conferir os dois irmãos
			long endPagIrma1 = pagPai.getSonAtIndexOf(i - 1);
			long endPagIrma2 = pagPai.getSonAtIndexOf(i + 1);
			indexFile.seek(endPagIrma1);
			indexFile.read(baIrma1);
			indexFile.seek(endPagIrma2);
			indexFile.read(baIrma2);
			Pagina paginaIrma1 = new Pagina(baIrma1, this.ordem);
			Pagina paginaIrma2 = new Pagina(baIrma2, this.ordem);
			if(paginaIrma1.getN() > this.ordem / 2) {
				return (i - 1);
			}
			else if(paginaIrma2.getN() > this.ordem / 2){
				return (i + 1);
			}
			else {
				return -1;
			}
		}
	}

	private void removerOrdenado(int key, Pagina pagAtual) throws Exception {
		for(int i=0; i<pagAtual.getN(); i++) {
			if(pagAtual.getPairAtIndexOf(i).getKey() == key) {
				for(int j=i; j< pagAtual.getN() - 1; j++) {
					pagAtual.setPairAtIndexOf(pagAtual.getPairAtIndexOf(j+1), j);
				}
				pagAtual.setN((short)(pagAtual.getN() - 1));
				break;
			}
		}
	}

	private KeyAddressPair getAntecessor(Pagina pagAtual, short pairIndex) throws Exception {
		byte[] ba = new byte[(20 * ordem) - 8];
		indexFile.seek(pagAtual.getSonAtIndexOf(pairIndex));
		indexFile.read(ba);
		pagAtual = new Pagina(ba, this.ordem);
		
		while(!pagAtual.isLeaf()) {
			long address = pagAtual.getSonAtIndexOf(pagAtual.getN());
			//Recebe o endereço do último filho
			
			indexFile.seek(address);
			indexFile.read(ba);
			pagAtual = new Pagina(ba, this.ordem);
			//A variável pagAtual é atualizada com o filho mais à direita
		}
		//Depois do while, pagAtual passa a ser a página-folha mais à direita dentre os filhos da que veio como parâmetro
		
		return pagAtual.getPairAtIndexOf(pagAtual.getN() - 1);
		//O par chave/endereço de maior chave dessa página é retornado
	}
	
	private long[] getEndAntecessor(Pagina pagAtual, long iniAddress, short pairIndex) throws Exception {
		byte[] ba = new byte[(20 * ordem) - 8];
		long parentAddress;
		
		if(!hasLeafChildren(pagAtual)) {
			//Se o filho da página onde ocorrerá a remoção não for folha, é possível já inicializar o endereço do pai como o filho à esquerda do par a ser removido 
			parentAddress = pagAtual.getSonAtIndexOf(pairIndex);
			indexFile.seek(parentAddress);
			indexFile.read(ba);
			pagAtual = new Pagina(ba, this.ordem);
		}
		else {
			parentAddress = iniAddress;
			//Se a página enviada como parâmetro já tiver um filho-folha, o endereço do pai será justamente o dessa página
		}
		
		
		while(!hasLeafChildren(pagAtual)) {
			parentAddress = pagAtual.getSonAtIndexOf(pagAtual.getN());
			//Recebe o endereço do último filho
			
			indexFile.seek(parentAddress);
			indexFile.read(ba);
			pagAtual = new Pagina(ba, this.ordem);
			//A variável pagAtual é atualizada com o filho mais à direita
		}
		//Depois do while, pagAtual é a página pai da folha onde está o antecessor
		long leafAddress = pagAtual.getSonAtIndexOf(pagAtual.getN());
		long[] resp = new long[2];
		
		resp[0] = leafAddress;
		resp[1] = parentAddress;
		
		return resp;
	}

	private boolean hasLeafChildren(Pagina pagAtual) throws Exception {
		//Confere se o primeiro filho da página é folha
		long firstSonAddress = pagAtual.getSonAtIndexOf(0);
		byte[] ba = new byte[(20 * ordem) - 8];
		indexFile.seek(firstSonAddress);
		indexFile.read(ba);
		Pagina son = new Pagina(ba, this.ordem);
		if(son.getSonAtIndexOf(0) == -1) {
			return true;
			//Se o primeiro ponteiro for igual a -1, significa que é folha
		}
		else {
			return false;
		}
	}
}
