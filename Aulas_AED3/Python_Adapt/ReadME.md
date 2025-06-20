### Trabalho Prático de Algoritmos e Estruturas de Dados III 
Instituição: PUC Minas – Coração Eucarístico
<br>Turma: 91.30.100 2025-1
<br>Matéria: Algoritmos e Estruturas de Dados III 
<br>Aluno: Gabriel da Silva Cassino 
<br>
- Base de dados:
   - [Projeto na Web - Prototipo](https://tpaeds320251.streamlit.app/)
  
<br>
[Link para pasta Inicial](https://github.com/kasshinokun/Q1_Q2_2025_Public/blob/main/Aulas_AED3/)
<br>
[Link para pasta da etapa 5](https://github.com/kasshinokun/Q1_Q2_2025_Public/blob/main/Aulas_AED3/TP_AEDS_III_E5)
#### Etapa 4 e 5
Buscou-se fazer a migração para Streamlit-Python, porém a versão final foi em Java
##### Python - descrição (Ver pasta Deploy)
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

