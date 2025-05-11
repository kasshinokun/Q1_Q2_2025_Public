package test_a;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Classe Arquivo que lê os dados do arquivo 'Dados.txt' ou grava valores de chave de forma aleatória
 * @author Valter Henrique
 */
public class Arquivo {

    // lista que irá armazenar as chaves que foram lidas do arquivo
    private List<Integer> list = new ArrayList<Integer>();

    public Arquivo() {}

    /**
     * Lendo arquivo que contem informações para carregar uma determinada árvore automaticamente
     * @param sArqLer
     * @return Retorna uma lista de inteiros sendo o primeiro termo da lista o número máximo de chaves e os demais as chaves a serem inseridas na árvore
     * @author Valter Henrique
     */
    public List<Integer> lerArquivo(String sArqLer) {

        //lendo sLinhas
        try {
            // ler o arquivo
            FileReader i = new FileReader(sArqLer);
            // bufferizando o que foi lido
            BufferedReader in = new BufferedReader(i);
            // o que foi lido será atribuido a uma string
            String sLinha;
            // que esta string por sua vez, será convertida em um valor do tipo inteiro
            int iValor;

            while ((sLinha = in.readLine()) != null) {
                if (sLinha.length() > 0) {
                    System.out.print(sLinha + ", ");

                    // convertendo de string para inteiro
                    iValor = Integer.parseInt(sLinha);

                    // adicionando este valores aos valores que deverão ser adicionados á arvore
                    list.add(iValor);
                }

            }
            // fechando os arquivos
            i.close();
        } catch (Exception x) {
            System.out.println(x.getMessage());
        }

        return list;
    }
        /**
         * Este método irá gerar valores aleatórios no arquivo que esta sendo passado como parâmetro
         * @param sArqGravar O caminho para o arquivo já exisnte, ele será sobreescrito após a operação
         * @param aNumMaxFilhos O número máximo de filhos que esta árvore terá
         * @param aValorMaxChaves Serve para delimitar o valor aleatório gerado aleatóriamente
         * @param aQtdChaves Limita um número de chaves aleatórias que serão criadas
         * @author Valter Henrique
         */
        public void gerarDadosAleatório(String sArqGravar, int aNumMaxFilhos, int aValorMaxChaves, int aQtdChaves) {

            Random random = new Random();
            List<Integer> listChaves = new ArrayList<Integer>();

        //lendo sLinhas
        try {
            // ler o arquivo
            FileReader i = new FileReader(sArqGravar);
            BufferedReader in = new BufferedReader(i);

            FileWriter writer = new FileWriter(sArqGravar);
            PrintWriter saida = new PrintWriter(writer);

            int iCont = 0;
            
            saida.println(aNumMaxFilhos);

            int iValor;

            while ( iCont < aQtdChaves) {
                iValor = random.nextInt(aValorMaxChaves);

                if (!listChaves.contains(iValor)){
                    listChaves.add(iValor);
                    saida.println(iValor);
                    iCont++;
                }
            }
            i.close();
            
            writer.close();
            saida.close();
            
        } catch (Exception x) {
            System.out.println(x.getMessage());
        }

    }

}