package estagio1.leitura;

import java.io.*;

import estagio1.DataObject;
import estagio1.leitura.LeitorArquivo;

public class DeleteProcess {
	
  	public static void deleteFile(RandomAccessFile randomAccessFile, long posicao)throws IOException{
  		
		randomAccessFile.seek(posicao);
       
		randomAccessFile.readInt();
		
        randomAccessFile.writeBoolean(false);
        
        posicao=randomAccessFile.getFilePointer();
        
        DataObject obj=new DataObject();
        
        obj.fromByteArray(LeitorArquivo.buildArray(randomAccessFile,posicao));
        
        System.out.println("\n"+obj.toStringObject()+"\n");
        
        System.out.println("A ID "+obj.getID_registro()+" foi apagada do registro.");
  	}
}
