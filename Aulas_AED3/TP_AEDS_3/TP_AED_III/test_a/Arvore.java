package test_a;

/**
 * Classe árvore que irá gerenciar as inserções e remoções que uma árvore B terá
 * @author Valter Henrique, Arthur Mazer, Vitor Villela
 */
public class Arvore {

    // nó raiz da árvore
    private No raiz;
    // número máximo de filhos que a árvore terá
    private final int iNumMaxFilhos;
    // número mínimo de chaves que os nós terão
    private final int iNumMinChaves;
    // número mínimo de chaves que os nós terão
    private int iNumMaxChaves;

    /**
     * Toda árvore precisa saber o número máximo de filhos que terá antes de começar a inserir elementos na mesma
     * @param aNumMaxFilhos
     * @author Valter Henrique
     */
    public Arvore(int aNumMaxFilhos) {
        // valor máximo de filhos que a árvore terá, informado pelo usuário
        iNumMaxFilhos = aNumMaxFilhos;
        // Calculando o mínimo de chaves que um nó nesta árvore poderá ter
        iNumMinChaves = (int) Math.floor(((double) (iNumMaxFilhos - 1)) / ((double) 2));
        // Calculando o máximo de chaves que os nós terão nessa árvore
        iNumMaxChaves = iNumMaxFilhos - 1;
        // inicializando a raiz da árvore
        raiz = new No();
    }

    /**
     * Verifica se a árvore esta vazia
     * @return true se árvore estiver vazia, false se tiver ao menos uma chave
     * @author Valter Henrique
     */
    public boolean vazia() {
        if (raiz.numChaves() == 0) {
            return true;
        }
        return false;
    }

    /**
     * Inserindo chave passada na árvore
     * @param aChave
     * @return true se conseguiu inserir chave na árvore, false senão conseguiu
     * @author Valter Henrique
     */
    public boolean insere(int aChave) {

        // buscando chave na árvore, caso retorne != null, quer dizer que encontrou um nó que possui a chave
        if (buscaChave(raiz, aChave) != null) {
            return false;

        } // senão não achar a chave na árvore, então inserir a chave na árvore
        else {
            // se houver espaço na raiz para ser inserido o valor
            if (raiz.numChaves() < iNumMaxChaves) {

                // quando não há filhos
                if (raiz.folha()) {
                    raiz.addChave(aChave);
                    raiz.ordenarNo();
                } else {
                    insereNoNaoCheio(raiz, aChave);
                }

            } // se não houver mais espaço na raiz
            else {
                if (raiz.numChaves() == iNumMaxChaves) {
                    if (raiz.folha()) {
                        No noFilho = raiz;
                        int i = procurarFilho(noFilho, aChave);

                        raiz = new No();

                        noFilho.addChave(aChave);
                        noFilho.ordenarNo();

                        divideNo(raiz, noFilho, i);

                    } else {
                        insereNoNaoCheio(raiz, aChave);
                    }

                }
            }

        }
        return true;
    }

    /**
     * Inserindo uma chave em um nó que não esta cheio
     * @param aNo O nó que não esta cheio
     * @param aChave A chave a ser inserida neste nó passado juntamente
     * @author Valter Henrique
     */
    public void insereNoNaoCheio(No aNo, int aChave) {

        // se o nó for folha, acabou a busca pela nó correto e insere a chave neste nó
        if (aNo.folha()) {
            aNo.addChave(aChave);
            aNo.ordenarNo();
        } // se o nó não for folha, quer dizer que tem filhos e então iremos procurar em qual filho é o melhor para receber a chave recursivamente
        else {
            // procurando o índice de qual filho irá receber a chave
            int i = this.procurarFilho(aNo, aChave);

            // se houver espaço no nó que vai receber a chave
            if (aNo.getFilho(i).numChaves() < iNumMaxChaves) {
                insereNoNaoCheio(aNo.getFilho(i), aChave);
            } else {
                // senão houver mais espaço no nó
                if (aNo.getFilho(i).numChaves() == iNumMaxChaves) {
                    // se nó a receber chave for folha e estiver cheio
                    if (aNo.getFilho(i).folha()) {
                        aNo.getFilho(i).addChave(aChave);
                        aNo.getFilho(i).ordenarNo();

                        divideNo(aNo, aNo.getFilho(i), i);
                    } else {
                        insereNoNaoCheio(aNo.getFilho(i), aChave);
                    }
                }
            }
        }
    }

    /**
     * Dividindo um nó
     * @param aPai O nó pai que terá como filho o nó a ser divido
     * @param aFilho O nó a ser dividido
     * @param i O índice de onde esta o nó a ser dividido
     * @author Valter Henrique
     */
    public void divideNo(No aPai, No aFilho, int aIndice) {

        // adicionando a chave no nó pai
        aPai.addChave(aFilho.getChave(iNumMinChaves));
        aPai.ordenarNo();
        aFilho.removeChavePeloIndice(iNumMinChaves);

        No noNovo = new No();

        // passando as chaves do filho para o novo nó
        while (aFilho.numChaves() > iNumMinChaves) {
            noNovo.addChave(aFilho.getChave(iNumMinChaves));
            aFilho.removeChavePeloIndice(iNumMinChaves);
        }

        // se aFilho não for folha, então temos que passar seus filhos para o novo nó
        if (!aFilho.folha()) {
            //passando os filhos (do meio da direita) do nó filho para o novo nó
            while (aFilho.numFilhos() > (iNumMinChaves + 1)) {
                noNovo.addFilho(aFilho.getFilho(iNumMinChaves + 1));
                aFilho.removeFilho(iNumMinChaves + 1);
            }
        }

        // se aPai for folha, quer dizer que é o novo nível acima da árvore
        if (aPai.folha()) {
            aPai.addFilho(aFilho);
            aPai.addFilhosNoIndice(aPai.numFilhos(), noNovo);
        } else {
            aPai.addFilhosNoIndice(aIndice + 1, noNovo);
        }

        // se ao passar a chave do meio para o pai e ele tiver mais chaves que o permitido, ele também precisará ser dividido
        if (aPai.numChaves() > iNumMaxChaves) {
            // pegando a maior chave de aPai para procurarmos quem é seu antecessor ou seja, se aPai é filho de um nó, queremos saber quem é seu pai
            int iMaiorChave = aPai.maiorChave();
            // buscando o pai de aPai
            No noPai = buscaPai(raiz, iMaiorChave);

            // se não achar o pai de aPai, quer dizer que ele é a raiz
            if (noPai == null) {
                No novaRaiz = new No();
                raiz = novaRaiz;

                divideNo(novaRaiz, aPai, aIndice);

            } else {
                // caso aPai tenha um pai, então aPai será dividido e o pai de aPai irá receber a sua chave do meio recursivamente
                aIndice = this.procurarFilho(noPai, iMaiorChave);
                divideNo(noPai, aPai, aIndice);

            }

        }
    }

    /**
     * Realiza a remoção de uma chave contida na árvore
     * @param aChave A chave a ser removida
     * @return true se achou e removeu a chave, false se não achou a chave na árvore
     * @author Arthur Mazer, Valter Henrique
     */
    public boolean remove(int aChave) {
        // se ao procurar a chave na árvore e não encontrar
        if (this.buscaChave(raiz, aChave) == null) {
            return false;
        } else {
            // se a chave a ser removida existir na árvore
            No noRemove = this.buscaChave(raiz, aChave);

            // se o nó que contém a chave for folha
            if (noRemove.folha()) {
                noRemove.removeChavePeloValor(aChave);

                if (noRemove != raiz) {
                    balanceia_folha(noRemove);
                }

            } // se o nó que contém a chave não for folha
            else {
                if (!noRemove.folha()) {

                    No noAntecessor = buscaAntecessor(aChave);

                    int iMaiorChaveAntecessor = noAntecessor.maiorChave();

                    System.out.println("O ANTECESSOR EH >>  " + iMaiorChaveAntecessor);

                    noAntecessor.removeChavePeloValor(iMaiorChaveAntecessor);

                    noRemove.removeChavePeloValor(aChave);
                    noRemove.addChave(iMaiorChaveAntecessor);
                    noRemove.ordenarNo();

                    balanceia_folha(noAntecessor);
                }
            }
        }
        return true;
    }

    /**
     * Balanceando o nó folho passado como parâmetro
     * @param aNo O nó a ser balanceado
     */
    //void balanceia_folha(No aPai, No aFilho) {
    void balanceia_folha(No aNo) {
        System.out.println("BALANCEANDO A ÁRVORE");

        if (aNo.numChaves() < iNumMinChaves) {
            No noPai = this.buscaPaiDoNo(aNo, raiz);

            int j = 0;
            while (noPai.getFilho(j) != aNo) {
                j++;
            }

            if (j == 0 || noPai.getFilho(j - 1).numChaves() == iNumMinChaves) {
                if ((j == noPai.numChaves()) || noPai.getFilho(j + 1).numChaves() == iNumMinChaves) {
                    diminuiAltura(aNo);
                } else {
                    balanceia_dir_esq(noPai, j, aNo, noPai.getFilho(j + 1));
                }
            } else {
                balanceia_dir_esq(noPai, j - 1, noPai.getFilho(j - 1), aNo);
            }
        }
    }

    /**
     * Balanceando (redistribuindo) as chaves entre os nós filhos e o seu respectivo nó pai
     * @param aPai Nó pai que possui os nós filhos aEsq e aDir
     * @param iIndice Indice onde esta localizado a chave que será removida
     * @param aEsq Nó filho a esquerda da posição aonde esta a chave a ser removida do nó pai
     * @param aDir Nó filho a direita da posição aonde esta a chave a ser removida do nó pai
     * @author Valter Henrique
     */
    void balanceia_dir_esq(No aPai, int iIndice, No aEsq, No aDir) {
        if (!aDir.folha()) {
            for (int i = aDir.numFilhos(); i > 1; i--) {
                aDir.addFilhosNoIndice(i + 1, aDir.getFilho(i));
            }
        }

        if (aDir.numChaves() > iNumMinChaves && aEsq.numChaves() < iNumMinChaves) {
            aEsq.addChave(aPai.getChave(iIndice));
            aPai.removeChavePeloIndice(iIndice);

            aPai.addChaveNoIndice(iIndice, aDir.menorChave());
            aDir.removeChavePeloValor(aDir.menorChave());

            aEsq.ordenarNo();
            aDir.ordenarNo();
            aPai.ordenarNo();
        } else {
            if (aEsq.numChaves() > iNumMinChaves && aDir.numChaves() < iNumMinChaves) {
                aDir.addChave(aPai.getChave(iIndice));
                aPai.removeChavePeloIndice(iIndice);

                aPai.addChave(aEsq.maiorChave());
                aEsq.removeChavePeloValor(aEsq.maiorChave());

                aEsq.ordenarNo();
                aDir.ordenarNo();
                aPai.ordenarNo();

            } else {
                aDir.addChaveNoIndice(0, aPai.getChave(iIndice));
                aPai.removeChavePeloIndice(iIndice);

                aPai.addChaveNoIndice(iIndice, aEsq.maiorChave());
                aEsq.removeChavePeloValor(aEsq.maiorChave());
            }
        }

        if (!aEsq.folha()) {
            aDir.addFilhosNoIndice(0, aEsq.getFilho(aEsq.numFilhos() - 1));
            aEsq.removeFilho(aEsq.numFilhos() - 1);
        }

    }

    /**
     * Diminuindo a altura da árvore
     * @param aNo Passando o nó que teve a sua chave removida
     * @author Valter Henrique
     */
    void diminuiAltura(No aNo) {
        if (aNo == raiz) {
            exibirNo(aNo);

            if (aNo.numChaves() == 0) {
                raiz = aNo.getFilho(0);
            }
        } else {
            No noPai = this.buscaPaiDoNo(aNo, raiz);
            if (aNo.numChaves() < iNumMinChaves) {

                int j = 0;
                while (noPai.getFilho(j) != aNo) {
                    j++;
                }

                if (j > 0) {
                    juncaoNo(noPai, j - 1);
                } else {
                    juncaoNo(noPai, j);
                }

                diminuiAltura(noPai);

            }
        }

    }

    /**
     * Juntando dois nós quando estes já não estiverem mais com as propriedades de uma árvore b
     * @param aNo Nó pai que possui os filhos noEsq e noDir, sendo assim realizando uma junção entre este nós de forma adequada
     * @param iIndice
     * @author Valter Henrique
     */
    void juncaoNo(No aNo, int iIndice) {
        No noEsq = aNo.getFilho(iIndice);
        No noDir = aNo.getFilho(iIndice + 1);

        noEsq.addChave(aNo.getChave(iIndice));
        aNo.removeChavePeloIndice(iIndice);

        while (noDir.numChaves() > 0) {
            noEsq.addChave(noDir.getChave(0));
            noDir.removeChavePeloIndice(0);
        }

        noEsq.ordenarNo();

        if (!noDir.folha()) {
            while (noDir.numFilhos() > 0) {
                noEsq.addFilho(noDir.getFilho(0));
                noDir.removeFilho(0);
            }
        }

        aNo.removeFilho(iIndice + 1);

    }

    /**
     * Busca por uma chave na árvore recursivamente
     * @param aNo O nó aonde será procurada a chave
     * @param aChave A chave aer buscada na árvore
     * @return O nó aonde esta a chave, null senão encontrar a chave na árvore
     * @author Valter Henrique
     */
    public No buscaChave(No aNo, int aChave) {
        int i = 0;
        int iNumChaves = aNo.numChaves();

        // procurando em qual filho deve estar a chave
        while (i < iNumChaves && aChave > aNo.getChave(i)) {
            i++;
        }

        // se achou a chave, retorna o Nó
        if (i < iNumChaves && aChave == aNo.getChave(i)) {
            return aNo;
        }

        // se não tiver filhos, então é folha
        if (aNo.getListFilhos().isEmpty()) {
            return null;
        } else {
            // aNo recebe o resultado da busca que foi realizada, desempilhando a pilha que foi contruída
            // devido a recursão realizada
            aNo = buscaChave(aNo.getListFilhos().get(i), aChave);
        }

        return aNo;

    }

    /**
     * Buscando o pai de um terminado nó passando somente a maior chave do nó o qual eu quero saber quem é seu pai, mande sempre a raiz como parâmetro que o método recursivamente irá encontrar o pai, caso não tenha nenhum pai, é por que ele já é a raiz
     * @param aNo Nó que queremos procurar se ele contém um filho que contém a maior chave do nó
     * @param aChave A maior chave de um nó o qual queremos saber quem é seu pai
     * @return O nó pai que contém o nó que contém a maior chave passada como parâmetro
     * @author Valter Henrique
     */
    public No buscaPai(No aNo, int aChave) {

        // procurando o índice de qual filho é o melhor para procurarmos abaixo
        int i = this.procurarFilho(aNo, aChave);

        // se aNo for folha, quer dizer que não tem mais folhas, então não há sentido em procurarmos por filhos que possuam a maior chave, já que eles não existem
        if (aNo.folha()) {
            return null;
        }

        // se aNo tiver um filho que contém a maior chave, então ele é o nó pai
        if (aNo.getFilho(i).contemChave(aChave)) {
            return aNo;
        } // se ele não for o pai, então iremos procurar recursivamente
        else {
            aNo = buscaPai(aNo.getFilho(i), aChave);
        }

        return aNo;
    }

    /**
     * Busca o pai de um determinado nó que esteja na arvore
     * @param aFilho O nó que deseja encontrar
     * @param aPai Inicialmente para iniciar a busca pela árvore, passe sempre o nó raiz da árvore
     * @return Retorna o pai do nó
     */
    public No buscaPaiDoNo(No aFilho, No aPai) {
        No aux;
        if (aFilho == raiz) {
            return null;
        } else {
            for (int i = 0; i < aPai.numFilhos(); i++) {
                if (aPai.getFilho(i) == aFilho) {
                    return aPai;
                } else if (aPai.getFilho(i) == null) {
                    return null;
                }
            }
            for (int i = 0; i < aPai.numFilhos(); i++) {
                aux = buscaPaiDoNo(aFilho, aPai.getFilho(i));
                if (aux != null) {
                    return aux;
                }
            }
        }
        return null;
    }

    /**
     * Realiza a busca do nó antecessor (ou seja, que contém uma chave que é menor, em pelo menos uma unidade) da chave passada por parâmetro
     * @param aChave A chave a qual quer saber sua antecessora
     * @return Retorna o nó que contém a chave antecessora
     */
    No buscaAntecessor(int aChave) {
        int iChave = aChave - 1;
        while (this.buscaChave(raiz, iChave) == null) {
            iChave--;
        }
        return this.buscaChave(raiz, iChave);
    }

    /**
     * Exibe as chaves da árvore
     * @author Valter Henrique
     */
    public void exibir(No aNo) {
        if (aNo.folha()) {
            exibirNo(aNo);
        } else {
            int i = 0;
            int k = 0;

            while (i < aNo.numFilhos()) {
                if (k < aNo.numChaves()) {
                    System.out.println("***********");
                    System.out.print("Nó Pai >> " + aNo.getChave(k));
                    System.out.print("\nNumero de filhos >> " + aNo.numFilhos());
                    System.out.println("\n***********");
                    k++;
                }
                exibir(aNo.getFilho(i));
                i++;
            }
        }
    }

    /**
     * Exibir chaves do nó passado como parâmetro
     * @param aNo O nó a ter as chaves exibidas
     * @author Valter Henrique
     */
    public void exibirNo(No aNo) {
        System.out.println("------------");
        if (aNo != null && aNo.numChaves() > 0) {
            for (int i = 0; i < aNo.numChaves(); i++) {
                System.out.print(aNo.getChave(i) + ", ");
            }
        } else {
            System.out.println("NÃO É POSSÍVEL EXIBIR O NÓ POIS ESTA VAZIO");
        }
        System.out.println("\n------------");
    }

    /**
     * Retorna a raiz da árvore, necessário para poder inicializar a busca de uma determinada chave
     * @return Nó raiz da árvore
     * @author Valter Henrique
     */
    public No getRaiz() {
        return raiz;
    }

    /**
     * Busca e retorna o índice de qual filho terá a chave a ser inserida
     * @param aNo Nó pai
     * @param aChave A chave a ser inserida
     * @return O índice de qual filho receberá a chave
     * @author Valter Henrique
     */
    public int procurarFilho(No aNo, int aChave) {
        int i = 0;
        int iTamanho = aNo.getListChaves().size();

        while (i < iTamanho && aChave > aNo.getChave(i)) {
            i++;
        }

        return i;

    }

    /**************** SHERMAN ***********************************/

    /*alterei a partir daqui, vou colocar os metodos get e set Ordem
    tive que tirar do atributo iNumMaximoChaves o identificador final
    porque pode alterar a ordem */
    /**
     * este metodo altera a ordem da arvore
     * @param x sera um valor, do tipo inteiro, passado para alterar o numero maximo de filhos que uma arvore pode ter
     */
    // VALTER : Sherman, mas aqui o número de chaves tem que ser passado como parâmetro para a árvore ser criada, ele já faz isso no construtor
    public void setMaximoChaves(int x) {
        iNumMaxChaves = x;
    }

    /**
     * este metodo retorna o numero maximo de filhos
     * @return do tipo inteiro
     */
    public int getMaximoChaves() {
        return iNumMaxChaves;
    }

    /**
     * Retorna o número minimo de chaves a serem armazenadas em um nó
     * @return INT
     */
    public int getMinimoChaves() {
        return iNumMinChaves;
    }

    /**
     * Método que permuta aChave e seu antecessor de nó
     * @param node
     * @param aChave
     */
    public void trocaAntecessor(No node, int aChave) {
        No node_aux = node.getAntecessor(aChave);
        int K;

        K = node_aux.getListChaves().get(node_aux.getListChaves().size() - 1);

        node_aux.removeChavePeloIndice(node_aux.getIndexChave(K));
        node_aux.addChave(aChave);

        node.removeChavePeloIndice(node.getIndexChave(aChave));
        node.addChave(K);
    }

    public void trocaSucessor(No node, int aChave) {
        No node_aux = node.getSucessor(aChave);
        int K;

        K = node_aux.getListChaves().get(0);

        node.removeChavePeloIndice(node.getIndexChave(aChave));
        node.addChave(K);
    }

    public No getPai(No node, No raiz) {

        int i;

        for (i = 0; i < raiz.getListChaves().size(); i++) {

            if (raiz.getListFilhos().get(i) == node) {
                return raiz;
            } else {
                return (this.getPai(node, raiz.getListFilhos().get(i)));
            }

        }
        return null;

    }

    public No irmaoEsquerdo(No node) {
        No pai_aux;
        pai_aux = this.getPai(node, this.getRaiz());

        if (this.getIndexFilho(node) == 0) {
            return null;
        } else {

            return pai_aux.getListFilhos().get(this.getIndexFilho(node) - 1);
        }

    }

    public No irmaoDireito(No node) { // este metodo soh dah certo quando o noh estah completamente cheio
        No pai_aux;
        pai_aux = this.getPai(node, this.getRaiz());

        if (this.getIndexFilho(node) == pai_aux.getListFilhos().size()) {
            return null;
        } else {
            // corrigindo o metodo : se this.getIndexFilho(node) + 1 FOR NULO, fazer uma condicao
            if (pai_aux.getListFilhos().get(this.getIndexFilho(node) + 1) != null) {
                return pai_aux.getListFilhos().get(this.getIndexFilho(node) + 1);
            } else {
                return null;
            }
        }

    }

    public int getIndexFilho(No node) {
        int i;
        No no_pai = this.getPai(node, raiz);

        for (i = 0; i < no_pai.getListFilhos().size(); i++) {

            if (no_pai.getListFilhos().get(i) == node) {
                return i;
            }
        }


        return -1;

    }

    public int getAlturaArvore(No n, int cont) {
        if (n.folha()) {
            return cont;
        } else {
            return getAlturaArvore(n.filhoEsquerdo(n.getChave(0)), cont + 1);

        }
    }
}
