package FileExplorer;//Nome do Subprojeto

/**
 * @version 2_2025_01_31
 * @author Gabriel da Silva Cassino
 */


import java.util.*;//Simplificação de bibliotecas necessarias 
import java.util.regex.*;//Simplificação de bibliotecas especificas e necessarias 
import java.util.stream.*;//Simplificação de bibliotecas especificas e necessárias
import java.util.stream.*;//Simplificação de bibliotecas especificas e necessárias

import java.io.*;//Simplificação de bibliotecas necessarias para arquivos

import java.nio.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.file.*;//Simplificação de bibliotecas especificas e necessárias
import java.nio.charset.*;//Simplificação de bibliotecas necessarias para caracteres


//Use o Eclipse para Rodar por Favor
public class FileReader {//Leitor de Arquivo
    public static void read_file(String pathFile) throws IOException {


        java.io.FileReader ler = new java.io.FileReader(pathFile);
        BufferedReader reader = new BufferedReader(ler);
                
        String linha;
        char c = '.'; 
        
        for (int i =1;(linha = reader.readLine()) != null;i++) {
            if(linha.indexOf(c) == -1) {
                
            	if((i>=4206&&i<=4208)||(i>=7183&&i<=7185)||(i>=8985&&i<=8988)) {
	                System.out.println("Linha 0"+i+": "+linha);//Exibe "Linha 012444: ??? 33092219940724001X"
	                //                 "Linha 0<i>  :  <linha>" 
            	}
                
            }else {
                System.out.println("Não execute 0"+i+": "+linha);
            }    
        }
    }
  //Use o Eclipse para Rodar por Favor    
    public static void read_file2(String pathFile) throws IOException {


        java.io.FileReader ler = new java.io.FileReader(pathFile);
        BufferedReader reader = new BufferedReader(ler);
               
        String linha;
        char c = '.'; 
        
        for (int i =1;(linha = reader.readLine()) != null;i++) {
            if(linha.indexOf(c) == -1) {
                
            	
                String[] result=linha.split(","); 
               //FileExplorer.Splitter_String(linha, i,k);
                System.out.println("Linha 0"+(i-1)+": "+result[0]+" "+result[1]);//Exibe "Linha 012444: ???        33092219940724001X"

            }else {
                System.out.println("Não execute 0"+i+": "+linha);
            }    
        }
    }
    //Apenas para analise(From---> https://mkyong.com/java/how-to-read-utf-8-encoded-data-from-a-file-java/)
    public static void readUnicodeClassic(String fileName) {

        File file = new File(fileName);

        try (FileInputStream fis = new FileInputStream(file);
             InputStreamReader isr = new InputStreamReader(fis, StandardCharsets.UTF_8);
             BufferedReader reader = new BufferedReader(isr)
        ) {

            String str;
            while ((str = reader.readLine()) != null) {
                System.out.println(str);
            }

        } catch (IOException e) {
            e.printStackTrace();
        }

    }
    /*Função com Problema no NetBeans(Função acima na integra para analise)
      
    ===================================================================================================================== 
    OBSERVAÇÃO FINAL:  O arquivo continha erros que foram corrigidos, o NetBeans ainda não exibe os caracteres chineses
    =====================================================================================================================
    
    public static void read_file(String pathFile) throws IOException {

        java.io.FileReader ler = new java.io.FileReader(pathFile);
        BufferedReader reader = new BufferedReader(ler);
        //Soluções possíveis UTF-16 e ISO8859-1 (pesquisar) no BufferedReader e FileInputStream

        
        String linha;
        char c = '.'; 
        for (int i =1;(linha = reader.readLine()) != null;i++) {
            if(linha.indexOf(c) == -1) {
                
                //String[] parts = linha.split(" ");
                //System.out.println("Linha 0"+i+": "+parts[0]+" "+parts[1]);//Exibe "Linha 012444: ???        33092219940724001X"
                //Problema exibir caracter chines no java          "Linha 0<i>:   <parte 0>  <parte 1>"       
                //e Problema exibir caracter chines e outindexarray na linha 4200 no java
                
                System.out.println("Linha 0"+i+": "+linha);//Exibe "Linha 012444: ???        33092219940724001X"
                //Problema exibir caracter chines no java          "Linha 0<i>:   <parte 0>  <parte 1>"        


                
            }else {
                System.out.println("Não execute 0"+i+": "+linha);
            }    
        }
    }
    
    */
}