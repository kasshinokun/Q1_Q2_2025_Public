package Encrypt;//Nome do Subprojeto

/**
 * @version 1_2025_02_14
 * @author Gabriel da Silva Cassino
 */

import java.lang.*;
import java.io.*;
import java.util.*;

public class MyEncrypt {
	
	public static void main(String[] args) {
		
		System.out.println("Hello World");
		teste_k();
	
	}
	
	
//=====================================================> Attributes 	
	
	//Mnemonics of AES class
	public static final int KEY_SIZE_128 = 128;
    public static final int KEY_SIZE_192 = 192;
    public static final int KEY_SIZE_256 = 256;
    public static final int NB_VALUE = 4;// The number of columns comprising a state in AES. This is a constant in AES. Value=4
    public static int NK_VALUE =0;// The number of 32 bit words in a key
    public static int NR_VALUE = 0;// The number of rounds in AES Cipher
    
    private static String DEFAULT_CHARSET = "UTF-8";//Charset
	
	
//=====================================================================Vetor de Bytes AES-256 A===================================================================================================
	
	//0              1         2            3        4          5           6         7          8          9          A          B         C           D           E           F
	static byte[] sbox={
	(byte)0x63,(byte)0x7c,(byte)0x77,(byte)0x7b,(byte)0xf2,(byte)0x6b,(byte)0x6f,(byte)0xc5,(byte)0x30,(byte)0x01,(byte)0x67,(byte)0x2b,(byte)0xfe,(byte)0xd7,(byte)0xab,(byte)0x76, //0        
	(byte)0xca,(byte)0x82,(byte)0xc9,(byte)0x7d,(byte)0xfa,(byte)0x59,(byte)0x47,(byte)0xf0,(byte)0xad,(byte)0xd4,(byte)0xa2,(byte)0xaf,(byte)0x9c,(byte)0xa4,(byte)0x72,(byte)0xc0, //1
	(byte)0xb7,(byte)0xfd,(byte)0x93,(byte)0x26,(byte)0x36,(byte)0x3f,(byte)0xf7,(byte)0xcc,(byte)0x34,(byte)0xa5,(byte)0xe5,(byte)0xf1,(byte)0x71,(byte)0xd8,(byte)0x31,(byte)0x15, //2 
	(byte)0x04,(byte)0xc7,(byte)0x23,(byte)0xc3,(byte)0x18,(byte)0x96,(byte)0x05,(byte)0x9a,(byte)0x07,(byte)0x12,(byte)0x80,(byte)0xe2,(byte)0xeb,(byte)0x27,(byte)0xb2,(byte)0x75, //3 
	(byte)0x09,(byte)0x83,(byte)0x2c,(byte)0x1a,(byte)0x1b,(byte)0x6e,(byte)0x5a,(byte)0xa0,(byte)0x52,(byte)0x3b,(byte)0xd6,(byte)0xb3,(byte)0x29,(byte)0xe3,(byte)0x2f,(byte)0x84, //4
	(byte)0x53,(byte)0xd1,(byte)0x00,(byte)0xed,(byte)0x20,(byte)0xfc,(byte)0xb1,(byte)0x5b,(byte)0x6a,(byte)0xcb,(byte)0xbe,(byte)0x39,(byte)0x4a,(byte)0x4c,(byte)0x58,(byte)0xcf, //5
	(byte)0xd0,(byte)0xef,(byte)0xaa,(byte)0xfb,(byte)0x43,(byte)0x4d,(byte)0x33,(byte)0x85,(byte)0x45,(byte)0xf9,(byte)0x02,(byte)0x7f,(byte)0x50,(byte)0x3c,(byte)0x9f,(byte)0xa8, //6
	(byte)0x51,(byte)0xa3,(byte)0x40,(byte)0x8f,(byte)0x92,(byte)0x9d,(byte)0x38,(byte)0xf5,(byte)0xbc,(byte)0xb6,(byte)0xda,(byte)0x21,(byte)0x10,(byte)0xff,(byte)0xf3,(byte)0xd2, //7
	(byte)0xcd,(byte)0x0c,(byte)0x13,(byte)0xec,(byte)0x5f,(byte)0x97,(byte)0x44,(byte)0x17,(byte)0xc4,(byte)0xa7,(byte)0x7e,(byte)0x3d,(byte)0x64,(byte)0x5d,(byte)0x19,(byte)0x73, //8
	(byte)0x60,(byte)0x81,(byte)0x4f,(byte)0xdc,(byte)0x22,(byte)0x2a,(byte)0x90,(byte)0x88,(byte)0x46,(byte)0xee,(byte)0xb8,(byte)0x14,(byte)0xde,(byte)0x5e,(byte)0x0b,(byte)0xdb, //9
	(byte)0xe0,(byte)0x32,(byte)0x3a,(byte)0x0a,(byte)0x49,(byte)0x06,(byte)0x24,(byte)0x5c,(byte)0xc2,(byte)0xd3,(byte)0xac,(byte)0x62,(byte)0x91,(byte)0x95,(byte)0xe4,(byte)0x79, //A
	(byte)0xe7,(byte)0xc8,(byte)0x37,(byte)0x6d,(byte)0x8d,(byte)0xd5,(byte)0x4e,(byte)0xa9,(byte)0x6c,(byte)0x56,(byte)0xf4,(byte)0xea,(byte)0x65,(byte)0x7a,(byte)0xae,(byte)0x08, //B
	(byte)0xba,(byte)0x78,(byte)0x25,(byte)0x2e,(byte)0x1c,(byte)0xa6,(byte)0xb4,(byte)0xc6,(byte)0xe8,(byte)0xdd,(byte)0x74,(byte)0x1f,(byte)0x4b,(byte)0xbd,(byte)0x8b,(byte)0x8a, //C
	(byte)0x70,(byte)0x3e,(byte)0xb5,(byte)0x66,(byte)0x48,(byte)0x03,(byte)0xf6,(byte)0x0e,(byte)0x61,(byte)0x35,(byte)0x57,(byte)0xb9,(byte)0x86,(byte)0xc1,(byte)0x1d,(byte)0x9e, //D
	(byte)0xe1,(byte)0xf8,(byte)0x98,(byte)0x11,(byte)0x69,(byte)0xd9,(byte)0x8e,(byte)0x94,(byte)0x9b,(byte)0x1e,(byte)0x87,(byte)0xe9,(byte)0xce,(byte)0x55,(byte)0x28,(byte)0xdf, //E
	(byte)0x8c,(byte)0xa1,(byte)0x89,(byte)0x0d,(byte)0xbf,(byte)0xe6,(byte)0x42,(byte)0x68,(byte)0x41,(byte)0x99,(byte)0x2d,(byte)0x0f,(byte)0xb0,(byte)0x54,(byte)0xbb,(byte)0x16}; //F

//=====================================================================Vetor de Bytes AES-256 B===================================================================================================	
	static byte[] rsbox = {
	(byte)0x52,(byte)0x09,(byte)0x6a,(byte)0xd5,(byte)0x30,(byte)0x36,(byte)0xa5,(byte)0x38,(byte)0xbf,(byte)0x40,(byte)0xa3,(byte)0x9e,(byte)0x81,(byte)0xf3,(byte)0xd7,(byte)0xfb,
	(byte)0x7c,(byte)0xe3,(byte)0x39,(byte)0x82,(byte)0x9b,(byte)0x2f,(byte)0xff,(byte)0x87,(byte)0x34,(byte)0x8e,(byte)0x43,(byte)0x44,(byte)0xc4,(byte)0xde,(byte)0xe9,(byte)0xcb,
    (byte)0x54,(byte)0x7b,(byte)0x94,(byte)0x32,(byte)0xa6,(byte)0xc2,(byte)0x23,(byte)0x3d,(byte)0xee,(byte)0x4c,(byte)0x95,(byte)0x0b,(byte)0x42,(byte)0xfa,(byte)0xc3,(byte)0x4e,
	(byte)0x08,(byte)0x2e,(byte)0xa1,(byte)0x66,(byte)0x28,(byte)0xd9,(byte)0x24,(byte)0xb2,(byte)0x76,(byte)0x5b,(byte)0xa2,(byte)0x49,(byte)0x6d,(byte)0x8b,(byte)0xd1,(byte)0x25,
	(byte)0x72,(byte)0xf8,(byte)0xf6,(byte)0x64,(byte)0x86,(byte)0x68,(byte)0x98,(byte)0x16,(byte)0xd4,(byte)0xa4,(byte)0x5c,(byte)0xcc,(byte)0x5d,(byte)0x65,(byte)0xb6,(byte)0x92,
	(byte)0x6c,(byte)0x70,(byte)0x48,(byte)0x50,(byte)0xfd,(byte)0xed,(byte)0xb9,(byte)0xda,(byte)0x5e,(byte)0x15,(byte)0x46,(byte)0x57,(byte)0xa7,(byte)0x8d,(byte)0x9d,(byte)0x84,
	(byte)0x90,(byte)0xd8,(byte)0xab,(byte)0x00,(byte)0x8c,(byte)0xbc,(byte)0xd3,(byte)0x0a,(byte)0xf7,(byte)0xe4,(byte)0x58,(byte)0x05,(byte)0xb8,(byte)0xb3,(byte)0x45,(byte)0x06,
	(byte)0xd0,(byte)0x2c,(byte)0x1e,(byte)0x8f,(byte)0xca,(byte)0x3f,(byte)0x0f,(byte)0x02,(byte)0xc1,(byte)0xaf,(byte)0xbd,(byte)0x03,(byte)0x01,(byte)0x13,(byte)0x8a,(byte)0x6b,
	(byte)0x3a,(byte)0x91,(byte)0x11,(byte)0x41,(byte)0x4f,(byte)0x67,(byte)0xdc,(byte)0xea,(byte)0x97,(byte)0xf2,(byte)0xcf,(byte)0xce,(byte)0xf0,(byte)0xb4,(byte)0xe6,(byte)0x73,
	(byte)0x96,(byte)0xac,(byte)0x74,(byte)0x22,(byte)0xe7,(byte)0xad,(byte)0x35,(byte)0x85,(byte)0xe2,(byte)0xf9,(byte)0x37,(byte)0xe8,(byte)0x1c,(byte)0x75,(byte)0xdf,(byte)0x6e,
	(byte)0x47,(byte)0xf1,(byte)0x1a,(byte)0x71,(byte)0x1d,(byte)0x29,(byte)0xc5,(byte)0x89,(byte)0x6f,(byte)0xb7,(byte)0x62,(byte)0x0e,(byte)0xaa,(byte)0x18,(byte)0xbe,(byte)0x1b,
	(byte)0xfc,(byte)0x56,(byte)0x3e,(byte)0x4b,(byte)0xc6,(byte)0xd2,(byte)0x79,(byte)0x20,(byte)0x9a,(byte)0xdb,(byte)0xc0,(byte)0xfe,(byte)0x78,(byte)0xcd,(byte)0x5a,(byte)0xf4,
	(byte)0x1f,(byte)0xdd,(byte)0xa8,(byte)0x33,(byte)0x88,(byte)0x07,(byte)0xc7,(byte)0x31,(byte)0xb1,(byte)0x12,(byte)0x10,(byte)0x59,(byte)0x27,(byte)0x80,(byte)0xec,(byte)0x5f,
	(byte)0x60,(byte)0x51,(byte)0x7f,(byte)0xa9,(byte)0x19,(byte)0xb5,(byte)0x4a,(byte)0x0d,(byte)0x2d,(byte)0xe5,(byte)0x7a,(byte)0x9f,(byte)0x93,(byte)0xc9,(byte)0x9c,(byte)0xef,
	(byte)0xa0,(byte)0xe0,(byte)0x3b,(byte)0x4d,(byte)0xae,(byte)0x2a,(byte)0xf5,(byte)0xb0,(byte)0xc8,(byte)0xeb,(byte)0xbb,(byte)0x3c,(byte)0x83,(byte)0x53,(byte)0x99,(byte)0x61,
	(byte)0x17,(byte)0x2b,(byte)0x04,(byte)0x7e,(byte)0xba,(byte)0x77,(byte)0xd6,(byte)0x26,(byte)0xe1,(byte)0x69,(byte)0x14,(byte)0x63,(byte)0x55,(byte)0x21,(byte)0x0c,(byte)0x7d};
	
//=====================================================================Anothers Variables AES-256===================================================================================================
    
	static byte[] plain_text= {(byte)0x6b,(byte)0xc1,(byte)0xbe,(byte)0xe2,(byte)0x2e,(byte)0x40,(byte)0x9f,(byte)0x96,(byte)0xe9,(byte)0x3d,(byte)0x7e,(byte)0x11,(byte)0x73,(byte)0x93,(byte)0x17,(byte)0x2a,
				    		   (byte)0xae,(byte)0x2d,(byte)0x8a,(byte)0x57,(byte)0x1e,(byte)0x03,(byte)0xac,(byte)0x9c,(byte)0x9e,(byte)0xb7,(byte)0x6f,(byte)0xac,(byte)0x45,(byte)0xaf,(byte)0x8e,(byte)0x51,
				    		   (byte)0x30,(byte)0xc8,(byte)0x1c,(byte)0x46,(byte)0xa3,(byte)0x5c,(byte)0xe4,(byte)0x11,(byte)0xe5,(byte)0xfb,(byte)0xc1,(byte)0x19,(byte)0x1a,(byte)0x0a,(byte)0x52,(byte)0xef,
				    		   (byte)0xf6,(byte)0x9f,(byte)0x24,(byte)0x45,(byte)0xdf,(byte)0x4f,(byte)0x9b,(byte)0x17,(byte)0xad,(byte)0x2b,(byte)0x41,(byte)0x7b,(byte)0xe6,(byte)0x6c,(byte)0x37,(byte)0x10};
	
    static byte[] key= {(byte)0x2b,(byte)0x7e,(byte)0x15,(byte)0x16,
    			        (byte)0x28,(byte)0xae,(byte)0xd2,(byte)0xa6,
    			        (byte)0xab,(byte)0xf7,(byte)0x15,(byte)0x88,
    			        (byte)0x09,(byte)0xcf,(byte)0x4f,(byte)0x3c};
	
	static byte[][] transform_matrix={{(byte)0x02,(byte)0x03,(byte)0x01,(byte)0x01},
									  {(byte)0x01,(byte)0x02,(byte)0x03,(byte)0x01},
									  {(byte)0x01,(byte)0x01,(byte)0x02,(byte)0x03},
									  {(byte)0x03,(byte)0x01,(byte)0x01,(byte)0x02}};						
    /*
    resulting cipher:
    3ad77bb40d7a3660a89ecaf32466ef97 
    f5d3d58503b9699de785895a96fdbaaf 
    43b1cd7f598ece23881b00e3ed030688 
    7b0c785e27e8ad3f8223207104725dd4  
    */
    
    

//=====================================================================Processes AES-256 A========================================================================================================
    private static void setValues(int AES_Code) {//Setting Rounds
		if (AES_Code==256) {
			NK_VALUE=8;        // The number of 32 bit words(8) in a key.
			NR_VALUE=14;       // The number of rounds(14) in AES Cipher 256 bits
		}else if (AES_Code==192){
			NK_VALUE=6;        // The number of 32 bit words(6) in a key.
			NR_VALUE=12;       // The number of rounds(12) in AES Cipher 192 bits
		}else if(AES_Code==128){
			NK_VALUE=4;        // The number of 32 bit words(4) in a key.
			NR_VALUE=10;       // The number of rounds(10) in AES Cipher 128 bits
		}else {
			NK_VALUE=-1;
			NR_VALUE=-1;
		}
	}
	public static boolean isValidKeySize(int keySize) {
        if (keySize == KEY_SIZE_128 ||
            keySize == KEY_SIZE_192 ||
            keySize == KEY_SIZE_256) 
            {
        	setValues(keySize);//Set Rounds and 
        	return true;
        } else {
            return false;
        }

    }
	//=================================> Returns from SBOX Matrix and RSBOX Matrix
	static byte getSBoxValue(byte num)//Getting byte from Sbox based on received byte
	{
	  return sbox[(int)num];
	}
	static byte getRSBoxValue(byte num)//Getting byte from RSbox based on received byte
	{
	  return rsbox[(int)num];
	}
	//====================================================================================

//==========================> Divide Information Into Blocks
	public static byte[][] splitIntoBlocks(String s){
		
		
		byte[][] Matrix128=new byte[4][16];//new matrix
		
		
		
		
		
		
		
		
		
		
		
		return Matrix128;
		
	}
	
	
	
	
	
	
//==========================> Key Expansion
	public static byte[][] xorMatrix(byte[][] RoundKey){//Round Key Matrix Generation
		
		byte[][] xorMatrixRound=new byte[4][4];//new matrix
		
		//Array from column
		byte[] g4column= {RoundKey[1][3],RoundKey[2][3],RoundKey[3][3],RoundKey[0][3]};//g function(Manual Process)

		//Loop to Generate Round Key Matrix
		for(int i=0;i<4;i++){
			for(int j=0;j<4;j++){
				if(i==0) {//For only Column 0
					//0 Column RoundKey xor (g function(3rd Column RoundKey))= xorMatrixRound 0
					xorMatrixRound[j][i] = (byte) (RoundKey[j][i] ^ g4column[i+j]);
				}else {
					//i Column RoundKey  xor (i-1) Column xorMatrixRound = i Column xorMatrixRound
					xorMatrixRound[j][i] = (byte) (RoundKey[j][i] ^ xorMatrixRound[j][i-1]); 
				}
			}
			
		}return  xorMatrixRound;
	}
	public static byte[][] MixColumns(byte[][] state){
		
		byte[][] state_mix=new byte[4][4];


		return state_mix;
	}
//===================================> Byte Array to Matrix and Matrix to Byte Array 
	public static byte[][] matrixBKey(byte[] Key){
		//Creating the matrix from the 16-byte block (byte array) of the key string
	    	
		byte[][] RoundKey=new byte[4][4];
    	
		for(int i=0;i<4;i++){
    		for(int j=0;j<4;j++){
    			RoundKey[i][j] = Key[(j * 4) + i];
    		}  
    	}
		return RoundKey;
    }
	public static byte[] arrayBKey(byte[][] Key){//Restoring the array from  key string 16-byte block matrix
    	byte[] RoundKey=new byte[16];
    	for(int i=0;i<4;i++){
    		for(int j=0;j<4;j++){
    			RoundKey[4*i+j]=Key[i][j];
    		}  
    	}
    	return RoundKey;
    }
//====================================================================Testes AES-256==============================================================================================================
	
	public static void teste_k(){//Getting Left and Right Nibble  from byte
		for (int i=0;i<sbox.length;i++) {
			int lo4 = sbox[i] & 0x0F;
			int hi4 = ( sbox[i] & 0xF0 ) >> 4;
			System.out.print(hi4+" "+lo4+"|");
			if((i+1)%16==0) {
				System.out.println(getSBoxValue((byte)0x45)+" "+getRSBoxValue((byte)0x6e))
				;
			}
		}
			
		
		
	}
}
