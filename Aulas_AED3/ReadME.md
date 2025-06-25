### Trabalho Prático de Algoritmos e Estruturas de Dados III 
Instituição: PUC Minas – Coração Eucarístico
<br>Turma: 91.30.100 2025-1
<br>Matéria: Algoritmos e Estruturas de Dados III 
<br>Aluno: Gabriel da Silva Cassino 
<br>
- Base de dados:
   - [Projeto na Web - Prototipo](https://tpaeds320251.streamlit.app/)
  
   - ```Sobre```:
<br>Para a criação do arquivo de dados foi utilizada a base de dados sobre acidentes de 
<br>trânsito proveniente do site https://www.kaggle.com/datasets/oktayrdeki/traffic-accidents 
<br>contendo 209306 registros. Tal escolha de uma base tão vasta tem por objetivo aprimorar técnicas e 
<br>desenvolver novas.
   - ```Nomes e caminho do arquivo:```
<br>```Nome e caminho do arquivo com dados originais```:TP_AED_E3/data/traffic_accidents_rev2.csv
<br>```Nome e caminho do arquivo com dados traduzidos```:TP_AED_E3/data/traffic_accidents_pt_br_rev2.csv
   - ```Uso nas etapas:```:
<br>Etapa 1: inicialmente --> Arquivo csv original, posteriormente substituido pelo csv traduzido
<br>Etapa 2 em diante: -----> Arquivo csv traduzido e arquivo amostra

#### Observação
O projeto simplificado estará em TP_AED_E3, para permitir uma melhor análise do que foi feito pelo aluno.
<br>
<br>Por enquanto está em Java, mas a intenção é realizar um port para Streamlit-Python permitindo a execução
<br>em qualquer lugar ou dispositivo.
<br>
<br>O trabalho prático em Java está no caminho: 
<br>Cada estágio de apresentação está em sua pasta, contendo seus respectivos métodos em classes especializadas ou não 
<br>e podendo ou não ter classes de subprocessos, provendo uma melhor gestão e modularização em caso de manutenção e,
<br>quanto a leitura e escrita, em alguns estágios há pastas com os referidos nomes dos processos contendos em si as
<br>classes necessárias ao mesmo.
<br>
#### Etapa 1
Etapa 1 foi dividida em modulos

[Link da pasta](https://github.com/kasshinokun/Q1_Q2_2025_Public/tree/main/Aulas_AED3/TP_AEDS_3)
##### Objeto da Etapa
A classe DataObject recebe a ID e um vetor de Strings, os quais são atribuídos ao objeto da <br>classe, usufruindo de tratamentos de entrada de dados pela classe Functions
<br>A ID é uma variavel int gerada pelo código
<br>As colunas 3, 9 e 14 do csv foram deixados como Lista de Strings
<br>As colunas 15 a 20 são campos float,
<br>As colunas 21 a 23 são campos int, além da ID
<br>porém as colunas 22 e 23 se valem do Timestamp da data para serem geradas via código,apesar de 
<br>serem referidas no arquivo csv
<br>As demais colunas são campos String.
<br>A propria gera o vetor de bytes a partir de seu objeto e também reconstroi o objeto em <br>si mesma.

##### Escrita
A classe EscritorArquivo realiza parte do processo de escrita auxiliada pelas classes 
<br>EscritorUpdateArquivo e LeitorArquivo

###### Escrita Update e metodos dependentes
Por conta da estrutura usada o update é escrito por uma classe especifica, retornando a 
<br>classe EscritorArquivo para finalizar e sendo apoiada por DeleteProcess e LeitorArquivo

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
A classe EscritorIndex realiza parte do processo de escrita auxiliada pelas classes 
<br>EscritorUpdateIndex, LeitorIndex e LeitorArquivo.

###### Escrita Update e metodos dependentes
Por conta da estrutura usada o update é escrito por uma classe especifica, retornando a 
<br>classe EscritorArquivo para finalizar e sendo apoiada por DeleteProcess e LeitorArquivo

##### Leitura
A classe LeitorIndex realiza parte do processo de leitura auxiliada pelas classes <br>EscritorUpdateIndex, LeitorArquivo e alguns metodos da Etapa 1, tendo especialização 
<br>interna para a leitura unica ou geral, e exclusão.

##### Apendice
As classes FileExplorer e FileReader permitem o acesso externo a pasta podendo acessar e 
<br>ler o aquivo csv em qualquer parte do dispositivo em uso, retornando a leitura as 
<br>classes LeitorIndex ou EscritorIndex
<br>
<br>Em adicional a classe ```MergedHashingImplementations``` é um protótipo de ```Bucket e Lista``` 
<br>```Invertida``` porem foi mantida em teste, mas tem possibilidade de uso futuro, está presente
<br>na pasta ```estagio2/addons```

##### Erros de input
A classe Functions ainda é usada para realiza os tratamentos de entrada de dados das classes e objetos do TP 
<br>na Etapa 2 assim como na Etapa 1

#### Etapa 3
[pasta Etapa 3](https://github.com/kasshinokun/Q1_Q2_2025_Public/tree/main/Aulas_AED3/TP_AED_E3)

Os códigos de compactação e descompactação de Huffman e LZW dependendo da classe pode haver dependência ou não
<br>e especialização em tipo de leitura/escrita para executar os processos sobre o dado recebido(arquivo .db ou .csv)
##### Huffman
Codigo de Huffman especializado para o Arquivo CSV 
##### HuffmanByte
Codigo de Huffman especializado para qualquer arquivo, pois lê e escreve em byte
<br>e serão chamadas por ```callerCompact```
##### LZW
Foi dividido em 2
###### LZWC
Codigo de LZW para compactação especializado para qualquer arquivo, pois lê e escreve em byte assim como o HuffmanByte, 
<br>é uma pseudo-dependente de LZWD, pois somente descompacta se chamar LZWD, porem compacta sem depender de LZWD

###### LZWD
Codigo de LZW para descompactação especializado para qualquer arquivo, pois lê e escreve em byte, é uma pseudo-dependente de LZWC, 
<br>pois somente descompacta se chamada por LZWC

##### Testes com LZ77 e LZ78
Codigo de LZW para compactação e descompactação especializado para qualquer arquivo, 
<br>pois lê e escreve em byte, representados e implementados na classes presentes 
<br>na pasta ```estagio3/addons```, tem por foco o teste de compactação em arquivos pequenos 

[Link para pasta da etapa 5](https://github.com/kasshinokun/Q1_Q2_2025_Public/blob/main/Aulas_AED3/TP_AEDS_III_E5)
#### Etapa 4 e 5
Buscou-se fazer a migração para Streamlit-Python, porém a versão final foi em Java
##### Python
[Projeto-Prototipo Pasta de testes e deploy](https://github.com/kasshinokun/Q1_Q2_2025_Public/tree/main/Aulas_AED3/Python_Adapt)

Arquivo de Indice: [ID-cabeçalho-int]-->[Índices]
<br>Estrutura de Índice: [ID-int][validador-bool][checksum-String][Posição-long]
<br><br>Arquivo de dados: [ID-cabeçalho-int]-->[Registros]
<br>Estrutura de Registros: [ID-int][validador-bool][checksum-String][Registro em Dicionario JSON-vetor de bytes]
<br>
<br>Índice invertido de Buckets de Arvore B, para acelerar buscas(não chegou a ser implementado)
<br>
<br>Objetivo para estrutura da aplicação:
<br>Procedimento Main: chama procedimento de etapa como uma função ou procedimento Python
<br><br>-->Páginas:
<br>Ver Todos: Visualizaria todos como Dicionario JSON ou como Objeto, paginados de 20 a 100 registros por página
<br>Buscar por ID: Busca por ID e pseudo índice invertido, visualizaria como Dicionario JSON ou como Objeto
<br>Buscar por ID: Busca por ID e pseudo índice invertido, visualizaria como Dicionario JSON ou como Objeto
<br>Atualizar por ID: Busca por ID , visualizaria como Dicionario JSON ou como Objeto e atualiza
<br>Excluir por ID: Busca por ID , visualizaria como Dicionario JSON ou como Objeto e exclui
<br>Compactação: processos em LZW e Huffman, com grafico comparativo
<br>Criptografia: Criptografia em Blowfish, AES Padrão, AES-RSA e por Cifragem Vigenere-Cesár
<br>Busca por Casamento Padrão: Usaria a estrutura do índice invertido de arvore b para trazer as ID's com os padroes
##### Versão Final em Java (ver link para pasta etapa 5)
Foi feita a adaptação para aproximar o código Java a estrutura em Python
<br>Cada etapa foi um estágio, tendo Vigenere-Cesar como apendice de StageFour(Estagio 4) e teste de toda estrutura no módulo 5
<br>O Modulo/Estágio I - Essencialmente operções CRUD sem melhorias e busca simples com adicional do Aho-Corasik
<br>O Modulo/Estágio II - operções CRUD com melhorias e busca sofisticada usando indice e indice invertido, além da busca com adicional do Aho-Corasik
<br>Criptografia e Compactação seguirão os moldes do projeto em Python

