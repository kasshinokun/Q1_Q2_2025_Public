/*
#------------Teste Java PostgreSQL
# Created 07-01-2024
# Version 1_2024_01_08
*/


/*Java:

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
}
public int getlevel(String name_level){
	String[] level = {"admin","technical","user"};
	return Arrays.asList(level).indexOf(name_level);
}
public void set_user(String name, String password, String level){
	user USER=new user(name,password,getlevel(level));
}
*/

-----------------------------------------------------------------------------------------
-- PostgreSQL:
-- --------------------------------------Database: db_test
CREATE DATABASE IF NOT EXISTS db_test
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Portuguese_Brazil.1252'
    LC_CTYPE = 'Portuguese_Brazil.1252'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;
-- --------------------------------------Tables (Tabelas)--------------------------------
-- MySQL Table Access Level:
-- (PT-BR: MYSQL Tabela Nível de Acesso)
CREATE TABLE IF NOT EXISTS tbl_LVL(
	ID_LVL SERIAL PRIMARY KEY,
    NM_LVL VARCHAR(200) UNIQUE
);

-- MySQL Table Users:
-- (PT-BR: MYSQL Tabela Usuarios)
CREATE TABLE IF NOT EXISTS tbl_USER(
	ID_USER SERIAL PRIMARY KEY,
    NM_USER VARCHAR(200),
    PWD_USER VARCHAR(14) UNIQUE, 
    LVL_USER INT NOT NULL,
	 
    FOREIGN KEY (LVL_USER) REFERENCES tbl_LVL(ID_LVL)
);

-----------------------------------------------------------------------------------------
-----------------------------------CRUD - CREATE
-- PostgreSQL CREATE
-----------Test only (Somente Teste)
SELECT tbl_LVL.ID_LVL FROM tbl_LVL
   WHERE NM_LVL='admin'
-----------End Test (Fim do Teste)

-- EN-US: $<name>$ is a Delimiter equals MySQL Procedures/Functions Delimiter
-- PT-BR: $<nome>$ é um Delimiter igual ao  Delimiter dos Procedimentos/Funções do MySQL
CREATE OR REPLACE PROCEDURE SET_USR(
user_name VARCHAR(200), 
pass_word VARCHAR(14),
lvl_usr VARCHAR(200))
LANGUAGE plpgsql
-- EN-US: if you want use some statement from sql, please use LANGUAGE SQL
-- PT-BR: Se voce desejar usar alguma sintaxe do sql, por favor use LANGUAGE SQL
AS $BODY$
DECLARE
	_user_name VARCHAR(200) := user_name;
	_pass_word VARCHAR(14)  := pass_word;
	_id_level int           :=(SELECT ID_LVL FROM tbl_LVL
   								WHERE NM_LVL=lvl_usr);
BEGIN
   INSERT INTO tbl_USER(NM_USER,PWD_USER,LVL_USER)
   VALUES(_user_name,_pass_word,_id_level);
END;
$BODY$;
-- EN-US: $<name>$ is a Delimiter equals MySQL Procedures/Functions Delimiter
-- PT-BR: $<nome>$ é um Delimiter igual ao  Delimiter dos Procedimentos/Funções do MySQL

-----------------------------------------------------------------------------------------
-----------------------------------CRUD - UPDATE
/*JAVA:
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

-- PostgreSQL UPDATE
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


-----------Test only (Somente Teste)
-- Target(Objetivo):1,'Maria Strong','Sky12345','admin'
UPDATE tbl_USER
   SET NM_USER='Mary Strong',
   PWD_USER='Sky12345',
   LVL_USER=1
   WHERE ID_USER=1;

SELECT * FROM tbl_USER;

-- back to default(retornando ao padrão)  
UPDATE tbl_USER
   SET NM_USER='Mary Wood'
   WHERE ID_USER=1;

SELECT * FROM tbl_USER;

-----------End Test (Fim do Teste)

-- EN-US: $<name>$ is a Delimiter equals MySQL Procedures/Functions Delimiter
-- PT-BR: $<nome>$ é um Delimiter igual ao  Delimiter dos Procedimentos/Funções do MySQL
CREATE OR REPLACE PROCEDURE UPSET_USR(
user_id INT,
user_name VARCHAR(200), 
pass_word VARCHAR(14),
lvl_usr VARCHAR(200)) 
LANGUAGE plpgsql
-- EN-US: if you want use some statement from sql, please use LANGUAGE SQL
-- PT-BR: Se voce desejar usar alguma sintaxe do sql, por favor use LANGUAGE SQL
AS $BODY$
DECLARE
	_id_user_tbl int        := user_id;
	_user_name VARCHAR(200) := user_name;
	_pass_word VARCHAR(14)  := pass_word;
	_id_level int           :=(SELECT ID_LVL FROM tbl_LVL
   								WHERE NM_LVL=lvl_usr);
BEGIN
   UPDATE tbl_USER
   SET NM_USER=_user_name,
   PWD_USER=_pass_word,
   LVL_USER=_id_level
   WHERE ID_USER=_id_user_tbl;
END;
$BODY$;
-- EN-US: $<name>$ is a Delimiter equals MySQL Procedures/Functions Delimiter
-- PT-BR: $<nome>$ é um Delimiter igual ao  Delimiter dos Procedimentos/Funções do MySQL

-----------------------------------------------------------------------------------------
INSERT INTO tbl_LVL(NM_LVL)
VALUES('admin'),('technical'),('user');

SELECT * FROM tbl_LVL;

CALL SET_USR('Mary Wood','Sky12345','admin');

SELECT * FROM tbl_USER;

CALL UPSET_USR(1,'Mary Strong','Sky12345','admin');

SELECT * FROM tbl_USER;
-----------------------------------------------------------------------------------------
/*
PT-BR: Etapas para apagar a base de dados em estágios
EN-US: Steps to delete the database in stages
*/

DROP PROCEDURE IF EXISTS db_test.UPSET_USR;
DROP PROCEDURE IF EXISTS db_test.SET_USR;
DROP TABLE IF EXISTS db_test.tbl_USER;
DROP TABLE IF EXISTS db_test.tbl_LVL;
DROP DATABASE IF EXISTS db_test;