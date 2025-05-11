package estagio1.FileExplorer;//Nome do Subprojeto

/**
 * @version 2_2025_02_06
 * @author Gabriel da Silva Cassino
 */


import java.util.*;//Simplificação de bibliotecas necessarias 
import java.util.regex.*;//Simplificação de bibliotecas especificas e necessarias 
import java.util.stream.*;//Simplificação de bibliotecas especificas e necessárias

import estagio1.EscritorArquivo;
import estagio2.Escrita.EscritorIndex;

import java.util.stream.*;//Simplificação de bibliotecas especificas e necessárias

import java.io.*;//Simplificação de bibliotecas necessarias para arquivos

import java.nio.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.file.*;//Simplificação de bibliotecas especificas e necessárias
import java.nio.charset.*;//Simplificação de bibliotecas necessarias para caracteres
import java.sql.*;
import java.text.*;

//Use o Eclipse para Rodar por Favor
public class FileReader {//Leitor de Arquivo
	
	//Teste inicial e identificação dos erros
	public static void read_file(String pathFile,int typeWrite) throws IOException {
		String sep = File.separator;// Separador do sistema operacional em uso
		
		//Parte 1
		if (typeWrite==1) {
			String pathDb="data".concat(sep.concat("traffic_accidents.db"));
			EscritorArquivo.writeAllFile(typeWrite,pathFile,pathDb);
		}
		//Parte 2- A
		if (typeWrite==2) {
			String pathDb="index".concat(sep.concat("traffic_accidents.db"));
			String pathIndex="index".concat(sep.concat("indexTrafficAccidents.db"));
			EscritorIndex.writeAllIndex(1,pathFile,pathDb,pathIndex);
		}
		//Parte 2- B
		if (typeWrite==3) {
			String pathDb="index".concat(sep.concat("arvore_b")).concat(sep.concat("banco.db"));
			EscritorArquivo.writeAllFile(typeWrite,pathFile,pathDb);
		}
	}
    
    
}