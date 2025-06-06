### Trabalho Prático de Algoritmos e Estruturas de Dados III 
<br>Instituição: PUC Minas – Coração Eucarístico
<br>Turma: 91.30.100
<br>Matéria: Algoritmos e Estruturas de Dados III 
<br>Aluno: Gabriel da Silva Cassino 

#### Observação
O projeto simplificado estará em TP_AED_E3, para permitir uma melhor análise do que foi <br>feito pelo aluno.

#### Etapa 1
Etapa 1 foi dividida em modulos

##### Objeto da Etapa
A classe DataObject recebe a ID e um vetor de Strings, os quais são atribuídos ao objeto da <br>classe, usufruindo de tratamentos de entrada de dados pela classe Functions
<br>A ID é uma variavel int gerada pelo código
<br>As colunas 3, 9 e 14 do csv foram deixados como Lista de Strings
<br>As colunas 15 a 20 são campos float,
<br>As colunas 21 a 23 são campos int, além da ID
<br>porém as colunas 22 e 23 se valem do Timestamp da data para serem geradas apesar de <br>serem referidas no arquivo csv
<br>As demais colunas são campos String.
<br>A propria gera o vetor de bytes a partir de seu objeto e também reconstroi o objeto em <br>si mesma.

##### Escrita
A classe EscritorArquivo realiza parte do processo de escrita auxiliada pelas classes <br>EscritorUpdateArquivo e LeitorArquivo

###### Escrita Update e metodos dependentes
Por conta da estrutura usada o update é escrito por uma classe especifica, retornando a <br>classe EscritorArquivo para finalizar e sendo apoiada por DeleteProcess e LeitorArquivo

##### Leitura
A classe LeitorArquivo realiza parte do processo de leitura auxiliada pelas classes <br>EscritorUpdateArquivo e LeitorArquivo, tendo especialização em ReadProcess e DeleteProcess

##### Apendice
As classes FileExplorer e FileReader permitem o acesso externo a pasta podendo acessar e <br>ler o aquivo csv em qualquer parte do dispositivo em uso, retornando a leitura as <br>classes LeitorArquivo ou EscritorArquivo

##### Erros de input
A classe Functions realiza os tratamentos de entrada de dados das classes e objetos do TP <br>na Etapa 1

#### Etapa 2
Etapa 2 também foi dividida em modulos similar a Etapa 1

##### Objeto da Etapa
A classe DataIndex não recebe a ID, apenas o vetor de Strings, os quais são atribuídos ao objeto da <br>classe, usufruindo de tratamentos de entrada de dados pela classe Functions
<br>A ID é uma variavel int gerada pelo código em tempo de execução gravada em arquivo <br>separado.
<br>As colunas 3, 9 e 14 do csv foram deixados como Vetor de Strings
<br>As colunas 15 a 20 são campos float,
<br>As colunas 21 a 23 são campos int, além da ID
<br>porém as colunas 22 e 23 se valem do Timestamp da data para serem geradas apesar de <br>serem referidas no arquivo csv
<br>As demais colunas são campos String.
<br>A propria gera o vetor de bytes a partir de seu objeto e também reconstroi o objeto em <br>si mesma.

##### Escrita
A classe EscritorIndex realiza parte do processo de escrita auxiliada pelas classes <br>EscritorUpdateIndex, LeitorIndex e LeitorArquivo.

###### Escrita Update e metodos dependentes
Por conta da estrutura usada o update é escrito por uma classe especifica, retornando a <br>classe EscritorArquivo para finalizar e sendo apoiada por DeleteProcess e LeitorArquivo

##### Leitura
A classe LeitorIndex realiza parte do processo de leitura auxiliada pelas classes <br>EscritorUpdateIndex, LeitorArquivo e alguns metodos da Etapa 1, tendo especialização 
<br>interna para a leitura unica ou geral, e exclusão.

##### Apendice
As classes FileExplorer e FileReader permitem o acesso externo a pasta podendo acessar e <br>ler o aquivo csv em qualquer parte do dispositivo em uso, retornando a leitura as <br>classes LeitorIndex ou EscritorIndex
<br>Em adicional a classe MergedHashingImplementations é um protótipo de Bucket e Lista <br>Invertida porem foi mantida em teste, mas tem possibilidade de uso futuro

##### Erros de input
A classe Functions realiza os tratamentos de entrada de dados das classes e objetos do TP <br>na Etapa 2 assim como na Etapa 1

#### Etapa 3
##### Huffman
Codigo de Huffman especializado para o Arquivo CSV 
##### HuffmanByte
Codigo de Huffman especializado para qualquer arquivo, pois lê e escreve em byte
##### LZW
Foi dividido em 2
###### LZWC
Codigo de LZW para compactação especializado para qualquer arquivo, pois lê e escreve em byte assim como o HuffmanByte, é uma pseudo-dependente de LZWD, pois 
<br>somente descompacta se chamar LZWD, porem compacta sem depender de LZWD

###### LZWD
Codigo de LZW para descompactação especializado para qualquer arquivo, 
<br>pois lê e escreve em byte, é uma pseudo-dependente de LZWC, pois 
<br>somente descompacta se chamada por LZWC

##### Testes com LZ77 e LZ78
Codigo de LZW para compactação e descompactação especializado para qualquer arquivo, 
<br>pois lê e escreve em byte direciona a teste de arquivos pequenos 
