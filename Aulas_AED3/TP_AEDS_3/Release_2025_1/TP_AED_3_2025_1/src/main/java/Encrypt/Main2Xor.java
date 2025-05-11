package Encrypt;

import java.util.*;

public class Main2Xor {
  
  public static byte[][] xorMatrix(byte[][] RoundKey){
                byte[][] xorMatrixRound=new byte[4][4];
                for(int i=0;i<4;i++){
        		for(int j=0;j<4;j++){
                                //RoundKey 0 xor g(RoundKey 3)= xorMatrixRound 0
                                if(j==0&&i!=3){
                                   xorMatrixRound[i][0]=(byte)(RoundKey[i][0]^RoundKey[3][i+1]); 
				} 
				else if(j==0&&i==3){
                                   xorMatrixRound[3][0]=(byte)(RoundKey[3][0]^RoundKey[3][0]); 
				} 
			     
                                //RoundKey 1 xor xorMatrixRound 0= xorMatrixRound 1
                                //RoundKey 2 xor xorMatrixRound 1= xorMatrixRound 2
                                //RoundKey 3 xor xorMatrixRound 2= xorMatrixRound 3
                                else{
                                     xorMatrixRound[i][j]=(byte)(RoundKey[i][j]^xorMatrixRound[i][j-1]); 
                                }
                        }  
        	}return xorMatrixRound;
        }
  public static void main(String[] args) {
    System.out.println("Hello, World!");
    
    byte[][] RoundKey={{(byte)0x73,(byte)0x73,(byte)0x69,(byte)0x72},
                       {(byte)0x61,(byte)0x68,(byte)0x73,(byte)0x69},
                       {(byte)0x74,(byte)0x63,(byte)0x62,(byte)0x6e},
                       {(byte)0x69,(byte)0x6a,(byte)0x6f,(byte)0x67}};
    
    byte[][] Expansion=xorMatrix(RoundKey);
    
    
    
    
  }
}