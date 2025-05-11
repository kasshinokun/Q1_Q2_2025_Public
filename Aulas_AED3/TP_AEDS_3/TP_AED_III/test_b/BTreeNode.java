package test_b;

import object.indexed.Index;

public class BTreeNode {
	Index[] keys;
    int t;
    BTreeNode[] children;
    int n;
    boolean leaf;
    
    public BTreeNode(int t, boolean leaf) {
        this.t = t;
        this.leaf = leaf;
        this.keys = new Index[2 * t - 1];
        this.children = new BTreeNode[2 * t];
        this.n = 0;
    }
    public void traverse() {
        int i;
        for (i = 0; i < n; i++) {
            if (!leaf) {
                children[i].traverse();
            }
            System.out.println(" " + keys[i].toStringIndex());
        }
        if (!leaf) {
            children[i].traverse();
        }
    }
    
    public BTreeNode search(Index key) {
    	
    	int i = 0;
        while (i < n && key.getKey() > keys[i].getKey()) {
            i++;
        }
        if (i < n && keys[i].equals(key)) {
            return this;
        }
        if (leaf) {
            return null;
        }
        return children[i].search(key);
    }

    
    void splitChild(int i, BTreeNode y) {
        BTreeNode z = new BTreeNode(y.t, y.leaf);
        z.n = t - 1;
        for (int j = 0; j < t - 1; j++) {
            z.keys[j] = y.keys[j + t];
        }
        if (!y.leaf) {
            for (int j = 0; j < t; j++) {
                z.children[j] = y.children[j + t];
            }
        }
        y.n = t - 1;
        for (int j = n; j >= i + 1; j--) {
            children[j + 1] = children[j];
        }
        children[i + 1] = z;
        for (int j = n - 1; j >= i; j--) {
            keys[j + 1] = keys[j];
        }
        keys[i] = y.keys[t - 1];
        n++;
    }
    
    void insertNonFull(Index key) {
        int i = n - 1;
        if (leaf) {
            while (i >= 0 && keys[i].getKey() > key.getKey()) {
                keys[i + 1] = keys[i];
                i--;
            }
            keys[i + 1] = key;
            n++;
        } else {
            while (i >= 0 && keys[i].getKey() > key.getKey()) {
                i--;
            }
            i++;
            if (children[i].n == 2 * t - 1) {
                splitChild(i, children[i]);
                if (keys[i].getKey() < key.getKey()) {
                    i++;
                }
            }
            children[i].insertNonFull(key);
        }
    }
    
}


