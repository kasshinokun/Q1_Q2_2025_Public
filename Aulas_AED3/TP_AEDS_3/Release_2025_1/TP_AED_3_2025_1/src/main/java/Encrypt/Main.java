package Encrypt;


import java.math.*;

public class Main
{
	public static void main(String[] args) {
		String hello="Hello World Java";
		System.out.println(hello);

    byte[] hex=hello.getBytes();
        
    System.out.println(hex.length);
    
    matrixBKey(hex);
  }
  public static byte[][] matrixBKey(byte[] Key){
    byte[][] RoundKey=new byte[4][4];
    for(int i=0;i<4;i++){
      for(int j=0;j<4;j++){
        RoundKey[i][j] = Key[(j * 4) + i];
      }  
      
    }return RoundKey;
  }
  public static byte[][] xorMatrix(byte[][] RoundKey){
	byte[][] xorMatrixRound=new byte[4][4];
	for(int i=0;i<4;i++){
	  for(int j=0;j<4;j++){
	                       //RoundKey 1 xor RoundKey 3= xorMatrixRound 1
	                       //RoundKey 2 xor xorMatrixRound 1= xorMatrixRound 2
	                       //RoundKey 3 xor xorMatrixRound 2= xorMatrixRound 3
	                       //RoundKey 4 xor xorMatrixRound 3= xorMatrixRound 4
	    	  xorMatrixRound[i][j]=(byte)(i+j);
	      }  
	      
	    }
	    
	    
	    return xorMatrixRound;
	    
	  }
  public static char[][] matrixCKey(char[] Key){
    char[][] RoundKey=new char[4][4];
    
    for(int i=0;i<4;i++){
      for(int j=0;j<4;j++){
        RoundKey[i][j] = Key[(j * 4) + i];
        System.out.print(Key[(j * 4) + i]);
      }  
      System.out.println();
    }return RoundKey;
  }

}