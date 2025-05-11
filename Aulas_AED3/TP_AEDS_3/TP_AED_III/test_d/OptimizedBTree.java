package test_d;
/*

package object.indexed.tree;
import java.io.*;
import java.util.Random;

public class OptimizedBTree {

    static final int DEGREE = 32;
    static final int MAX_KEYS = 2 * DEGREE - 1;
    static final int MAX_CHILDREN = 2 * DEGREE;

    static class BTreeNode {
        boolean isLeaf;
        int numKeys;
        int[] keys = new int[MAX_KEYS];
        long[] values = new long[MAX_KEYS];
        long[] children = new long[MAX_CHILDREN];
        long pos; // Node's position in the file

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
                    // Create new B-Tree
                    BTreeNode root = new BTreeNode();
                    root.isLeaf = true;
                    root.numKeys = 0;
                    rootPos = allocateNode(file);
                    root.pos = rootPos;
                    root.write(file);
                    writeRootPointer(file, rootPos);

                } else {
                    // Load existing B-Tree
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
            long alignedPos = (pos % nodeSize == 0) ? pos : (pos / nodeSize + 1) * nodeSize; // [cite: 53]
            file.seek(alignedPos);
            file.write(new byte[(int) nodeSize]); // Reserve space (important for alignment)
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
                if (rootPos == 0) { // Special case: Empty tree
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

                if (root.numKeys == MAX_KEYS) {
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
                if (child.numKeys == MAX_KEYS) {
                    splitChild(file, node, i);
                    node.read(file, nodePos); // Re-read node after split (important!)
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
            newChild.numKeys = DEGREE - 1;

            long newChildPos = allocateNode(file);
            newChild.pos = newChildPos;

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
            parent.children[index + 1] = newChildPos;

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
                    // Simple delete from leaf
                    for (int j = i; j < node.numKeys - 1; j++) {
                        node.keys[j] = node.keys[j + 1];
                        node.values[j] = node.values[j + 1];
                    }
                    node.numKeys--;
                    node.write(file);
                } else {
                    // Delete from internal node (more complex)
                    deleteFromInternalNode(file, node, i);
                }
            } else {
                if (node.isLeaf) {
                    System.out.println("Key " + key + " not found.");
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

                if (leftChild.numKeys >= DEGREE) {
                    // Find predecessor and replace
                    int predecessorKey = getPredecessor(file, node.children[index]);
                    long predecessorValue = getPredecessorValue(file, node.children[index]);
                    deleteRecursive(file, node.children[index], predecessorKey); // Delete predecessor
                    node.keys[index] = predecessorKey;
                    node.values[index] = predecessorValue;
                    node.write(file);
                    return;
                }
            }

            if (node.children[index + 1] != 0) {
                BTreeNode rightChild = new BTreeNode();
                rightChild.read(file, node.children[index + 1]);

                if (rightChild.numKeys >= DEGREE) {
                    // Find successor and replace
                    int successorKey = getSuccessor(file, node.children[index + 1]);
                    long successorValue = getSuccessorValue(file, node.children[index + 1]);
                    deleteRecursive(file, node.children[index + 1], successorKey); // Delete successor
                    node.keys[index] = successorKey;
                    node.values[index] = successorValue;
                    node.write(file);
                    return;
                }
            }

            // Merge
            mergeChild(file, node, index);
            deleteRecursive(file, node.children[index], key);
        }

        private int getPredecessor(RandomAccessFile file, long nodePos) throws IOException {
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
            return node.values[node.numKeys - 1];
        }

        private int getSuccessor(RandomAccessFile file, long nodePos) throws IOException {
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

            leftChild.keys[DEGREE - 1] = parent.keys[index];
            leftChild.values[DEGREE - 1] = parent.values[index];

            for (int i = 0; i < DEGREE - 1; i++) {
                leftChild.keys[DEGREE + i] = rightChild.keys[i];
                leftChild.values[DEGREE + i] = rightChild.values[i];
            }

            if (!leftChild.isLeaf) {
                for (int i = 0; i < DEGREE; i++) {
                    leftChild.children[DEGREE + i] = rightChild.children[i];
                }
            }

            leftChild.numKeys = 2 *
*/
/*
I have tested the code in an online Java IDE and here are the errors and improvements:
Errors:
java.lang.ArrayIndexOutOfBoundsException: This error occurs in several methods, including insertNonFull, splitChild, delete, and mergeChild. It happens when the code tries to access an array index that is out of the valid range. This is often due to incorrect loop conditions or index calculations when shifting or copying keys and children within nodes.


java.io.EOFException: This error occurs during file read operations, specifically in the readNode method. It indicates that the end of the file was reached unexpectedly while trying to read data for a node. This might happen if the node size is not correctly calculated or if there are inconsistencies in how node positions are stored and retrieved.


java.io.IOException: This is a general exception for I/O operations and can occur in any method that interacts with the RandomAccessFile. The specific reasons can vary, such as file access issues, disk errors, or incorrect file operations.


java.lang.IllegalArgumentException: This error occurs in the seek method of RandomAccessFile. It indicates that the file pointer position is negative. This could be due to errors in calculating the position of nodes within the file.  
Improvements:
Node Size Alignment: Ensure that nodes are stored at file offsets that are multiples of the node size.


File Handling: Use try-with-resources to ensure that the RandomAccessFile is properly closed after use.


Delete Operation: Implement the full delete operation, including handling deletion from internal nodes, merging, and borrowing.


Code Clarity: Improve code readability by adding comments and using more descriptive variable names.


Error Handling: Add more specific error handling to catch and handle potential exceptions.

*/


import java.io.*;
import java.util.Random;

import test_d.IterativeBTree.BTree;

public class OptimizedBTree {

    static final int DEGREE = 32; // Minimum degree (affects performance)
    static final int MAX_KEYS = 2 * DEGREE - 1;
    static final int MAX_CHILDREN = 2 * DEGREE;

    static class BTreeNode {
        boolean isLeaf;
        int numKeys;
        int[] keys = new int[MAX_KEYS];
        long[] values = new long[MAX_KEYS];
        long[] children = new long[MAX_CHILDREN];
        long pos; // Node's position in the file

        BTreeNode() {
            this.pos = -1;
        }

        void read(RandomAccessFile file, long pos) throws IOException {
            if(pos<=(file.length()-BTreeNode.getNodeSize())){
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
            else {
            	file.seek(pos);
            	isLeaf = true;
                numKeys = 0;
                long nodeSize = BTreeNode.getNodeSize();
                long alignedPos = ((pos-8) % nodeSize == 0) ? pos : 8+(((pos-8) / nodeSize + 1) * nodeSize); //
                file.seek(alignedPos);
                file.write(new byte[(int) nodeSize]); // Reserve space (important for alignment)
                pos=alignedPos;
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

        void printNode() { // For debugging
            System.out.print("Node(Leaf=" + isLeaf + ", n=" + numKeys + ", keys=[");
            for (int i = 0; i < numKeys; i++) {
                System.out.print(keys[i] + ":" + values[i] + " ");
            }
            System.out.print("], children=[");
            for (int i = 0; i < numKeys + 1; i++) {
                System.out.print(children[i] + " ");
            }
            System.out.println("])");
        }
    }

    static class BTree {
        private String filename;
        private long rootPos;

        BTree(String filename) throws IOException {
            this.filename = filename;
            try (RandomAccessFile file = new RandomAccessFile(filename, "rw")) {
                if (file.length() == 0) {
                    // Create new B-Tree
                    BTreeNode root = new BTreeNode();
                    root.isLeaf = true;
                    root.numKeys = 0;
                    rootPos = allocateNode(file);
                    root.pos = rootPos;
                    root.write(file);
                    writeRootPointer(file, rootPos);

                } else {
                    // Load existing B-Tree
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
            file.write(new byte[(int) nodeSize]); // Reserve space (important for alignment)
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
                if (rootPos == 0) { // Special case: Empty tree
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

                if (root.numKeys == MAX_KEYS) {
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
                if (child.numKeys == MAX_KEYS) {
                    splitChild(file, node, i);
                    node.read(file,nodePos); // Re-read node after split (important!)
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
            newChild.numKeys = DEGREE - 1;

            long newChildPos = allocateNode(file);
            newChild.pos = newChildPos;

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
            parent.children[index + 1] = newChildPos;

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
                    // Simple delete from leaf
                    for (int j = i + 1; j < node.numKeys; j++) {
                        node.keys[j - 1] = node.keys[j];
                        node.values[j - 1] = node.values[j];
                    }
                    node.numKeys--;
                    node.write(file);
                } else {
                    // Delete from internal node (more complex)
                    deleteFromInternalNode(file, node, i);
                }
            } else {
                if (node.isLeaf) {
                    System.out.println("Key " + key + " not found.");
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

                if (leftChild.numKeys >= DEGREE) {
                    // Find predecessor and replace
                    int predecessorKey = getPredecessorKey(file, node.children[index]);
                    long predecessorValue = getPredecessorValue(file, node.children[index]);
                    deleteRecursive(file, node.children[index], predecessorKey); // Delete predecessor
                    node.keys[index] = predecessorKey;
                    node.values[index] = predecessorValue;
                    node.write(file);
                    return;
                }
            }

            if (node.children[index + 1] != 0) {
                BTreeNode rightChild = new BTreeNode();
                rightChild.read(file, node.children[index + 1]);

                if (rightChild.numKeys >= DEGREE) {
                    // Find successor and replace
                    int successorKey = getSuccessorKey(file, node.children[index + 1]);
                    long successorValue = getSuccessorValue(file, node.children[index + 1]);
                    deleteRecursive(file, node.children[index + 1], successorKey); // Delete successor
                    node.keys[index] = successorKey;
                    node.values[index] = successorValue;
                    node.write(file);
                    return;
                }
            }

            // Merge
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

            // Add the separator key from the parent node
            leftChild.keys[leftChild.numKeys] = parent.keys[index];
            leftChild.values[leftChild.numKeys] = parent.values[index];
            leftChild.numKeys++;

            // Copy keys and children from the right child to the left child
            for (int i = 0; i < rightChild.numKeys; i++) {
                leftChild.keys[leftChild.numKeys + i] = rightChild.keys[i];
                leftChild.values[leftChild.numKeys + i] = rightChild.values[i];
            }
            if (!leftChild.isLeaf) {
                for (int i = 0; i <= rightChild.numKeys; i++) { // <= for children
                    leftChild.children[leftChild.numKeys + i] = rightChild.children[i];
                }
            }
            leftChild.numKeys += rightChild.numKeys;

            // Shift keys and children in the parent node
            for (int i = index + 1; i < parent.numKeys; i++) {
                parent.keys[i - 1] = parent.keys[i];
                parent.values[i - 1] = parent.values[i];
                parent.children[i] = parent.children[i + 1];
            }
            parent.numKeys--;

            // Write the modified nodes to the file
            leftChild.write(file);
            parent.write(file);

            // Free the right child's space (optional, depends on file management)
            // For simplicity, we don't explicitly free space in this example.
        }

        public void close(RandomAccessFile file) throws IOException {
            file.close();
        }
    }

    public static void main(String[] args) throws IOException {
        BTree tree = new BTree("index/arvore_b/optmizedbtree.db");

        for (int i = 1; i <= 1000000; i++) {
            tree.insert(i, i * 10L);
        }

        System.out.println("Search 999999: " + tree.search(999999));
        System.out.println("Search 42: " + tree.search(42));
        System.out.println("Search 1000001: " + tree.search(1000001));
    }
   }
