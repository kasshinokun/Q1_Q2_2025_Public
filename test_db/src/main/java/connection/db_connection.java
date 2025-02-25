package connection;
import java.sql.*;
import javax.sql.*;
import javax.naming.*;
/**
 * @version 1_2025_01_06
 * @co-author Gabriel da Silva Cassino
 */

//With:
//==========Source URL:https://www.devmedia.com.br/classe-generica-para-conexao-com-db_connection-e-mysql/5492
/**
*
* @author mayron
 Modded by Gabriel to show functions_op based on setted language
*/
public class db_connection {

    private String local;
    private String user;
    private String password;
    private Connection c;
    private Statement statement;
    private String str_conection;
    private String driverjdbc;
    private boolean state;
    private int lang; //Modification to set language
    
    public db_connection(String bd, String local, String door,
    String str_database, String user, String password, int lang) {
        if (bd.equals("PostgreSQL")){
            setLanguage(lang); 
            setConnectionState(false);
            setStr_conection("jdbc:postgresql://"+ local +":" + door +"/"+ str_database);
            setLocal(local);
            setPassword(password);
            setUser(user);
            setDriverjdbc("org.postgresql.Driver");
        }else {
            if (bd.equals("MySQL")) {
                setLanguage(lang);
                setStr_conection("jdbc:mysql://"+ local +":" + door +"/"+ str_database);
                setLocal(local);
                setPassword(password);
                setUser(user);
                setDriverjdbc("com.mysql.cj.jdbc.Driver");
            }
        }
    }
    
    public void configUser(String user, String password) {
        setUser(user);
        setPassword(password);
    }

    public void configLocal(String str_database) {
        setLocal(str_database);
    }

    //Conection with database
    public void connect(){
        try {
            Class.forName(getDriverjdbc());
            setC(DriverManager.getConnection(getStr_conection(), getUser(), getPassword()));
            setStatement(getC().createStatement());
            //Feedback if opened connection with sucess
            functions_op.state_connection(3, getLanguage());
            setConnectionState(true);
        }
        catch(ClassNotFoundException e) {
            // Fail if JDBC driver wasn't installed
            functions_op.state_connection(0, getLanguage());
            e.printStackTrace();
        }catch (SQLException e) {
            // Fail if it have problems to conect with database
            functions_op.state_connection(1, getLanguage());
            e.printStackTrace();

        }catch (Exception e) {
            // Fail if it have problems on execution process
            functions_op.state_connection(2, getLanguage());
            System.err.println(e);
            e.printStackTrace();
        }
    }

    public void disconect(){
        try {
            getC().close();
            //Feedback if closed connection with sucess
            functions_op.state_connection(4, getLanguage());
        }catch (SQLException e) {
            // Fail if it have problems to conect with database
            functions_op.state_connection(1, getLanguage());
            e.printStackTrace();
        }
    }
    //To get ResultSet return from database
    public ResultSet getResultSet(String query){
        try {
            return getStatement().executeQuery(query);
        }catch (SQLException e) {
            // Fail if it have problems to conect with database
            functions_op.state_connection(1, getLanguage());
            e.printStackTrace();
            return null;
        }
    }
    // GETs AND SETs
    public void setConnectionState(boolean state){
        this.state=state;
    }
    
    public boolean getConnectionState(){
        return this.state;
    }
    
    public void setLanguage(int lang){
        this.lang = lang;
    }
    
    public int getLanguage(){
        return this.lang;
    }
    
    public String getLocal() {
        return this.local;
    }

    public void setLocal(String local) {
        this.local = local;
    }

    public String getUser() {
        return this.user;
    }

    public void setUser(String user) {
        this.user = user;
    }

    public String getPassword() {
        return this.password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public Connection getC() {
        return this.c;
    }

    public void setC(Connection c) {
        this.c = c;
    }

    public Statement getStatement() {
        return this.statement;
    }

    public void setStatement(Statement statement) {
        this.statement = statement;
    }

    public String getStr_conection() {
        return this.str_conection;
    }

    public void setStr_conection(String str_conection) {
        this.str_conection = str_conection;
    }

    public String getDriverjdbc() {
        return this.driverjdbc;
    }

    public void setDriverjdbc(String driverjdbc) {
        this.driverjdbc = driverjdbc;
    }
}
