package TP_AED_3_2023.file;

//importa as bibliotecas necessarias
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

//importa funções e procedimentos do package
import TP_AED_3_2023.functions.*;
import TP_AED_3_2023.file.*;
import TP_AED_3_2023.object.*;

public class Procedures_1 {
//===adaptações para escrita em posições designadas no arquivo binario===========================   
    private static void read(String path, int condition){//leitura combinada para processos Read, Update e Delete
        
        int op=0;
        
        if(condition==2||condition==3||condition==4){
            
            do{
                System.out.print("\nPor favor digite uma ID para buscar:______");
                op=Functions.only_Int();
            }while(op<=0);
        
        }
        //Declarando objetos
        RandomAccessFile raf=null;//Stream para leitura     
        byte[] arr;//vetor de bytes
        obj i=new obj();//objeto para receber os valores
        
        try{
            raf=new RandomAccessFile(path,"rw");//instancia pelo caminho recebido
             
            int size;//variavel para tamanho do vetor 
            
            raf.seek(0);
            
            int h1=raf.readInt();
            System.out.println(Changes.set_Locale("\nCabeçalho do arquivo = " + h1));
            boolean resp=true;
            
            while(raf.getFilePointer()<raf.length()){
                try{
                    long posReg=raf.getFilePointer();//coleta a posição do cabeçalho
                    
                    char c1=raf.readChar();//leitura do caracter de validação de registro
                    if(c1=='*'){
                        System.out.print("\nCarregando registros...."+posReg);            
                        
                        size=raf.readInt();//Leitura para definir o tamanho do vetor de bytes
                        arr=new byte[size];//Instancia um novo vetor de bytes 
                        raf.read(arr);//leitura do vetor
                        
                        i.fba(arr);//recebe o retorno a partir da função
                        
                        if(condition==1){
                        //se condition codificada para ler todos os registros(codigo interno da aplicação)    
                            Procedures_1.ToString(i);//exibe por procedimento generico 
                        }
                        else if(condition>1){
                            
                            if(condition==2&i.getId()==op){
                            //se for ID buscada e condition codificada para busca unica(codigo interno da aplicação)
                                System.out.print("\n\nBusca: ID "+op+" localizado.");
                                Procedures_1.ToString(i);//print by generic procedure
                                resp=false;
                                break;
                            }
                            else if(condition==3&i.getId()==op){
                            //se for ID buscada e condition codificada para atualização(codigo interno da aplicação)
                                System.out.print(Changes.set_Locale("\n\nAtualização: ID "+op+" localizado."));
                                Procedures_1.ToString(i);//print by generic procedure
                                editRegistry("",i,2);
                                
                                
                                byte arr2[]=i.tba();//cria e atribui valor a vetor
                                int size2=arr2.length;//novo tamanho de vetor
                                
                                //Processo de atualização
                                if(size2>size){//se maior .....
                                    //busca a posição do registro
                                    raf.seek(posReg);

                                    //muda a lapide para '$'
                                    raf.writeChar('$');//escrever mudando a lapide para apagar

                                    //localiza o fim do arquivo
                                    long tail=find_end(raf);
                                    
                                    //escrever no fim do arquivo
                                    write_raf(tail,arr2,'*',size2,raf);

                                    // mensagem de feedback
                                    System.out.println("\nRegistro foi atualizado e armazenado no fim do arquivo.");

                                }else {
                                	                                   
                                    raf.seek(posReg);//Segue para aposição designada
                                    
                                    write_raf(posReg,arr2,'*',size,raf);//Escreve o registro
				    
                                    System.out.println("\nRegistro foi atualizado no local.\n");

                                } 
                                
                                resp=false;//muda variavel e encerra
                                break;
                            }
                            else if(condition==4&i.getId()==op){
                                //se for ID buscada e condition codificada para exclusão(codigo interno da aplicação)
                                System.out.print(Changes.set_Locale("\n\nExclusão: ID "+op+" localizado."));
                                Procedures_1.ToString(i);//print by generic procedure
                                
                                //busca a posição do registro
                                raf.seek(posReg);
                                
                                //muda a lapide para '$'
                                raf.writeChar('$');//escrever mudando a lapide para apagar

                                System.out.println("Registro ID: "+op+" deletado");
                                resp=false;//muda variavel e encerra
                                break;
                            }
                        }
                        
                    }else{ 
                        
                        raf.getFilePointer();//Busca a próxima posição
                        
                        //Tentativas de corrigir o erro de update no local
                        //numero 1
                        /*while(raf.readByte()==0&raf.getFilePointer()<raf.length()){
                            raf.getFilePointer();
                        }*/
                        //numero 2
                        //raf.skipBytes(raf.readInt());//Funciona apenas com exclusão
                    }
                    
                }catch (EOFException eof) {
                    System.out.println(Changes.set_Locale("\nFim do arquivo alcançado."));
                    break;
                } catch (IOException g) {
                    System.out.println(Changes.set_Locale("\nErro no processo de leitura."));
                    break;
                }
            }if((condition==2||condition==3||condition==4)&resp==true){
                System.out.println(Changes.set_Locale("\nRegistro: ID "+op+" não localizado."));
            }
        //tratamento de exceções   
        } catch (IOException e) {
            System.out.println(Changes.set_Locale("\nArquivo não existe."));
        } finally {
            try {
                if(raf!=null){
                    raf.close();
                }
            } catch (IOException f) {
                f.printStackTrace();
            }
        }
    }
    private static void editRegistry(String path,obj i,int condition){//Criação e Edição de registro combinada(Create, Update)
       
        if(condition==1){//novo registro
            try{
                
                RandomAccessFile raf = new RandomAccessFile(path,"rw");
                
                int id=getHeader(path);//recebe o valor atualizado para o cabeçalho
                i.setId(++id);
                System.out.println("\nCriando novo registro:");
                System.out.print("\nID---------------------------------: "+Functions.format_id(i.getId())+"\n");
                
                System.out.print("\nAno--------------------------------: ");
                i.setTour_y(Functions.only_Int(),2); 
                System.out.print( "Data do Tour de France-------------: ");
                i.set_Date(Functions.read_data(Functions.reading(),i.getTour_y()));
                System.out.print(Changes.set_Locale("Número do Tour de France-----------: "));
                i.setTour_n(Functions.only_Int()); 
                System.out.print( "Nome do Vencedor-------------------: ");
                i.setTour_w(Functions.reading()); 
                System.out.print(Changes.set_Locale("País do Vencedor-------------------: "));
                i.setRider_c(Functions.reading()); 
                System.out.print( "Equipe do Vencedor-----------------: ");
                i.setRider_t(Functions.reading()); 
                System.out.print(Changes.set_Locale( "Distância do Tour de France(km)----: "));
                i.setTour_l(Functions.only_Int());  
                System.out.print( "Idade------------------------------: ");
                i.setRider_a(Functions.only_Int());  
                System.out.print( "BMI do Ciclista--------------------: ");
                i.setRider_b(Functions.only_Float()); 
                System.out.print( "Peso(Kg)---------------------------: ");
                i.setRider_w(Functions.only_Int()); 
                System.out.print( "Altura (metros)--------------------: ");
                i.setRider_h(Functions.only_Double()); 
                System.out.print( "Tipo do Atleta---------------------: ");
                i.setRt_PPS(Functions.reading()); 
                System.out.print( "Modalidade do Atleta---------------: ");
                i.setCrt_PPS(Functions.reading());
                Procedures_1.ToString(i);//Exibe registro
                create(i);//salvando registro
                
                   
            }
            catch(IOException f) {
                System.out.println(Changes.set_Locale("\nErro na análise do arquivo "+path+".")); 
            }
            
            
            
        }else{
            System.out.print(Changes.set_Locale("\nEdição de registro:"));
            System.out.print("\nID Atual---------------------------: "+i.getId());
            System.out.print("\nAno Atual--------------------------: "+i.getTour_y());
            System.out.print("\nAno--------------------------------: ");
            i.setTour_y(Functions.only_Int(),2); 
            System.out.print( "\nData Atual do Tour de France-------: "+i.get_Date());
            System.out.print( "\nData do Tour de France-------------: ");
            i.set_Date(Functions.read_data(Functions.reading(),i.getTour_y()));
            System.out.print(Changes.set_Locale("\nNúmero Atual do Tour de France-----: "+i.getTour_n()));
            System.out.print(Changes.set_Locale("\nNúmero do Tour de France-----------: "));
            i.setTour_n(Functions.only_Int()); 
            System.out.print("\nNome Atual do Vencedor-------------: "+i.getTour_w());
            System.out.print( "\nNome do Vencedor-------------------: ");
            i.setTour_w(Functions.reading()); 
            System.out.print(Changes.set_Locale("\nPaís Atual do Vencedor-------------: "+i.getRider_c()));
            System.out.print(Changes.set_Locale("\nPaís do Vencedor-------------------: "));
            i.setRider_c(Functions.reading()); 
            System.out.print("\nEquipe Atual do Vencedor-----------: "+i.getRider_c());
            System.out.print( "\nEquipe do Vencedor-----------------: ");
            i.setRider_t(Functions.reading()); 
            System.out.print(Changes.set_Locale("\nDistância Atual do Tour de France--: "+i.getTour_l()));
            System.out.print(Changes.set_Locale("\nDistância do Tour de France(km)----: "));
            i.setTour_l(Functions.only_Int());  
            System.out.print("\nIdade Atual -----------------------: "+i.getRider_a());
            System.out.print( "\nIdade------------------------------: ");
            i.setRider_a(Functions.only_Int());  
            System.out.print( "\nBMI Atual do Ciclista--------------: "+i.getRider_b());
            System.out.print( "\nBMI do Ciclista--------------------: ");
            i.setRider_b(Functions.only_Float()); 
            System.out.print( "\nPeso Atual (Kg)--------------------: "+i.getRider_w());
            System.out.print( "\nPeso(Kg)---------------------------: ");
            i.setRider_w(Functions.only_Int()); 
            System.out.print( "\nAltura Atual (metros)--------------: "+i.getRider_h());
            System.out.print( "\nAltura (metros)--------------------: ");
            i.setRider_h(Functions.only_Double()); 
            System.out.print( "\nTipo Atual do Atleta---------------: "+i.getRt_PPS());
            System.out.print( "\nTipo do Atleta---------------------: ");
            i.setRt_PPS(Functions.reading()); 
            System.out.print( "\nModalidade Atual do Atleta---------: "+i.getCrt_PPS());
            System.out.print( "\nModalidade do Atleta---------------: ");
            i.setCrt_PPS(Functions.reading());
        
        }
    }
    //processo de escrita
    public static void write_raf(long pos, byte[]arr,char x,int size, RandomAccessFile raf){
        
        try{
        
            raf.seek(pos);//busca a posição designada no arquivo

            raf.writeChar(x);//escreve o caracter lapide
            
            raf.writeInt(size);//escreve o tamanho do vetor

            raf.write(arr);//escreve o vetor no arquivo
            
        }catch(IOException e){
        
        
        }
    
    }
//===adaptações para localizar posições no arquivo binario=======================================
    //identificação do valor do cabeçalho
    
    //atualiza o cabeçalho do arquivo
    //obtendo o fim do arquivo
    public static long find_end(RandomAccessFile raf){
        long tail=0;
        try{
            tail=(long)raf.length();
        }catch(IOException e){//exceções dentro do processo
                
        }
        return tail;//retorna o valor do fim do arquivo(EOF)
    }
//===adaptações para fora da classe==============================================================
    public static<T> void ToString(T x){
       System.out.println("\n"+x.toString());//exibe objeto
    }
    public static<T> String getC_T(T x){
       return x.getClass().getSimpleName();//Obtem o nome da classe  a partir do objeto
    }
//===========Criação de arquivo binário - Operações CRUD=========================================
    public static void create_one(){//cria apenas um registro no fim do arquivo binario
        editRegistry("src/data/tour.db",new obj(),1);
    }
    private static void create(obj user){
        try{
            String path="src/data/tour.db";
            RandomAccessFile file = new RandomAccessFile(path, "rw");
            
            //Não há tratativa para registro duplicado com ID diferente
            file.writeInt(user.getId());//Atualiza o cabeçalho
            
            char tombstone='*';
            byte[] arr=user.tba();
            int size=arr.length;
            long tail=find_end(file);
            
            write_raf(tail, arr,tombstone,size,file);
            
        }catch(IOException e) {
        
        }
		
    }
//===========Busca em arquivo binário - Operações CRUD===========================================
    public static void searchAll(){
    //procedimento para leitura de todos os registros dentro do arquivo binario
        String path="src/data/tour.db";
        if(Files.exists(Paths.get(path))){
            System.out.println("\nArquivo "+path+" localizado.");
            read(path,1);//leitura dos registros
        }else{
            System.out.println(Changes.set_Locale("\nArquivo "+path+" não localizado."));
        }
    }
    public static void search(){//procedimento para busca de registro dentro do arquivo binario
        read("src/data/tour.db",2);
    }
//===========Atualização em arquivo binário - Operações CRUD=====================================    
    public static void update(){//procedimento para atualização de registro dentro do arquivo binario
        read("src/data/tour.db",3);
    }
//===========Exclusão em arquivo binário - Operações CRUD========================================
    //do registro
    public static void delete(){//procedimento para deleção registro dentro do arquivo binario
        read("src/data/tour.db",4);
    }
    //do proprio arquivo
    public static void delete_All(String path){//procedimento para chamar deleção do arquivo binario
        
        try{
            Files.delete(Paths.get(path));
            System.out.println("\nArquivo Deletado com sucesso.");  
        }
	catch (IOException e) {
	    System.out.println(Changes.set_Locale("\nErro no processo de exclusão."));
	}
        System.out.println("\nRetornando ao Menu Principal.....");
    }
//===========Arquivo CSV - Criação de arquivo binário============================================
    public static void create_from_file(){
        //criar o arquivo binario a partir de um arquivo csv designado
        String file="src/data/tour.csv";
        int op;
        do{
            System.out.println(Changes.set_Locale("\n1) Olá, deseja ler o arquivo base?"));
            System.out.println("2) Ou posso buscar o arquivo base");
            System.out.println("em Documentos?");
                       
            System.out.println("\n0) Caso queira retornar aperte [0]");
            System.out.print(Changes.set_Locale("\nPor favor escolha uma opção:"));
            op=Functions.only_Int();
            switch(op){
                case 1:
                    System.out.println(Changes.set_Locale("\nProcesso Padrão"));
                    seek_default();
                    op=0;
                    break;
                    
                case 2:
                    System.out.println("\nProcesso Customizado");
                    seek_custom();
                    op=0;
                    break;
                case 0:
                    System.out.println("\nRetornando ao Menu Inicial.....");
                    break;
                default:
                    System.out.println("\nTente novamente!");
            }
        }while(op!=0);
        
        
    }//Processo padrão
    private static void seek_default(){
        
        System.out.println("\nBuscando .......");
        String path="src/data/tour.csv";
        boolean resp=Files.exists(Paths.get(path));
        if(resp==true){
            System.out.println("\nArquivo "+path+" localizado.");
            read_csv(path);
            
        }
        else{
            System.out.print(Changes.set_Locale("\nArquivo "+path+" não localizado.\n"));
        
            System.out.println("\nPosso tentar criar do backup?");
            System.out.println("\n1) Executar\nPara sair aperte qualquer tecla");
            int op=Functions.only_Int();
            if(op==1){
                load_backup();
            }else{
                System.out.println(Changes.set_Locale("\nRestauração abortada."));
            }
        }
        System.out.println("\nEncerrando procedimento......");
    }//Customizado
    private static void seek_custom(){//busca o arquivo csv na pasta documentos em qualquer sistema
        System.out.println("\nCustom");
        
        String userP=(System.getProperty("user.home").concat("/Documents/tour.csv"));
        System.out.println("\nBuscando ......."+userP);
        
        boolean resp=Files.exists(Paths.get(userP));
        if(resp==true){
            System.out.println("\nArquivo "+userP+" localizado.");
            read_csv(userP);
        }
        else{
            System.out.println("\nArquivo "+userP+" nao localizado.\n");
        
            System.out.println("\nPosso tentar criar do backup?");
            System.out.println("\n1) Executar\nPara sair aperte qualquer tecla");
            int op=Functions.only_Int();
            if(op==1){
                load_backup();
            }else{
                System.out.println(Changes.set_Locale("\nRestauração abortada."));
            }
        }
        System.out.println("\nEncerrando procedimento......");
    }
    //Extras==================================================================================
    private static void load_backup(){//recria o arquivo a partir do backup
        boolean resp=false;
        System.out.println("\nEm desenvolvimento, ver codigos no final da classe functions");
        String path="src/data/tour_2.csv";//localização para restaurar
        
        Restore.restoreCSV(path);//restaura o arquivo a partir de um arquivo .db
        
        resp=Files.exists(Paths.get(path));//Analisa se o arquivo existe
        
        if(resp==true){//se for possivel restaurar
            System.out.println("\nArquivo "+path+" restaurado.");
            read_csv(path);
        }  
    }
    
    //Leitura do arquivo csv==================================================================
    private static void read_csv(String path){//leitura do arquivo base e começa a escrita
        try{
            
            RandomAccessFile file = new RandomAccessFile(path,"r");
            
            
	    String[] data;
            obj user=new obj(); 
            
            file.readLine();//leitura para ignora o cabeçalho do arquivo
	    
            while (true) {
                //configura e divide os futuros atributos
                data = file.readLine().replace(",",".").split(";");
	        int id=getHeader("src/data/tour.db");//recebe o valor presente no cabeçalho
                //Instancia e atribui valores
                user.setObj(++id,
                		Integer.parseInt(data[0]),
                		1,
                        data[1],
                        Integer.parseInt(data[2]),
                        data[3],
                        data[4],
                        data[5],
                        Integer.parseInt(data[6]),
                        Integer.parseInt(data[7]),
                        Float.parseFloat(data[8]),
                        Integer.parseInt(data[9]),        
                        Double.parseDouble(data[10]),
                        data[11],
                        data[12]);
                create(user);//escreve os registros
		
                ToString(user);//mostra o registro para feedback
	    }
	       
        }catch(EOFException | NullPointerException e){
            System.out.println("\nLeitura finalizada do arquivo.");
           
        }catch (NoSuchFileException f) {
            System.out.println(Changes.set_Locale("\nArquivo/Pasta não encontrado(a)."));
        }catch(IOException e){
            System.out.println("\nErro na leitura do arquivo.");
        }
        
    }
    //Adaptação em breve
    private static int update_header(RandomAccessFile raf){
        
        int head=0;
        int h1=head;
        
        try{
        
            raf.seek(0);
            
            head=raf.readInt();
            
            boolean resp=true;
            
            while(raf.getFilePointer()<raf.length()){
                try{
                    char c1=raf.readChar();//leitura do caracter de validação de registro
                    if(c1=='*'){               
                    
                        obj i=new obj();
                        
                        int size=raf.readInt();//Leita para definir o tamanho do vetor de bytes
                        
                        byte[] arr=new byte[size];//Instancia um novo vetor de bytes 
                        
                        raf.read(arr);//leitura do vetor
                        
                        i.fba(arr);//recebe o retorno a partir da função
                        
                        h1=i.getId();//lê a ID do objeto e atualiza
                        
                        //System.out.print("\nCarregando...."+Functions.percent(h1, head)+" %.");//feedback para o usuario
                        
                    }else{
                        raf.skipBytes(raf.readInt());
                    }

                } catch (EOFException eof) {
                    System.out.println(Changes.set_Locale("\nFim do arquivo alcançado."));
                    break;
                } catch (IOException g) {
                    System.out.println(Changes.set_Locale("\n1_Arquivo não existe."));
                    break;
                }
            }
        }catch (EOFException eof) {
            System.out.println(Changes.set_Locale("\nAtualização de ID concluída com sucesso."));
        }
        catch (IOException e) {
            System.out.println("\nErro durante o processo solicitado.");
        } finally {
            try {
                if(raf!=null){
                    raf.close();
                }
            } catch (IOException f) {
                System.out.println("\nErro durante o processo solicitado.");
            }
        }
        
        return h1;//retorna o valor atualizado para o cabeçalho do arquivo
    }
    public static int getHeader(String path){//Identificação do valor no cabeçalho
        int id=0;
        try{
            RandomAccessFile raf=new RandomAccessFile(path,"r");
            raf.seek(0);
            id=raf.readInt();//Leitura para definir o cabeçalho
            
        }catch(IOException e){
            System.out.println("\nAdequando processos.......\n");
            
            //e.printStackTrace();
            
        }
        return id;//retorna o valor encontrado no cabeçalho
    }
    
}
