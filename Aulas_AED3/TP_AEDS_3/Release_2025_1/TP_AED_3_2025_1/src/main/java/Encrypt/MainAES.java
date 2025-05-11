package Encrypt;
import javax.crypto.Cipher;  
import javax.crypto.SecretKey;  
import javax.crypto.SecretKeyFactory;  
import javax.crypto.spec.IvParameterSpec;  
import javax.crypto.spec.PBEKeySpec;  
import javax.crypto.spec.SecretKeySpec;  
import java.nio.charset.StandardCharsets;  
import java.security.InvalidAlgorithmParameterException;  
import java.security.InvalidKeyException;  
import java.security.NoSuchAlgorithmException;  
import java.security.spec.InvalidKeySpecException;  
import java.security.spec.KeySpec;  
import java.util.Base64;  
import javax.crypto.BadPaddingException;  
import javax.crypto.IllegalBlockSizeException;  
import javax.crypto.NoSuchPaddingException; 
import Encrypt.Encryption.*;
public class MainAES {

	public static void main(String[] args) {
		String strMessage = "AES Encryption";
		testAES (strMessage);
		AES_Original(strMessage);
	}	
	public static void testAES (String strMessage){	
		AESAlgorithm alg = new AESAlgorithm(AESAlgorithm.KEY_SIZE_256); // up to 4096
    	byte[] bytesKey = alg.createKey();
    	//byte[] bytesKey = alg.createKey("PBKDF2WithHmacSHA256");
    	int[] wordsKeyExpansion = alg.createKeyExpansion(bytesKey);
    	
        byte[] bytesMessage = strMessage.getBytes();
    	byte[] bytesEncrypted = alg.cipher(bytesMessage, wordsKeyExpansion);
    	byte[] bytesDecrypted = alg.invCipher(bytesEncrypted, wordsKeyExpansion);
    	System.out.println(strMessage);
    	System.out.println(new String(bytesEncrypted));
    	System.out.println(new String(bytesDecrypted));
    }
	public static void AES_Original(String originalval){ 

		  
		/* Call the encrypt() method and store result of encryption. */  
		String encryptedval = Encryption.encrypt(originalval,"PBKDF2WithHmacSHA256");  
		/* Call the decrypt() method and store result of decryption. */  
		String decryptedval = Encryption.decrypt(encryptedval,"PBKDF2WithHmacSHA256");  
		/* Display the original message, encrypted message and decrypted message on the console. */  
		System.out.println("Original value: " + originalval);  
		System.out.println("Encrypted value: " + encryptedval);  
		System.out.println("Decrypted value: " + decryptedval);  
	}  
}
