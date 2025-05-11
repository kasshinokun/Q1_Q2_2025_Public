package test_c;
public class NodeTree{
    PageTree data;
    NodeTree left, right;
    int height;
    public NodeTree(PageTree data) {
        this.data = data;
        //left = right = null;
        this.height = 1;
    }
}
