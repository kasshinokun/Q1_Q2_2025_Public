package estagio2;

import java.util.concurrent.TimeUnit;
import estagio1.EscritorArquivo;
import estagio1.leitura.Functions;
import estagio1.leitura.LeitorArquivo;
import estagio2.Leitura.LeitorIndex;
import estagio2.Escrita.EscritorIndex;

import estagio2.addons.MergedHashingImplementations;
public class Menu2 {

	public static void main(String[] args) {
		
		
	}
	public static void parte_II() {
		String pathDb="index/traffic_accidents.db";
		
		String pathIndex="index/indexTrafficAccidents.db";
		
		int op=0;
		do {
			System.out.println("\n==================================================");
			System.out.println("\nProcessos TP AEDS III - Parte II\n");
			System.out.println("=============Arquivo Sequencial===================\n");
			System.out.println("1) Processos de Escrita - A");
			System.out.println("2) Processos de Leitura - A");
			System.out.println("\n===================Bucket =========================\n");
			System.out.println("7) Processos de Escrita e Leitura - Apendice");			
			System.out.println("\n===================Arvore B========================\n");
			System.out.println("3) Processos de Escrita - B");
			System.out.println("4) Processos de Leitura - B");
			System.out.println("\n===================Bucket =========================\n");
			System.out.println("5) Processos de Escrita - C");
			System.out.println("6) Processos de Leitura - C");
			System.out.println("\n====================================================");
			System.out.print("\n0) Sair\n\nEscolha um valor-------> :");
			op=Functions.only_Int();
			switch(op) {
				//Parte A
				case 1:
					EscritorIndex.Start();
					break;
				case 2:
					LeitorIndex.Start();
				    break;
				//Apendice Experimental
				case 3:
					try {
					System.out.println("\n====================================================");
					System.out.println("Em desenvolvimento - Create e Insert Autonomo");
					System.out.println("Processo de Criação de CSV,");
					System.out.println("Indexação, Indexação em Bucket");
					System.out.println("Busca em Bucket de 210 mil registros");
					System.out.println("gerados aleatoriamente,");
					System.out.println("Por hora não há os metodos de Delete");
					System.out.println("e Update, código criado a partir de");
					System.out.println("conhecimentos do aluno aliado ao Gemini");
					System.out.println("para revisar erros de Java.lang.StackOverFlowError");
					System.out.println("Java.io.EOFException, e demais Exceptions observadas");
					System.out.println("\n====================================================");
					System.out.println("Todos os testes de código foram mantidos na estrutura");
					System.out.println("====================================================");
					TimeUnit.MINUTES.sleep(1);
					System.out.println("\n====================================================");
					MergedHashingImplementations.main(null);
					System.out.println("\n====================================================");
					}catch(InterruptedException e) {
						System.out.println("\nExceção de Interrupção");
					}
					break;
				//Parte B
				case 4:
					System.out.println("Em desenvolvimento");
				    break;
				case 5:
					System.out.println("Em desenvolvimento");
					break;
				//Parte C
				case 6:
					System.out.println("Em desenvolvimento");
				    break;
				case 7:
				    System.out.println("Em desenvolvimento");
				    break;
				default:
					if(op==0) {
						System.out.println("\nVoltando ao Menu Principal.");
					}else {
						System.out.println("\nTente novamente, escolha fora do escopo.\n");
					}
			}
		}while(op!=0);

	}

}
