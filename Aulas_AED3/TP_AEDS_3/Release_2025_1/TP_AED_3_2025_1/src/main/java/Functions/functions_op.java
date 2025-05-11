package Functions;

import java.util.*;

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

public class functions_op {
        
    public static int template(){//input validate(on development)
        Scanner reader=new Scanner(System.in);
        if(reader.hasNextInt()){
            return reader.nextInt();
        }else{
            return -1;
        }
    }
}
