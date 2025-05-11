package test_a;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;

/**
 * Classe nó que irá conter os dados relativos a cada nó da árvore
 * @author Valter Henrique, Arthur Mazer, Vitor Villela
 */
public class No {
    // lista de chaves que o nó irá possuir
    private List<Integer> listChaves = new ArrayList<Integer>();
    // lista de filho que o nó irá possuir
    private List<No> listFilhos = new ArrayList<No>();
    
    

    /**
     * Retorna a lista de chaves de inteiros
     * @return the listChaves
     * @author Valter Henrique
     */
    public List<Integer> getListChaves() {
        return listChaves;
    }

    /**
     * Retorna a lista de filhos
     * @return the listFilhos
     * @author Valter Henrique
     */
    public List<No> getListFilhos() {
        return listFilhos;
    }

    /**
     * Adiciona chave ao nó que chamou o método, adiciona a chave sempre no fim da lista
     * @param aChave
     * @author Valter Henrique
     */
    public void addChave(int aChave) {

        listChaves.add(aChave);
    }

    /**
     * Inserindo a chave em uma posição da lista de forma que os valores posterioes a essa posição se desloquem para direita após essa inserção
     * @param index O indice aonde quer inserir a chave
     * @param aChave A chave a ser inserida
     * @author Valter Henrique
     */
    public void addChaveNoIndice(int index, int aChave) {
        listChaves.add(index, aChave);
    }

    /**
     * Inserindo um nó em uma posição da lista de filhos de forma que os nós posteriores a essa posição se desloquem para direita após a inserção
     * @param index O índice de aonde deve ocorrer essa inserção
     * @param aNo O nó a ser inserido
     * @author Valter Henrique
     */
    public void addFilhosNoIndice(int index, No aNo) {
        listFilhos.add(index, aNo);
    }

    /**
     * Retorna a chave no indíce informado
     * @param index O indice que contem a chave
     * @return O indice o qual contém a chave
     * @author Valter Henrique
     */
    public int getChave(int index) {
        return listChaves.get(index);
    }

    /**
     *Adiciona filho ao nó que chamou o método
     * @param aNo
     * @author Valter Henrique
     */
    public void addFilho(No aNo) {
        listFilhos.add(aNo);
    }

    /**
     * Removendo determinada chave do nó, passando o seu índice apenas lembrando que a 'list' já reordena a numeração dos índices após a remoção
     * @param aNo - o nó que terá a chave removida
     * @param index - o índice aonde será removido a chave
     * @author Valter Henrique
     */
    public void removeChavePeloIndice(int index) {
        this.listChaves.remove(index);
    }

    /**
     * Removendo determinada chave passando o seu valor apenas
     * @param aChave A chave a ser removida
     * @author Valter Henrique
     */
    public void removeChavePeloValor(int aChave) {
        if (this.listChaves.contains(aChave)) {
            int i = 0;
            while (aChave != this.listChaves.get(i)) {
                i++;
            }
            this.listChaves.remove(i);
        }
    }

    /**
     * Removendo determinado filho, passando o seu índice apenas lembrando que a 'list' já reordena a numeros dos ínidices após a remoção
     * @param index Indice de qual filho será removido
     * @author Valter Henrique
     */
    public void removeFilho(int index) {
        listFilhos.remove(index);
    }

    /**
     * Retorna o número de chaves ativas que o nó possui
     * @param aNo
     * @return o número de chaves ativas que o nó possui atualmente
     * @author Valter Henrique
     */
    public int numChaves() {
        return listChaves.size();
    }

    /**
     * Retorna o número de filhos que o nó possui
     * @return O número de nós que o nó possui
     * @author Valter Henrique
     */
    public int numFilhos() {
        return listFilhos.size();
    }

    /**
     * Retorna o iterador da lista de Chaves
     * @return iterador para a lista de chaves
     * @author Valter Henrique
     */
    public Iterator getIteratorChaves() {
        return listChaves.iterator();
    }

    /**
     * Método que verifica se o nó contém a chave
     * @param aChave A chave a qual procuramos
     * @return Retorna true se contiver a chave procurada, false se não tiver a chave
     * @author Valter Henrique
     */
    public boolean contemChave(int aChave) {
        return this.listChaves.contains(aChave);
    }

    /**
     * Retorna a chave de maior valor dentro de um nó passado como parâmetro
     * @return Retorna a chave de maior valor neste nó
     * @author Valter Henrique
     */
    public int maiorChave() {
        return this.listChaves.get(this.listChaves.size() - 1);
    }

    /**
     * Retorna a menor chave que o nó possui
     * @return A chave de menor valor
     * @author Valter Henrique
     */
    public int menorChave() {
        return this.listChaves.get(0);
    }

    /**
     * Ordena as chaves ativas dentro de um nó
     * @param aNo O nó a ser ordenado
     * @author Valter Henrique
     */
    public void ordenarNo() {
        Collections.sort(this.listChaves);
    }

    /**************** SHERMAN ***********************************/
    /** Retorna o filho desejado
     * @param index
     * @return nó no indíce informado
     * @author Arthur Mazer
     */
    public No getFilho(int index) {
        return this.listFilhos.get(index);
    }

    /** Caso o filho mais a esquerda do NÓ for null já prova que ele é folha!
     * @return true se nó for folha, false se nó não for folha
     * @author Arthur Mazer
     */
    public boolean folha() {
        if (this.listFilhos.isEmpty()) {
            return true;
        }

        return false;

    }

    public No filhoEsquerdo(int aChave) {
        return (this.getListFilhos().get(this.getIndexChave(aChave)));
    }

    public No filhoDireito(int aChave) {
        return (this.getListFilhos().get(this.getIndexChave(aChave) + 1));
    }

    /**
     * Método que retorna o índice da chave dentro de um nó, caso a chave
     * nao exista no nó, retorna -1
     * @param aChave
     * @return int
     */
    public int getIndexChave(int aChave) {
        int i;
        for (i = 0; i < this.getListChaves().size(); i++) {

            if (this.getListChaves().get(i) == aChave) {
                return i;
            }

        }

        return -1;
    }

    /**
     * Método que devolve o nó que contem a Chave antecessora da Chave desejada
     * @param aChave
     * @return No
     */
    public No getAntecessor(int aChave) {
        return this.noAntecessor(this.getFilho(this.getIndexChave(aChave)));
    }

    /**
     * Método auxilar ao getAntecessor
     * @param node
     * @return no
     */
    public No noAntecessor(No node) {
        if (node.folha()) {
            return node;
        } else {
            return node.noAntecessor(node.getFilho(node.getListFilhos().size() - 1));

        }
    }

    /**
     * Método que devolve o nó que contem a Chave sucessora da Chave desejada
     * @param aChave
     * @return No
     */
    public No getSucessor(int aChave) {
        return this.noAntecessor(this.getFilho(this.getIndexChave(aChave + 1)));
    }

    /**
     * Método auxilar ao getSucessor
     * @param node
     * @return no
     */
    public No noSucessor(No node) {
        if (node.folha()) {
            return node;
        } else {
            return node.noSucessor(node.getFilho(0));

        }
    }

   
}