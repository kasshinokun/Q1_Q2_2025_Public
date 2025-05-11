
//JRE usando Java-SE 21

package test;
//Source: https://www.universidadejava.com.br/java/java-leitura-arquivo/
import java.io.*;

/**
 * Classe utilizada para gravar um objeto em um arquivo e depois 
 * ler o objeto do arquivo.
 */
public class TestePessoa {

/**
 * Classe utilizada para demonstrar o uso da interface Serializable.
 */


	public static void main(String[] args) {
		TestePessoa tp = new TestePessoa();
		String caminho = "arquivo.txt";
		Pessoa manuel = new Pessoa("Manuel");
		tp.gravarObjeto(manuel, caminho);
		
		Pessoa pessoa = tp.lerObjeto(caminho);
		System.out.println(pessoa.getNome());
	}
	
	private void gravarObjeto(Pessoa pessoa, String caminho) {
		try {
			ObjectOutputStream oos = new ObjectOutputStream(
			new FileOutputStream(caminho));
			oos.writeObject(pessoa);
			oos.close();
		} catch (FileNotFoundException ex) {
			System.out.println("Erro ao ler o arquivo: " + caminho);
		} catch (IOException ex) {
			System.out.println("Erro ao gravar o objeto no arquivo");
		}
	}
	
	private Pessoa lerObjeto(String caminho) {
		Pessoa pessoa = null;
	
		try {
			ObjectInputStream ois = new ObjectInputStream(
			new FileInputStream(caminho));
			pessoa = (Pessoa) ois.readObject();
			ois.close();
		} catch (ClassNotFoundException ex) {
			System.out.println("Erro ao converter o arquivo em objeto");
		} catch (IOException ex) {
			System.out.println("Erro ao ler o objeto do arquivo");
		}
		
		return pessoa;
	}
}