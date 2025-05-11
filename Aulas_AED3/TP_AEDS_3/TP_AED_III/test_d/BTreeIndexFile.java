package test_d;

import java.io.*;
import java.util.*;

public class BTreeIndexFile{
    public static class BTreeNode {
        static final int DEGREE = 50;
        static final int MAX_KEYS = 2 * DEGREE - 1;
        static final int MAX_CHILDREN = 2 * DEGREE;

        boolean isLeaf;
        int numKeys;
        int[] keys;
        long[] values;
        long[] children;

        public BTreeNode() {
            keys = new int[MAX_KEYS];
            values = new long[MAX_KEYS];
            children = new long[MAX_CHILDREN];
        }

        void read(RandomAccessFile file, long pos) throws IOException {
            if (pos < 0 || pos >= file.length()) {
                throw new EOFException("Invalid read position: " + pos);
            }
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

        void write(RandomAccessFile file, long pos) throws IOException {
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

    public static class BTree {
        RandomAccessFile file;
        long rootPos;

        public BTree(String filename) throws IOException {
            File f = new File(filename);
            if (!f.exists() || f.length() == 0) {
                file = new RandomAccessFile(f, "rw");
                rootPos = 8;
                writeRootPointer(rootPos);
                BTreeNode root = new BTreeNode();
                root.isLeaf = true;
                root.numKeys = 0;
                root.write(file, rootPos);
            } else {
                file = new RandomAccessFile(f, "rw");
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
            if (nodePos < 0 || nodePos >= file.length()) return null;
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);
            int i = 0;
            while (i < node.numKeys && key > node.keys[i]) i++;
            if (i < node.numKeys && key == node.keys[i]) return node.values[i];
            if (node.isLeaf) return null;
            return searchRecursive(node.children[i], key);
        }

        public void insert(int key, long value) throws IOException {
            BTreeNode root = new BTreeNode();
            root.read(file, rootPos);
            if (root.numKeys == BTreeNode.MAX_KEYS) {
                long newRootPos = file.length();
                BTreeNode newRoot = new BTreeNode();
                newRoot.isLeaf = false;
                newRoot.numKeys = 0;
                newRoot.children[0] = rootPos;
                writeRootPointer(newRootPos);
                rootPos = newRootPos;
                splitChild(newRoot, 0, newRootPos);
                insertNonFull(newRoot, key, value, newRootPos);
            } else {
                insertNonFull(root, key, value, rootPos);
            }
        }

        private void insertNonFull(BTreeNode node, int key, long value, long nodePos) throws IOException {
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
                    node.write(file, nodePos);
                    return;
                } else {
                    while (i >= 0 && key < node.keys[i]) i--;
                    i++;

                    long childPos = node.children[i];
                    if (childPos < 0 || childPos >= file.length()) {
                        throw new EOFException("Invalid child position: " + childPos);
                    }

                    BTreeNode child = new BTreeNode();
                    child.read(file, childPos);

                    if (child.numKeys == BTreeNode.MAX_KEYS) {
                        splitChild(node, i, nodePos);
                        node.read(file, nodePos); // reload parent after split
                        if (key > node.keys[i]) i++;
                        childPos = node.children[i];
                        child.read(file, childPos);
                    }

                    node = child;
                    nodePos = childPos;
                }
            }
        }

        private void splitChild(BTreeNode parent, int index, long parentPos) throws IOException {
            BTreeNode fullChild = new BTreeNode();
            long fullChildPos = parent.children[index];
            fullChild.read(file, fullChildPos);

            BTreeNode newChild = new BTreeNode();
            newChild.isLeaf = fullChild.isLeaf;
            newChild.numKeys = BTreeNode.DEGREE - 1;
            long newChildPos = file.length();

            for (int j = 0; j < BTreeNode.DEGREE - 1; j++) {
                newChild.keys[j] = fullChild.keys[j + BTreeNode.DEGREE];
                newChild.values[j] = fullChild.values[j + BTreeNode.DEGREE];
            }
            if (!fullChild.isLeaf) {
                for (int j = 0; j < BTreeNode.DEGREE; j++) {
                    newChild.children[j] = fullChild.children[j + BTreeNode.DEGREE];
                }
            }
            fullChild.numKeys = BTreeNode.DEGREE - 1;

            for (int j = parent.numKeys; j >= index + 1; j--) {
                parent.children[j + 1] = parent.children[j];
            }
            parent.children[index + 1] = newChildPos;

            for (int j = parent.numKeys - 1; j >= index; j--) {
                parent.keys[j + 1] = parent.keys[j];
                parent.values[j + 1] = parent.values[j];
            }
            parent.keys[index] = fullChild.keys[BTreeNode.DEGREE - 1];
            parent.values[index] = fullChild.values[BTreeNode.DEGREE - 1];
            parent.numKeys++;

            fullChild.write(file, fullChildPos);
            newChild.write(file, newChildPos);
            parent.write(file, parentPos);
        }

        public boolean update(int key, long newValue) throws IOException {
            return updateRecursive(rootPos, key, newValue);
        }

        private boolean updateRecursive(long nodePos, int key, long newValue) throws IOException {
            if (nodePos < 0 || nodePos >= file.length()) return false;
            BTreeNode node = new BTreeNode();
            node.read(file, nodePos);
            int i = 0;
            while (i < node.numKeys && key > node.keys[i]) i++;
            if (i < node.numKeys && key == node.keys[i]) {
                node.values[i] = newValue;
                node.write(file, nodePos);
                return true;
            }
            if (node.isLeaf) return false;
            return updateRecursive(node.children[i], key, newValue);
        }
    }
}

