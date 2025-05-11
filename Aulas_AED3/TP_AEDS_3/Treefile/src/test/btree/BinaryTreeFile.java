package test.btree;
import java.io.*;

public class BinaryTreeFile {
	
	public static void writeTree(Node root) {
        String filename = "tree.dat";

        // Serialize the tree to a file
        try (DataOutputStream dos = new DataOutputStream(new FileOutputStream(filename))) {
            serialize(root, dos);
            System.out.println("Tree serialized to " + filename);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static void readTree(Node root) {
        String filename = "tree.dat";
        
        // Deserialize the tree from the file
        try (DataInputStream dis = new DataInputStream(new FileInputStream(filename))) {
            Node newRoot = deserialize(dis);
            System.out.println("Tree deserialized from " + filename);
            // You can add code here to verify the tree structure if needed
            
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    // Preorder traversal serialization
    public static void serialize(Node node, DataOutputStream dos) throws IOException {
        if (node == null) {
            dos.writeInt(-1); // Represent null with -1
            return;
        }
        dos.writeInt(node.data);
        serialize(node.left, dos);
        serialize(node.right, dos);
    }

    // Preorder traversal deserialization
    public static Node deserialize(DataInputStream dis) throws IOException {
        int data = dis.readInt();
        if (data!=-1) {
        	System.out.println("Data: " + data);
        }
        if (data == -1) {
            return null;
        }
        Node node = new Node(data);
        node.left = deserialize(dis);
        node.right = deserialize(dis);
        return node;
    }

    

    
}