package menu;

import estagio1.Menu;
import estagio1.leitura.Functions;
import estagio2.Menu2;
import estagio3.callerCompact;
public class main {

	public static void main(String[] args){

		int op=0;
		do {
			System.out.println("\nProcessos TP AEDS III\n");
			System.out.println("1) Processos - Parte I");
			System.out.println("2) Processos - Parte II");
			System.out.println("3) Processos - Parte III");
			System.out.println("4) Processos - Parte IV");
			System.out.println("5) Processos - Parte V");			
			System.out.println("\n0) Sair\n\nEscolha um valor-------> :");
			op=Functions.only_Int();
			switch(op) {
				case 1:
					Menu.parte_I();
					break;
				case 2:
					Menu2.parte_II();
				    break;
				case 3:
					callerCompact.main(args);
				    break;
				case 4:
					System.out.println("\nAguarde em desenvolvimento");
				    break;
				case 5:
					System.out.println("\nAguarde em desenvolvimento");
				    break;
				default:
					if(op==0) {
						System.out.println("\nMuito Obrigado\nPrograma Encerrado.\n");
					}else {
						System.out.println("\nTente novamente, escolha fora do escopo.");
					}
			}
		}while(op!=0);
		System.exit(0);	
	}

}
