package test_d;
import java.io.*;

public class BTreeIndexFileTwo {
    static final int DEGREE = 32;
    static final int MAX_KEYS = 2 * DEGREE - 1;
    static final int MAX_CHILDREN = 2 * DEGREE;

    static class BTreeNode {
        boolean isLeaf;
        int numKeys;
        int[] keys = new int[MAX_KEYS];
        long[] addresses = new long[MAX_KEYS];
        long[] children = new long[MAX_CHILDREN];

        void read(RandomAccessFile file, long pos) throws IOException {
            file.seek(pos);
            isLeaf = file.readBoolean();
            numKeys = file.readInt();
            for (int i = 0; i < MAX_KEYS; i++) {
                keys[i] = file.readInt();
                addresses[i] = file.readLong();
            }
            for (int i = 0; i < MAX_CHILDREN; i++) {
                children[i] = file.readLong();
            }
        }

        void write(RandomAccessFile file, long pos) throws IOException {
            file.seek(pos);
            file.writeBoolean(isLeaf);
            file.writeInt(numKeys);
            for (int i = 0; i < MAX_KEYS; i++) {
                file.writeInt(keys[i]);
                file.writeLong(addresses[i]);
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
        RandomAccessFile file;
        long rootPos;

        public BTree(String filename) throws IOException {
            File f = new File(filename);
            file = new RandomAccessFile(f, "rw");

            if (file.length() == 0) {
                rootPos = 8;
                writeRootPointer(rootPos);
                BTreeNode root = new BTreeNode();
                root.isLeaf = true;
                root.numKeys = 0;
                root.write(file, rootPos);
            } else {
                file.seek(0);
                rootPos = file.readLong();
            }
        }

        private void writeRootPointer(long pos) throws IOException {
            file.seek(0);
            file.writeLong(pos);
        }

        public Long search(int key) throws IOException {
            return searchRecursive(rootPos, key);
        }

        private Long searchRecursive(long nodePos, int key) throws IOException {
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);

            int i = 0;
            while (i < node.numKeys && key > node.keys[i]) i++;

            if (i < node.numKeys && key == node.keys[i]) return node.addresses[i];

            if (node.isLeaf) return null;
            return searchRecursive(node.children[i], key);
        }

        public void insert(int key, long address) throws IOException {
            BTreeNode root = new BTreeNode();
            root.read(file, rootPos);

            if (root.numKeys == MAX_KEYS) {
                long newRootPos = file.length();
                BTreeNode newRoot = new BTreeNode();
                newRoot.isLeaf = false;
                newRoot.numKeys = 0;
                newRoot.children[0] = rootPos;

                splitChild(newRoot, 0, newRootPos);
                insertNonFull(newRoot, newRootPos, key, address);

                writeRootPointer(newRootPos);
                rootPos = newRootPos;
            } else {
                insertNonFull(root, rootPos, key, address);
            }
        }

        private void insertNonFull(BTreeNode node, long nodePos, int key, long address) throws IOException {
            int i = node.numKeys - 1;

            if (node.isLeaf) {
                while (i >= 0 && key < node.keys[i]) {
                    node.keys[i + 1] = node.keys[i];
                    node.addresses[i + 1] = node.addresses[i];
                    i--;
                }
                node.keys[i + 1] = key;
                node.addresses[i + 1] = address;
                node.numKeys++;
                node.write(file, nodePos);
            } else {
                while (i >= 0 && key < node.keys[i]) i--;
                i++;

                BTreeNode child = new BTreeNode();
                child.read(file, node.children[i]);

                if (child.numKeys == MAX_KEYS) {
                    splitChild(node, i, nodePos);

                    node.read(file, nodePos); // reload
                    if (key > node.keys[i]) i++;
                }

                child.read(file, node.children[i]);
                insertNonFull(child, node.children[i], key, address);
            }
        }

        private void splitChild(BTreeNode parent, int index, long parentPos) throws IOException {
            BTreeNode fullChild = new BTreeNode();
            long fullChildPos = parent.children[index];
            fullChild.read(file, fullChildPos);

            BTreeNode newChild = new BTreeNode();
            newChild.isLeaf = fullChild.isLeaf;
            newChild.numKeys = DEGREE - 1;

            long newChildPos = file.length();

            for (int j = 0; j < DEGREE - 1; j++) {
                newChild.keys[j] = fullChild.keys[j + DEGREE];
                newChild.addresses[j] = fullChild.addresses[j + DEGREE];
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
            parent.children[index + 1] = newChildPos;

            for (int j = parent.numKeys - 1; j >= index; j--) {
                parent.keys[j + 1] = parent.keys[j];
                parent.addresses[j + 1] = parent.addresses[j];
            }

            parent.keys[index] = fullChild.keys[DEGREE - 1];
            parent.addresses[index] = fullChild.addresses[DEGREE - 1];
            parent.numKeys++;

            fullChild.write(file, fullChildPos);
            newChild.write(file, newChildPos);
            parent.write(file, parentPos);
        }
    }
}
