package test_c;
public class AVLPageTree {

	public NodeTree root;

    // Get the height of the node
    int height(NodeTree node) {
        if (node == null)
            return 0;
        return node.height;
    }

    // Get maximum of two integers
    int max(int a, int b) {
        return (a > b) ? a : b;
    }

    // Right rotate subtree rooted with node
    NodeTree rightRotate(NodeTree node) {
    	NodeTree leftChild = node.left;
    	NodeTree temp = leftChild.right;

        // Perform rotation
        leftChild.right = node;
        node.left = temp;

        // Update heights
        node.height = max(height(node.left), height(node.right)) + 1;
        leftChild.height = max(height(leftChild.left), height(leftChild.right)) + 1;

        // Return new root
        return leftChild;
    }

    // Left rotate subtree rooted with node
    NodeTree leftRotate(NodeTree node) {
    	NodeTree rightChild = node.right;
    	NodeTree temp = rightChild.left;

        // Perform rotation
        rightChild.left = node;
        node.right = temp;

        // Update heights
        node.height = max(height(node.left), height(node.right)) + 1;
        rightChild.height = max(height(rightChild.left), height(rightChild.right)) + 1;

        // Return new root
        return rightChild;
    }

    // Get balance factor of node
    int getBalance(NodeTree node) {
        if (node == null)
            return 0;
        return height(node.left) - height(node.right);
    }

    // Insert a key into the AVL tree and return the new root of the subtree
    NodeTree insert(NodeTree root, PageTree key) {
        if (root == null)
            return new NodeTree(key);

        if (key.numPage < root.data.numPage)
            root.left = insert(root.left, key);
        else if (key.numPage > root.data.numPage)
            root.right = insert(root.right, key);
        else
            return root;

        // Update height of root
        root.height = 1 + max(height(root.left), height(root.right));

        // Get balance factor
        int balance = getBalance(root);

        // Left Left Case
        if (balance > 1 && key.numPage < root.left.data.numPage)
            return rightRotate(root);

        // Right Right Case
        if (balance < -1 && key.numPage > root.right.data.numPage)
            return leftRotate(root);

        // Left Right Case
        if (balance > 1 && key.numPage > root.left.data.numPage) {
            root.left = leftRotate(root.left);
            return rightRotate(root);
        }

        // Right Left Case
        if (balance < -1 && key.numPage < root.right.data.numPage) {
            root.right = rightRotate(root.right);
            return leftRotate(root);
        }

        return root;
    }

    // Utility functions for traversal
    void preOrder(NodeTree node) {
        if (node != null) {
        	System.out.println(node.data.pagePrint());
            preOrder(node.left);
            preOrder(node.right);
        }
    }

    void inOrder(NodeTree node) {
        if (node != null) {
            inOrder(node.left);
            System.out.println(node.data.pagePrint());
            inOrder(node.right);
        }
    }

    void postOrder(NodeTree node) {
        if (node != null) {
            postOrder(node.left);
            postOrder(node.right);
            System.out.println(node.data.pagePrint());
        }
    }

    
}