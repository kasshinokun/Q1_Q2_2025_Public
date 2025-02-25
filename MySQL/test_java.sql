#------------Teste Java MySQL
# Created 07-01-2024
# Version 1_2024_01_08

/*JAVA-CREATE:

import java.util.Arrays;
public class user
{
	int id;
    String name;
    String password;
    int level;
	public user(int id,String name, String password, int level){
		this.id=id;
        this.name=name; 
        this.password=password; 
        this.level=level;
    }
}
public int getlevel(String name_level){
	String[] level = {"admin","technical","user"};
	return Arrays.asList(level).indexOf(name_level);
}
public void set_user(int id, String name, String password, String level){
	user=new user(id,name,password,getlevel(level));
}
*/

# MySQL Table Access Level:
# (PT-BR: MYSQL Tabela Nível de Acesso)
CREATE DATABASE IF NOT EXISTS db_test;
CREATE TABLE IF NOT EXISTS db_test.tbl_LVL(
	ID_LVL INT AUTO_INCREMENT,
    NM_LVL VARCHAR(200), 
    PRIMARY KEY (ID_LVL),
    UNIQUE KEY (NM_LVL)
);

# MySQL Table Users:
# (PT-BR: MYSQL Tabela Usuarios)
CREATE TABLE IF NOT EXISTS db_test.tbl_USER(
	ID_USER INT AUTO_INCREMENT,
    NM_USER VARCHAR(200),
    PWD_USER VARCHAR(14), 
    LVL_USER INT NOT NULL,
	PRIMARY KEY (ID_USER),
    UNIQUE KEY (PWD_USER),
    FOREIGN KEY (LVL_USER) REFERENCES db_test.tbl_LVL(ID_LVL)
);

# MySQL CREATE
DELIMITER $$
CREATE PROCEDURE db_test.SET_USR(
user_name VARCHAR(200), 
pass_word VARCHAR(14),
lvl_usr VARCHAR(200)) 
BEGIN
   DECLARE name_usr  VARCHAR(200);
   DECLARE passwd_usr  VARCHAR(14);
   DECLARE id_lvl_usr  INT;
   SET name_usr=user_name;
   SET passwd_usr=pass_word;
   SET id_lvl_usr=(SELECT ID_LVL FROM db_test.tbl_LVL
   WHERE NM_LVL=lvl_usr);
   INSERT INTO db_test.tbl_USER(NM_USER,PWD_USER,LVL_USER)
   VALUES(name_usr,passwd_usr,id_lvl_usr);
END$$
DELIMITER ;
#---------------------------------------------------------------------------------------------------------
/*JAVA-UPDATE:
import java.util.Arrays;
public class user
{
    String name;
    String password;
    int level;
	public user(String name, String password, int level){
        this.name=name; 
        this.password=password; 
        this.level=level;
    }
	public void setName(String name){
        this.name=name;
	}
}
public int getlevel(String name_level){
	String[] level = {"admin","technical","user"};
	return Arrays.asList(level).indexOf(name_level);
}
public class list_user{
	ArrayList<user> list_users;
    int n; //Number of stored values inside arraylist(numero de valores contidos no arraylist)
    public list_user(){
		this.list_users=new ArrayList<user>();
        this.n=0;
    }
    public void set_list(user USER){
		this.list_users.add(USER);
        this.n=n+1;
    }
    public void upset_list(int id, user USER){
		id=id-1;//Index start in 0 not in 1(o indice começa em 0 e não em 1)
        this.list_users.add(id,USER);
    }
}
public void upset_user(int id,String name, String password, String level){
	user USER=new user(name,password,getlevel(level));
	list_user LIST_USR=new list_user();
	LIST_USR.set_list(user USER);
	USER.setName('Mary Strong');
	LIST_USR.upset_list(0,user USER);
}
*/

# MySQL UPDATE
/*EN-US
To make it easier, the best option is to use UPDATE
as well as SELECT, as it will make programming within Java
and MySQL easier.
*/
/*PT-BR
Para tornar mais facil, a melhor opção é usar o UPDATE
igual ao SELECT, pois facilitará a programação dentro do Java
e do MySQL
*/
DELIMITER $$
CREATE PROCEDURE db_test.UPSET_USR(
user_id INT,
user_name VARCHAR(200), 
pass_word VARCHAR(14),
lvl_usr VARCHAR(200)) 
BEGIN
   
   DECLARE name_usr  VARCHAR(200);
   DECLARE passwd_usr  VARCHAR(14);
   DECLARE id_lvl_usr  INT;
   
   SET name_usr=user_name;
   SET passwd_usr=pass_word;
   SET id_lvl_usr=(SELECT ID_LVL FROM db_test.tbl_LVL
   WHERE NM_LVL=lvl_usr);
   
   UPDATE db_test.tbl_USER
   SET NM_USER=name_usr,
   PWD_USER=passwd_usr,
   LVL_USER=id_lvl_usr
   WHERE ID_USER=user_id;
END$$
DELIMITER ;

INSERT INTO db_test.tbl_LVL(NM_LVL)
VALUES('admin'),('technical'),('user');

SELECT * FROM db_test.tbl_LVL;

CALL db_test.SET_USR('Mary Wood','Sky12345','admin');

SELECT * FROM db_test.tbl_USER;

CALL db_test.UPSET_USR(1,'Mary Strong','Sky12345','admin');

SELECT * FROM db_test.tbl_USER;

/*
PT-BR: Etapas para apagar a base de dados em estágios
EN-US: Steps to delete the database in stages
*/

DROP PROCEDURE IF EXISTS db_test.UPSET_USR;
DROP PROCEDURE IF EXISTS db_test.SET_USR;
DROP TABLE IF EXISTS db_test.tbl_USER;
DROP TABLE IF EXISTS db_test.tbl_LVL;
DROP DATABASE IF EXISTS db_test;