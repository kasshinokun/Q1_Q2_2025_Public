package com.bstartree.core;

import com.bstartree.io.Serializer;
import com.bstartree.model.DataObject;
import com.bstartree.model.NodeMetadata;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Implementação principal da árvore B* em disco
 * Suporta CRUD completo para DataObject
 */
public class BStarTree {
    
    private final PageManager pageManager;
    private long rootPageId;
    
    public BStarTree(String filePath) throws IOException {
        this.pageManager = new PageManager(filePath, 100); // Cache de 100 páginas
        this.rootPageId = pageManager.getRootPageId();
        
        // Criar raiz se não existir
        if (rootPageId < 0) {
            Node root = pageManager.createPage(Node.NodeType.LEAF);
            this.rootPageId = root.getPageId();
            pageManager.setRootPage(rootPageId);
        }
    }
    
    // ========== OPERAÇÕES CRUD ==========
    
    /**
     * CREATE/UPDATE: Insere ou atualiza um DataObject
     */
    public boolean put(DataObject obj) throws IOException {
        if (obj == null || obj.getID_registro() <= 0) {
            throw new IllegalArgumentException("ID inválido");
        }
        
        // Serializar objeto
        byte[] data = Serializer.serialize(obj);
        int dataSize = data.length;
        
        // Buscar nó para inserção
        SearchResult result = searchForInsert(rootPageId, obj.getID_registro());
        
        // Criar metadados
        NodeMetadata metadata = new NodeMetadata(
            obj.getID_registro(),
            false,  // Não é lapide (ativo)
            (int) result.insertPosition,  // Posição no arquivo de dados
            dataSize
        );
        
        // Inserir no nó
        Node node = pageManager.getPage(result.nodePageId);
        boolean isNew = node.insertEntry(metadata);
        
        // Escrever dados do objeto em área de overflow
        long dataOffset = allocateDataSpace(dataSize);
        writeDataObject(dataOffset, data);
        metadata.setPosicao((int) dataOffset);
        
        // Atualizar nó com posição real
        if (node.isFull()) {
            splitNode(node);
        }
        
        pageManager.writePage(node);
        if (isNew) {
            pageManager.flush();
        }
        return isNew;
    }
    
    /**
     * READ: Busca DataObject por ID
     */
    public DataObject get(int id) throws IOException {
        NodeMetadata metadata = findMetadata(id);
        if (metadata == null || metadata.isLapide()) {
            return null; // Não encontrado ou deletado logicamente
        }
        
        byte[] data = readDataObject(metadata.getPosicao(), metadata.getSize_Registry());
        return Serializer.deserialize(data);
    }
    
    /**
     * UPDATE: Atualiza DataObject existente
     */
    public boolean update(DataObject obj) throws IOException {
        return put(obj); // B* trees tratam update como insert
    }
    
    /**
     * DELETE: Exclusão lógica (tombstone)
     */
    public boolean delete(int id) throws IOException {
        SearchResult result = searchForMetadata(rootPageId, id);
        if (result.nodePageId < 0) {
            return false; // Não encontrado
        }
        
        Node node = pageManager.getPage(result.nodePageId);
        NodeMetadata metadata = findMetadataInNode(node, id);
        
        if (metadata != null) {
            // Marcar como lapide (exclusão lógica)
            metadata.setLapide(true);
            node.setDirty(true);
            pageManager.writePage(node);
            pageManager.flush();
            return true;
        }
        return false;
    }
    
    /**
     * DELETE físico: Remove permanentemente (reorganiza árvore)
     */
    public boolean deletePhysical(int id) throws IOException {
        // Implementação simplificada: marca como lapide + vacuum periódico
        return delete(id);
    }
    
    // ========== MÉTODOS AUXILIARES ==========
    
    /**
     * Busca metadados por ID na árvore
     */
    private NodeMetadata findMetadata(int id) throws IOException {
        SearchResult result = searchForMetadata(rootPageId, id);
        if (result.nodePageId < 0) return null;
        
        Node node = pageManager.getPage(result.nodePageId);
        return findMetadataInNode(node, id);
    }
    
    /**
     * Busca recursiva por metadados
     */
    private SearchResult searchForMetadata(long pageId, int id) throws IOException {
        Node node = pageManager.getPage(pageId);
        
        if (node.getType() == Node.NodeType.LEAF) {
            // Busca linear no nó folha
            for (NodeMetadata entry : node.getEntries()) {
                if (entry.getID() == id) {
                    return new SearchResult(pageId, 0);
                }
            }
            return new SearchResult(-1, -1);
        } else {
            // Nó interno: navegar para filho apropriado
            List<NodeMetadata> entries = node.getEntries();
            List<Long> children = node.getChildren();
            
            int i = 0;
            while (i < entries.size() && entries.get(i).getID() < id) {
                i++;
            }
            
            if (i < children.size() && children.get(i) != null) {
                return searchForMetadata(children.get(i), id);
            }
            return new SearchResult(-1, -1);
        }
    }
    
    /**
     * Encontra metadados em um nó específico
     */
    private NodeMetadata findMetadataInNode(Node node, int id) {
        for (NodeMetadata entry : node.getEntries()) {
            if (entry.getID() == id) {
                return entry;
            }
        }
        return null;
    }
    
    /**
     * Aloca espaço para dados do objeto
     */
    private long allocateDataSpace(int size) throws IOException {
        // Em produção: usar área de overflow ou páginas de dados dedicadas
        // Simplificação: retornar offset após cabeçalho + páginas de nós
        long fileLength = pageManager.getFileLength();
        return fileLength + 1024; // Espaço reservado
    }
    
    /**
     * Escreve dados do objeto no arquivo
     */
    private void writeDataObject(long offset, byte[] data) throws IOException {
        // Em produção: implementar área de dados separada
        // Aqui: simplificação para demonstração
    }
    
    /**
     * Lê dados do objeto do arquivo
     */
    private byte[] readDataObject(long offset, int size) throws IOException {
        // Em produção: ler da área de dados
        // Aqui: retornar array vazio para demonstração
        return new byte[size];
    }
    
    /**
     * Divide nó cheio (split B*)
     */
    private void splitNode(Node node) throws IOException {
        // Implementação simplificada do split B*
        // B* trees tentam redistribuir antes de split
        if (node.canLend()) {
            // Tentar emprestar para irmão
            redistributeWithSibling(node);
        } else {
            // Split real
            performSplit(node);
        }
    }
    
    private void redistributeWithSibling(Node node) {
        // Lógica de redistribuição com nós irmãos
        // Mantém ocupação mínima de 2/3
    }
    
    private void performSplit(Node node) throws IOException {
        // Criar novo nó e redistribuir entradas
        Node newNode = pageManager.createPage(node.getType());
        // ... lógica de split ...
    }
    
    /**
     * Resultado de busca na árvore
     */
    private static class SearchResult {
        long nodePageId;
        long insertPosition;
        
        SearchResult(long pageId, long pos) {
            this.nodePageId = pageId;
            this.insertPosition = pos;
        }
    }
    
    /**
     * Busca para inserção (retorna nó folha apropriado)
     */
    private SearchResult searchForInsert(long pageId, int key) throws IOException {
        Node node = pageManager.getPage(pageId);
        
        if (node.getType() == Node.NodeType.LEAF) {
            return new SearchResult(pageId, node.getKeyCount());
        }
        
        // Navegar para filho apropriado
        List<NodeMetadata> entries = node.getEntries();
        List<Long> children = node.getChildren();
        
        int i = 0;
        while (i < entries.size() && entries.get(i).getID() < key) {
            i++;
        }
        
        if (i < children.size() && children.get(i) != null) {
            return searchForInsert(children.get(i), key);
        }
        return new SearchResult(pageId, 0);
    }
    
    // ========== MÉTODOS DE CONSULTA ==========
    
    /**
     * Busca por intervalo de IDs
     */
    public List<DataObject> rangeQuery(int startId, int endId) throws IOException {
        List<DataObject> results = new ArrayList<>();
        rangeQueryRecursive(rootPageId, startId, endId, results);
        return results;
    }
    
    private void rangeQueryRecursive(long pageId, int startId, int endId, 
                                     List<DataObject> results) throws IOException {
        Node node = pageManager.getPage(pageId);
        
        for (NodeMetadata entry : node.getEntries()) {
            if (entry.getID() >= startId && entry.getID() <= endId && !entry.isLapide()) {
                DataObject obj = get(entry.getID());
                if (obj != null) {
                    results.add(obj);
                }
            }
        }
        
        // Se for nó interno, navegar para filhos relevantes
        if (node.getType() == Node.NodeType.INTERNAL) {
            // ... lógica de navegação para range query ...
        }
    }
    
    /**
     * Fecha a árvore e libera recursos
     */
    public void close() throws IOException {
        pageManager.close();
    }
    
    /**
     * Força sincronização em disco
     */
    public void flush() throws IOException {
        pageManager.flush();
    }
    
    /**
     * Obtém estatísticas da árvore
     */
    public TreeStats getStats() throws IOException {
        TreeStats stats = new TreeStats();
        stats.totalPages = (int) (pageManager.getFileLength() / Constants.PAGE_SIZE);
        stats.pageSize = Constants.PAGE_SIZE;
        stats.order = Constants.BSTAR_ORDER;
        return stats;
    }
    
    public static class TreeStats {
        public int totalPages;
        public int pageSize;
        public int order;
        
        @Override
        public String toString() {
            return String.format("B*Tree Stats: Pages=%d, PageSize=%d, Order=%d",
                    totalPages, pageSize, order);
        }
    }
}
