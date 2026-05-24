package com.bstartree.model;

/**
 * Metadados de cada nó da árvore B*
 * Contém: ID, Lapide, Posicao, Size_Registry
 */
public class NodeMetadata {
    
    private int ID;                    // ID do Registro (chave)
    private boolean Lapide;            // Flag de exclusão lógica (tombstone)
    private int Posicao;               // Posição/offset no arquivo
    private int Size_Registry;         // Tamanho do registro serializado
    
    public NodeMetadata() {
        this.ID = -1;
        this.Lapide = false;
        this.Posicao = -1;
        this.Size_Registry = 0;
    }
    
    public NodeMetadata(int id, boolean lapide, int posicao, int size) {
        this.ID = id;
        this.Lapide = lapide;
        this.Posicao = posicao;
        this.Size_Registry = size;
    }
    
    // Getters e Setters
    public int getID() { return ID; }
    public void setID(int id) { this.ID = id; }
    
    public boolean isLapide() { return Lapide; }
    public void setLapide(boolean lapide) { Lapide = lapide; }
    
    public int getPosicao() { return Posicao; }
    public void setPosicao(int posicao) { Posicao = posicao; }
    
    public int getSize_Registry() { return Size_Registry; }
    public void setSize_Registry(int size) { Size_Registry = size; }
    
    /**
     * Serializa os metadados para array de bytes
     * Formato: [ID:4][Lapide:1][Posicao:4][Size_Registry:4] = 13 bytes
     */
    public byte[] toBytes() {
        byte[] buffer = new byte[13];
        int offset = 0;
        
        // ID (4 bytes - big-endian)
        buffer[offset++] = (byte) ((ID >> 24) & 0xFF);
        buffer[offset++] = (byte) ((ID >> 16) & 0xFF);
        buffer[offset++] = (byte) ((ID >> 8) & 0xFF);
        buffer[offset++] = (byte) (ID & 0xFF);
        
        // Lapide (1 byte)
        buffer[offset++] = Lapide ? (byte) 1 : (byte) 0;
        
        // Posicao (4 bytes)
        buffer[offset++] = (byte) ((Posicao >> 24) & 0xFF);
        buffer[offset++] = (byte) ((Posicao >> 16) & 0xFF);
        buffer[offset++] = (byte) ((Posicao >> 8) & 0xFF);
        buffer[offset++] = (byte) (Posicao & 0xFF);
        
        // Size_Registry (4 bytes)
        buffer[offset++] = (byte) ((Size_Registry >> 24) & 0xFF);
        buffer[offset++] = (byte) ((Size_Registry >> 16) & 0xFF);
        buffer[offset++] = (byte) ((Size_Registry >> 8) & 0xFF);
        buffer[offset] = (byte) (Size_Registry & 0xFF);
        
        return buffer;
    }
    
    /**
     * Desserializa metadados de array de bytes
     */
    public static NodeMetadata fromBytes(byte[] buffer, int offset) {
        NodeMetadata meta = new NodeMetadata();
        int pos = offset;
        
        // ID
        meta.ID = ((buffer[pos++] & 0xFF) << 24) |
                  ((buffer[pos++] & 0xFF) << 16) |
                  ((buffer[pos++] & 0xFF) << 8) |
                  (buffer[pos++] & 0xFF);
        
        // Lapide
        meta.Lapide = buffer[pos++] != 0;
        
        // Posicao
        meta.Posicao = ((buffer[pos++] & 0xFF) << 24) |
                       ((buffer[pos++] & 0xFF) << 16) |
                       ((buffer[pos++] & 0xFF) << 8) |
                       (buffer[pos++] & 0xFF);
        
        // Size_Registry
        meta.Size_Registry = ((buffer[pos++] & 0xFF) << 24) |
                             ((buffer[pos++] & 0xFF) << 16) |
                             ((buffer[pos++] & 0xFF) << 8) |
                             (buffer[pos] & 0xFF);
        
        return meta;
    }
    
    @Override
    public String toString() {
        return String.format("NodeMetadata{ID=%d, Lapide=%b, Posicao=%d, Size=%d}",
                ID, Lapide, Posicao, Size_Registry);
    }
}
