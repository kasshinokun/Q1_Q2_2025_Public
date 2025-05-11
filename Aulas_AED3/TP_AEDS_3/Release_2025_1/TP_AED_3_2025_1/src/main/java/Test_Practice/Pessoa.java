
//JRE usando Java-SE 23

package Test_Practice;//Nome do Subprojeto

/**
 * @version 1_2025_02_08
 * @author Gabriel da Silva Cassino
 */

import java.io.Serializable;

public class Pessoa implements Serializable {
	private static final long serialVersionUID = 7220145288709489651L;
	  
	private String nome;
	  
	public Pessoa(String nome) {
		this.nome = nome;
	}
	  
	public String getNome() {
		return nome;
	}
}
  
