#!/bin/bash
# package.sh - Script para compilar e empacotar o projeto B*Tree Disk

set -e

PROJECT_NAME="BStarTreeDisk"
VERSION="1.0.0"
OUTPUT_ZIP="${PROJECT_NAME}-${VERSION}.zip"

echo "=== Compilando ${PROJECT_NAME} ==="

# Criar diretórios de saída
mkdir -p build/classes
mkdir -p build/lib

# Compilar todas as classes Java
find src -name "*.java" > sources.txt
javac -d build/classes -sourcepath src @sources.txt

# Criar manifest para JAR (opcional)
cat > build/manifest.mf << EOF
Manifest-Version: 1.0
Main-Class: com.bstartree.core.BStarTree
Created-By: B*Tree Disk Implementation
EOF

# Criar JAR com as classes (opcional)
cd build/classes
jar cfm ../lib/${PROJECT_NAME}.jar ../manifest.mf .
cd ../..

# Copiar arquivos de configuração e documentação
cp README.md build/
cp -r src build/src

# Criar arquivo ZIP final
echo "=== Criando arquivo ${OUTPUT_ZIP} ==="
cd build
zip -r ../${OUTPUT_ZIP} . -x "*.git*" -x "*.log"
cd ..

# Limpar arquivos temporários
rm -f sources.txt

echo "=== Build concluído com sucesso! ==="
echo "Arquivo gerado: ${OUTPUT_ZIP}"
echo ""
echo "Estrutura do ZIP:"
unzip -l ${OUTPUT_ZIP} | head -20

# Instruções de uso
cat << 'USAGE'

=== INSTRUÇÕES DE USO ===

1. Extraia o arquivo ZIP:
   unzip BStarTreeDisk-1.0.0.zip

2. Compile (se necessário):
   javac -cp "build/classes:." -d out src/com/bstartree/**/*.java

3. Exemplo de uso:

   import com.bstartree.core.BStarTree;
   import com.bstartree.model.DataObject;
   
   public class Exemplo {
       public static void main(String[] args) throws Exception {
           // Criar/abrir árvore
           BStarTree tree = new BStarTree("dados.bst");
           
           // Criar objeto
           DataObject obj = new DataObject();
           obj.setID_registro(1);
           obj.setCrash_date("01/01/2024 10:30:00 AM");
           obj.setWeather_condition("Clear");
           // ... preencher outros campos ...
           
           // CRUD
           tree.put(obj);           // CREATE/UPDATE
           DataObject result = tree.get(1);  // READ
           tree.delete(1);          // DELETE lógico
           
           tree.close();
       }
   }

4. Características:
   - Armazenamento em disco com páginas de 4KB (similar SQLite)
   - Cache LRU para performance
   - Exclusão lógica com flag "Lapide"
   - Serialização binária compacta
   - Suporte a range queries

USAGE
