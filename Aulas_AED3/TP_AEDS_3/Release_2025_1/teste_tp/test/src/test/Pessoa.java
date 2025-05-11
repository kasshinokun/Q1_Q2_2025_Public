
//JRE usando Java-SE 21

package test;

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
  
