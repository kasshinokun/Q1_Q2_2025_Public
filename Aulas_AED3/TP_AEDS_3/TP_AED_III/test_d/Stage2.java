package test_d;

import java.io.IOException;
import java.io.RandomAccessFile;

import test_d.OptimizedBTree.BTreeNode;

public class Stage2 {
	
	static int DEGREETREE = 16; // Grau mínimo (define o intervalo para o número de chaves)
	public static class BTreeNode {
       
		// Variáveis ​​Declaradas
		int[] keys; // Array para armazenar chaves
		long[] values; // Array para armazenar valores

		static int DEGREE = 16; // Grau mínimo (define o intervalo para o número de chaves)

		long[] children; // Array para armazenar ponteiros para filhos
		int numKeys; // Número atual de chaves
		boolean isLeaf; // Verdadeiro quando o nó é folha, senão Falso

		static int MAX_KEYS = 2 * DEGREE - 1;
		static int MAX_CHILDREN = 2 * DEGREE;

		long pos; // Posição do nó no arquivo
        
        public BTreeNode() {
        	this.isLeaf = true;
        	this.keys = new int[MAX_KEYS];
        	this.values = new long[MAX_KEYS];
        	this.children = new long[MAX_CHILDREN];
            
            numKeys = 0;
            
            this.pos=8;
        }
        
        public BTreeNode(int t, boolean leaf,long pos) {
            this.DEGREE = t;
            
            this.MAX_KEYS = 2 * DEGREE - 1;
            this.MAX_CHILDREN = 2 * DEGREE;
            
            this.isLeaf = leaf;

            this.keys = new int[MAX_KEYS];
            this.values = new long[MAX_KEYS];
            this.children = new long[MAX_CHILDREN];
            
            numKeys = 0;
            
            this.pos=pos;
        }
     
        void read(RandomAccessFile file, long pos) throws IOException {
            this.pos = pos;
            
            if(pos<=(file.length()-getNodeSize())){
	            file.seek(pos);
	            
	            isLeaf = file.readBoolean();
	            numKeys = file.readInt();
	            for (int i = 0; i < MAX_KEYS; i++) {
	                keys[i] = file.readInt();
	                values[i] = file.readLong();
	            }
	            for (int i = 0; i < MAX_CHILDREN; i++) {
	                children[i] = file.readLong();
	            }
            }else {
            	this.DEGREE = this.DEGREE;
                
                this.MAX_KEYS = 2 * DEGREE - 1;
                this.MAX_CHILDREN = 2 * DEGREE;
                
                this.isLeaf = true;

                this.keys = new int[MAX_KEYS];
                this.values = new long[MAX_KEYS];
                this.children = new long[MAX_CHILDREN];
                
                numKeys = 0;
                
                long nodeSize = getNodeSize();
                long alignedPos = (pos % nodeSize == 0) ? pos : ((pos / nodeSize + 1) * nodeSize); //
                file.seek(alignedPos);
                file.write(new byte[(int) nodeSize]); // Reserva espaço (importante para alinhamento)
                
                pos=alignedPos;
                
                this.pos = pos;
            }
        }
        static int getNodeSize() {
            return 1 + 4 + MAX_KEYS * (4 + 8) + MAX_CHILDREN * 8;
        }
        void write(RandomAccessFile file) throws IOException {
            if (pos == -1) {
                pos = file.length();
            }
            file.seek(pos);
            file.writeBoolean(isLeaf);
            file.writeInt(numKeys);
            for (int i = 0; i < MAX_KEYS; i++) {
                file.writeInt(keys[i]);
                file.writeLong(values[i]);
            }
            for (int i = 0; i < MAX_CHILDREN; i++) {
                file.writeLong(children[i]);
            }
        }
        void printNode() { // Para depuração e analise
            System.out.print("Node(Leaf=" + this.isLeaf + ", n=" + this.numKeys + ", keys=[");
            for (int i = 0; i < numKeys; i++) {
                System.out.print(this.keys[i] + ":" + this.values[i] + " ");
            }
            System.out.print("],\nchildren=[");
            for (int i = 0; i < this.numKeys + 1; i++) {
                System.out.print(children[i] + " ");
            }
            System.out.println("])");
        }
	}
	public class BTree {
        private String filename;
        private long rootPos;

        BTree(String filename) throws IOException {
            this.filename = filename;
            try (RandomAccessFile file = new RandomAccessFile(filename, "rw")) {
                if (file.length() == 0) {
                    // Cria uma B-Tree
                    BTreeNode root = new BTreeNode();
                    root.isLeaf = true;
                    root.numKeys = 0;
                    rootPos = allocateNode(file);
                    root.pos = rootPos;
                    root.write(file);
                    writeRootPointer(file, rootPos);

                } else {
                    // carrega a B-Tree existente
                    rootPos = readRootPointer(file);
                }
            }
        }

        private long readRootPointer(RandomAccessFile file) throws IOException {
            file.seek(0);
            return file.readLong();
        }

        private void writeRootPointer(RandomAccessFile file, long rootPos) throws IOException {
            file.seek(0);
            file.writeLong(rootPos);
        }

        private long allocateNode(RandomAccessFile file) throws IOException {
            long pos = file.length();
            long nodeSize = BTreeNode.getNodeSize();
            long alignedPos = (pos % nodeSize == 0) ? pos : (pos / nodeSize + 1) * nodeSize; //
            file.seek(alignedPos);
            file.write(new byte[(int) nodeSize]); // Reserva espaço (importante para alinhamento)
            return alignedPos;
        }

        public Long search(int key) throws IOException {
            try (RandomAccessFile file = new RandomAccessFile(filename, "r")) {
                return searchRecursive(file, rootPos, key);
            }
        }

        private Long searchRecursive(RandomAccessFile file, long nodePos, int key) throws IOException {
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);

            int i = 0;
            while (i < node.numKeys && key > node.keys[i]) {
                i++;
            }
            if (i < node.numKeys && key == node.keys[i]) {
                return node.values[i];
            } else if (node.isLeaf) {
                return null;
            } else {
                return searchRecursive(file, node.children[i], key);
            }
        }

        public void insert(int key, long value) throws IOException {
            try (RandomAccessFile file = new RandomAccessFile(filename, "rw")) {
                if (rootPos == 0) { // caso especial: B-tree vazia 
                    
                	BTreeNode root = new BTreeNode();
                    root.isLeaf = true;
                    root.keys[0] = key;
                    root.values[0] = value;
                    root.numKeys = 1;
                    rootPos = allocateNode(file);
                    root.pos = rootPos;
                    root.write(file);
                    writeRootPointer(file, rootPos);
                    return;
                }

                BTreeNode root = new BTreeNode();
                root.read(file, rootPos);

                if (root.numKeys == root.MAX_KEYS) {
                    BTreeNode newRoot = new BTreeNode();
                    newRoot.isLeaf = false;
                    newRoot.numKeys = 0;
                    newRoot.children[0] = rootPos;

                    long newRootPos = allocateNode(file);
                    newRoot.pos = newRootPos;
                    splitChild(file, newRoot, 0);

                    rootPos = newRootPos;
                    insertNonFull(file, newRoot, key, value, newRootPos);
                    writeRootPointer(file, rootPos);

                } else {
                    insertNonFull(file, root, key, value, rootPos);
                }
            }
        }

        private void insertNonFull(RandomAccessFile file, BTreeNode node, int key, long value, long nodePos) throws IOException {
            int i = node.numKeys - 1;
            if (node.isLeaf) {
                while (i >= 0 && key < node.keys[i]) {
                    node.keys[i + 1] = node.keys[i];
                    node.values[i + 1] = node.values[i];
                    i--;
                }
                node.keys[i + 1] = key;
                node.values[i + 1] = value;
                node.numKeys++;
                node.write(file);

            } else {
                while (i >= 0 && key < node.keys[i]) {
                    i--;
                }
                i++;
                
                BTreeNode child = new BTreeNode();
                child.read(file, node.children[i]);
                if (child.numKeys == child.MAX_KEYS) {
                    splitChild(file, node, i);
                    node.read(file,nodePos); // Re-leitura node apos split (importante!)
                    if (key > node.keys[i]) {
                        i++;
                    }
                }
                insertNonFull(file, child, key, value, node.children[i]);
            }
        }

        private void splitChild(RandomAccessFile file, BTreeNode parent, int index) throws IOException {
            BTreeNode fullChild = new BTreeNode();
            fullChild.read(file, parent.children[index]);

            BTreeNode newChild = new BTreeNode();
            newChild.isLeaf = fullChild.isLeaf;
            newChild.numKeys = DEGREETREE - 1;

            long newChildPos = allocateNode(file);
            newChild.pos = newChildPos;

            for (int j = 0; j < DEGREETREE - 1; j++) {
                newChild.keys[j] = fullChild.keys[j + DEGREETREE];
                newChild.values[j] = fullChild.values[j + DEGREETREE];
            }

            if (!fullChild.isLeaf) {
                for (int j = 0; j < DEGREETREE; j++) {
                    newChild.children[j] = fullChild.children[j + DEGREETREE];
                }
            }

            fullChild.numKeys = DEGREETREE - 1;

            for (int j = parent.numKeys; j >= index + 1; j--) {
                parent.children[j + 1] = parent.children[j];
            }
            parent.children[index + 1] = newChildPos;

            for (int j = parent.numKeys - 1; j >= index; j--) {
                parent.keys[j + 1] = parent.keys[j];
                parent.values[j + 1] = parent.values[j];
            }

            parent.keys[index] = fullChild.keys[DEGREETREE - 1];
            parent.values[index] = fullChild.values[DEGREETREE - 1];
            parent.numKeys++;

            fullChild.write(file);
            newChild.write(file);
            parent.write(file);
        }

        public boolean update(int key, long newValue) throws IOException {
            try (RandomAccessFile file = new RandomAccessFile(filename, "rw")) {
                return updateRecursive(file, rootPos, key, newValue);
            }
        }

        private boolean updateRecursive(RandomAccessFile file, long nodePos, int key, long newValue) throws IOException {
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);

            int i = 0;
            while (i < node.numKeys && key > node.keys[i]) {
                i++;
            }

            if (i < node.numKeys && node.keys[i] == key) {
                node.values[i] = newValue;
                node.write(file);
                return true;
            } else if (node.isLeaf) {
                return false;
            } else {
                return updateRecursive(file, node.children[i], key, newValue);
            }
        }

        public void delete(int key) throws IOException {
            try (RandomAccessFile file = new RandomAccessFile(filename, "rw")) {
                deleteRecursive(file, rootPos, key);
            }
        }

        private void deleteRecursive(RandomAccessFile file, long nodePos, int key) throws IOException {
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);

            int i = 0;
            while (i < node.numKeys && key > node.keys[i]) {
                i++;
            }

            if (i < node.numKeys && node.keys[i] == key) {
            	if (node.isLeaf) {
	            	// Exclusão simples da folha
	            	for (int j = i + 1; j < node.numKeys; j++) {
		            	node.keys[j - 1] = node.keys[j];
		            	node.values[j - 1] = node.values[j];
	            	}
	            	node.numKeys--;
	            	node.write(file);
            	} else {
	            	// Exclusão do nó interno (mais complexo)
	            	deleteFromInternalNode(file, node, i);
            	}
        	} else {
            	if (node.isLeaf) {
            		System.out.println("Chave " + key + " não encontrada.");
            	} else {
            		deleteRecursive(file, node.children[i], key);
            	}
        	}
        }

        private void deleteFromInternalNode(RandomAccessFile file, BTreeNode node, int index) throws IOException {
            int key = node.keys[index];

            if (node.children[index] != 0) {
                BTreeNode leftChild = new BTreeNode();
                leftChild.read(file, node.children[index]);

                if (leftChild.numKeys >= DEGREETREE) {
                    // localiza predecessor e substitui
                    int predecessorKey = getPredecessorKey(file, node.children[index]);
                    long predecessorValue = getPredecessorValue(file, node.children[index]);
                    deleteRecursive(file, node.children[index], predecessorKey); // apaga predecessor
                    node.keys[index] = predecessorKey;
                    node.values[index] = predecessorValue;
                    node.write(file);
                    return;
                }
            }

            if (node.children[index + 1] != 0) {
                BTreeNode rightChild = new BTreeNode();
                rightChild.read(file, node.children[index + 1]);

                if (rightChild.numKeys >= DEGREETREE) {
                	// localiza sucessor e substitui
                    
                    int successorKey = getSuccessorKey(file, node.children[index + 1]);
                    long successorValue = getSuccessorValue(file, node.children[index + 1]);
                    deleteRecursive(file, node.children[index + 1], successorKey); // apaga sucessor
                    node.keys[index] = successorKey;
                    node.values[index] = successorValue;
                    node.write(file);
                    return;
                }
            }

            //excuta um Merge
            mergeChild(file, node, index);
            deleteRecursive(file, node.children[index], key);
        }

        private int getPredecessorKey(RandomAccessFile file, long nodePos) throws IOException {
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);
            while (!node.isLeaf) {
                node.read(file, node.children[node.numKeys]);
            }
            return node.keys[node.numKeys - 1];
        }

        private long getPredecessorValue(RandomAccessFile file, long nodePos) throws IOException {
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);
            while (!node.isLeaf) {
                node.read(file, node.children[node.numKeys]);
            }
            return node.values[node.values.length - 1];
        }

        private int getSuccessorKey(RandomAccessFile file, long nodePos) throws IOException {
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);
            while (!node.isLeaf) {
                node.read(file, node.children[0]);
            }
            return node.keys[0];
        }

        private long getSuccessorValue(RandomAccessFile file, long nodePos) throws IOException {
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);
            while (!node.isLeaf) {
                node.read(file, node.children[0]);
            }
            return node.values[0];
        }

        private void mergeChild(RandomAccessFile file, BTreeNode parent, int index) throws IOException {
            BTreeNode leftChild = new BTreeNode();
            leftChild.read(file, parent.children[index]);
            BTreeNode rightChild = new BTreeNode();
            rightChild.read(file, parent.children[index + 1]);

         // Adiciona a chave separadora do nó pai
            leftChild.keys[leftChild.numKeys] = parent.keys[index];
            leftChild.values[leftChild.numKeys] = parent.values[index];
            leftChild.numKeys++;

            // Copia chaves e filhos do filho da direita para o filho da esquerda
            for (int i = 0; i < rightChild.numKeys; i++) {
	            leftChild.keys[leftChild.numKeys + i] = rightChild.keys[i];
	            leftChild.values[leftChild.numKeys + i] = rightChild.values[i];
            }
            if (!leftChild.isLeaf) {
	            for (int i = 0; i <= rightChild.numKeys; i++) { // <= para filhos
	            	leftChild.children[leftChild.numKeys + i] = rightChild.children[i];
	            }
            }
            leftChild.numKeys += rightChild.numKeys;

            //Shift chaves e filhos no nó pai
            for (int i = index + 1; i < parent.numKeys; i++) {
	            parent.keys[i - 1] = parent.keys[i];
	            parent.values[i - 1] = parent.values[i];
	            parent.children[i] = parent.children[i + 1];
            }
            parent.numKeys--;

            // Grava os nós modificados no arquivo
            leftChild.write(file);
            parent.write(file);

            // Libera espaço para o filho direito (opcional, depende do gerenciamento de arquivos)
            // Para simplificar, não libera espaço explicitamente
        }

        public void close(RandomAccessFile file) throws IOException {
            file.close();
        }
    }
}
