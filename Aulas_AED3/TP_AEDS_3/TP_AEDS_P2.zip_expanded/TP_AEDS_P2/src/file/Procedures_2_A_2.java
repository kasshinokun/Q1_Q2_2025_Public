package file;

import file.*;
import functions.*;

import index.*;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

public class Procedures_2_A_2 {
    static String path_i="src/data/indexed/index_byte.db";//caminho padrão do indice
    public static int getHeaderIndex(){
        int id=0;
        try{
            RandomAccessFile raf=new RandomAccessFile(path_i,"r");
            File index = new File(path_i);
            if(index.exists()){
                raf.seek(0);
                int size=(int)raf.readByte();//Leita para definir o tamanho do vetor de bytes
                byte[] arr=new byte[size];//Instancia um novo vetor de bytes 
                raf.read(arr);//leitura do vetor
                H_Index h=new H_Index();
                h.fba(arr);
                id=h.getIndexId();//Por hora, será necessário somente a Id para Feedback para o usuário
                
                
            }              
        }catch(IOException e){
            e.getMessage();
        
        }
        return id;
    }
    private static void updateHeaderIndex(RandomAccessFile raf,int id,long pos,long find)
            throws IOException,FileNotFoundException{
        
        raf.seek(0);
        H_Index i=new H_Index(id,pos,find);
        byte[]arr=i.tba();
        raf.writeByte(arr.length);
        raf.write(arr);
        
    }
    public static void writeIndex(int id,long pos,int condition,long pointer){
        //Declarando objetos
        RandomAccessFile raf=null;//Stream para leitura    
        try{
            byte b=(byte)0;
            if(condition==1){//Apenas grava um registro
                raf=new RandomAccessFile(path_i,"rw");

                updateHeaderIndex( raf, id, pos,raf.length());//Atualiza o cabeçalho do índice

                raf.seek(raf.length());//busca o fim do arquivo
                
                b++;//transforma o valor de 0 para 1
                
            }else if(condition==2){//atualiza em posição designada
                raf.seek(pointer);//Vai para posição designada
                
                b++;
                
                if(id==getHeaderIndex()){//se for o ultimo registro
                    updateHeaderIndex(raf,id,pos,pointer);//Atualiza o cabeçalho              
                }
            }
            else if(condition==3){//Exclusão Lógica
                
                raf.seek(pointer);
            
            }
            
            C_Index k=new C_Index(id,b,pos);//instancia o objeto

            byte[]arr2=k.tba();//instancia o vetor de bytes a partir do objeto
            raf.writeByte(arr2.length);//escreve o tamanho em byte
            raf.write(arr2);//escreve o objeto
            
        }catch(IOException f){
            f.getMessage();
            
        }  
    }
    public static void readIndex(int condition){
        //Declarando objetos
        RandomAccessFile index=null;//Stream para leitura     
        int op=0;//variavel para entrada
        long pointer;//ponteiro das posiçoes no indice
        
        if(condition==2||condition==3||condition==4){
            
            do{
                System.out.print("\nPor favor digite uma ID para buscar:______");
                op=Functions.only_Int();
            }while(op<=0);
        
        }
        try{
            index=new RandomAccessFile(path_i,"r"); 
            index.seek(0);
            int size=(int)index.readByte();//Leita para definir o tamanho do vetor de bytes
            byte[] arr=new byte[size];//Instancia um novo vetor de bytes 
            index.read(arr);//leitura do vetor
            H_Index h=new H_Index();
            h.fba(arr);
            if(op==h.getIndexId()){
                int id=h.getIndexId();
                long pos=h.getIndexPos();
                long find=h.getFind();//armazena o local
                //exibe a ID
                System.out.print("\nID---------------------------------: "+Functions.format_id(id));
                if(condition==2){//Busca específica 
                    //Exibe o registro solicitado
                    Procedures_2_A_1.readWinner(0,pos,1);
                }else if(condition==3){//Atualização
                    //Exibe o registro solicitado
                    Procedures_2_A_1.readWinner(id,pos,2);
                    writeIndex(id,pos,2,find);//escreve o registro
                }else{//Exclusão
                    //Exibe o registro solicitado
                    Procedures_2_A_1.readWinner(0,pos,3);
                    //Chama o processo de exclusão
                    
                    op=prelude_delete(1);//processo de escolha de exclusão
                    op=0;//Zera a variavel
                    if(op==1){
                        //Exclusão lógica
                        writeIndex(id,pos,3,find);//repassa os parametros

                    }else{
                        size++;//incrementa em 1
                        delete(index,find,size);//Exclusão física
                    }
                }
                
            }else{
                System.out.println("Posição Inicial: 0");
                boolean resp=false;//para análise final das buscas durante a leitura
                while(true){
                    pointer=index.getFilePointer();
                    //System.out.println("Posição: "+pointer);
                    int size2=(int)index.readByte();
                    byte[]arr2=new byte[size2];
                    C_Index i=new C_Index();
                    index.read(arr2);//leitura do vetor
                    i.fba(arr2);
                    if(i.getValidate()==1&&condition==1){//Leitura de todos os registros
                        int id=i.getIndexId();
                        System.out.print("\nID---------------------------------: "+Functions.format_id(id));
                        Procedures_2_A_1.readWinner(0,i.getIndexPos(),1);
                    }
                    else{

                        if(condition==2&i.getIndexId()==op){//busca específica
                            if(i.getValidate()==0){

                                System.out.print("\nBusca: ID "+op+" foi deletada anteriormente deletada da base de dados.");

                            }else{
                                //se for ID buscada e condition codificada para busca unica(codigo interno da aplicação)
                                System.out.print("\n\nBusca: ID "+op+" localizado.");
                                int id=i.getIndexId();
                                System.out.print("\nID---------------------------------: "+Functions.format_id(id));
                                Procedures_2_A_1.readWinner(0,i.getIndexPos(),1);                                
                            }
                            resp=true;
                            break;
                        }
                        else if(condition==3&i.getIndexId()==op){//Atualização
                            if(i.getValidate()==0){

                                System.out.print("\nBusca: ID "+op+" foi deletada anteriormente deletada da base de dados.");

                            }else{
                                //se for ID buscada e condition codificada para busca unica(codigo interno da aplicação)
                                System.out.print("\n\nBusca: ID "+op+" localizado.");
                                int id=i.getIndexId();
                                long pos=i.getIndexPos();
                                System.out.print("\nID---------------------------------: "+Functions.format_id(id));
                                Procedures_2_A_1.readWinner(0,pos,2); 
                                writeIndex(id,pos,2,pointer);
                            }
                            resp=true;
                            break;
                        }else if(condition==4&i.getIndexId()==op){//Exclusão
                            if(i.getValidate()==0){
                                //Feedback para o usuário
                                System.out.print("\nBusca: ID "+op+" foi deletada anteriormente da base de dados.");

                            }else{
                                //se for ID buscada e condition codificada para busca unica(codigo interno da aplicação)
                                System.out.print("\n\nBusca: ID "+op+" localizado.");
                                int id=i.getIndexId();
                                long pos=i.getIndexPos();
                                System.out.print("\nID---------------------------------: "+Functions.format_id(id));
                                Procedures_2_A_1.readWinner(0,i.getIndexPos(),3);
                                //chama o processo de exclusão
                                op=0;//Zera a variavel
                                op=prelude_delete(1);//processo de escolha de exclusão
                                
                                if(op==1){
                                    //Exclusão lógica
                                    writeIndex(id,pos,3,pointer);//repassa os parametros

                                }else{
                                    size++;//incrementa em 1
                                    delete(index,pointer,size);//Exclusão física
                                }
                            }
                            resp=true;
                            break;
                        }
                    }                    
                }if(resp==false){
                    System.out.print(Changes.set_Locale("\nBusca sem resultados válidos."));
                }
            }
        }catch(EOFException e){
             System.out.println("\nEncerrando Processos.\n");     
        }catch(IOException f){
            f.getMessage();
        } 
    }
    public static int prelude_delete(int stage){//Enunciado para deletar
        int op=0;
        String local="";
        if(stage==1){
            local="de Indice";
        }else{
            local="de Registro";
        }
        do{
            System.out.print("\nProcesso de exclusão "+local+" - Opções:");
            System.out.print("\n1) - Lógica (muda apenas o byte validador)");
            System.out.print("\n2) - Física (apaga diretamente no disco)  ");
            op=Functions.only_Int();
        }while(op<=0&op>2);
        return op;
    }
    public static void delete(RandomAccessFile raf,long pos,int size)
            throws IOException,FileNotFoundException{
        byte[]arr3=new byte[size];//cria um vetor para sobrescrever o setor
        Arrays.fill(arr3,(byte)0);//zera o vetor
        raf.seek(pos);//Segue para aposição designada
        raf.write(arr3);//escrever na posição designada
         
    }
    public static void delete_Index(){//procedimento para chamar deleção do arquivo binario
        
        try{
            Files.delete(Paths.get(path_i));
            System.out.println("\nArquivo "+path_i+" Deletado com sucesso.");  
        }
	catch (IOException e) {
	    System.out.println(Changes.set_Locale("\nErro no processo de exclusão."));
	}
        System.out.println("\nRetornando ao Menu Principal.....");
    }
}
