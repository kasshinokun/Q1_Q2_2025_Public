package com.bstartree.io;

import java.io.IOException;
import java.io.RandomAccessFile;

/**
 * Camada de abstração para I/O em disco
 * Similar ao VFS do SQLite
 */
public class DiskIO {
    
    private final RandomAccessFile file;
    private final String filePath;
    
    public DiskIO(String filePath) throws IOException {
        this.filePath = filePath;
        this.file = new RandomAccessFile(filePath, "rw");
    }
    
    /**
     * Lê bytes do arquivo na posição especificada
     */
    public byte[] read(long position, int length) throws IOException {
        synchronized (file) {
            file.seek(position);
            byte[] buffer = new byte[length];
            int bytesRead = file.read(buffer);
            if (bytesRead < length) {
                // Preencher com zeros se chegou no fim
                for (int i = bytesRead; i < length; i++) {
                    buffer[i] = 0;
                }
            }
            return buffer;
        }
    }
    
    /**
     * Escreve bytes no arquivo na posição especificada
     */
    public void write(long position, byte[] data) throws IOException {
        synchronized (file) {
            file.seek(position);
            file.write(data);
        }
    }
    
    /**
     * Obtém tamanho atual do arquivo
     */
    public long getFileLength() throws IOException {
        return file.length();
    }
    
    /**
     * Força sincronização com disco (fsync)
     * Similar ao sqlite3_os_sync()
     */
    public void sync() throws IOException {
        file.getFD().sync();
    }
    
    /**
     * Fecha o arquivo
     */
    public void close() throws IOException {
        if (file != null) {
            file.close();
        }
    }
    
    public String getFilePath() {
        return filePath;
    }
}
