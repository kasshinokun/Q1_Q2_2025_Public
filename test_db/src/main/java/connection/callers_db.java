package connection;

/**
 * @version 1_2025_01_06
 * @author Gabriel da Silva Cassino
 */
public class callers_db {
    public static void main(int i,String bd) {
        
        String user = "user321";
        String password = "123456";
        String local="localhost";
        String door="";
        String str_connection="db_test";
        
        
        if (i==1){
            if (bd.equals("PostgreSQL")){
                door="5432";
            }else {
                if (bd.equals("MySQL")) {
                    door="3306";
                }
            }
            int lang=1;
            System.out.println("English-USA");
            db_connection c = new db_connection(bd,local,door,str_connection,user,password,lang);
            //db_connection("DATABASE'S TYPE","LOCAL/IP","PORT","MY DATABASE","USER","PASSWORD","LANGUAGE(INT)");
            
            c.connect();
            
            
            
            
            
            if (c.getConnectionState()==true){
                c.disconect();
            }
        }else{
            if (bd.equals("PostgreSQL")){
                door="5432";
            }else {
                if (bd.equals("MySQL")) {
                    door="3306";
                }
            }
            System.out.println("Portugues-Brasil");
            int lang=2;
            db_connection c = new db_connection(bd,local,door,str_connection,user,password,lang);
            //db_connection("TIPO DO BANCO DE DADOS","LOCAL/IP","PORTA","MEU DB","USUARIO","SENHA","IDIOMA(INT)");
            
            c.connect();
            
            
            
            
            
            if (c.getConnectionState()==true){
                c.disconect();
            }
        } 
    }  
}
