package object.professor;

//Criado por Professor Wallison

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
public class ClienteDAO {
    private Arquivo<Cliente> arqClientes;

    public ClienteDAO() throws Exception {
        arqClientes = new Arquivo<>("clientes", Cliente.class.getConstructor());
    }

    public Cliente buscarCliente(int id) throws Exception {
        return arqClientes.read(id);
    }

    public boolean incluirCliente(Cliente cliente) throws Exception {
        return arqClientes.create(cliente) > 0;
    }

    public boolean alterarCliente(Cliente cliente) throws Exception {
        return arqClientes.update(cliente);
    }

    public boolean excluirCliente(int id) throws Exception {
        return arqClientes.delete(id);
    }
}
