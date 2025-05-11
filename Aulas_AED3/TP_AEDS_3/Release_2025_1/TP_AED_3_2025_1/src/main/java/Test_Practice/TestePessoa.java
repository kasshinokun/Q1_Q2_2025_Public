
//JRE usando Java-SE 23

package Test_Practice;//Nome do Subprojeto

/**
 * @version 1_2025_02_08
 * @author Gabriel da Silva Cassino
 */

//Source: https://www.universidadejava.com.br/java/java-leitura-arquivo/
import java.io.*;
import java.util.ArrayList;

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
		String outputPATH = "Pessoa.txt";
		
		Pessoa manuel = new Pessoa("Manuel");
		Pessoa jose = new Pessoa("José");
		
		tp.gravarObjeto(manuel, outputPATH);
		tp.gravarObjeto(jose, outputPATH);
		System.out.println(tp.lerObjeto(outputPATH).getNome());
	
	}
	
	private void gravarObjeto(Pessoa pessoa, String outputPATH) {
		try {
			
			ObjectOutputStream oos = new ObjectOutputStream(
			new FileOutputStream(outputPATH,true));//Overwrite ou se true(FileOutputStream(outputPATH,true)) adiciona
			oos.writeObject(pessoa);
			 
			oos.close();
		} catch (FileNotFoundException ex) {
			System.out.println("Erro ao ler o arquivo: " + outputPATH);
		} catch (IOException ex) {
			System.out.println("Erro ao gravar o objeto no arquivo");
		}
	}
	private Pessoa lerObjeto(String outputPATH) {
		Pessoa pessoa = null;
	
		try {
			ObjectInputStream ois = new ObjectInputStream(
			new FileInputStream(outputPATH));//Le apenas um, mas não o arquivo
			
			pessoa = (Pessoa) ois.readObject();
				
				
			ois.close();
		} catch (ClassNotFoundException ex) {
			System.out.println("Erro ao converter o arquivo em objeto");
		} catch (IOException ex) {
			System.out.println("Erro ao ler o objeto do arquivo");
		}
		
		return pessoa;
	}
//=================================================================================================================================
	// Source: --> https://codespindle.com/Java/Java_objectinputstream_Objectoutputstream.html#:~:text=If%20you%20are%20writing%20to%20a%20file%20that%20already%20exists,that%20takes%20a%20boolean%20parameter.
	
	public static void teste(Pessoa[] lista,String outputPATH) 
			throws InterruptedException, 
			FileNotFoundException, 
			IOException,
			ClassNotFoundException {
	      
		try
	  	{
	 
			ObjectOutputStream objout = new ObjectOutputStream(new FileOutputStream(outputPATH,true));
		  	for(int i=0;i<lista.length;i++)
		  	{		
			  	objout.writeObject(lista[i]);
	  		}
	  		objout.writeObject(new endoffile());
	  		objout.close();
	  		//reading the objects from the input file 
	  
	  		ObjectInputStream objin = new ObjectInputStream(new FileInputStream(outputPATH));
	  		Object obj = null;
	  		while((obj =  objin.readObject()) instanceof endoffile == false){
	              System.out.println(((Pessoa)obj).getNome());
	        }
	    	objin.close();
	  	}	
	  	catch(Exception e)
	  	{
			System.out.println("I am catching exception here");
			System.out.println(e.getMessage());
	  	}
	}
  
	
//=====================================================================================================================================
	
	
	
	
	
}