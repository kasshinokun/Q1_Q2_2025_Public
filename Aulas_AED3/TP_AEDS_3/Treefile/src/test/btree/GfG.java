package test.btree;


class GfG {
    
    // This function deletes a given key x from the 
    // given BST  and returns the modified root of 
    // the BST (if it is modified).
    static Node delNode(Node root, int x) {
      
        // Base case
        if (root == null) {
            return root;
        }

        // If key to be searched is in a subtree
        if (root.data > x) {
            root.left = delNode(root.left, x);
        } else if (root.data < x) {
            root.right = delNode(root.right, x);
        } else {
            // If root matches with the given key

            // Cases when root has 0 children or
            // only right child
            if (root.left == null) {
                return root.right;
            }

            // When root has only left child
            if (root.right == null) {
                return root.left;
            }

            // When both children are present
            Node succ = getSuccessor(root);
            root.data = succ.data;
            root.right = delNode(root.right, succ.data);
        }
        return root;
    }
 
    // Note that it is not a generic inorder successor 
    // function. It mainly works when the right child
    // is not empty, which is the case we need in BST
    // delete. 
    static Node getSuccessor(Node curr) {
        curr = curr.right;
        while (curr != null && curr.left != null) {
            curr = curr.left;
        }
        return curr;
    }  

    // Utility function to do inorder traversal
    static void inorder(Node root) {
        if (root != null) {
            inorder(root.left);
            System.out.print(root.data + " ");
            inorder(root.right);
        }
    }

    // Driver code
    public static void main(String[] args) {
        Node root = new Node(10);
        root.left = new Node(5);
        root.right = new Node(15);
        root.right.left = new Node(12);
        root.right.right = new Node(18);

        int x = 15;
        root = delNode(root, x);
        inorder(root);
    }
}
