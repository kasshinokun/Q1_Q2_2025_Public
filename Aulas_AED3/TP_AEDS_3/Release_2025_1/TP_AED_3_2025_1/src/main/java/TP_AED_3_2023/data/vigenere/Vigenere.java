package TP_AED_3_2023.data.vigenere;//Nome do subprojeto

//Este código é uma adaptação pode haver traços proveniente dos exemplos estudados
//Mas a minha lógica foi implementada

public class Vigenere {
    
    public static final char START_ASC_II = ' '; // ASCII-32
    public static final char END_ASC_II = '~';   // ASCII-126
    
    public static final int ASC_II_SIZE=END_ASC_II - START_ASC_II + 1;//Intervalo de 95
    
    public static final char START_ASC_II_EX = (char)161; // ASCII-161
    public static final char END_ASC_II_EX = (char)256;   // ASCII-256
    
    public static final int ASC_II_EX_SIZE=END_ASC_II_EX - START_ASC_II_EX + 1;//Intervalo de 96 
    
    public static final int ASC_II_ALL_SIZE=ASC_II_SIZE + ASC_II_EX_SIZE;//Soma dos Intervalos

    private int textSize;//String Recebida
    private int keySize;//Tamanho da Chave
    private String key;//String Chave

    public Vigenere(){}//Construtor padrão
    
    //Construtor por parâmetro(Somente a Chave)
    public Vigenere(String key){
        setKeySize(key);
        setKey(key);
    }
    //Construtor por parâmetro(String Recebida e Chave)
    public Vigenere(String plaintext, String key){
        setTextSize(plaintext);
        setKeySize(key);
        setKey(key);
    }
    //Setters
    public void setTextSize(String plaintext){
        this.textSize = plaintext.length();
    }
    public void setKeySize(String key){
        this.keySize = key.length();
    }
    public void setKey(String key){
        this.key=key;
    }
    //Getters
    public int getTextSize(){
        return this.textSize;
    }
    public int getKeySize(){
        return this.keySize;
    }
    public String getKey(){
        return this.key;
    }
    //Cifragem de Vigenere
    public String Encrypt(String plaintext){
        if(getKey()==""){
            System.out.println("CHAVE Não Encontrada");
            return"";
        }else{
            setTextSize(plaintext);//Instancia na classe
            
            //Instancia o StringBuilder para cria a nova String
            final StringBuilder encryptedText = new StringBuilder(getTextSize());
            for (int i = 0; i < getTextSize(); i++) {
                final char plainChar = plaintext.charAt(i);

                //este deve ser um método, chamado tanto para o texto simples quanto para a chave
                //String recebida
                final int plainGroupNumber; 
                if (plainChar >= START_ASC_II && plainChar <= END_ASC_II) {
                    plainGroupNumber = plainChar - START_ASC_II;
                } else if (plainChar >= START_ASC_II_EX && plainChar <= END_ASC_II_EX) {
                    plainGroupNumber = ASC_II_SIZE + plainChar - START_ASC_II_EX;
                } else {
                    //simplesmente mantem os outros caracteres
                    encryptedText.append(plainChar);
                    continue;
                }
                //Chave
                final char keyChar = getKey().charAt(i % getKeySize());
                final int keyGroupNumber; 
                if (keyChar >= START_ASC_II && keyChar <= END_ASC_II) {
                    keyGroupNumber = keyChar - START_ASC_II;
                } else if (keyChar >= START_ASC_II_EX && keyChar <= END_ASC_II_EX) {
                    keyGroupNumber = ASC_II_SIZE + keyChar - START_ASC_II_EX;
                } else {
                    throw new IllegalStateException("Caracter Invalido na CHAVE");
                }

                //este deve ser um método separado
                final int cipherGroupNumber;
                //Soma as variaveis e aplica modulo da soma
                cipherGroupNumber = (plainGroupNumber + keyGroupNumber) % ASC_II_ALL_SIZE;

                //código para contornar a maneira estranha de lidar com modulo 
                //em Java para números negativos
                final char cipherChar;
                if (cipherGroupNumber < ASC_II_SIZE) {
                    cipherChar = (char) (START_ASC_II + cipherGroupNumber);//Se entre 32 e 126
                } else {
                    cipherChar = (char) (START_ASC_II_EX + cipherGroupNumber - ASC_II_SIZE);//Se entre 161 e 256
                }
                encryptedText.append(cipherChar);//adiciona o caracter
            }

            return encryptedText.toString();//retorna a nova String
        }
    }
    //Decifragem de Vigenere
    public String Decrypt(String plaintext) {
        if(getKey()==""){
            return"";
        }else{
            setTextSize(plaintext);//Instancia na classe
            
            //Instancia o StringBuilder para cria a nova String
            final StringBuilder decryptedText = new StringBuilder(getTextSize());
            for (int i = 0; i < getTextSize(); i++) {
                final char plainChar = plaintext.charAt(i);

                //este deve ser um método, chamado tanto para o texto simples quanto para a chave
                //String recebida
                final int plainGroupNumber; 
                if (plainChar >= START_ASC_II && plainChar <= END_ASC_II) {
                    plainGroupNumber = plainChar - START_ASC_II;
                } else if (plainChar >= START_ASC_II_EX && plainChar <= END_ASC_II_EX) {
                    plainGroupNumber = ASC_II_SIZE + plainChar - START_ASC_II_EX;
                } else {
                    //simplesmente mantem os outros caracteres
                    decryptedText.append(plainChar);
                    continue;
                }
                //Chave
                final char keyChar = getKey().charAt(i % getKeySize());
                final int keyGroupNumber; 
                if (keyChar >= START_ASC_II && keyChar <= END_ASC_II) {
                    keyGroupNumber = keyChar - START_ASC_II;
                } else if (keyChar >= START_ASC_II && keyChar <= END_ASC_II_EX) {
                    keyGroupNumber = ASC_II_SIZE + keyChar - START_ASC_II;
                } else {
                    throw new IllegalStateException("Caracter Invalido na CHAVE");
                }

                //este deve ser um método separado
                final int cipherGroupNumber;
                

                //código para contornar resultado 
                //em Java com números negativos
                final int someCipherGroupNumber = plainGroupNumber - keyGroupNumber;
                if (someCipherGroupNumber < 0) {
                    cipherGroupNumber = (someCipherGroupNumber + ASC_II_ALL_SIZE);//realiza uma soma com intervalo geral
                } else {
                    cipherGroupNumber = someCipherGroupNumber;//Aplica o valor recebido
                }


                //este deve ser um método separado(Definindo o char)
                //código para contornar resultado 
                //em Java com números negativos
                final char cipherChar;
                if (cipherGroupNumber < ASC_II_SIZE) {
                    cipherChar = (char) (START_ASC_II + cipherGroupNumber);//Se entre 32 e 126
                } else {
                    cipherChar = (char) (START_ASC_II_EX + cipherGroupNumber - ASC_II_SIZE);//Se entre 161 e 256
                }
                decryptedText.append(cipherChar);//adiciona o caracter
            }

            return decryptedText.toString();//retorna a nova String
        }
    }
}