package test_d;
import java.io.*;

public class IterativeBTree {

    static final int DEGREE = 32;
    static final int MAX_KEYS = 2 * DEGREE - 1;
    static final int MAX_CHILDREN = 2 * DEGREE;

    static class BTreeNode {
        boolean isLeaf;
        int numKeys;
        int[] keys = new int[MAX_KEYS];
        long[] values = new long[MAX_KEYS];
        long[] children = new long[MAX_CHILDREN];
        long pos;

        BTreeNode() {
            this.pos = -1;
        }

        void read(RandomAccessFile file, long pos) throws IOException {
            this.pos = pos;
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

        static int getNodeSize() {
            return 1 + 4 + MAX_KEYS * (4 + 8) + MAX_CHILDREN * 8;
        }
    }

    static class BTree {
        private String filename;
        private long rootPos;

        BTree(String filename) throws IOException {
            this.filename = filename;
            try (RandomAccessFile file = new RandomAccessFile(filename, "rw")) {
                if (file.length() == 0) {
                    BTreeNode root = new BTreeNode();
                    root.isLeaf = true;
                    root.numKeys = 0;
                    rootPos = allocateNode(file);
                    root.pos = rootPos;
                    root.write(file);
                    writeRootPointer(file, rootPos);
                } else {
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
            file.seek(pos);
            file.write(new byte[BTreeNode.getNodeSize()]);
            return pos;
        }

        public Long search(int key) throws IOException {
            try (RandomAccessFile file = new RandomAccessFile(filename, "r")) {
                long nodePos = rootPos;
                while (true) {
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
                        nodePos = node.children[i];
                    }
                }
            }
        }

        public void insert(int key, long value) throws IOException {
            try (RandomAccessFile file = new RandomAccessFile(filename, "rw")) {
                BTreeNode root = new BTreeNode();
                root.read(file, rootPos);

                if (root.numKeys == MAX_KEYS) {
                    BTreeNode newRoot = new BTreeNode();
                    newRoot.isLeaf = false;
                    newRoot.numKeys = 0;
                    newRoot.children[0] = rootPos;
                    newRoot.pos = allocateNode(file);

                    splitChild(file, newRoot, 0);

                    rootPos = newRoot.pos;
                    writeRootPointer(file, rootPos);
                    insertNonFull(file, newRoot, key, value);
                } else {
                    insertNonFull(file, root, key, value);
                }
            }
        }

        private void insertNonFull(RandomAccessFile file, BTreeNode node, int key, long value) throws IOException {
            while (true) {
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
                    return;
                } else {
                    while (i >= 0 && key < node.keys[i]) {
                        i--;
                    }
                    i++;

                    BTreeNode child = new BTreeNode();
                    child.read(file, node.children[i]);

                    if (child.numKeys == MAX_KEYS) {
                        splitChild(file, node, i);
                        node.read(file, node.pos);
                        if (key > node.keys[i]) {
                            i++;
                        }
                    }

                    child.read(file, node.children[i]);
                    node = child;
                }
            }
        }

        private void splitChild(RandomAccessFile file, BTreeNode parent, int index) throws IOException {
            BTreeNode fullChild = new BTreeNode();
            fullChild.read(file, parent.children[index]);

            BTreeNode newChild = new BTreeNode();
            newChild.isLeaf = fullChild.isLeaf;
            newChild.numKeys = DEGREE - 1;
            newChild.pos = allocateNode(file);

            for (int j = 0; j < DEGREE - 1; j++) {
                newChild.keys[j] = fullChild.keys[j + DEGREE];
                newChild.values[j] = fullChild.values[j + DEGREE];
            }

            if (!fullChild.isLeaf) {
                for (int j = 0; j < DEGREE; j++) {
                    newChild.children[j] = fullChild.children[j + DEGREE];
                }
            }

            fullChild.numKeys = DEGREE - 1;

            for (int j = parent.numKeys; j >= index + 1; j--) {
                parent.children[j + 1] = parent.children[j];
            }
            parent.children[index + 1] = newChild.pos;

            for (int j = parent.numKeys - 1; j >= index; j--) {
                parent.keys[j + 1] = parent.keys[j];
                parent.values[j + 1] = parent.values[j];
            }

            parent.keys[index] = fullChild.keys[DEGREE - 1];
            parent.values[index] = fullChild.values[DEGREE - 1];
            parent.numKeys++;

            fullChild.write(file);
            newChild.write(file);
            parent.write(file);
        }

    }

    public static void main(String[] args) throws IOException {
        BTree tree = new BTree("index/arvore_b/iterativebtree.db");

        for (int i = 1; i <= 1000000; i++) {
            tree.insert(i, i * 10L);
        }

        System.out.println("Search 999999: " + tree.search(999999));
        System.out.println("Search 42: " + tree.search(42));
        System.out.println("Search 1000001: " + tree.search(1000001));
    }
}
