# B*Tree Disk - Implementação Java

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

