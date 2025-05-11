package test_d;




public class ArvoreB2 {}
// === Optimized ArvoreB (B-Tree) ===
// Keys = int, Values = long
/*
import java.io.*;

public class ArvoreB2 {
    private File indexDir;
    private File file;
    private RandomAccessFile indexFile;
    private short ordem;

    private static final int BYTES_PER_PAIR = 4 + 8 + 8; // int key + long value + long rightSon
    private static final int BYTES_PER_SON = 8; // long

    public ArvoreB2(String fileName, short ordem) throws IOException {
        this.ordem = ordem;
        indexDir = new File("index");
        indexDir.mkdir();
        this.file = new File("index/" + fileName);
        this.indexFile = new RandomAccessFile(file, "rw");

        if (indexFile.length() == 0) {
            indexFile.seek(0);
            indexFile.writeLong(8);
            indexFile.write(criarPagina());
        }
    }

    public byte[] criarPagina() throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DataOutputStream dos = new DataOutputStream(baos);
        dos.writeShort(0); // n pairs

        // pairs (int key + long value + long right son)
        for (int i = 0; i < this.ordem - 1; i++) {
            dos.writeInt(-1);
            dos.writeLong(-1);
            dos.writeLong(-1);
        }

        // sons (ordem pointers)
        for (int i = 0; i < this.ordem; i++) {
            dos.writeLong(-1);
        }

        return baos.toByteArray();
    }

    public void inserir(int chave, long endereco) throws Exception {
        indexFile.seek(0);
        long raizPos = indexFile.readLong();
        KeyAddressPair aux = inserir(chave, endereco, raizPos);

        if (aux != null) {
            // split root: create new root
            long novaRaizPos = indexFile.length();
            Pagina raiz = new Pagina(criarPagina(), this.ordem);
            raiz.setPairAtIndexOf(aux, 0);
            raiz.setN((short) 1);

            raiz.setSonAtIndexOf(aux.getLeftSon(), 0);
            raiz.setSonAtIndexOf(aux.getRightSon(), 1);

            indexFile.seek(0);
            indexFile.writeLong(novaRaizPos);
            indexFile.seek(novaRaizPos);
            indexFile.write(raiz.getBa());
        }
    }
	*//*
    private KeyAddressPair inserir(int chave, long endereco, long pagPos) throws Exception {
        Pagina pag = readPagina(pagPos);

        if (!pag.isLeaf()) {
            int i;
            for (i = 0; i < pag.getN(); i++) {
                if (chave < pag.getPairAtIndexOf(i).getKey()) {
                    break;
                }
            }
            long filhoPos = pag.getSonAtIndexOf(i);
            KeyAddressPair promoted = inserir(chave, endereco, filhoPos);

            if (promoted == null) return null;

            if (pag.getN() < this.ordem - 1) {
                inserirOrdenado(promoted, pag);
                pag.setSonAtIndexOf(promoted.getLeftSon(), getSonIndex(promoted, pag));
                pag.setSonAtIndexOf(promoted.getRightSon(), getSonIndex(promoted, pag) + 1);
                writePagina(pag, pagPos);
                return null;
            } else {
                return split(pag, promoted, pagPos);
            }
        } else {
            // Leaf insertion
            if (pag.getN() < this.ordem - 1) {
                KeyAdressPair novoPar = new KeyAdressPair(chave, endereco);
                inserirOrdenado(novoPar, pag);
                writePagina(pag, pagPos);
                return null;
            } else {
                KeyAdressPair novoPar = new KeyAdressPair(chave, endereco);
                return split(pag, novoPar, pagPos);
            }
        }
    }
*//*
    private KeyAdressPair split(Pagina pag, KeyAdressPair novoPar, long pagPos) throws Exception {
        KeyAdressPair[] temp = new KeyAdressPair[this.ordem];
        for (int i = 0; i < pag.getN(); i++) temp[i] = pag.getPairAtIndexOf(i);
        temp[pag.getN()] = novoPar;

        Arrays.sort(temp, Comparator.comparingInt(KeyAdressPair::getKey));

        int meio = this.ordem / 2;
        KeyAdressPair promovido = temp[meio];

        Pagina pagEsq = new Pagina(criarPagina(), this.ordem);
        Pagina pagDir = new Pagina(criarPagina(), this.ordem);

        for (int i = 0; i < meio; i++) inserirOrdenado(temp[i], pagEsq);
        for (int i = meio + 1; i < this.ordem; i++) inserirOrdenado(temp[i], pagDir);

        long posDir = indexFile.length();
        writePagina(pagEsq, pagPos);
        writePagina(pagDir, posDir);

        promovido.setLeftSon(pagPos);
        promovido.setRightSon(posDir);

        return promovido;
    }

    private void inserirOrdenado(KeyAddressPair pair, Pagina pagina) throws Exception {
        int i = pagina.getN();
        while (i > 0 && pagina.getPairAtIndexOf(i - 1).getKey() > pair.getKey()) {
            pagina.setPairAtIndexOf(pagina.getPairAtIndexOf(i - 1), i);
            i--;
        }
        pagina.setPairAtIndexOf(pair, i);
        pagina.setN((short) (pagina.getN() + 1));
    }

    private int getSonIndex(KeyAddressPair pair, Pagina pag) throws Exception {
        for (int i = 0; i < pag.getN(); i++) {
            if (pag.getPairAtIndexOf(i).getKey() == pair.getKey()) return i;
        }
        return pag.getN();
    }

    private Pagina readPagina(long pos) throws Exception {
        int size = 2 + (BYTES_PER_PAIR * (ordem - 1)) + (BYTES_PER_SON * ordem);
        byte[] ba = new byte[size];
        indexFile.seek(pos);
        indexFile.readFully(ba);
        return new Pagina(ba, ordem);
    }

    private void writePagina(Pagina pag, long pos) throws IOException {
        indexFile.seek(pos);
        indexFile.write(pag.getBa());
    }
}
*/
