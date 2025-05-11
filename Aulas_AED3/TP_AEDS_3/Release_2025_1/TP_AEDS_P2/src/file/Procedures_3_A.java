package file;

import data.huffman.*;

import data.caesar.Caesar;
import data.vigenere.Vigenere;
import functions.*;

public class Procedures_3_A {
    
    public static void callCaesar(){
        
        String plainText="a ;@5$Amanhã é Domingo.";
        
        int shift = 23;
        
        System.out.println("String Base----------: " + plainText);
 
        String ciphertext2 = Caesar.encrypt(plainText, shift);
        System.out.println("String Cifrada-------: " + ciphertext2);
        
        String decrypted2 = Caesar.decrypt(ciphertext2, shift);
        System.out.println("String Decifrada-----:" + decrypted2);
        System.out.println("A Decifragem ocorreu : "
                + decrypted2.equals(plainText));
    }
    public static void callVigenere(){
        
        String PlainText=("@/x$Amanhã tem prova");
        String Key=("notas");
        System.out.println("\nUsando a Classe Vigenere\nString Base: "+PlainText);
        System.out.println("Key: "+Key);
        Vigenere V=new Vigenere(Key);
        String Vigenere=V.Encrypt(PlainText);
        System.out.println("\nEncriptando Vigenere: "+Vigenere);
        String RevertVigenere=V.Decrypt(Vigenere);
        System.out.println("\nDecriptando Vigenere: "+RevertVigenere);
    
    }
    
      
}
