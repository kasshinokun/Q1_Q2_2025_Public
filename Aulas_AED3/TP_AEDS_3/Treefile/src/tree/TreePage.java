package tree;
import java.io.*;

public class TreePage {
	
	// global variables that are populated by reading the first metadata block and re-used across the program
	int degree;
	int key_len;
	long root_address;
	String index_filename;
	String data_filename;

	
	public class NodePage {
		
	    long address;
	    boolean is_leaf;
	    int[] keys;
	    long[] children;
	    long[] pointers;
	    long next; // address of next block
	    long prev; // address of prev block
	    
	    /* read Node object from index file at 'address' */
	    public void read_from_disk()throws Exception
	    {
	        if (address <= 0) // block hasn't been written to disk yet, can't read it
	            throw new NullPointerException("Erro de endereço ");

	        int buf;
	        long offset = 0;

	        // Open the binary file and read into memory
	        RandomAccessFile infile =new RandomAccessFile(index_filename, "rw");
	        infile.seek(address);

	        // read is_leaf bool 
	        is_leaf=infile.readBoolean();

	        // read next addr pointer
	        next=infile.readLong();

	        // read prev addr pointer
	        prev=infile.readLong();

	        // read the number of keys stored
	        int keys_size=infile.readInt();

	        // read the keys
	        this.keys=new int[keys_size];
	        for (int i = 0 ; i < keys_size ; i++) 
	        {
	        	keys[i]=infile.readInt();   
	        }
	        if (is_leaf == false) // internal node - read children 
	        {
	            this.children=new long[keys_size];
	            for (int i = 0 ; i < keys_size + 1 ; i++) 
	            {
	            	children[i]=infile.readLong();
	            }
	        } 
	        else // leaf node - read pointers
	        {
	        	this.children=new long[keys_size];
	            for (int i = 0 ; i <keys_size ; i++) 
	            {
	            	pointers[i]=infile.readLong();
	            }
	        }
	    }

	    
	}


}
