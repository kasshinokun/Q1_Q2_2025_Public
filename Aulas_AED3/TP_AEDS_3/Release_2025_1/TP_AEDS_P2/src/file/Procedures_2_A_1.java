package file;

//importa as bibliotecas necessarias
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

//importa funções e procedimentos do package
import functions.*;
import file.*;
import static file.Procedures_2_A_2.delete;
import index.*;
import object.*;

//funções especificas para o indice
import static file.Procedures_2_A_2.getHeaderIndex;
import static file.Procedures_2_A_2.prelude_delete;
import static file.Procedures_2_A_2.writeIndex;

public class Procedures_2_A_1 {
    
    static String path_w="src/data/indexed/tour_byte.db";
    
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
        String path="src/data/tour.csv";//localização para restaurar
        
        Restore.restoreCSV(path);//restaura o arquivo a partir de um arquivo .db
        
        resp=Files.exists(Paths.get(path));//Analisa se o arquivo existe
        
        if(resp==true){//se for possivel restaurar
            System.out.println("\nArquivo "+path+" restaurado.");
            read_csv(path);
        }  
    }
    
    //Leitura do arquivo csv==================================================================
    public static void read_csv(String path){//leitura do arquivo base e começa a escrita
        try{
            
            RandomAccessFile file = new RandomAccessFile(path,"r");
            
            String[] data;
            Winner user=new Winner(); 
            
            file.readLine();//leitura para ignora o cabeçalho do arquivo
	    
            while (true) {
                //configura e divide os futuros atributos
                data = file.readLine().replace(",",".").split(";");
	        //codigo para id(em desenvolvimento)
                user.setWinner(Integer.parseInt(data[0]),1,
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
                int id=getHeaderIndex();
                System.out.print("\nID---------------------------------: "+Functions.format_id(++id));
                Procedures_1.ToString(user);//mostra o registro para feedback
                //código para escrever os registros        
		writeWinner(user,1,id,0);
                
	    }
	       
        }catch(EOFException | NullPointerException e){
            System.out.println("\nLeitura finalizada do arquivo.");
           
        }catch (NoSuchFileException f) {
            System.out.println(Changes.set_Locale("\nArquivo/Pasta não encontrado(a)."));
        }catch(IOException e){
            System.out.println("\nErro na leitura do arquivo.");
        }
        
    }
 //=======================================================================================================================================   
    //Processo CRUD
    //Edição-Criação ou Atualização de objeto
    public static void create_one(){
        
        editRegistry(0,new Winner (),1);
        
    }
    private static void editRegistry(int id,Winner i,int condition){
        
        if(condition==1){//Criação de novo registro
            
                
                                
            System.out.println("\nCriando novo registro:");
            id=getHeaderIndex();
            System.out.print("\nID---------------------------------: "+Functions.format_id(++id));
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
            Procedures_1.ToString(i);//mostra o registro para feedback
            writeWinner(i,1,id,0);//escreve o registro       
        }
        else{//Atualização de registro
            System.out.print(Changes.set_Locale("\nEdição de registro:"));
            System.out.print("\nID Atual---------------------------: "+Functions.format_id(id));
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
            Procedures_1.ToString(i);//mostra o registro para feedback
                
        }
    }
    public static void writeWinner(Winner i,int condition,int id,long pointer){
        //Declarando objetos
        RandomAccessFile raf=null;//Stream para leitura    
        try{
            
            raf=new RandomAccessFile(path_w,"rw");
            
            if(condition==1){
                //muda a posição para o fim
                pointer=Procedures_1.find_end(raf);
            }else{
            
            }
            raf.seek(pointer);
            byte[]arr=i.tba();
            raf.writeByte(arr.length);
            raf.write(arr);
            writeIndex(id,pointer,1,0);
        }catch(IOException f){
            
            //System.out.println("\nErro.");
        }
    }
    
    public static void readWinner(int id,long position,int condition){
        //Declarando objetos
        RandomAccessFile registry=null;//Stream para leitura     
        try{
            
            registry=new RandomAccessFile(path_w,"rw");
            registry.seek(position);
                
            int size=(int)registry.readByte();
            byte[]arr=new byte[size];
            registry.read(arr);
            Winner w=new Winner();
            w.fba(arr);
            Procedures_1.ToString(w);
            if(condition==2){
                editRegistry(id,w,2);//envia para alterar
                //Recria o vetor de bytes
                byte[]arr2=w.tba();
                int size2=arr2.length;
                //compara os tamanhos
                if(size<size2){
                    position=registry.length();
                    registry.seek(registry.length());
                    registry.writeByte(size2);
                    registry.write(arr2);
                }else{
                    
                    delete(registry,position,size);//Exclusão física
                    registry.writeByte(size2);//escreve o tamanho do novo vetor
                    registry.write(arr2);//escreve o objeto
                
                }
            }else if(condition==3){
                int op=prelude_delete(2);
                if(op==2){
                    size++;//incrementa em 1
                    delete(registry,position,size);//Exclusão física
                    //Feedback, pois esta parte é isolada do gestor de indice
                    System.out.println(Changes.set_Locale("Na proxima etapa, será necessário apagar o índice."));
                }
            }   
          
        }catch(IOException f){
            f.getMessage();
            //System.out.println("\nErro.");
        }
    }
    public static void delete_Registry(){//procedimento para chamar deleção do arquivo binario
        
        try{
            Files.delete(Paths.get(path_w));
            System.out.println("\nArquivo "+path_w+" Deletado com sucesso.");  
        }
	catch (IOException e) {
	    System.out.println(Changes.set_Locale("\nErro no processo de exclusão."));
	}
        System.out.println("\nRetornando ao Menu Principal.....");
    }
    
    
    
    
    
    
}
