package object.professor;

//Criado por Professor Wallison

import java.io.IOException;

public interface Registro {
    public void setId(int i);
    public int getId();
    public byte[] toByteArray() throws IOException;
    public void fromByteArray(byte[] b) throws IOException;
}
