import struct

class Pessoa:
    def __init__(self, nome: str, idade: int, posicaobyte: int):
        self.nome = nome
        self.idade = idade
        self.posicaobyte = posicaobyte
    def __str__(self) -> str:
        return f"Pessoa(nome='{self.nome}', idade={self.idade}, posicaobyte={self.posicaobyte})"
    
    def __repr__(self) -> str:
        return self.__str__()

if __name__ == "__main__":
    # Criando uma pessoa
    pessoa1 = Pessoa("João Silva", 30, 123456789)

    # Convertendo para bytes
   
    print(f"Bytes: {pessoa1}")

   