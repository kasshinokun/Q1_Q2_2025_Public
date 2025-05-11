package TP_AED_3_2023.data.caesar;//Nome do subprojeto

//Este código é uma adaptação pode haver traços proveniente dos exemplos estudados
//Mas a minha lógica foi implementada


import TP_AED_3_2023.data.caesar.*;//import do package

public class Caesar {

    public static final char START_ASC_II = ' '; // ASCII-32
    public static final char END_ASC_II = '~';   // ASCII-126
    
    public static final int ASC_II_SIZE=END_ASC_II - START_ASC_II + 1;//Intervalo de 95
    
    public static final char START_ASC_II_EX = (char)161; // ASCII-161
    public static final char END_ASC_II_EX = (char)256;   // ASCII-256
    
    public static final int ASC_II_EX_SIZE=END_ASC_II_EX - START_ASC_II_EX + 1;//Intervalo de 96 
    
    public static String encrypt(String input, int shift){
        // cria um stream de saida com o mesmo tamanho da String
        StringBuilder output = new StringBuilder(input.length());

        for (int i = 0; i < input.length(); i++) {
            
            //obtem o proximo caracter
            char inputChar = input.charAt(i);
            
            // calculate o deslocamento
            int calculatedShift = shift;

            char startOfAlphabet;//caracter para receber o valor
            if ((inputChar >= START_ASC_II)
                    && (inputChar <= END_ASC_II)) {//caracteres entre os intervalos
                
                //Atribui o valor Inicial do setor (ASCII 32-126)
                startOfAlphabet = START_ASC_II;
            }else if ((inputChar >= START_ASC_II_EX)
                    && (inputChar <= END_ASC_II_EX)) {//caracteres entre os intervalos
                
                //Atribui o valor Inicial do setor (ASCII 161-256)
                startOfAlphabet = START_ASC_II_EX;
            } else {
                
                //quanto aos demais são adicionados normalmente
                output.append(inputChar);
                
                //e segue para o proximo caracter
                continue;
            }                
                
            //obtem o caracter-base apos subtração de valores entre caracteres
            int inputCharIndex =
                    inputChar - startOfAlphabet;

            //Cifragem por meio do modulo
            int outputCharIndex =
                    (inputCharIndex + calculatedShift) % ASC_II_SIZE;

            // converte o novo indice do caracter de saida na tabela ASCII
            char outputChar =
                    (char) (outputCharIndex + startOfAlphabet);

            //adiciona o caracter temporariamente antes do retorno
            output.append(outputChar);
        }

        return output.toString();//Retorna a string
    }
    public static String decrypt(String input, int shift){
        // cria um stream de saida com o mesmo tamanho da String
        StringBuilder output = new StringBuilder(input.length());

        for (int i = 0; i < input.length(); i++) {
            
            //obtem o proximo caracter
            char inputChar = input.charAt(i);
            
            // calcula o deslocamento reverso
            int calculatedShift = (ASC_II_SIZE - shift);

            char startOfAlphabet;//caracter para receber o valor
            if ((inputChar >= START_ASC_II)
                    && (inputChar <= END_ASC_II)) {//caracteres entre os intervalos
                
                //Atribui o valor Inicial do setor (ASCII 32-126)
                startOfAlphabet = START_ASC_II;
            }else if ((inputChar >= START_ASC_II_EX)
                    && (inputChar <= END_ASC_II_EX)) {//caracteres entre os intervalos
                
                //Atribui o valor Inicial do setor (ASCII 161-256)
                startOfAlphabet = START_ASC_II_EX;
            }  else {
                
                
                //quanto aos demais são adicionados normalmente
                output.append(inputChar);
                
                //e segue para o proximo caracter
                continue;
                
            }                
                
            //obtem o caracter-base apos subtração de valores entre caracteres
            int inputCharIndex =
                    inputChar - startOfAlphabet;

            //Decifragem por meio do modulo
            int outputCharIndex =
                    (inputCharIndex + calculatedShift) % ASC_II_SIZE;

            // converte o novo indice do caracter de saida na tabela ASCII
            char outputChar =
                    (char) (outputCharIndex + startOfAlphabet);

            //adiciona o caracter temporariamente antes do retorno
            output.append(outputChar);
        }

        return output.toString();//Retorna a string
    
    }
}