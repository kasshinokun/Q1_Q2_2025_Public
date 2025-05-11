package object.indexed.tree.crud;

/* 
 * Código cedido pelo @author
 * @author Bruno Henrique Reis Almeida
 * @modder Gabriel da Silva Cassino
*/

import java.io.*;
import java.util.*;
import java.nio.*;
import java.nio.file.*;
import static java.nio.file.StandardCopyOption.*;

import estagio1.leitura.Functions;
import estagio1.leitura.LeitorArquivo;

import object.DataTreeObject;
import object.indexed.tree.ArvoreB;
import object.indexed.tree.EscritorTree;
import object.indexed.tree.LeitorTree;

public class Main {

	
	static ArvoreB btree;
	
    public static void main(String[] args) throws Exception {
    	
    	String userP=System.getProperty("user.home");//Pasta do Usuario do PC
		String documentDir="Documents";//Local padrão
        String sep = File.separator;// Separador do sistema operacional em uso
		String fileDir="TP_AEDS_III";
		String archive="traffic_accidents_pt_br_rev2.csv";
		//String archive="traffic_accidents_rev2.csv";
		
		//Locais predefinidos:
		//Na pasta Documentos
		String pathDocumentDir=userP.concat(sep.concat(documentDir).concat(sep.concat(fileDir).concat(sep.concat(archive))));
		//Dentro da aplicação
		String arquivoCSV = "data".concat(sep.concat(archive));
		
		String pathDir="index".concat(sep.concat("arvore_b"));//Diretorio da Arvore
				
		Functions.checkDirectory(pathDir);//Verifica se existe, senão existir cria o caminho
		
		String pathDb=pathDir.concat(sep.concat("banco.db"));
        
        //O arquivo de dados é criado na pasta ""index/arvore_b/" e é aberto para o acesso aleatório
        
		
			
        //São instanciados os objetos dos arquivos de índice
		btree = new ArvoreB("btree.index", (short)31);//Instancia a Arvore 31 filhos e 32 ponteiros
		//multilista = new Multilista();//Bucket(Lista Invertida)
				
		int op=1;//variavel de escolha
		
		do {
			System.out.println("\n==================Arvore B========================");
			System.out.println("\n===================Padrão=========================");
			System.out.println("\nProcessos de escrita\n");
			System.out.println("1) escrever todos os registros no arquivo inicial");
			System.out.println("2) escrever apenas um registro no arquivo inicial");
			System.out.println("3) ler id 5");
			System.out.println("10) teste leitura de "+pathDb);
			System.out.println("\n==================Apendice========================");
			System.out.println("\nAnalise a criterio:\nCódigo reaproveitado para adicionar funcionalidade\n");
			System.out.println("11) explorador de arquivo para arquivo inicial");
			System.out.println("\n0) Sair\n\nEscolha um valor-------> :");
			op=Functions.only_Int();
			switch(op) {
				case 1:
					EscritorTree.cargaBase(btree,op,arquivoCSV,pathDb);
					break;
				case 2:
					EscritorTree.cargaBase(btree,op,arquivoCSV,pathDb);
					break;
				case 3:
					System.out.println("Em desenvolvimento");
					DataTreeObject obj=LeitorTree.read(5,btree,pathDb);
					System.out.println(obj.toStringObject());
					break;
				case 10:
					LeitorTree.readAll(pathDb,1,0);//Todos
					break;
				default:
					if(op==0) {
						System.out.println("\nVoltando ao ao Menu da Parte II.");
					}else {
						System.out.println("\nTente novamente, escolha fora do escopo.");
					}
			}
		}while(op!=0);
        
    }
    
   
    
    
    
    
    
    
    
    
    
    
    
}