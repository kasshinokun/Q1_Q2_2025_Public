package ASCII;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;

public class xor_process {
	
	public static void main(String[] args) {
		System.out.println("String Base is 你.");
		testalpha();

	}
	
	public static void testalpha() {
		byte[][] transform_matrix=matrixBKey("satishcjisboring".getBytes());
		for (byte[] a: transform_matrix) {
			System.out.println(byteArrayToHex(a));
		}
		System.out.println();
		byte[][] get_mix=xorMatrix(transform_matrix);
		for (byte[] b: get_mix) {
			System.out.println(byteArrayToHex(b));
		}
		byte[][] confirm= {{(byte)0x00,(byte)0x01,(byte)0x02,(byte)0x03},
						   {(byte)0x04,(byte)0x05,(byte)0x06,(byte)0x07},
						   {(byte)0x08,(byte)0x09,(byte)0x0a,(byte)0x0b},
						   {(byte)0x0c,(byte)0x0d,(byte)0x0e,(byte)0x0f}};
		System.out.println();
		System.out.println(byteArrayToHex(arrayBKey(confirm)));
	}	
	
	public static String byteArrayToHex(byte[] a) {
	   StringBuilder sb = new StringBuilder(a.length * 2);
	   for(byte b: a)
	      sb.append(String.format("%02x ", b));
	   return sb.toString();
	}
	public static byte[][] matrixBKey(byte[] Key){//Creating the matrix from key string 16-byte block array
													
    	byte[][] RoundKey=new byte[4][4];
    	for(int i=0;i<4;i++){
    		for(int j=0;j<4;j++){
    			RoundKey[i][j] = Key[(j * 4) + i];
    		}  
    	}return RoundKey;
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
	public static byte[][] xorMatrix(byte[][] RoundKey){//Round Key Matrix Generation
		
		byte[][] xorMatrixRound=new byte[4][4];//new array
		
		//Array from column
		byte[] g4column= {RoundKey[1][3],RoundKey[2][3],RoundKey[3][3],RoundKey[0][3]};//g function(Manual Process)

		//Loop to Generate Round Key Matrix
		for(int i=0;i<4;i++){
			for(int j=0;j<4;j++){
				if(i==0) {//For only Column 0
					//0 Column RoundKey xor (g function(3rd Column RoundKey))= xorMatrixRound 0
					xorMatrixRound[j][i] = (byte) (RoundKey[j][i] ^ g4column[i+j]);
				}else {
					//i Column RoundKey  xor i-1 Column xorMatrixRound = i Column xorMatrixRound
					xorMatrixRound[j][i] = (byte) (RoundKey[j][i] ^ xorMatrixRound[j][i-1]); 
				}
			}
			
		}return  xorMatrixRound;
	}
	//==================================================>Split Information
	// Convert object to byte[]
	  public static byte[] convertObjectToBytes2(Object obj) throws IOException {
	      ByteArrayOutputStream boas = new ByteArrayOutputStream();
	      try (ObjectOutputStream ois = new ObjectOutputStream(boas)) {
	          ois.writeObject(obj);
	          return boas.toByteArray();
	      }
	  }
	public static byte[][] splitIntoBlocks(byte[] Information){
				
		byte[][] Matrix128;
		int size=Information.length;
		if(size%16==0) {
			Matrix128=new byte[(size/16)][16];//new matrix
		}else {
			Matrix128=new byte[(size/16)+1][16];//new matrix
		}
		for(int i=0;i<(size/16);i++) {
			for(int j=0;i<16||(16*i+j+1)==size;j++) {
				Matrix128[i][j]=Information[16*i+j];
			}
		}
		
		
		
		
		
		
		
		
		
		return Matrix128;
		
	}
	
}
