# B*Tree Disk - Implementação Java

- Protótipo construído com código original e otimização com Qwen 3.6 Plus em 24-05-2026

Árvore B* persistida em disco usando bibliotecas nativas do Java, com arquitetura similar ao SQLite3.

## 📋 Características

- ✅ Armazenamento em disco com páginas de 4096 bytes
- ✅ Cache LRU para otimização de I/O
- ✅ Operações CRUD completas para `DataObject`
- ✅ Cada nó contém: `ID (int)`, `Lapide (boolean)`, `Posicao (int)`, `Size_Registry (int)`
- ✅ Serialização binária compacta (similar ao record format do SQLite)
- ✅ Exclusão lógica com tombstone (flag Lapide)
- ✅ Suporte a consultas por intervalo (range queries)
- ✅ Sincronização em disco (fsync) para durabilidade

## 🗂️ Estrutura do Arquivo

```
arquivo.bst
├── [0-99]      Cabeçalho do arquivo (100 bytes)
│   ├── Magic Number (8 bytes)
│   ├── Versão (4 bytes)
│   ├── Page Size (4 bytes)
│   ├── Next Page ID (4 bytes)
│   └── Root Page ID (4 bytes)
│
├── [100+]      Páginas de nós B*
│   ├── Cabeçalho da página (100 bytes)
│   ├── Metadados do nó (tipo, parent, key count)
│   ├── Entradas (NodeMetadata x N)
│   └── Ponteiros para filhos (nós internos)
│
└── [EOF+]      Área de dados (overflow para objetos grandes)
```

## 🚀 Uso Básico

```java
import com.bstartree.core.BStarTree;
import com.bstartree.model.DataObject;

public class Main {
    public static void main(String[] args) throws Exception {
        // Inicializar árvore
        BStarTree tree = new BStarTree("accidents.bst");
        
        // CREATE
        DataObject obj = new DataObject();
        obj.setID_registro(1001);
        obj.setCrash_date("15/03/2024 14:30:00 PM");
        obj.setWeather_condition("Rain");
        obj.setInjuries_total(2.0f);
        // ... preencher demais campos ...
        
        tree.put(obj);  // Insert or Update
        
        // READ
        DataObject found = tree.get(1001);
        System.out.println("Encontrado: " + found);
        
        // UPDATE
        found.setWeather_condition("Clear");
        tree.update(found);
        
        // DELETE (lógico - mantém dados com flag Lapide=true)
        tree.delete(1001);
        
        // Range Query
        List results = tree.rangeQuery(1000, 2000);
        
        // Fechar (sincroniza em disco)
        tree.close();
    }
}
```

## ⚙️ Configurações Avançadas

```java
// Ajustar tamanho do cache (padrão: 100 páginas)
PageManager pm = new PageManager("dados.bst", 500);

// Forçar sincronização manual
tree.flush();  // Equivalente ao sqlite3_wal_checkpoint()

// Obter estatísticas
BStarTree.TreeStats stats = tree.getStats();
System.out.println(stats);
// Output: B*Tree Stats: Pages=150, PageSize=4096, Order=16
```

## 📦 Empacotamento

Execute o script para gerar o arquivo ZIP:

```bash
chmod +x package.sh
./package.sh
```

O arquivo `BStarTreeDisk-1.0.0.zip` conterá:
```
📦 BStarTreeDisk-1.0.0.zip
 ┣ 📂 src/                    # Código fonte Java
 ┃ ┗ 📂 com/bstartree/
 ┃   ┣ 📂 core/              # BStarTree, PageManager, Node
 ┃   ┣ 📂 model/             # DataObject, NodeMetadata
 ┃   ┣ 📂 io/                # Serializer, DiskIO
 ┃   ┗ 📂 util/              # Utilitários
 ┣ 📂 build/classes/         # Classes compiladas
 ┣ 📂 build/lib/             # JAR opcional
 ┣ 📄 README.md              # Este arquivo
 ┗ 📄 package.sh             # Script de build
```

## 🔧 Dependências

- Java 8 ou superior
- Nenhuma biblioteca externa (apenas JDK nativo)

## 📚 Referências

- Formato de arquivo inspirado no [SQLite File Format](https://sqlite.org/fileformat.html)
- Algoritmo B* baseado em: Bayer, R. & Unterauer, K. (1977). "Prefix B-trees"
- Padrão de serialização similar ao [SQLite Record Format](https://sqlite.org/fileformat2.html#record_format)

## ⚠️ Limitações

1. Esta é uma implementação educacional - para produção, considere usar SQLite JDBC ou bancos embutidos maduros
2. Área de overflow para dados grandes é simplificada na demonstração
3. Recuperação de crash (WAL/rollback journal) não implementada
4. Transações ACID completas requerem extensão adicional

## 🤝 Contribuições

Sinta-se à vontade para:
- Reportar bugs via issues
- Sugerir melhorias (ex: compressão, criptografia)
- Implementar recursos faltantes (WAL, vacuum, etc.)

---
*Implementação educacional - 2026*
```

---

## 📦 Como Gerar o ZIP

1. **Salve todos os arquivos** na estrutura de diretórios indicada
2. **Torne o script executável**:
   ```bash
   chmod +x package.sh
   ```
3. **Execute o empacotamento**:
   ```bash
   ./package.sh
   ```
4. **Resultado**: Arquivo `BStarTreeDisk-1.0.0.zip` pronto para distribuição

---

## 🔑 Pontos-Chave da Implementação

| Componente | Função | Similaridade SQLite |
|-----------|--------|-------------------|
| `PageManager` | Gerencia páginas de 4KB com cache LRU | Pager do SQLite |
| `DiskIO` | Abstração de RandomAccessFile com sync() | VFS do SQLite |
| `Node` | Estrutura de nó B* serializável | B-tree page do btree.c |
| `Serializer` | Serialização binária compacta | Record format do SQLite |
| `Lapide` | Exclusão lógica (tombstone) | Similar a DELETE com flag |
| `Posicao` | Offset do dado no arquivo | Similar a rowid/payload pointer |

> **Nota**: Esta implementação foca nos conceitos fundamentais. Para uso em produção, recomendo utilizar o [SQLite JDBC](## 🚀 Uso Básico

```java
import com.bstartree.core.BStarTree;
import com.bstartree.model.DataObject;

public class Main {
    public static void main(String[] args) throws Exception {
        // Inicializar árvore
        BStarTree tree = new BStarTree("accidents.bst");
        
        // CREATE
        DataObject obj = new DataObject();
        obj.setID_registro(1001);
        obj.setCrash_date("15/03/2024 14:30:00 PM");
        obj.setWeather_condition("Rain");
        obj.setInjuries_total(2.0f);
        // ... preencher demais campos ...
        
        tree.put(obj);  // Insert or Update
        
        // READ
        DataObject found = tree.get(1001);
        System.out.println("Encontrado: " + found);
        
        // UPDATE
        found.setWeather_condition("Clear");
        tree.update(found);
        
        // DELETE (lógico - mantém dados com flag Lapide=true)
        tree.delete(1001);
        
        // Range Query
        List results = tree.rangeQuery(1000, 2000);
        
        // Fechar (sincroniza em disco)
        tree.close();
    }
}
```

## ⚙️ Configurações Avançadas

```java
// Ajustar tamanho do cache (padrão: 100 páginas)
PageManager pm = new PageManager("dados.bst", 500);

// Forçar sincronização manual
tree.flush();  // Equivalente ao sqlite3_wal_checkpoint()

// Obter estatísticas
BStarTree.TreeStats stats = tree.getStats();
System.out.println(stats);
// Output: B*Tree Stats: Pages=150, PageSize=4096, Order=16
```

## 📦 Empacotamento

Execute o script para gerar o arquivo ZIP:

```bash
chmod +x package.sh
./package.sh
```

O arquivo `BStarTreeDisk-1.0.0.zip` conterá:
```
📦 BStarTreeDisk-1.0.0.zip
 ┣ 📂 src/                    # Código fonte Java
 ┃ ┗ 📂 com/bstartree/
 ┃   ┣ 📂 core/              # BStarTree, PageManager, Node
 ┃   ┣ 📂 model/             # DataObject, NodeMetadata
 ┃   ┣ 📂 io/                # Serializer, DiskIO
 ┃   ┗ 📂 util/              # Utilitários
 ┣ 📂 build/classes/         # Classes compiladas
 ┣ 📂 build/lib/             # JAR opcional
 ┣ 📄 README.md              # Este arquivo
 ┗ 📄 package.sh             # Script de build
```

## 🔧 Dependências

- Java 8 ou superior
- Nenhuma biblioteca externa (apenas JDK nativo)

## 📚 Referências

- Formato de arquivo inspirado no [SQLite File Format](https://sqlite.org/fileformat.html)
- Algoritmo B* baseado em: Bayer, R. & Unterauer, K. (1977). "Prefix B-trees"
- Padrão de serialização similar ao [SQLite Record Format](https://sqlite.org/fileformat2.html#record_format)

## ⚠️ Limitações

1. Esta é uma implementação educacional - para produção, considere usar SQLite JDBC ou bancos embutidos maduros
2. Área de overflow para dados grandes é simplificada na demonstração
3. Recuperação de crash (WAL/rollback journal) não implementada
4. Transações ACID completas requerem extensão adicional

## 🤝 Contribuições

Sinta-se à vontade para:
- Reportar bugs via issues
- Sugerir melhorias (ex: compressão, criptografia)
- Implementar recursos faltantes (WAL, vacuum, etc.)

---
*Implementação educacional - 2026*
```

---

## 📦 Como Gerar o ZIP

1. **Salve todos os arquivos** na estrutura de diretórios indicada
2. **Torne o script executável**:
   ```bash
   chmod +x package.sh
   ```
3. **Execute o empacotamento**:
   ```bash
   ./package.sh
   ```
4. **Resultado**: Arquivo `BStarTreeDisk-1.0.0.zip` pronto para distribuição

---

## 🔑 Pontos-Chave da Implementação

| Componente | Função | Similaridade SQLite |
|-----------|--------|-------------------|
| `PageManager` | Gerencia páginas de 4KB com cache LRU | Pager do SQLite |
| `DiskIO` | Abstração de RandomAccessFile com sync() | VFS do SQLite |
| `Node` | Estrutura de nó B* serializável | B-tree page do btree.c |
| `Serializer` | Serialização binária compacta | Record format do SQLite |
| `Lapide` | Exclusão lógica (tombstone) | Similar a DELETE com flag |
| `Posicao` | Offset do dado no arquivo | Similar a rowid/payload pointer |

> **Nota**: Esta implementação foca nos conceitos fundamentais. Para uso em produção, recomendo utilizar o [SQLite JDBC](https://github.com/xerial/sqlite-jdbc) ou bibliotecas como [MapDB](https://mapdb.org/) que oferecem recursos avançados de implementação de persistência.








