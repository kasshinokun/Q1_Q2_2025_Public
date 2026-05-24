package com.bstartree.core;

import com.bstartree.io.DiskIO;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Gerenciador de páginas em disco
 * Implementa cache LRU similar ao SQLite
 */
public class PageManager {
    
    private final DiskIO diskIO;
    private final Map<Long, Node> pageCache;
    private final int cacheSize;
    private long nextPageId;
    
    public PageManager(String filePath, int cacheSize) throws IOException {
        this.diskIO = new DiskIO(filePath);
        this.cacheSize = cacheSize;
        this.pageCache = new LinkedHashMap<Long, Node>(cacheSize, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<Long, Node> eldest) {
                // Escreve página "suja" antes de remover do cache
                if (eldest.getValue().isDirty()) {
                    try {
                        writePage(eldest.getValue());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
                return size() > cacheSize;
            }
        };
        this.nextPageId = 1; // Página 0 é reservada para cabeçalho
        
        // Inicializa arquivo se necessário
        initializeFile();
    }
    
    /**
     * Inicializa o arquivo com cabeçalho similar ao SQLite
     */
    private void initializeFile() throws IOException {
        if (diskIO.getFileLength() == 0) {
            byte[] header = new byte[Constants.FILE_HEADER_SIZE];
            int offset = 0;
            
            // Magic number (8 bytes)
            long magic = Constants.MAGIC_NUMBER;
            for (int i = 7; i >= 0; i--) {
                header[offset++] = (byte) ((magic >> (i * 8)) & 0xFF);
            }
            
            // Versão (4 bytes)
            header[offset++] = (byte) ((Constants.FILE_VERSION >> 24) & 0xFF);
            header[offset++] = (byte) ((Constants.FILE_VERSION >> 16) & 0xFF);
            header[offset++] = (byte) ((Constants.FILE_VERSION >> 8) & 0xFF);
            header[offset++] = (byte) (Constants.FILE_VERSION & 0xFF);
            
            // Tamanho da página (4 bytes)
            header[offset++] = (byte) ((Constants.PAGE_SIZE >> 24) & 0xFF);
            header[offset++] = (byte) ((Constants.PAGE_SIZE >> 16) & 0xFF);
            header[offset++] = (byte) ((Constants.PAGE_SIZE >> 8) & 0xFF);
            header[offset++] = (byte) (Constants.PAGE_SIZE & 0xFF);
            
            // ID da próxima página livre (4 bytes)
            header[offset++] = (byte) ((nextPageId >> 24) & 0xFF);
            header[offset++] = (byte) ((nextPageId >> 16) & 0xFF);
            header[offset++] = (byte) ((nextPageId >> 8) & 0xFF);
            header[offset++] = (byte) (nextPageId & 0xFF);
            
            // ID da página raiz (4 bytes) - inicialmente -1
            header[offset++] = (byte) 0xFF;
            header[offset++] = (byte) 0xFF;
            header[offset++] = (byte) 0xFF;
            header[offset++] = (byte) 0xFF;
            
            diskIO.write(0, header);
            diskIO.sync();
        } else {
            // Ler cabeçalho existente
            byte[] header = diskIO.read(0, Constants.FILE_HEADER_SIZE);
            // Validar magic number...
            nextPageId = readNextPageId(header);
        }
    }
    
    private long readNextPageId(byte[] header) {
        int offset = 16;
        return ((long)(header[offset++] & 0xFF) << 24) |
               ((header[offset++] & 0xFF) << 16) |
               ((header[offset++] & 0xFF) << 8) |
               (header[offset] & 0xFF);
    }
    
    /**
     * Obtém uma página do cache ou disco
     */
    public Node getPage(long pageId) throws IOException {
        if (pageCache.containsKey(pageId)) {
            return pageCache.get(pageId);
        }
        
        byte[] pageData = diskIO.read(pageId * Constants.PAGE_SIZE, Constants.PAGE_SIZE);
        Node node = Node.deserialize(pageData, pageId);
        pageCache.put(pageId, node);
        return node;
    }
    
    /**
     * Cria uma nova página
     */
    public Node createPage(Node.NodeType type) throws IOException {
        long newPageId = nextPageId++;
        Node newNode = new Node(newPageId, type);
        pageCache.put(newPageId, newNode);
        updateHeader();
        return newNode;
    }
    
    /**
     * Escreve uma página no disco
     */
    public void writePage(Node node) throws IOException {
        byte[] pageData = node.serialize();
        diskIO.write(node.getPageId() * Constants.PAGE_SIZE, pageData);
        node.setDirty(false);
    }
    
    /**
     * Atualiza cabeçalho com próxima página livre
     */
    private void updateHeader() throws IOException {
        byte[] header = diskIO.read(0, Constants.FILE_HEADER_SIZE);
        int offset = 16;
        header[offset++] = (byte) ((nextPageId >> 24) & 0xFF);
        header[offset++] = (byte) ((nextPageId >> 16) & 0xFF);
        header[offset++] = (byte) ((nextPageId >> 8) & 0xFF);
        header[offset] = (byte) (nextPageId & 0xFF);
        diskIO.write(0, header);
    }
    
    /**
     * Define a página raiz no cabeçalho
     */
    public void setRootPage(long rootPageId) throws IOException {
        byte[] header = diskIO.read(0, Constants.FILE_HEADER_SIZE);
        int offset = 20;
        header[offset++] = (byte) ((rootPageId >> 24) & 0xFF);
        header[offset++] = (byte) ((rootPageId >> 16) & 0xFF);
        header[offset++] = (byte) ((rootPageId >> 8) & 0xFF);
        header[offset] = (byte) (rootPageId & 0xFF);
        diskIO.write(0, header);
    }
    
    /**
     * Obtém ID da página raiz
     */
    public long getRootPageId() throws IOException {
        byte[] header = diskIO.read(0, Constants.FILE_HEADER_SIZE);
        int offset = 20;
        long rootId = ((long)(header[offset++] & 0xFF) << 24) |
                     ((header[offset++] & 0xFF) << 16) |
                     ((header[offset++] & 0xFF) << 8) |
                     (header[offset] & 0xFF);
        return rootId == 0xFFFFFFFFL ? -1 : rootId;
    }
    
    /**
     * Fecha o gerenciador e sincroniza alterações
     */
    public void close() throws IOException {
        // Escrever todas as páginas sujas
        for (Node node : pageCache.values()) {
            if (node.isDirty()) {
                writePage(node);
            }
        }
        diskIO.sync();
        diskIO.close();
    }
    
    /**
     * Força sincronização em disco
     */
    public void flush() throws IOException {
        for (Node node : pageCache.values()) {
            if (node.isDirty()) {
                writePage(node);
            }
        }
        diskIO.sync();
    }
}
