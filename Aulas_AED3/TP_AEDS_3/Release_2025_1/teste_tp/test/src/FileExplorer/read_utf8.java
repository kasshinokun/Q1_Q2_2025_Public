
//JRE usando Java-SE 21

// https://mkyong.com/java/how-to-read-utf-8-encoded-data-from-a-file-java/
/**
 * @version 1_2025_01_31
 * @author  Mkyong
 * @release-editor Gabriel da Silva Cassino
 */


package FileExplorer;

//Simplificação de bibliotecas necessarias 
import java.io.*;
import java.nio.charset.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class read_utf8{

    public static void main(String[] args) {

    	String sep = File.separator;// Separador do sistema operacional em uso
        String fileName = System.getProperty("user.home")+sep+"Documents"+sep+"NetBeansProjects"+sep+"FileExplorer"+sep+"src"+sep+"main"+sep+"java"+sep+"FileExplorer"+sep+"texto.txt";
       
        readUnicodeBufferedReader(fileName);
        
        //Outras opções de procedimentos
        //readUnicodeJava11(fileName);
        //readUnicodeFiles(fileName);
        //readUnicodeClassic(fileName);

    }

    // Java 7 - Files.newBufferedReader(path, StandardCharsets.UTF_8)
    // Java 8 - Files.newBufferedReader(path) // default UTF-8
    public static void readUnicodeBufferedReader(String fileName) {

        Path path = Paths.get(fileName);

        // Java 8, default UTF-8
        try (BufferedReader reader = Files.newBufferedReader(path)) {

            String str;
            while ((str = reader.readLine()) != null) {
                System.out.println(str);
            }

        } catch (IOException e) {
            e.printStackTrace();
        }

    }

//Outras opções de procedimentos-----------------------------------------------------------------------------------------------------------    
 // Java 11, adds charset to FileReader //opção 1
    public static void readUnicodeJava11(String fileName) {

        Path path = Paths.get(fileName);

        try (java.io.FileReader fr = new java.io.FileReader(fileName, StandardCharsets.UTF_8);
             BufferedReader reader = new BufferedReader(fr)) {

            String str;
            while ((str = reader.readLine()) != null) {
                System.out.println(str);
            }

        } catch (IOException e) {
            e.printStackTrace();
        }

    }
    
    //opção 2
    public static void readUnicodeFiles(String fileName) {

        Path path = Paths.get(fileName);
        try {

            // Java 11
            String s = Files.readString(path, StandardCharsets.UTF_8);
            System.out.println(s);

            // Java 8
            List<String> list = Files.readAllLines(path, StandardCharsets.UTF_8);
            list.forEach(System.out::println);

            // Java 8
            Stream<String> lines = Files.lines(path, StandardCharsets.UTF_8);
            lines.forEach(System.out::println);

        } catch (IOException e) {
            e.printStackTrace();
        }

    }
    
    //opção 3
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
}