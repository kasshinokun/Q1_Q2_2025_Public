package connection;

/**
 * @version 1_2025_01_06
 * @author Gabriel da Silva Cassino
 */
import java.sql.*;

public class generate_process {
    
    private db_connection connection;
    
    public generate_process(String bd,String local,String door,
        String str_connection,String user,String password,int lang)
                throws IllegalArgumentException {//Manual Setting
    
        if(setConnection(bd,local,door,str_connection,user,password,lang)==false){
            throw new IllegalArgumentException(functions_op.invalid_argument(lang));
        }else{
            functions_op.state_connection(3, getConnection().getLanguage());   
        }
    } 
    public generate_process(db_connection connection){// Based on created connection
    
        if(setConnection(connection)==false){
            throw new IllegalArgumentException(functions_op.invalid_argument(connection.getLanguage()));
        }else{
            functions_op.state_connection(3, getConnection().getLanguage());   
        }
    
    }
    
    public boolean setConnection(String bd,String local,String door,
        String str_connection,String user,String password,int lang){//Manual Setting
        
        this.connection = new db_connection(bd,local,door,str_connection,user,password,lang);
             
        getConnection().connect();   
        
        return getConnection().getConnectionState();
            
        
    }
    
    public boolean setConnection(db_connection connection){// Based on created connection
    
        this.connection = connection;
             
        getConnection().connect();   
        
        return getConnection().getConnectionState();
    
    }
        
    public db_connection getConnection(){
        return this.connection;
    }
    
    public class user{
        
        private String name;
        private String password;
        private String level;
        private int lang; //Modification to set language
        
        public user(String name, String password, String level,int lang)
                throws IllegalArgumentException {
            if(level!="admin"|level!="technical"|level!="user"){
                throw new IllegalArgumentException(functions_op.invalid_argument(lang));
            }else{
                setName(name);
                setPassword(password);
                setLevel(level);
                setLanguage(lang);
            }
        }
        
        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public void setPassword(String password) {
            this.password = password;
        }

        public String getPassword() {
            return password;
        }
        
        public String getLevel() {
            return level;
        }

        public void setLevel(String level) {
            this.level = level;
        }
        public void setLanguage(int lang){
            this.lang = lang;
        }

        public int getLanguage(){
            return lang;
        }
    }
    
    //-------------------------------------------MySQL only    
    //Process CRUD CREATE  
    public void registerUser(String name,
         String password,
         String level,
         int lang){
         try{
            
            user USR= new user(name, password, level,lang);

            if (getConnection().getConnectionState()==true){

                String query = "CALL db_test.SET_USR(?,?,?);"; 
                PreparedStatement pstmt = getConnection().getC().prepareStatement(query);
                pstmt.setString(1,USR.getName()); 
                pstmt.setString(2,USR.getPassword());
                pstmt.setString(3,USR.getLevel());
                pstmt.execute();
                functions_op.state_connection(4,lang);
            }
         }catch(Exception e){
            e.printStackTrace();
            System.out.println(functions_op.invalid_argument(lang));
        }

    }  
    
    //Process CRUD READ  

    
    
    
    
    //Process CRUD UPDATE stage 1
    
    
    
    
    
    //Process CRUD UPDATE stage 2
    private void updateUser(int id,String name,
         String password,
         String level,
         int lang){
         try{
            
             
            user USR= new user(name, password, level,lang);

            if (getConnection().getConnectionState()==true){

                String query = "CALL db_test.UPSET_USR(?,?,?,?);"; 
                
                
                
                
                functions_op.state_connection(4,lang);
            }
         }catch(Exception e){
            e.printStackTrace();
            System.out.println(functions_op.invalid_argument(lang));
        }

    }
    
    //Process CRUD DELETE
    
}
