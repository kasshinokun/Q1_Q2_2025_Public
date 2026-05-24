package com.bstartree.core;

import com.bstartree.model.NodeMetadata;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Nó da árvore B* em disco
 * Estrutura similar às páginas do SQLite
 */
public class Node {
    
    public enum NodeType {
        LEAF,      // Nó folha (contém dados)
        INTERNAL   // Nó interno (contém ponteiros)
    }
    
    private long pageId;                    // ID da página no arquivo
    private NodeType type;                  // Tipo do nó
    private int parentPageId;               // ID da página pai (-1 se raiz)
    private List<NodeMetadata> entries;     // Entradas do nó
    private List<Long> children;            // Ponteiros para filhos (nós internos)
    private int keyCount;                   // Número de chaves válidas
    private boolean isDirty;                // Flag de modificação
    
    public Node(long pageId, NodeType type) {
        this.pageId = pageId;
        this.type = type;
        this.parentPageId = -1;
        this.entries = new ArrayList<>(Constants.BSTAR_ORDER * 2);
        this.children = new ArrayList<>(Constants.BSTAR_ORDER * 2 + 1);
        this.keyCount = 0;
        this.isDirty = false;
    }
    
    // Getters e Setters
    public long getPageId() { return pageId; }
    public NodeType getType() { return type; }
    public int getParentPageId() { return parentPageId; }
    public void setParentPageId(int parentPageId) { 
        this.parentPageId = parentPageId; 
        this.isDirty = true; 
    }
    public List<NodeMetadata> getEntries() { return entries; }
    public List<Long> getChildren() { return children; }
    public int getKeyCount() { return keyCount; }
    public boolean isDirty() { return isDirty; }
    public void setDirty(boolean dirty) { isDirty = dirty; }
    
    /**
     * Verifica se o nó está cheio (para splitting)
     * B* trees mantêm nós com pelo menos 2/3 de ocupação
     */
    public boolean isFull() {
        return keyCount >= (Constants.BSTAR_ORDER * 2) - 1;
    }
    
    /**
     * Verifica se o nó pode emprestar para um irmão
     */
    public boolean canLend() {
        return keyCount > Constants.BSTAR_ORDER;
    }
    
    /**
     * Insere uma entrada no nó (mantendo ordem)
     */
    public boolean insertEntry(NodeMetadata entry) {
        int pos = findInsertPosition(entry.getID());
        if (pos < keyCount && entries.get(pos).getID() == entry.getID()) {
            // Atualiza entrada existente
            entries.set(pos, entry);
            isDirty = true;
            return false; // Não foi inserção nova
        }
        entries.add(pos, entry);
        keyCount++;
        isDirty = true;
        return true;
    }
    
    /**
     * Encontra posição para inserção usando busca binária
     */
    private int findInsertPosition(int id) {
        int low = 0, high = keyCount;
        while (low < high) {
            int mid = (low + high) >>> 1;
            if (entries.get(mid).getID() < id) {
                low = mid + 1;
            } else {
                high = mid;
            }
        }
        return low;
    }
    
    /**
     * Remove uma entrada pelo ID
     */
    public boolean removeEntry(int id) {
        int pos = findEntryPosition(id);
        if (pos >= 0 && pos < keyCount) {
            entries.remove(pos);
            keyCount--;
            isDirty = true;
            return true;
        }
        return false;
    }
    
    /**
     * Busca posição de uma entrada existente
     */
    private int findEntryPosition(int id) {
        int low = 0, high = keyCount - 1;
        while (low <= high) {
            int mid = (low + high) >>> 1;
            int midId = entries.get(mid).getID();
            if (midId == id) return mid;
            if (midId < id) low = mid + 1;
            else high = mid - 1;
        }
        return -1;
    }
    
    /**
     * Serializa o nó para bytes (formato de página)
     */
    public byte[] serialize() throws IOException {
        byte[] page = new byte[Constants.PAGE_SIZE];
        int offset = Constants.DATA_OFFSET;
        
        // Cabeçalho do nó (20 bytes)
        page[offset++] = (byte) (type == NodeType.LEAF ? 1 : 2);  // Tipo
        page[offset++] = (byte) ((parentPageId >> 24) & 0xFF);    // Parent
        page[offset++] = (byte) ((parentPageId >> 16) & 0xFF);
        page[offset++] = (byte) ((parentPageId >> 8) & 0xFF);
        page[offset++] = (byte) (parentPageId & 0xFF);
        page[offset++] = (byte) ((keyCount >> 24) & 0xFF);        // Key count
        page[offset++] = (byte) ((keyCount >> 16) & 0xFF);
        page[offset++] = (byte) ((keyCount >> 8) & 0xFF);
        page[offset++] = (byte) (keyCount & 0xFF);
        
        // Reservar espaço para ponteiros de filhos (se interno)
        if (type == NodeType.INTERNAL) {
            offset += children.size() * Long.BYTES;
        }
        
        // Serializar entradas
        for (NodeMetadata entry : entries) {
            byte[] entryBytes = entry.toBytes();
            System.arraycopy(entryBytes, 0, page, offset, entryBytes.length);
            offset += entryBytes.length;
        }
        
        // Serializar ponteiros de filhos (se interno)
        if (type == NodeType.INTERNAL) {
            int ptrOffset = Constants.DATA_OFFSET + 20; // Após cabeçalho
            for (Long childPage : children) {
                long pageId = childPage != null ? childPage : -1L;
                page[ptrOffset++] = (byte) ((pageId >> 56) & 0xFF);
                page[ptrOffset++] = (byte) ((pageId >> 48) & 0xFF);
                page[ptrOffset++] = (byte) ((pageId >> 40) & 0xFF);
                page[ptrOffset++] = (byte) ((pageId >> 32) & 0xFF);
                page[ptrOffset++] = (byte) ((pageId >> 24) & 0xFF);
                page[ptrOffset++] = (byte) ((pageId >> 16) & 0xFF);
                page[ptrOffset++] = (byte) ((pageId >> 8) & 0xFF);
                page[ptrOffset++] = (byte) (pageId & 0xFF);
            }
        }
        
        return page;
    }
    
    /**
     * Desserializa página para nó
     */
    public static Node deserialize(byte[] page, long pageId) {
        int offset = Constants.DATA_OFFSET;
        
        // Ler cabeçalho
        int typeByte = page[offset++] & 0xFF;
        NodeType type = (typeByte == 1) ? NodeType.LEAF : NodeType.INTERNAL;
        
        int parentPageId = ((page[offset++] & 0xFF) << 24) |
                          ((page[offset++] & 0xFF) << 16) |
                          ((page[offset++] & 0xFF) << 8) |
                          (page[offset++] & 0xFF);
        
        int keyCount = ((page[offset++] & 0xFF) << 24) |
                      ((page[offset++] & 0xFF) << 16) |
                      ((page[offset++] & 0xFF) << 8) |
                      (page[offset++] & 0xFF);
        
        Node node = new Node(pageId, type);
        node.parentPageId = parentPageId;
        node.keyCount = keyCount;
        
        // Se for nó interno, pular ponteiros temporariamente
        if (type == NodeType.INTERNAL) {
            offset += (keyCount + 1) * Long.BYTES;
        }
        
        // Ler entradas
        for (int i = 0; i < keyCount; i++) {
            NodeMetadata entry = NodeMetadata.fromBytes(page, offset);
            node.entries.add(entry);
            offset += 13; // Tamanho de NodeMetadata
        }
        
        // Se for nó interno, ler ponteiros
        if (type == NodeType.INTERNAL) {
            int ptrOffset = Constants.DATA_OFFSET + 20;
            for (int i = 0; i <= keyCount; i++) {
                long childId = ((long)(page[ptrOffset++] & 0xFF) << 56) |
                              ((long)(page[ptrOffset++] & 0xFF) << 48) |
                              ((long)(page[ptrOffset++] & 0xFF) << 40) |
                              ((long)(page[ptrOffset++] & 0xFF) << 32) |
                              ((page[ptrOffset++] & 0xFF) << 24) |
                              ((page[ptrOffset++] & 0xFF) << 16) |
                              ((page[ptrOffset++] & 0xFF) << 8) |
                              (page[ptrOffset++] & 0xFF);
                node.children.add(childId >= 0 ? childId : null);
            }
        }
        
        return node;
    }
}
