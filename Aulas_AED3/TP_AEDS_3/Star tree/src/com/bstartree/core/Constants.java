package com.bstartree.core;

/**
 * Constantes para a árvore B* em disco
 * Inspirado no formato de páginas do SQLite3
 */
public final class Constants {
    
    // Tamanho da página em bytes (padrão SQLite: 4096)
    public static final int PAGE_SIZE = 4096;
    
    // Tamanho do cabeçalho da página (similar ao SQLite)
    public static final int PAGE_HEADER_SIZE = 100;
    
    // Offset para dados úteis na página
    public static final int DATA_OFFSET = PAGE_HEADER_SIZE;
    
    // Espaço útil por página
    public static final int USABLE_SPACE = PAGE_SIZE - PAGE_HEADER_SIZE;
    
    // Ordem da árvore B* (fator de ramificação)
    public static final int BSTAR_ORDER = 16;
    
    // Tamanho máximo de uma chave (ID)
    public static final int KEY_SIZE = Integer.BYTES;
    
    // Magic number para validação do arquivo (similar ao SQLite)
    public static final long MAGIC_NUMBER = 0x4253545244415441L; // "BSTRDATA"
    
    // Versão do formato do arquivo
    public static final int FILE_VERSION = 1;
    
    // Offset do cabeçalho do arquivo
    public static final int FILE_HEADER_SIZE = 100;
    
    private Constants() {
        // Classe utilitária
    }
}
