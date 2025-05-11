package estagio1;

import estagio1.leitura.Functions;
import estagio1.leitura.LeitorArquivo;

public class Menu {

	public static void parte_I(){
		String pathDb="data/traffic_accidents.db";
		
		String pathIndex="index/indexTrafficAccidents.db";
		
		int op=0;
		do {
			System.out.println("\n==================================================");
			System.out.println("\nProcessos TP AEDS III - Parte I\n");
			System.out.println("1) Processos de escrita");
			System.out.println("2) Processos de Leitura");
			System.out.println("\n0) Sair\n\nEscolha um valor-------> :");
			op=Functions.only_Int();
			switch(op) {
				case 1:
					EscritorArquivo.Start();
					break;
				case 2:
					LeitorArquivo.optionsMain(pathDb, pathIndex);
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
