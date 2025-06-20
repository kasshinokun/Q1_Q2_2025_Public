package estagio3;
import estagio1.leitura.Functions;
import estagio3.Huffman; 
import estagio3.HuffmanByte; 
import estagio3.LZWC;
import estagio3.addons.LZ78Unified; 
public class callerCompact {
    public static void main(String[] args) {
    	int op=0;
		do {
			System.out.println("\n==================================================");
			System.out.println("\nProcessos TP AEDS III - Parte III\n");
			System.out.println("=============Arquivo Sequencial===================\n");
			System.out.println("1) Processo Huffman/LZW A (Baseado no arquivo csv)");
			System.out.println("2) Processo Huffman/LZW B (Baseado no arquivo de dados da etapa 1)");
			System.out.println("\n====================================================");
			System.out.print("\n0) Sair\n\nEscolha um valor-------> :");
			op=Functions.only_Int();
			switch(op) {
				//Parte A
				case 1:
					Processo_A();
					break;
				case 2:
					Processo_B();
					break;
				default:
					if(op==0) {
						System.out.println("\nVoltando ao Menu Principal.");
					}else {
						System.out.println("\nTente novamente, escolha fora do escopo.\n");
					}
			}
		}while(op!=0);

	}
    public static void Processo_A() {
    	System.out.println("----------- Processo Huffman/LZW A (Baseado no arquivo csv) ----------------------------------------------------");
    	System.out.println("Será executado a primeira versão de Huffman a partir da linquagem C");
    	System.out.println("Será executado a segunda versão de Huffman a partir da linquagem C preparada para ler como byte");
    	System.out.println("Será executado a primeira versão do LZW");
    	System.out.println("Todos trabalhando com o arquivo: \"traffic_accidents_pt_br_rev2.csv\"");
    	System.out.println("\n\nMas primeiramente rodará um pequeno arquivo para teste de eficiência: \"sample.txt\"");
    	System.out.println("Autogerado pelo código");
    	//Comparação com arquivos pequenos
    	System.out.println("-----------------------------------------------------------------------------");
		Huffman.processing();
        System.out.println("-----------------------------------------------------------------------------");
        HuffmanByte.processing();
        System.out.println("-----------------------------------------------------------------------------");
        LZWC.processing();
        System.out.println("-----------------------------------------------------------------------------");
        
    	System.out.println("\n\nHuffman - HuffmanByte - LZW com o arquivo: \"traffic_accidents_pt_br_rev2.csv\"\nComprressão");
        
        //Comparação de Compactação
        Huffman.compressProcess("traffic_accidents_pt_br_rev2.csv","traffic_accidents_pt_br_rev2_huffman.huff");
        System.out.println("-----------------------------------------------------------------------------");
        HuffmanByte.compressProcess("traffic_accidents_pt_br_rev2.csv","traffic_accidents_pt_br_rev2_byte_huffman.huff");
        System.out.println("-----------------------------------------------------------------------------");
        LZWC.compressProcess("traffic_accidents_pt_br_rev2.csv","traffic_accidents_pt_br_rev2_lzw.lzw");
        System.out.println("-----------------------------------------------------------------------------");
        
        System.out.println("\n\nHuffman - HuffmanByte - LZW com o arquivo: \"traffic_accidents_pt_br_rev2.csv\"\nDescomprressão");
        
        //Comparação de Descompactação
        Huffman.decompressProcess("traffic_accidents_pt_br_rev2.csv","traffic_accidents_pt_br_rev2_huffman.huff","traffic_accidents_pt_br_rev2_1.csv");
        System.out.println("-----------------------------------------------------------------------------");
        HuffmanByte.decompressProcess("traffic_accidents_pt_br_rev2.csv","traffic_accidents_pt_br_rev2_huffman.huff","traffic_accidents_pt_br_rev2_2.csv");
        System.out.println("-----------------------------------------------------------------------------");
        LZWC.decompressProcess("traffic_accidents_pt_br_rev2.csv","traffic_accidents_pt_br_rev2_lzw.lzw","traffic_accidents_pt_br_rev2_3.csv");
        System.out.println("-----------------------------------------------------------------------------");
    
    }
    public static void Processo_B() {
        System.out.println("\n\n----------- Processo Huffman/LZW B (Baseado no arquivo de dados da etapa 1) ----------------------------------------------------");
        System.out.println("A seguir será exibido uma adaptação que busca usar o LZ78, sendo este uma adaptação"
        		+ "\npara ler qualquer arquivo sem restrição adaptação"
        		+ "\nAdaptado para lidar com o UTF-8 Português Brasileiro"
        		+ "\nPois como byte a conversão não era afetada nos testes,"
        		+ "\nporém, quando era texto dava erro de caracter por causa do UTF-8");
        System.out.println("\n\nEste código primeiramente também rodará um pequeno arquivo "
        		+ "\npara teste de eficiência: \"brazilian_portuguese_sample.txt\"");
    	System.out.println("Autogerado pelo código");
        LZ78Unified.createSampleData();
        System.out.println("Agora Compressão/Descompressão por LZ78 Adaptado"
        		+ "\nPor hora é apenas demostrativo\n");
        LZ78Unified.demonstrationLZW();
        System.out.println("Demais códigos de teste foram deixados para análise do processo de desenvolvimento");
        
    }
}
