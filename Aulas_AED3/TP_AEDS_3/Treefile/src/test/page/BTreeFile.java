package test.page;

import java.io.*;
import java.util.*;
import test.estagio1.LeitorArquivo;

public class BTreeFile {
		public static void main(String[] args) {
			
			//PageTree p=new PageTree(256);
			
			String sep = File.separator;// Separador do sistema operacional em uso
			
			String sArquivo="index".concat(sep+"indexTrafficAccidents.db");
			
			String sArquivoTree="index".concat(sep+"indexTree.db");
			
			storeIndexOnLeaf(sArquivo,sArquivoTree);
		
		}public static void readAllSequential(String sArquivoTree) {	
			try {	
			
				NodeTree root=rebuildTree(new RandomAccessFile(sArquivoTree,"rw"));
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
			
		}
		public static void storeIndexOnLeaf(String pathFile,String pathDb) {
			
			RandomAccessFile randomAccessFile= null;

	        try {
	        	//Acessar Arquivo de Indices
	        	randomAccessFile = new RandomAccessFile(pathFile,"r");
	            //Ponteiro do Cabeçalho
	        	int ID_Header=LeitorArquivo.getLastID(randomAccessFile);
	        	System.out.println("\nCabeçalho do arquivo = " +ID_Header);
	        	//Inicio do Loop
	        	int i=1;
	        	int numPage=0;
	        	
	        	//Instatiate Null Tree
	        	AVLPageTree tree =new AVLPageTree();
	        	
	        	//while (true&&i<=127) {
	        	while (true&&i<=ID_Header) {
	        		
	                try {
	                	int sizePage=676;
	                	Registro[] children=new Registro[31];
	                	int order=children.length+1;
						long pointers[]=new long[order];
						Arrays.fill(pointers,-1);//nulos por enquanto
						
						int nextPage=2*numPage+1;
						
						pointers[0]=12+(sizePage*(nextPage));//32n
											
						//pointers[0]=8+(676*(2*numPage+1));//32n
						
						//pointers[0]=order*(nextPage);//32n
						
						//pointers[0]=(children.length+1)*(2*numPage+1);//32n
	                	
						for(int j=0;j<children.length;j++,i++) { 
							//long pointerKey=randomAccessFile.getFilePointer();//coleta o ponteiro
							
							int Key=randomAccessFile.readInt();//
							    		
							long posKey=randomAccessFile.readLong();
							    		
							byte lapide=randomAccessFile.readByte();
							   
							//Gravar no objeto
							children[j]=new Registro(Key,lapide,posKey);
							
							//Ponteiros
							pointers[j+1]=pointers[0]+sizePage*(j+1);//n*32n
							
							//pointers[j+1]=(children.length+1)*(numPage+1)*(j+2);//n*32n
							
							//pointers[j+1]=12+(676*(numPage+1)*(j+2));//64n
							
							//pointers[1]=pointers[0]+order;//32n
							
							//pointers[1]=12+(676*(2*numPage+2));//64n
							
							//pointers[1]=12+(sizePage*(2*numPage+2));//64n
							
							if(j==children.length-1 ||i==ID_Header) {
								
								long parentPage;
								if(numPage==0)
									parentPage = -1;
									//long parentPage=numPage%order!=0?order:(order*numPage);
									//long parentPage=numPage==0?order:(order*numPage);
								else
									//long parentPage = numPage%2==0?(2*numPage-2)/2:(2*numPage-1)/2;
									parentPage =  numPage%2==0?12+(sizePage*((numPage-2)/2)):12+(sizePage*((numPage-1)/2));
									//parentPage = numPage%2==0?(numPage-2)/2:(numPage-1)/2;
								PageTree pageTree=new PageTree(order,numPage,parentPage,j+1,true,children,pointers);
								                 //int degree,   
								                       //int numPage,
								                               //long parentPage,
								                                          //int numChild, 
								                                               //boolean leaf, 
								                                                   //Registro[] children,
								                                                             //long[] pointers
								//tree.root = tree.insert(tree.root, page);
								System.out.println(pageTree.pagePrint());
							}
							
						}
	                	numPage++;
	                	
	                } catch (EOFException eofe) {
	                    System.out.println("Fim do arquivo atingido.");
	                    break;
	                } catch (IOException ioe) {
	                    ioe.printStackTrace();
	                }
	            }//Show Tree
	        	//System.out.println("Inorder traversal of constructed AVL tree is : ");
	            //tree.inOrder(tree.root);
	            //System.out.println();
	        	
	        } catch (IOException ioe) {
	            ioe.printStackTrace();
	        } finally {
	            try {
	            	randomAccessFile.close();
	            } catch (IOException ioe) {
	                ioe.printStackTrace();
	            }
	        }
	        
	    }
	    // Preorder traversal serialization
	    public static void serializeTree(NodeTree node, RandomAccessFile writerTree) throws IOException {
	        if (node == null) {
	        	//writerTree.writeInt(-1); // Represent null with -1
	            return;
	        }
	        
	        writerTree.writeInt(node.data.degree);//Grau da Arvore
			writerTree.writeInt(node.data.numPage+1);//Próxima Página
			writerTree.writeInt(node.data.children[node.data.numChild-1].getKey());//Ultima ID
			
			//Feedback
			System.out.println("\n----------------------------------> Header "+writerTree.getFilePointer());
			writerTree.seek(LeitorArquivo.find_end(writerTree));
			//Header da Página		
			writerTree.writeInt(node.data.numPage);
			writerTree.writeInt(node.data.numChild);
			writerTree.writeBoolean(node.data.leaf);
			writerTree.writeLong(node.data.parentPage);
			//Feedback
			System.out.println("\n----------------------------------> P0 "+writerTree.getFilePointer());		
			writerTree.writeLong(node.data.pointers[0]);
			
			//Filhos da Página
			for(int i=0;i<node.data.getChildren().length;i++) {
				if(node.data.children[i]!=null) {
					writerTree.writeInt(node.data.children[i].getKey());
					writerTree.writeByte(node.data.children[i].isValidation()==true?(byte)1:(byte)0);
					writerTree.writeLong(node.data.children[i].getAddress());
					writerTree.writeLong(node.data.pointers[i+1]);
					//Feedback
					System.out.println("\n---------------------------------"+i+">"+node.data.children[i].getKey());
					System.out.println("-----------------Address-Node-End"+i+">"+writerTree.getFilePointer());
				}else {
					writerTree.writeInt(0);
					writerTree.writeByte(0);
					writerTree.writeLong(0);
					writerTree.writeLong(-1);
					//Feedback
					System.out.println("\n---------------------------------"+i+">"+" Vazio");
				}
				
			}
	        serializeTree(node.left, writerTree);
	        serializeTree(node.right, writerTree);
	    }

	    //Preorder traversal deserialization
	    public static NodeTree rebuildTree(RandomAccessFile writerTree) throws IOException {
	    	try {
				//Header do Indice
				int ordem=writerTree.readInt();//Grau da Arvore
				int nextPage=writerTree.readInt();//Próxima Página
				int lastID=writerTree.readInt();//Ultima ID
				long positionTree=writerTree.getFilePointer();
				//Feedback
				System.out.println("\n----------------------------------> Header PageTree Index ------>"+positionTree);
				System.out.println("Grau =======> "+ordem);
				System.out.println("Next PageTree ==> "+nextPage);
				System.out.println("Ultima ID ==> "+lastID);
				return deserializeTree(ordem,positionTree,writerTree);
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
				return null;
			}
			
	    }	
	    public static NodeTree deserializeTree(int ordem,long position,RandomAccessFile dis){	
	    	try {
	    	
		    	if (position>dis.length()) {
		            return null;
		        }else {
		    	
			    	dis.seek(position);
			        
		        	Registro[] children=new Registro[ordem-1];
					long pointers[]=new long[ordem];
					Arrays.fill(pointers,-1);//nulos por enquanto
					
			        int numberPage=dis.readInt();
		    		int numChildren=dis.readInt();
		    		boolean validateLeaf=dis.readBoolean();
		    		long parent=dis.readLong();
		    		long leftNode=dis.readLong();
		    		long rightNode;
		    		pointers[0]=leftNode;
		    		
		    		//Feedback
		    		System.out.println("----------------------------------> Children's PageTree <--------------");
					for(int i=1;i<ordem;i++) {
						int key=dis.readInt();
						byte lapide=dis.readByte();
						long address=dis.readLong();
						children[i-1]=new Registro(key,lapide,address);
						pointers[i]=dis.readLong();
					}
					
					PageTree p=new PageTree(ordem,numberPage,parent,numChildren,validateLeaf,children,pointers);
					rightNode=pointers[1];
					//System.out.println(p. pagePrint());
					NodeTree node = new NodeTree(p);
			        node.left = deserializeTree(ordem,leftNode,dis);
			        node.right = deserializeTree(ordem,rightNode,dis);
			        return node;
		        }
	    	}catch(EOFException d) {
	    		System.out.println("Fim de arquivo");
	    		return null;
	    	
	    	}catch(IOException e) {
	    		e.printStackTrace();
	    		return null;
	    	}
	    }    
	    
	}