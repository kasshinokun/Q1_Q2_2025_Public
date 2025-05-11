package TP_AED_II_2023_1.File;//Nome do Subprojeto

/**
 * @version 1_2025_01_28
 * @author Gabriel da Silva Cassino
 */

import java.util.*;//Simplificação de bibliotecas necessarias 
import java.util.regex.*;//Simplificação de bibliotecas especificas e necessarias 
import java.util.stream.*;//Simplificação de bibliotecas especificas e necessárias

import java.io.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.*;//Simplificação de bibliotecas necessarias para arquivos
import java.nio.file.*;//Simplificação de bibliotecas especificas e necessárias

import TP_AED_II_2023_1.AVL.*;//Importa classe do package 
import TP_AED_II_2023_1.List.*;//Importa classe do package 

public class Procedures {//Exibição dos processos
    public static Scanner reader=new Scanner(System.in);//Entrada do teclado
    public static void optionStart(){//Busca diretorios
        System.out.println("\n=========Analise de Arquivo - 1==============");
        
        String userP=System.getProperty("user.home");//Pasta do Usuario do PC
        String folder="\\Documents";//Local padrão
        
        System.out.println("\nTipo de Busca:\n1)Busca seguindo roteiro do Trabalho Pratico\n2)Escolha do Usuario\n");
        int op=Integer.parseInt(reader.nextLine());
        if(op==1){
            //Enunciado e Informação ao Usuario
            System.out.println("\nIMPORTANTE:\nO programa somente listara arquivos (.txt)");
            System.out.println("na Pasta Documentos Padrao deste Computador.");
            System.out.println("\nPesquisando e Listando.....\n");

            //Instancia String com PATH default da pasta Documentos
            String folderPath=(userP.concat(folder));
            executaTP2(folderPath);//Continuação dos processos
        }else if(op==2){//Se for 2
            int op2=1;
            System.out.println("OBS.: Processo demonstrativo de codigo=======\n");
            System.out.println("Listando Diretorios..........\n");
            
            File[] directoriesUser=ListDirectories(userP);//Instacia vetor do tipo File e recebe vetor da função
            boolean resp=false;
            while(resp==true||op2==1) {
                
                for(int i=0;i<directoriesUser.length;i++){//Laço de repetição para analise de pastas
                    //se for pasta exibira o nome em tela
                    System.out.println("Pasta Encontrada 0"+(i)+"): "+directoriesUser[i].getName());//Nome do arquivo encontrado
                }
                System.out.println("\n");//Salta linha
                System.out.println("Escolha  uma pasta:..........");//Solicita ao usuario
                op=Integer.parseInt(reader.nextLine());//aguarda escolha
                
                if(op>=0&&op<directoriesUser.length){//analise da opção em relação ao vetor
                    if(directoriesUser[op].isDirectory()==true){
                        //Concatena Path em String
                        userP=(userP.concat("\\"+directoriesUser[op].getName()));
                        System.out.println("Posso listar pastas dentro de: "+directoriesUser[op].getName());
                        System.out.println("1 - Continuar \n-Digite um valor qualquer para prosseguir");
                        op2=Integer.parseInt(reader.nextLine());//aguarda escolha
                        
                        if(op2==1){
                                
                            directoriesUser=ListDirectories(userP);//Recebe vetor da função
                            resp=directoriesUser.length==0?false:true;//se vazio, encerra
                        }
                    }
                }                
            }//se repetira enquanto resp for true(opção valida ou vetor com itens)
            typeFiles(userP);//envia a procedimento de escolha de tipo de arquivo a ser lido
            
        }else{//caso contrario......
            System.out.println("\n==Opcao Invalida....Finalizando Processo.....");//Encerra
            System.out.println("==Retornando ao Menu Principal===============\n");//Enunciado
        }
   
    }
    private static File[] ListDirectories(String nome){//lista pasta e retorna//Escolha do usuario
        File[] directoriesUser= new File(nome).listFiles(File::isDirectory);//lista somente diretorios
        return directoriesUser;//retorna vetor
    }
    private static void typeFiles(String nome){//Escolha de extensão de arquivo-via procedimento interno da classe
        String extension="";
        int op;//Variavel de escolha
        do{
            System.out.println("\n=========Analise de Arquivo - 2==============");
            System.out.println("\nQue tipo de arquivo preciso ler:");
            System.out.println("\n1) .txt");
            System.out.println("2) .java");
            System.out.println("\n======Por favor escolha uma opcao: ==========");//Enunciado
            op=Integer.parseInt(reader.nextLine());
            switch(op){
                case 0://despedida do usuario e agradecimento
                    System.out.println("\n===============Muito obrigado================");
                    System.out.println("==Retornando ao Menu Principal===============\n");//Enunciado
                    break;
                case 1://Atribui valor a String
                    extension=".txt";
                    System.out.println("\nPesquisa por arquivo .txt");
                    listFiles(nome,extension);
                    break;
                case 2://Atribui valor a String
                    extension=".java";
                    System.out.println("\nPesquisa por arquivo .java");
                    listFiles(nome,extension);
                    break;
            default:
                //Se não estiver no intervalo, informa ao usuario
                //e reapresenta o menu
                System.out.println("\n============Opcao Invalida.==================");
                System.out.println("======Tente novamente por gentileza!=========\n");
            }      
        }while( op<0||op>2);//Se repetira enquanto não for zero
   
    }
    public static void typeFiles(){//Escolha de extensão de arquivo-Modo Demostrativo
        String extension="";//extensão de arquivo
        String path=(System.getProperty("user.home").concat("\\Documents"));//Pasta padrão
        int op;//Variavel de escolha
        do{
            System.out.println("OBS.: Processo demonstrativo de codigo=======\n");
            System.out.println("\n===Analise de Arquivo - User\\Documentos\\==");
            System.out.println("\nQue tipo de arquivo preciso ler:");
            System.out.println("\n1) .txt");
            System.out.println("2) .java");
            System.out.println("\n======Por favor escolha uma opcao: ==========");//Enunciado
            op=Integer.parseInt(reader.nextLine());
            switch(op){
                case 0://despedida do usuario e agradecimento
                    System.out.println("\n===============Muito obrigado================");
                    System.out.println("==Retornando ao Menu Principal===============\n");//Enunciado
                    break;
                case 1://Atribui valor a String
                    extension=".txt";
                    System.out.println("\nPesquisa por arquivo .txt");
                    listFiles(path,extension);
                    break;
                case 2://Atribui valor a String
                    extension=".java";
                    System.out.println("\nPesquisa por arquivo .java");
                    listFiles(path,extension);
                    break;
            default:
                //Se não estiver no intervalo, informa ao usuario
                //e reapresenta o menu
                System.out.println("\n============Opcao Invalida.==================");
                System.out.println("======Tente novamente por gentileza!=========\n");
            }      
        }while( op<0||op>2);//Se repetira enquanto não for zero
        
    }
    public static void executarTP(){//Processos do TP parte 1
        
        System.out.println("\n========Execucao de todos os Processos=======");
        System.out.println("============do Trabalho Pratico==============\n");
        reader=new Scanner(System.in);//coleta a entrada do teclado
        
        optionStart();//Lista Diretorios       
        
    }
    private static void executaTP2(String folderPath){//Processos do TP parte 2
        
        String extension = ".txt";//Extensão do arquivo
        File folder = new File(folderPath);
        
        File[] files = folder.listFiles((File pathname) -> pathname.getName().endsWith(extension));
        
        for(int i=0;i<files.length;i++){//Laço de repetição para analise de arquivos
            //se for arquivo do tipo .txt exibira o nome em tela
            System.out.println("Arquivo Encontrado 0"+(i)+"): "+files[i].getName());//Nome do arquivo encontrado
        }
        
        if(files.length!=0){//senão estiver vazio.....
            chooseFile(files,folderPath,extension,true);//envia ao procedimento
        }else{
            System.out.println("Nao ha arquivos .txt");//Informa ao usuario            
        }
    }
    private static void listFiles(String path, String extension){//Lista arquivos baseados na extensão
        System.out.println("\n=====Analise de Arquivo - 2 Continuacao======");
        System.out.println("OBS.: Processo demonstrativo de codigo=======\n");
        File folder = new File(path);//caminho da pasta
        
        File[] files = folder.listFiles((File pathname) -> pathname.getName().endsWith(extension));
        if(files.length!=0){
            for(int i=0;i<files.length;i++){//Laço de repetição para analise de arquivos
                //se for arquivo do tipo .txt exibira o nome em tela
                System.out.println("Arquivo Encontrado 0"+(i)+"): "+files[i].getName());//Nome do arquivo encontrado
            }
            chooseFile(files,path,extension,false);
        }else{
            System.out.println("Nao foram encontrados arquivos "+extension+"\n");
        }
    }
    private static void chooseFile(File[] files,String path,String extension,boolean resp){//listagem e escolha de arquivo
        int op=0;//Variavel de escolha
        do{
            System.out.println("\nDigite o numero do arquivo("+extension+") desejado:");//Solicitação ao Usuario
            op=Integer.parseInt(reader.nextLine());
        }while(op<0||op>files.length/*||(files[op].getName().endsWith(".txt")==false)*/);

        System.out.println("\nArquivo Escolhido 0"+(op)+"): "+files[op].getName());//Nome do arquivo escolhido

        //Concatena Path em String
        String nome=(path.concat("\\"+files[op].getName()));

       
        if(resp==false){
            System.out.println();//Salta linha
            readStrings(nome,false);//exibição apenas
        }else{
            System.out.println();//Salta linha
            readStrings(nome,true);//Processos na AVL
        }
    }
    private static void readStrings(String nome,boolean Case){//Buffer para ler Strings no arquivo
        
        AVL tree=new AVL();//Instancia AVL 
        if(Case==true){
            System.out.println("\nAbrindo arquivo:\n"+nome+".\n");//Enunciado
        }else{
            System.out.println("OBS.: Processo demonstrativo de codigo=======\n"); 
            System.out.println("\nAbrindo arquivo:\n"+nome+".\n");//Enunciado
        }
        try {
            System.out.println("Lendo Strings.............\n");//Enunciado
            boolean resp=false;//Verificar arquivo vazio ou não
            BufferedReader reader = new BufferedReader(new FileReader(nome));//Buffer de Arquivo
                       
            String linha = reader.readLine();//BufferedReader(não é o Scanner)
            
            
            while (linha != null) {//Se a String não for vazia

                //Instancia Matcher vinculando String a Pattern para deixar somente letras minusculas
                Matcher m1=Pattern.compile("[a-zA-Z]+").matcher(linha.toLowerCase());
                if(Case==false){//Execução demonstrativa
                    while(m1.find()){//A cada palavra localizada.......
                        resp=true;
                        System.err.println(m1.group());//Exibe as Strings na lista
                    }
                }else{//Execução do TP
                    while(m1.find()){//A cada palavra localizada.......
                        resp=true;
                        tree.add_Palavra(m1.group());//Armazena as Strings na lista
                    }
                }
                linha = reader.readLine();//Carrega a proxima String 
            }
            if(resp==true&&Case==true){//Processos do TP
                Manager.AVL(tree);//Retorna ao procedimento do TP
            }
            else if(resp==false&&(Case==true||Case==false)){
                //Se resp for igual a false
                System.out.println("O arquivo:\n"+nome+".\nNao possui Strings ou Dados");
            }
            reader.close();//Fecha o Buffer
        } catch (IOException e) {
            System.err.printf("Erro na abertura do arquivo: %s.\n",e.getMessage());//Ntificação
        }
        System.out.println();//Salta linha
    }
//===Processos de AVL Isolados ============================================================================
    public static void inserir(){//Inserção na AVL
        AVL tree=new AVL();
        System.out.println("\n========Insercao de Palavra - Usuario========");
        System.out.print("Digite uma Palavra:.............");
        String op=reader.nextLine();
        System.out.println("Inserindo "+op+" .......");
        tree.add_Palavra(op);
        System.out.println("\n======Insercao de Palavra - Predefinida======");
        System.out.println("Inserindo java .......");
        tree.add_Palavra("java");
        System.out.println("Inserindo Arroz .......");
        tree.add_Palavra("Arroz");  
        System.out.println("Inserindo Caneca .......");
        tree.add_Palavra("Caneca");
        exibir(tree);
        //despedida do usuario e agradecimento
        System.out.println("\n===============Muito obrigado================");
        System.out.println("==Retornando ao Menu Principal===============\n");//Enunciado
   
    }
    public static void buscar(AVL tree){
        
        System.out.println("\n========Pesquisa de Palavra - Usuario========");
        System.out.print("Digite uma Palavra:.............");
        String op=reader.nextLine();
        System.out.println();
        tree.pesquisar(op);
        System.out.println("\n======Pesquisa de Palavra - Predefinida======");
        tree.pesquisar("java");
        tree.pesquisar("Arroz");  
        tree.pesquisar("java");
        //despedida do usuario e agradecimento
        System.out.println("\n===============Muito obrigado================");
        System.out.println("==Retornando ao Menu Principal===============\n");//Enunciado
    }
    public static void exibir(AVL tree){//Procedimento para Exibir a AVL
        int opcao;//Variavel de escolha
        do{
            System.out.println("\n===Exibir AVL - Menu de Operacoes============");//Enunciado

            System.out.println("===01 - Arvore AVL - Pre-Order===============");//Enunciado
            System.out.println("===02 - Arvore AVL - In-Order================");//Enunciado
            System.out.println("===03 - Arvore AVL - Pos-Order===============");//Enunciado
            
            System.out.println("\n==========Digite 0 para Encerrar=============");//Enunciado

            System.out.println("\n======Por favor escolha uma opcao: ==========");//Enunciado
            opcao = Integer.parseInt(reader.nextLine());//armazena o valor
            switch(opcao){//Analise do que foi digitado

                case 1://Chama o procedimento
                    tree.imprimir(1);//Exibe a AVL
                    break;//Condição de parada
                case 2://Chama o procedimento
                    tree.imprimir(2);//Exibe a AVL
                    break;//Condição de parada
                case 3://Chama o procedimento
                    tree.imprimir(3);//Exibe a AVL
                    break;//Condição de parada
                
                default:
                    if(opcao==0){//despedida do usuario e agradecimento
                        System.out.println("\n===============Muito obrigado================");
                        System.out.println("==Retornando ao Menu Principal===============\n");//Enunciado
                        
                    }
                    else{//Se não estiver no intervalo, informa ao usuario
                        //e reapresenta o menu
                        System.out.println("\n============Opcao Invalida.==================");
                        System.out.println("======Tente novamente por gentileza!=========\n");
                    } 
            }      
        }while( opcao!=0);//Se repetira enquanto não for zero
        
    }
    public static void remover(AVL tree){
        System.out.println("\n=============Remocao de Palavras=============");
        System.out.print("Digite uma Palavra:.............");
        String op=reader.nextLine();
        System.out.println();
        tree.remover(op);
        //despedida do usuario e agradecimento
        System.out.println("\n===============Muito obrigado================");
        System.out.println("==Retornando ao Menu Principal===============\n");//Enunciado
    }
//===Processos de Lista Isolados ============================================================================
   public static void inserirLista(){
       Lista lista=new Lista();
       System.out.println("\n===Processos em Lista Dupla Encadeada========\n");
       System.out.println("===Inserindo Palavras========================");
       lista.inserirInicio("Arroz");
       lista.inserirInicio("Beterraba");
       lista.inserirInicio("Canela");
       lista.inserirInicio("Doce de Leite");
       lista.inserirInicio("Erva-Doce");
       lista.inserirInicio("Farinha de Trigo");
       lista.inserirFim("Arroz");
       lista.inserirPos("Arroz",4);
       lista.mostrar();
       System.out.println("===Busca por Palavra ========================");
       lista.buscar("Arroz");//Executa busca e exibe resultado da busca
       System.out.println("===Remocao de Palavras=======================");
       System.out.println("Inicio "+lista.removerInicio()+"\n");
       lista.mostrar();
       System.out.println("===Remocao de Palavras=======================");
       System.out.println("posicao 4: "+lista.removerPos(4)+"\n");
       lista.mostrar();
       System.out.println("===Remocao de Palavras=======================");
       System.out.println("Fim: "+lista.removerFim()+"\n");
       lista.mostrar();
       System.out.println("=============================================");
   }
   public static void inserirLista(Lista lista){//A criterio do usuario
       int pos;//posiçao a ser escolhida pelo usuario
       String palavra;//palavra a ser escolhida pelo usuario
       System.out.println("\n===Processos em Lista Dupla Encadeada========\n");
       System.out.println("===Inserindo Palavra no Inicio===============");
       System.out.print("Digite uma Palavra:.............");//Solicitação ao usuario
       palavra=reader.nextLine();//Armazena valor
       lista.inserirInicio(palavra);
       System.out.println("Inicio "+palavra+"\n");
       lista.mostrar();
       System.out.println("===Inserindo Palavra na Posicao==============");
       System.out.print("Digite uma Palavra:.............");//Solicitação ao usuario
       palavra=reader.nextLine();//Armazena valor
       System.out.print("Digite uma Posicao:.............");//Solicitação ao usuario//Solicitação ao usuario
       pos = Integer.parseInt(reader.nextLine());//Armazena valor
       System.out.println("posicao 0"+pos+": "+palavra+"\n");
       lista.inserirPos(palavra,pos);
       lista.mostrar();
       System.out.println("===Inserindo Palavra no Fim==================");
       System.out.print("Digite uma Palavra:.............");//Solicitação ao usuario
       palavra=reader.nextLine();//Armazena valor
       lista.inserirFim(palavra);
       System.out.println("Fim: "+palavra+"\n");
       lista.mostrar();
       System.out.println("===Busca por Palavra ========================");
       System.out.print("Digite uma Palavra:.............");//Solicitação ao usuario
       palavra=reader.nextLine();//Armazena valor
       lista.buscar(palavra);//Executa busca e exibe resultado da busca
       System.out.println();//Salta linha
       System.out.println("===Remocao de Palavras=======================");
       System.out.println("Inicio "+lista.removerInicio()+"\n");
       lista.mostrar();
       System.out.println("===Remocao de Palavras=======================");
       System.out.print("Digite uma Posicao:.............");//Solicitação ao usuario//Solicitação ao usuario
       pos = Integer.parseInt(reader.nextLine());//Armazena valor
       System.out.println("posicao 0"+pos+": "+lista.removerPos(pos)+"\n");
       lista.mostrar();
       System.out.println("===Remocao de Palavras=======================");
       System.out.println("Fim: "+lista.removerFim()+"\n");
       lista.mostrar();
       System.out.println("=============================================");
   }
//===Processos de AVL e Lista ============================================================================
   public static void inserirAVL_Lista(AVL tree, Lista lista){//Transfere da AVL para lista
       tree.inserirOrdenado(lista);  
   }
   public static void testeAVL(){//Teste AVL
       //desenvolvimento do procedimento inserir ordenado
       AVL tree=new AVL();//Instancia AVL
       Lista lista=new Lista();//Instancia Lista
       tree.add_Palavra("Arroz");
       tree.add_Palavra("Beterraba");
       tree.add_Palavra("Canela");
       tree.add_Palavra("Doce de Leite");
       tree.add_Palavra("Erva-Doce");
       tree.add_Palavra("Farinha de Trigo");
       tree.add_Palavra("Arroz");
       tree.remover("Java");
       //Adaptação para feedback----Fonte Programiz
       tree.feedBack();
       System.out.println();//Salta linha
       tree.inserirOrdenado(lista);//Envia Lista Vazia 
   }
    public static void testeLista(){//Teste Lista
       //desenvolvimento do procedimento swap
       Lista lista=new Lista();
       Celula a=new Celula();
       Celula b=new Celula();
       Celula c=new Celula();
       c.setPalavra("Batata",9);
       Celula d=new Celula();
       d.setPalavra("Doce de Leite",5);
       a.setPalavra("Caneca", 7);
       b.setPalavra("Jaca", 8);
       System.out.println("A: "+a.mostrarPalavra()+"\nB: "+b.mostrarPalavra());
       System.out.println();
       lista.swap(a,b);
       System.out.println("A: "+a.mostrarPalavra()+"\nB: "+b.mostrarPalavra());
       System.out.println();
       lista.addStart(a);
       System.out.println();
       lista.addEnd(b);
       System.out.println();
       lista.addPos(d, 0);
       lista.addPos(c, 2);
       
       System.out.println("A: "+a.mostrarPalavra()+"\nB: "+b.mostrarPalavra()+"\nC em 2: "+c.mostrarPalavra()+"\nD em 0: "+d.mostrarPalavra());
       lista.mostrar();
   }
    public static void MergeSort(){//teste
        System.out.println("\nTeste Lista - Merge Sort");
    
        Lista c = new Lista();
        c.inserirData("Batata",9);
        c.inserirData("Doce de Leite",5);
        c.inserirData("Caneca", 7);
        c.inserirData("Jaca", 8);
       
        System.out.println("Inserindo Palavras\n");
        c.print();
        System.out.println("\nExecutando MergeSort");
        c.sortItens();
        c.print();
        
        
    }
}
