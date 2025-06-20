package main;
// Principal ponto de entrada da aplicação
// Este arquivo contém todas as classes unificadas para o sistema de gerenciamento de dados de acidentes.

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.nio.charset.StandardCharsets; // Import for UTF-8 encoding

// Para Criptografia (JCE)
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.KeyFactory;
import java.security.interfaces.RSAPublicKey; // Importado para uso no getModulus
import java.security.interfaces.RSAPrivateKey; // Importado para uso no getModulus
import java.security.spec.InvalidKeySpecException;
import java.security.spec.MGF1ParameterSpec;
import javax.crypto.spec.OAEPParameterSpec;
// Removidos CipherInputStream e CipherOutputStream pois não estavam sendo usados


/**
 * Classe principal para iniciar o Sistema de Gerenciamento de Dados de Acidentes.
 * Esta classe atua como uma ponte para os diferentes módulos (StageOne, StageTwo, StageThree, StageFour)
 * e o teste interno do DataManager.
 */
public class startTrafficAccidents {

    public static void main(String[] args) {
        System.out.println("\n===== Sistema de Dados de Acidentes de Trânsito =====");

        int op = 0;
        do {
            System.out.println("\nSelecione um Módulo:");
            System.out.println("1) Módulo Parte I (Gerenciamento de Dados e Índices - Básico)");
            System.out.println("2) Módulo Parte II (Gerenciamento de Dados Otimizado)");
            System.out.println("3) Módulo Parte III (Compressão de Dados)");
            System.out.println("4) Módulo Parte IV (Criptografia de Dados)");
            System.out.println("5) Rodar Testes de Deleção e Atualização (Interno - DataManager)");
            System.out.println("\n0) Sair do Sistema\n\nEscolha um valor-------> :");
            op = Functions.only_Int();

            switch (op) {
                case 1:
                    StageOne.start();
                    break;
                case 2:
                    StageTwo.start();
                    break;
                case 3:
                    StageThree.start();
                    break;
                case 4:
                    StageFour.start(); // Agora StageFour tem um sub-menu
                    break;
                case 5:
                    System.out.println("\n--- Executando Testes Internos do DataManager ---");
                    AccidentDataApp_TestRunner.runDeletionTests();
                    AccidentDataApp_TestRunner.runUpdateTests();
                    System.out.println("\n--- Testes Internos Concluídos ---");
                    break;
                case 0:
                    System.out.println("\nSaindo do Sistema. Muito Obrigado!\n");
                    break;
                default:
                    System.out.println("\nOpção inválida. Tente novamente.");
            }
        } while (op != 0);
    }
}

// =========================================================================
// CLASSES DE INFRAESTRUTURA (Originalmente de AccidentDataApp.java)
// =========================================================================

/**
 * Implementação do algoritmo Aho-Corasick para busca eficiente de múltiplos padrões em texto.
 */
class AhoCorasick {
    private final Node root;
    private final List<String> patterns;

    /**
     * Classe Node para o autômato Aho-Corasick.
     * Cada nó representa um estado, armazena transições (goto), padrões de saída e um link de falha.
     */
    private static class Node {
        Map<Character, Node> children;
        Set<String> output; // Padrões que terminam neste nó
        Node failureLink;
        int id; // Para depuração/identificação

        public Node(int id) {
            this.id = id;
            this.children = new HashMap<>();
            this.output = new HashSet<>();
        }
    }

    public AhoCorasick(List<String> patterns) {
        this.patterns = patterns;
        this.root = new Node(0);
        buildAutomaton();
    }

    /**
     * Constrói o autômato Aho-Corasick (trie, função goto, links de falha, função de saída).
     */
    private void buildAutomaton() {
        // Insere padrões na trie
        int nodeIdCounter = 0; // A raiz é 0
        for (String pattern : patterns) {
            Node current = root;
            for (char ch : pattern.toCharArray()) {
                current.children.putIfAbsent(ch, new Node(++nodeIdCounter));
                current = current.children.get(ch);
            }
            current.output.add(pattern);
        }

        // Constrói links de falha usando BFS
        Queue<Node> queue = new LinkedList<>();

        // Inicializa links de falha para filhos diretos da raiz
        for (Node child : root.children.values()) {
            child.failureLink = root;
            queue.offer(child);
        }

        while (!queue.isEmpty()) {
            Node r = queue.poll();

            for (Map.Entry<Character, Node> entry : r.children.entrySet()) {
                char ch = entry.getKey();
                Node s = entry.getValue();
                queue.offer(s);

                Node state = r.failureLink;
                // Percorre links de falha até que um estado com uma transição para 'ch' seja encontrado ou a raiz seja alcançada
                while (state != root && !state.children.containsKey(ch)) {
                    state = state.failureLink;
                }

                // Define o link de falha para 's'
                if (state.children.containsKey(ch)) {
                    s.failureLink = state.children.get(ch);
                } else {
                    s.failureLink = root; // Fallback para a raiz
                }

                // Adiciona a saída do link de falha
                s.output.addAll(s.failureLink.output);
            }
        }
    }

    /**
     * Calcula o próximo estado no autômato dado o estado atual e um caractere.
     * @param current O nó/estado atual.
     * @param ch O caractere para transicionar.
     * @return O próximo nó/estado.
     */
    private Node nextState(Node current, char ch) {
        // Percorre links de falha até que um estado com uma transição para 'ch' seja encontrado ou a raiz seja alcançada
        while (current != root && !current.children.containsKey(ch)) {
            current = current.failureLink;
        }

        // Se existir uma transição, siga-a; caso contrário, retorne a raiz
        if (current.children.containsKey(ch)) {
            return current.children.get(ch);
        } else {
            return root;
        }
    }

    /**
     * Busca ocorrências de padrões no texto fornecido.
     * @param text O texto para buscar.
     * @return Uma lista de tuplas, onde cada tupla contém o índice final da correspondência e o padrão correspondente.
     */
    public List<Map.Entry<Integer, String>> search(String text) {
        List<Map.Entry<Integer, String>> foundMatches = new ArrayList<>();
        Node current = root;

        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            current = nextState(current, ch);

            if (!current.output.isEmpty()) {
                for (String pattern : current.output) {
                    foundMatches.add(new AbstractMap.SimpleEntry<>(i, pattern));
                }
            }
        }
        return foundMatches;
    }
}

/**
 * Representa um único registro de acidente, analisando dados de linhas CSV.
 */
class DataObject implements Serializable {
    private static final long serialVersionUID = 1L;

    private String defaultTimeString;
    private transient LocalDateTime crashDate;
    private String trafficControlDevice;
    private String weatherCondition;
    private List<String> lightingCondition;
    private String firstCrashType;
    private String trafficwayType;
    private String alignment;
    private String roadwaySurfaceCond;
    private String roadDefect;
    private List<String> crashType;
    private boolean intersectionRelatedI;
    private String damage;
    private String primContributoryCause;
    private int numUnits;
    private List<String> mostSevereInjury;
    private double injuriesTotal;
    private double injuriesFatal;
    private double injuriesIncapacitating;
    private double injuriesNonIncapacitating;
    private double injuriesReportedNotEvident;
    private double injuriesNoIndication;
    private int crashHour;
    private int crashDayOfWeek;
    private int crashMonth;

    // ATENÇÃO: Adicionado Locale.US para garantir a correta interpretação de "AM/PM"
    private static final DateTimeFormatter DATE_TIME_FORMATTER = DateTimeFormatter.ofPattern("MM/dd/yyyy hh:mm:ss a", Locale.US);

    public DataObject(String defaultTimeString, String trafficControlDevice, String weatherCondition,
                       String lightingCondition, String firstCrashType, String trafficwayType,
                       String alignment, String roadwaySurfaceCond, String roadDefect, String crashType,
                       String intersectionRelatedI, String damage, String primContributoryCause,
                       int numUnits, String mostSevereInjury, double injuriesTotal, double injuriesFatal,
                       double injuriesIncapacitating, double injuriesNonIncapacitating,
                       double injuriesReportedNotEvident, double injuriesNoIndication,
                       int crashHour, int crashDayOfWeek, int crashMonth) {
        this.defaultTimeString = defaultTimeString;
        this.crashDate = parseDateTime(defaultTimeString);
        this.trafficControlDevice = trafficControlDevice;
        this.weatherCondition = weatherCondition;
        this.lightingCondition = toListOfStrings(lightingCondition);
        this.firstCrashType = firstCrashType;
        this.trafficwayType = trafficwayType;
        this.alignment = alignment;
        this.roadwaySurfaceCond = roadwaySurfaceCond;
        this.roadDefect = roadDefect;
        this.crashType = toListOfStrings(crashType);
        this.intersectionRelatedI = Functions.getBooleanFromString(intersectionRelatedI);
        this.damage = damage;
        this.primContributoryCause = primContributoryCause;
        this.numUnits = numUnits;
        this.mostSevereInjury = toListOfStrings(mostSevereInjury);
        this.injuriesTotal = injuriesTotal;
        this.injuriesFatal = injuriesFatal;
        this.injuriesIncapacitating = injuriesIncapacitating;
        this.injuriesNonIncapacitating = injuriesNonIncapacitating;
        this.injuriesReportedNotEvident = injuriesReportedNotEvident;
        this.injuriesNoIndication = injuriesNoIndication;
        this.crashHour = crashHour;
        this.crashDayOfWeek = (crashDate != null) ? Functions.getDayWeek(crashDate.toLocalDate()) : crashDayOfWeek;
        this.crashMonth = (crashDate != null) ? Functions.getNumMonth(crashDate.toLocalDate()) : crashMonth;
    }

    // Construtor para desserialização de Map
    public DataObject(Map<String, Object> dataMap) {
        this.defaultTimeString = (String) dataMap.get("default_time_string");
        this.crashDate = parseDateTime(this.defaultTimeString);
        this.trafficControlDevice = (String) dataMap.get("traffic_control_device");
        this.weatherCondition = (String) dataMap.get("weather_condition");
        this.lightingCondition = toListOfStrings((String) dataMap.get("lighting_condition"));
        this.firstCrashType = (String) dataMap.get("first_crash_type");
        this.trafficwayType = (String) dataMap.get("trafficway_type");
        this.alignment = (String) dataMap.get("alignment");
        this.roadwaySurfaceCond = (String) dataMap.get("roadway_surface_cond");
        this.roadDefect = (String) dataMap.get("road_defect");
        this.crashType = toListOfStrings((String) dataMap.get("crash_type"));
        this.intersectionRelatedI = (boolean) dataMap.get("intersection_related_i");
        this.damage = (String) dataMap.get("damage");
        this.primContributoryCause = (String) dataMap.get("prim_contributory_cause");
        this.numUnits = ((Number) dataMap.get("num_units")).intValue();
        this.mostSevereInjury = toListOfStrings((String) dataMap.get("most_severe_injury"));
        this.injuriesTotal = ((Number) dataMap.get("injuries_total")).doubleValue();
        this.injuriesFatal = ((Number) dataMap.get("injuries_fatal")).doubleValue();
        this.injuriesIncapacitating = ((Number) dataMap.get("injuries_incapacitating")).doubleValue();
        this.injuriesNonIncapacitating = ((Number) dataMap.get("injuries_non_incapacitating")).doubleValue();
        this.injuriesReportedNotEvident = ((Number) dataMap.get("injuries_reported_not_evident")).doubleValue();
        this.injuriesNoIndication = ((Number) dataMap.get("injuries_no_indication")).doubleValue();
        this.crashHour = ((Number) dataMap.get("crash_hour")).intValue();
        this.crashDayOfWeek = ((Number) dataMap.get("crash_day_of_week")).intValue();
        this.crashMonth = ((Number) dataMap.get("crash_month")).intValue();
    }

    private LocalDateTime parseDateTime(String timeString) {
        if (timeString == null || timeString.trim().isEmpty()) {
            System.err.println("Aviso: String de data/hora vazia ou nula. Retornando null para crashDate.");
            return null;
        }
        try {
            return LocalDateTime.parse(timeString, DATE_TIME_FORMATTER);
        } catch (DateTimeParseException e) {
            // Imprime a mensagem de erro da exceção para depuração
            System.err.println("Erro ao analisar data/hora '" + timeString + "': " + e.getMessage());
            // Sugestão para o usuário (pode ser removida em produção se o logging for usado)
            System.err.println("Verifique se o formato da data no CSV corresponde a 'MM/dd/yyyy hh:mm:ss a' (ex: '01/01/2023 12:00:00 PM').");
            return null;
        }
    }

    private List<String> toListOfStrings(String value) {
        if (value == null || value.trim().isEmpty()) {
            return new ArrayList<>();
        }
        // Tentativa de dividir por ',' ou '/' se ambos estiverem presentes ou apenas um.
        // Se a string contiver ambos os delimitadores e eles precisarem de tratamento mais sofisticado,
        // uma lógica de parsing mais complexa ou uma biblioteca de CSV seria necessária.
        if (value.contains(",") && value.contains("/")) {
            return Arrays.stream(value.split("[,/]+")) // Divide por um ou mais vírgulas ou barras
                    .map(String::trim)
                    .filter(s -> !s.isEmpty())
                    .collect(Collectors.toList());
        } else if (value.contains(",")) {
            return Arrays.stream(value.split(","))
                    .map(String::trim)
                    .filter(s -> !s.isEmpty())
                    .collect(Collectors.toList());
        } else if (value.contains("/")) {
            return Arrays.stream(value.split("/"))
                    .map(String::trim)
                    .filter(s -> !s.isEmpty())
                    .collect(Collectors.toList());
        } else {
            // Se nenhum delimitador for encontrado, trate a string inteira como um único item
            return Arrays.asList(value.trim());
        }
    }

    private String toSingleString(List<String> valueList) {
        return String.join(",", valueList);
    }

    public static DataObject fromCsvRow(String rowString) throws IllegalArgumentException {
        // Usa um delimitador que é menos provável de estar dentro dos campos (se os campos contêm vírgulas, por exemplo)
        // Se os campos podem ter ";" dentro deles, uma abordagem mais robusta seria necessária (ex: bibliotecas CSV)
        String[] parts = rowString.strip().split(";");
        // Verifica o número exato de partes esperado (24 colunas)
        if (parts.length != 24) {
            throw new IllegalArgumentException(String.format("Formato de linha inválido. Esperado 24 colunas, obtido %d. Linha: '%s'", parts.length, rowString));
        }

        // Helper para análise segura de inteiros
        Function<String, Integer> safeInt = (val) -> {
            try {
                // Tenta remover caracteres não numéricos, exceto ponto decimal para floats
                String cleanedVal = val.trim().replaceAll("[^\\d.-]", ""); // Permite dígitos, ponto e hífen para negativos
                if (cleanedVal.isEmpty()) return 0; // Se ficar vazio após a limpeza, retorna 0
                return Integer.parseInt(cleanedVal);
            } catch (NumberFormatException | NullPointerException e) {
                // Loga o erro, mas não o lança, para continuar o processamento da linha
                System.err.println("Aviso: Falha ao analisar inteiro '" + val + "'. Usando 0. Erro: " + e.getMessage());
                return 0;
            }
        };

        // Helper para análise segura de doubles/floats
        Function<String, Double> safeFloat = (val) -> {
            try {
                String cleanedVal = val.trim().replaceAll("[^\\d.]", ""); // Permite dígitos e ponto decimal
                if (cleanedVal.isEmpty()) return 0.0;
                return Double.parseDouble(cleanedVal);
            } catch (NumberFormatException | NullPointerException e) {
                System.err.println("Aviso: Falha ao analisar double/float '" + val + "'. Usando 0.0. Erro: " + e.getMessage());
                return 0.0;
            }
        };

        return new DataObject(
                parts[0].trim(), // default_time_string
                parts[1].trim(), // traffic_control_device
                parts[2].trim(), // weather_condition
                parts[3].trim(), // lighting_condition
                parts[4].trim(), // first_crash_type
                parts[5].trim(), // trafficway_type
                parts[6].trim(), // alignment
                parts[7].trim(), // roadway_surface_cond
                parts[8].trim(), // road_defect
                parts[9].trim(), // crash_type
                parts[10].trim(), // intersection_related_i (String "S" or "N")
                parts[11].trim(), // damage
                parts[12].trim(), // prim_contributory_cause
                safeInt.apply(parts[13]), // num_units
                parts[14].trim(), // most_severe_injury
                safeFloat.apply(parts[15]), // injuries_total
                safeFloat.apply(parts[16]), // injuries_fatal
                safeFloat.apply(parts[17]), // injuries_incapacitating
                safeFloat.apply(parts[18]), // injuries_non_incapacitating
                safeFloat.apply(parts[19]), // injuries_reported_not_evident
                safeFloat.apply(parts[20]), // injuries_no_indication
                safeInt.apply(parts[21]), // crash_hour
                safeInt.apply(parts[22]), // crash_day_of_week (will be overwritten if crashDate is parsed)
                safeInt.apply(parts[23]) // crash_month (will be overwritten if crashDate is parsed)
        );
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("default_time_string", defaultTimeString);
        map.put("traffic_control_device", trafficControlDevice);
        map.put("weather_condition", weatherCondition);
        map.put("lighting_condition", toSingleString(lightingCondition));
        map.put("first_crash_type", firstCrashType);
        map.put("trafficway_type", trafficwayType);
        map.put("alignment", alignment);
        map.put("roadway_surface_cond", roadwaySurfaceCond);
        map.put("road_defect", roadDefect);
        map.put("crash_type", toSingleString(crashType));
        map.put("intersection_related_i", intersectionRelatedI); // Boolean directly
        map.put("damage", damage);
        map.put("prim_contributory_cause", primContributoryCause);
        map.put("num_units", numUnits);
        map.put("most_severe_injury", toSingleString(mostSevereInjury));
        map.put("injuries_total", injuriesTotal);
        map.put("injuries_fatal", injuriesFatal);
        map.put("injuries_incapacitating", injuriesIncapacitating);
        map.put("injuries_non_incapacitating", injuriesNonIncapacitating);
        map.put("injuries_reported_not_evident", injuriesReportedNotEvident);
        map.put("injuries_no_indication", injuriesNoIndication);
        map.put("crash_hour", crashHour);
        map.put("crash_day_of_week", (crashDate != null) ? Functions.getDayWeek(crashDate.toLocalDate()) : 0);
        map.put("crash_month", (crashDate != null) ? Functions.getNumMonth(crashDate.toLocalDate()) : 0);
        return map;
    }

    // Getters para campos relevantes para indexação e exibição
    public List<String> getCrashType() { return crashType; }
    public double getInjuriesTotal() { return injuriesTotal; }
    public List<String> getLightingCondition() { return lightingCondition; }
    public List<String> getMostSevereInjury() { return mostSevereInjury; }
    public String getDefaultTimeString() { return defaultTimeString; }
    public String getTrafficControlDevice() { return trafficControlDevice; }
    public String getWeatherCondition() { return weatherCondition; }
    public String getFirstCrashType() { return firstCrashType; }
    public String getTrafficwayType() { return trafficwayType; }
    public String getAlignment() { return alignment; }
    public String getRoadwaySurfaceCond() { return roadwaySurfaceCond; }
    public String getRoadDefect() { return roadDefect; }
    public boolean getIntersectionRelatedI() { return intersectionRelatedI; }
    public String getDamage() { return damage; }
    public String getPrimContributoryCause() { return primContributoryCause; }
    public int getNumUnits() { return numUnits; }
    public double getInjuriesFatal() { return injuriesFatal; }
    public double getInjuriesIncapacitating() { return injuriesIncapacitating; }
    public double getInjuriesNonIncapacitating() { return injuriesNonIncapacitating; }
    public double getInjuriesReportedNotEvident() { return injuriesReportedNotEvident; }
    public double getInjuriesNoIndication() { return injuriesNoIndication; }
    public int getCrashHour() { return crashHour; }
    public int getCrashDayOfWeek() { return (crashDate != null) ? Functions.getDayWeek(crashDate.toLocalDate()) : 0; }
    public int getCrashMonth() { return (crashDate != null) ? Functions.getNumMonth(crashDate.toLocalDate()) : 0; }
    public LocalDateTime getCrashDate() { return crashDate; }

    @Override
    public String toString() {
        return "DataObject{" +
                "defaultTimeString='" + defaultTimeString + '\'' +
                ", crashType=" + crashType +
                ", injuriesTotal=" + injuriesTotal +
                '}';
    }
}

/**
 * Gerencia a serialização e desserialização de instâncias DataObject para/de arrays de bytes,
 * incluindo um cabeçalho com ID do registro, flag de validade e um checksum SHA256.
 */
class DataRecord implements Serializable {
    public static final String HEADER_FORMAT_STRING = "I?32sI";
    public static final int HEADER_SIZE = 4 + 1 + 32 + 4; // int + boolean + 32 bytes + int = 41 bytes

    private final int recordId;
    private final DataObject dataObject;
    private boolean isValid;

    public DataRecord(int recordId, DataObject dataObject, boolean isValid) {
        this.recordId = recordId;
        this.dataObject = dataObject;
        this.isValid = isValid;
    }

    public byte[] serialize() throws IOException, NoSuchAlgorithmException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        ObjectOutputStream oos = new ObjectOutputStream(bos);
        oos.writeObject(dataObject.toMap());
        oos.flush();
        byte[] dataBytes = bos.toByteArray();

        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] checksum = digest.digest(dataBytes);

        ByteBuffer headerBuffer = ByteBuffer.allocate(HEADER_SIZE);
        headerBuffer.order(ByteOrder.BIG_ENDIAN);

        headerBuffer.putInt(recordId);
        headerBuffer.put((byte) (isValid ? 1 : 0));
        headerBuffer.put(checksum);
        headerBuffer.putInt(dataBytes.length);

        ByteBuffer fullRecordBuffer = ByteBuffer.allocate(HEADER_SIZE + dataBytes.length);
        fullRecordBuffer.put(headerBuffer.array());
        fullRecordBuffer.put(dataBytes);

        return fullRecordBuffer.array();
    }

    public static DataRecord deserialize(byte[] recordBytes) throws IOException, ClassNotFoundException, NoSuchAlgorithmException {
        if (recordBytes.length < HEADER_SIZE) {
            throw new IllegalArgumentException("Buffer de bytes muito pequeno para conter o cabeçalho.");
        }

        ByteBuffer headerBuffer = ByteBuffer.wrap(recordBytes, 0, HEADER_SIZE);
        headerBuffer.order(ByteOrder.BIG_ENDIAN);

        int recordId = headerBuffer.getInt();
        boolean isValid = headerBuffer.get() == 1;
        byte[] checksumRead = new byte[32];
        headerBuffer.get(checksumRead);
        int dataSize = headerBuffer.getInt();

        if (recordBytes.length < HEADER_SIZE + dataSize) {
            throw new IllegalArgumentException("Buffer de bytes muito pequeno para conter todos os dados.");
        }

        byte[] dataBytes = Arrays.copyOfRange(recordBytes, HEADER_SIZE, HEADER_SIZE + dataSize);

        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] calculatedChecksum = digest.digest(dataBytes);

        if (!Arrays.equals(calculatedChecksum, checksumRead)) {
            System.err.println("Incompatibilidade de checksum para o ID do registro " + recordId + ". Os dados podem estar corrompidos.");
            isValid = false;
        }

        ByteArrayInputStream bis = new ByteArrayInputStream(dataBytes);
        ObjectInputStream ois = null;
        DataObject dataObject;
        try {
            ois = new ObjectInputStream(bis);
            @SuppressWarnings("unchecked")
            Map<String, Object> dataDict = (Map<String, Object>) ois.readObject();
            dataObject = new DataObject(dataDict);
        } finally {
            if (ois != null) {
                ois.close();
            }
        }


        return new DataRecord(recordId, dataObject, isValid);
    }

    public int getRecordId() { return recordId; }
    public DataObject getDataObject() { return dataObject; }
    public boolean isValid() { return isValid; }
    public void setValid(boolean valid) { isValid = valid; }
}

/**
 * Representa uma entrada no arquivo de índice, armazenando um ID de registro, sua posição e um sinalizador de validade.
 */
class IndexEntry {
    public static final String ENTRY_FORMAT_STRING = "I?Q";
    public static final int ENTRY_SIZE = 4 + 1 + 8; // int + boolean + long = 13 bytes

    private final int recordId;
    private final long position;
    private boolean isValid;

    public IndexEntry(int recordId, long position, boolean isValid) {
        this.recordId = recordId;
        this.position = position;
        this.isValid = isValid;
    }

    public byte[] serialize() {
        ByteBuffer buffer = ByteBuffer.allocate(ENTRY_SIZE);
        buffer.order(ByteOrder.BIG_ENDIAN);
        buffer.putInt(recordId);
        buffer.put((byte) (isValid ? 1 : 0));
        buffer.putLong(position);
        return buffer.array();
    }

    public static IndexEntry deserialize(byte[] entryBytes) {
        if (entryBytes.length < ENTRY_SIZE) {
            throw new IllegalArgumentException("Buffer de bytes muito pequeno para conter a entrada do índice.");
        }
        ByteBuffer buffer = ByteBuffer.wrap(entryBytes);
        buffer.order(ByteOrder.BIG_ENDIAN);
        int recordId = buffer.getInt();
        boolean isValid = buffer.get() == 1;
        long position = buffer.getLong();
        return new IndexEntry(recordId, position, isValid);
    }

    public int getRecordId() { return recordId; }
    public long getPosition() { return position; }
    public boolean isValid() { return isValid; }
    public void setValid(boolean valid) { valid = valid; }
}

/**
 * Gerencia índices invertidos usando persistência baseada em arquivos, imitando o módulo shelve do Python.
 * Cada índice é armazenado como um HashMap serializado para um arquivo separado.
 * Esta abordagem lê/grava todo o mapa ao abrir/fechar/sincronizar.
 */
class InvertedIndexManager {
    private final String invFilepathPrefix;

    private Map<String, List<Integer>> crashTypeIndex;
    private Map<String, List<Integer>> injuriesTotalIndex;
    private Map<String, List<Integer>> lightingConditionIndex;
    private Map<String, List<Integer>> mostSevereInjuryIndex;

    public InvertedIndexManager(String invFilepathPrefix) {
        this.invFilepathPrefix = invFilepathPrefix;
        loadIndexes();
    }

    /**
     * Carrega índices invertidos de seus respectivos arquivos.
     * Se os arquivos não existirem, inicializa mapas vazios.
     */
    @SuppressWarnings("unchecked")
    private void loadIndexes() {
        crashTypeIndex = loadMapFromFile(invFilepathPrefix + "_crash_type.dat");
        injuriesTotalIndex = loadMapFromFile(invFilepathPrefix + "_injuries_total.dat");
        lightingConditionIndex = loadMapFromFile(invFilepathPrefix + "_lighting_condition.dat");
        mostSevereInjuryIndex = loadMapFromFile(invFilepathPrefix + "_most_severe_injury.dat");
    }

    /**
     * Auxiliar para carregar um HashMap de um arquivo.
     */
    private Map<String, List<Integer>> loadMapFromFile(String filename) {
        try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream(filename))) {
            return (Map<String, List<Integer>>) ois.readObject();
        } catch (FileNotFoundException e) {
            System.out.println("Arquivo de índice não encontrado: " + filename + ". Iniciando com índice vazio.");
            return new HashMap<>();
        } catch (IOException | ClassNotFoundException e) {
            System.err.println("Erro ao carregar índice de " + filename + ": " + e.getMessage());
            return new HashMap<>();
        }
    }

    /**
     * Auxiliar para salvar um HashMap em um arquivo.
     */
    private void saveMapToFile(Map<String, List<Integer>> map, String filename) {
        try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(filename))) {
            oos.writeObject(map);
        } catch (IOException e) {
            System.err.println("Erro ao salvar índice em " + filename + ": " + e.getMessage());
        }
    }

    /**
     * Adiciona um ID de registro a uma chave específica em um mapa de índice.
     */
    private void addToIndex(Map<String, List<Integer>> index, String key, int recordId) {
        index.computeIfAbsent(key, k -> new ArrayList<>()).add(recordId);
    }

    /**
     * Remove um ID de registro de todas as listas em um mapa de índice.
     */
    private void removeFromIndex(Map<String, List<Integer>> index, int recordId) {
        Set<String> keysToProcess = new HashSet<>(index.keySet());
        for (String key : keysToProcess) {
            List<Integer> recordIdsList = index.get(key);
            if (recordIdsList != null) {
                recordIdsList.removeIf(id -> id.equals(recordId));
                if (recordIdsList.isEmpty()) {
                    index.remove(key);
                }
            }
        }
    }

    public void addEntry(DataObject dataObject, int recordId) {
        for (String val : dataObject.getCrashType()) {
            addToIndex(crashTypeIndex, val, recordId);
        }
        addToIndex(injuriesTotalIndex, String.valueOf(dataObject.getInjuriesTotal()), recordId);
        for (String val : dataObject.getLightingCondition()) {
            addToIndex(lightingConditionIndex, val, recordId);
        }
        for (String val : dataObject.getMostSevereInjury()) {
            addToIndex(mostSevereInjuryIndex, val, recordId);
        }
        sync();
    }

    public List<Integer> getRecordIdsByCrashType(String crashTypeValue) {
        return crashTypeIndex.getOrDefault(crashTypeValue, Collections.emptyList());
    }

    public List<Integer> getRecordIdsByInjuriesTotal(double injuriesTotalValue) {
        return injuriesTotalIndex.getOrDefault(String.valueOf(injuriesTotalValue), Collections.emptyList());
    }

    public List<Integer> getRecordIdsByLightingCondition(String lightingConditionValue) {
        return lightingConditionIndex.getOrDefault(lightingConditionValue, Collections.emptyList());
    }

    public List<Integer> getRecordIdsByMostSevereInjury(String mostSevereInjuryValue) {
        return mostSevereInjuryIndex.getOrDefault(mostSevereInjuryValue, Collections.emptyList());
    }

    /**
     * Busca tipos de acidente usando Aho-Corasick.
     * @param patterns Uma lista de padrões para buscar.
     * @return Um conjunto de IDs de registro que correspondem a qualquer um dos padrões.
     */
    public Set<Integer> searchCrashTypeWithAhoCorasick(List<String> patterns) {
        AhoCorasick automaton = new AhoCorasick(patterns);
        Set<Integer> foundRecordIds = new HashSet<>();

        for (String keyInIndex : crashTypeIndex.keySet()) {
            List<Map.Entry<Integer, String>> matches = automaton.search(keyInIndex);
            if (!matches.isEmpty()) {
                foundRecordIds.addAll(crashTypeIndex.get(keyInIndex));
            }
        }
        return foundRecordIds;
    }

    public void deleteRecordFromIndexes(int recordId) {
        removeFromIndex(crashTypeIndex, recordId);
        removeFromIndex(injuriesTotalIndex, recordId);
        removeFromIndex(lightingConditionIndex, recordId);
        removeFromIndex(mostSevereInjuryIndex, recordId);
        sync();
    }

    public void updateIndexesForRecord(int recordId, DataObject oldDataObject, DataObject newDataObject) {
        // Remove entradas antigas
        for (String val : oldDataObject.getCrashType()) {
            removeFromIndex(crashTypeIndex, recordId);
        }
        removeFromIndex(injuriesTotalIndex, recordId);
        for (String val : oldDataObject.getLightingCondition()) {
            removeFromIndex(lightingConditionIndex, recordId);
        }
        for (String val : oldDataObject.getMostSevereInjury()) {
            removeFromIndex(mostSevereInjuryIndex, recordId);
        }

        // Adiciona novas entradas
        for (String val : newDataObject.getCrashType()) {
            addToIndex(crashTypeIndex, val, recordId);
        }
        addToIndex(injuriesTotalIndex, String.valueOf(newDataObject.getInjuriesTotal()), recordId);
        for (String val : newDataObject.getLightingCondition()) {
            addToIndex(lightingConditionIndex, val, recordId);
        }
        for (String val : newDataObject.getMostSevereInjury()) {
            addToIndex(mostSevereInjuryIndex, val, recordId);
        }
        sync();
    }

    /**
     * Salva todos os mapas de índice atuais em seus respectivos arquivos.
     */
    public void sync() {
        saveMapToFile(crashTypeIndex, invFilepathPrefix + "_crash_type.dat");
        saveMapToFile(injuriesTotalIndex, invFilepathPrefix + "_injuries_total.dat");
        saveMapToFile(lightingConditionIndex, invFilepathPrefix + "_lighting_condition.dat");
        saveMapToFile(mostSevereInjuryIndex, invFilepathPrefix + "_most_severe_injury.dat");
    }

    /**
     * Fecha o gerenciador de índice (nesta implementação baseada em arquivo, ele apenas sincroniza).
     */
    public void close() {
        sync();
    }
}

/**
 * O DataManager principal responsável por armazenar, recuperar, atualizar e excluir registros DataObject.
 * Ele gerencia um arquivo de dados primário (.db) e um arquivo de índice (.idx), e interage com InvertedIndexManager.
 */
class DataManager {
    private final String dbFilepath;
    private final String indexFilepath;
    protected final InvertedIndexManager invertedIndexManager;
    protected int currentId;
    protected Map<Integer, IndexEntry> indexMap;

    public DataManager(String dbFilepath, String indexFilepath, String invFilepathPrefix) {
        this.dbFilepath = dbFilepath;
        this.indexFilepath = indexFilepath;
        this.invertedIndexManager = new InvertedIndexManager(invFilepathPrefix);
        this.currentId = 0;
        this.indexMap = new HashMap<>();
        loadIndex();
    }

    /**
     * Carrega o mapa de índice em memória do arquivo de índice.
     */
    private void loadIndex() {
        File indexFile = new File(indexFilepath);
        if (!indexFile.exists()) {
            return;
        }

        try (RandomAccessFile raf = new RandomAccessFile(indexFile, "r")) {
            long fileSize = raf.length();
            while (raf.getFilePointer() < fileSize) {
                byte[] entryBytes = new byte[IndexEntry.ENTRY_SIZE];
                int bytesRead = raf.read(entryBytes);
                if (bytesRead < IndexEntry.ENTRY_SIZE) {
                    System.err.println("Aviso: Entrada de índice incompleta lida. Ignorando o restante do arquivo.");
                    break;
                }
                try {
                    IndexEntry entry = IndexEntry.deserialize(entryBytes);
                    if (entry.isValid() || !indexMap.containsKey(entry.getRecordId())) {
                         indexMap.put(entry.getRecordId(), entry);
                         if (entry.getRecordId() >= currentId) {
                            currentId = entry.getRecordId() + 1;
                        }
                    } else if (!entry.isValid() && indexMap.containsKey(entry.getRecordId())) {
                        if (indexMap.get(entry.getRecordId()).isValid()) {
                            indexMap.remove(entry.getRecordId());
                        }
                    }

                } catch (IllegalArgumentException e) {
                    System.err.println(String.format("Erro ao carregar entrada de índice: %s. Ignorando entrada corrompida.", e.getMessage()));
                }
            }
        } catch (IOException e) {
            System.err.println("Erro ao carregar arquivo de índice: " + e.getMessage());
        }
    }

    /**
     * Anexa uma entrada de índice ao arquivo de índice e atualiza o mapa em memória.
     */
    private void writeIndexEntry(IndexEntry entry) {
        try (RandomAccessFile raf = new RandomAccessFile(indexFilepath, "rw")) {
            raf.seek(raf.length());
            raf.write(entry.serialize());
        } catch (IOException e) {
            System.err.println("Erro ao escrever entrada de índice: " + e.getMessage());
        }
        indexMap.put(entry.getRecordId(), entry);
    }

    /**
     * Adiciona um novo registro DataObject ao banco de dados.
     * @param dataObject O DataObject a ser adicionado.
     * @return O ID do registro recém-adicionado, ou -1 se ocorreu um erro.
     */
    public int addRecord(DataObject dataObject) {
        int recordId = currentId++;
        DataRecord dataRecord = null;
        try {
            dataRecord = new DataRecord(recordId, dataObject, true);
            byte[] serializedData = dataRecord.serialize();

            long currentPosition = 0;
            File dbFile = new File(dbFilepath);
            if (dbFile.exists()) {
                currentPosition = dbFile.length();
            }

            try (RandomAccessFile raf = new RandomAccessFile(dbFile, "rw")) {
                raf.seek(currentPosition);
                raf.write(serializedData);
            }

            IndexEntry indexEntry = new IndexEntry(recordId, currentPosition, true);
            writeIndexEntry(indexEntry);

            invertedIndexManager.addEntry(dataObject, recordId);
            return recordId;

        } catch (IOException | NoSuchAlgorithmException e) {
            System.err.println("Erro ao adicionar registro: " + e.getMessage());
            currentId--;
            return -1;
        }
    }

    /**
     * Recupera um DataObject pelo seu ID de registro.
     * @param recordId O ID do registro a ser recuperado.
     * @return O DataObject se encontrado e válido, caso contrário null.
     */
    public DataObject getRecord(int recordId) {
        IndexEntry indexEntry = indexMap.get(recordId);
        if (indexEntry == null || !indexEntry.isValid()) {
            return null;
        }

        try (RandomAccessFile raf = new RandomAccessFile(dbFilepath, "r")) {
            raf.seek(indexEntry.getPosition());

            byte[] headerBytes = new byte[DataRecord.HEADER_SIZE];
            int bytesRead = raf.read(headerBytes);
            if (bytesRead < DataRecord.HEADER_SIZE) {
                System.err.println(String.format("Leitura de cabeçalho incompleta para o ID do registro %d. Esperado %d, obtido %d.", recordId, DataRecord.HEADER_SIZE, bytesRead));
                return null;
            }

            ByteBuffer headerBuffer = ByteBuffer.wrap(headerBytes);
            headerBuffer.order(ByteOrder.BIG_ENDIAN);
            headerBuffer.getInt();
            boolean isValidDb = headerBuffer.get() == 1;
            byte[] checksumRead = new byte[32];
            headerBuffer.get(checksumRead);
            int dataSize = headerBuffer.getInt();

            if (!isValidDb) {
                return null;
            }

            byte[] dataBytes = new byte[dataSize];
            bytesRead = raf.read(dataBytes);
            if (bytesRead < dataSize) {
                System.err.println(String.format("Leitura de dados incompleta para o ID do registro %d. Esperado %d, obtido %d.", recordId, dataSize, bytesRead));
                return null;
            }

            ByteBuffer fullRecordBuffer = ByteBuffer.allocate(DataRecord.HEADER_SIZE + dataSize);
            fullRecordBuffer.put(headerBytes);
            fullRecordBuffer.put(dataBytes);

            DataRecord dataRecord = DataRecord.deserialize(fullRecordBuffer.array());

            if (!dataRecord.isValid()) {
                System.err.println("O ID do registro recuperado " + recordId + " tem incompatibilidade de checksum.");
                return null;
            }
            return dataRecord.getDataObject();

        } catch (FileNotFoundException e) {
            System.err.println("Arquivo de banco de dados não encontrado: " + dbFilepath);
            return null;
        } catch (IOException | ClassNotFoundException | NoSuchAlgorithmException e) {
            System.err.println(String.format("Erro ao ler o registro ID %d do DB: %s", recordId, e.getMessage()));
            return null;
        } catch (Exception e) {
            System.err.println(String.format("Ocorreu um erro inesperado ao recuperar o registro ID %d: %s", recordId, e.getMessage()));
            e.printStackTrace();
            return null;
        }
    }

    /**
     * Exclui logicamente um registro, marcando seu cabeçalho no banco de dados e sua entrada de índice como inválida.
     * Também o remove dos índices invertidos.
     * @param recordId O ID do registro a ser excluído.
     * @return Verdadeiro se a exclusão foi bem-sucedida, falso caso contrário.
     */
    public boolean deleteRecord(int recordId) {
        IndexEntry indexEntry = indexMap.get(recordId);
        if (indexEntry == null || !indexEntry.isValid()) {
            System.out.println(String.format("Registro com ID %d não encontrado ou já está marcado como inválido para exclusão.", recordId));
            return false;
        }

        // Declare oldDataSize in a broader scope
        int oldDataSize = -1; // Initialize with a default invalid value

        try {
            DataObject oldDataObject = getRecord(recordId);
            if (oldDataObject == null) {
                System.err.println(String.format("Não foi possível recuperar o DataObject para o ID do registro %d para limpeza de exclusão.", recordId));
                return false;
            }

            try (RandomAccessFile raf = new RandomAccessFile(dbFilepath, "rw")) {
                raf.seek(indexEntry.getPosition());

                byte[] headerBytesOriginal = new byte[DataRecord.HEADER_SIZE];
                int bytesRead = raf.read(headerBytesOriginal);
                if (bytesRead < DataRecord.HEADER_SIZE) {
                    System.err.println(String.format("Erro: Cabeçalho incompleto para o ID do registro %d na posição %d.", recordId, indexEntry.getPosition()));
                    return false;
                }

                ByteBuffer originalHeaderBuffer = ByteBuffer.wrap(headerBytesOriginal);
                originalHeaderBuffer.order(ByteOrder.BIG_ENDIAN);
                originalHeaderBuffer.getInt(); // Skip recordId
                originalHeaderBuffer.get();    // Skip isValidDb
                byte[] dummyChecksum = new byte[32];
                originalHeaderBuffer.get(dummyChecksum); // Skip checksum
                oldDataSize = originalHeaderBuffer.getInt(); // Assign to the outer-scoped variable

                ByteBuffer invalidHeaderBuffer = ByteBuffer.allocate(DataRecord.HEADER_SIZE);
                invalidHeaderBuffer.order(ByteOrder.BIG_ENDIAN);
                invalidHeaderBuffer.putInt(recordId);
                invalidHeaderBuffer.put((byte) 0); // Mark as invalid
                invalidHeaderBuffer.put(new byte[32]); // Zero out checksum
                invalidHeaderBuffer.putInt(oldDataSize); // oldDataSize is now in scope
                raf.write(invalidHeaderBuffer.array());
            }

            indexMap.remove(recordId);
            writeIndexEntry(new IndexEntry(recordId, indexEntry.getPosition(), false));


            invertedIndexManager.deleteRecordFromIndexes(recordId);
            System.out.println(String.format("Registro ID %d marcado com sucesso como logicamente excluído e removido dos índices.", recordId));
            return true;

        } catch (FileNotFoundException e) {
            System.err.println("Arquivo de banco de dados não encontrado: " + dbFilepath);
            return false;
        } catch (IOException e) {
            System.err.println(String.format("Ocorreu um erro durante a exclusão do registro ID %d: %s", recordId, e.getMessage()));
            e.printStackTrace();
            return false;
        }
    }

    /**
     * Atualiza um registro existente. Se os novos dados forem maiores, o registro antigo é logicamente excluído,
     * e o novo registro é anexado ao final do arquivo. Se for menor ou igual, é sobrescrito no local.
     * @param recordId O ID do registro a ser atualizado.
     * @param newDataObject O novo conteúdo do DataObject.
     * @return Verdadeiro se a atualização foi bem-sucedida, falso caso contrário.
     */
    public boolean updateRecord(int recordId, DataObject newDataObject) {
        IndexEntry originalIndexEntry = indexMap.get(recordId);
        if (originalIndexEntry == null || !originalIndexEntry.isValid()) {
            System.out.println(String.format("Registro com ID %d não encontrado ou é inválido para atualização.", recordId));
            return false;
        }

        long originalPosition = originalIndexEntry.getPosition();
        int originalRecordTotalSize;
        DataObject oldDataObject;
        int oldDataSize;
        try (RandomAccessFile raf = new RandomAccessFile(dbFilepath, "r")) {
            raf.seek(originalPosition);

            byte[] headerBytesOld = new byte[DataRecord.HEADER_SIZE];
            int bytesRead = raf.read(headerBytesOld);
            if (bytesRead < DataRecord.HEADER_SIZE) {
                System.err.println(String.format("Erro: Cabeçalho incompleto para o ID do registro %d na posição %d.", recordId, originalPosition));
                return false;
            }

            ByteBuffer oldHeaderBuffer = ByteBuffer.wrap(headerBytesOld);
            oldHeaderBuffer.order(ByteOrder.BIG_ENDIAN);
            oldHeaderBuffer.getInt();
            oldHeaderBuffer.get();
            byte[] oldChecksum = new byte[32];
            oldHeaderBuffer.get(oldChecksum);
            oldDataSize = oldHeaderBuffer.getInt();

            byte[] oldDataBytes = new byte[oldDataSize];
            bytesRead = raf.read(oldDataBytes);
            if (bytesRead < oldDataSize) {
                System.err.println(String.format("Erro: Dados incompletos para o ID do registro %d na posição %d.", recordId, originalPosition));
                return false;
            }

            ByteBuffer oldFullRecordBuffer = ByteBuffer.allocate(DataRecord.HEADER_SIZE + oldDataSize);
            oldFullRecordBuffer.put(headerBytesOld);
            oldFullRecordBuffer.put(oldDataBytes);
            DataRecord oldDataRecord = DataRecord.deserialize(oldFullRecordBuffer.array());
            oldDataObject = oldDataRecord.getDataObject();

            originalRecordTotalSize = DataRecord.HEADER_SIZE + oldDataSize;

        } catch (FileNotFoundException e) {
            System.err.println("Arquivo de banco de dados não encontrado: " + dbFilepath);
            return false;
        } catch (IOException | ClassNotFoundException | NoSuchAlgorithmException e) {
            System.err.println(String.format("Erro ao ler dados de registro antigos para atualização do ID %d: %s", recordId, e.getMessage()));
            return false;
        }

        try {
            DataRecord newRecord = new DataRecord(recordId, newDataObject, true);
            byte[] serializedNewRecord = newRecord.serialize();
            int newRecordTotalSize = serializedNewRecord.length;

            try (RandomAccessFile raf = new RandomAccessFile(dbFilepath, "rw")) {
                if (newRecordTotalSize > originalRecordTotalSize) {
                    System.out.println(String.format("Registro %d novo tamanho (%d) > tamanho original (%d). Anexando novo registro.", recordId, newRecordTotalSize, originalRecordTotalSize));

                    raf.seek(originalPosition);
                    ByteBuffer invalidHeaderBuffer = ByteBuffer.allocate(DataRecord.HEADER_SIZE);
                    invalidHeaderBuffer.order(ByteOrder.BIG_ENDIAN);
                    invalidHeaderBuffer.putInt(recordId);
                    invalidHeaderBuffer.put((byte) 0);
                    invalidHeaderBuffer.put(new byte[32]);
                    invalidHeaderBuffer.putInt(oldDataSize); // Use oldDataSize here to mark original as invalid with its original size
                    raf.write(invalidHeaderBuffer.array());

                    long newPosition = raf.length();
                    raf.seek(newPosition);
                    raf.write(serializedNewRecord);

                    IndexEntry newIndexEntry = new IndexEntry(recordId, newPosition, true);
                    writeIndexEntry(newIndexEntry);

                } else {
                    System.out.println(String.format("Registro %d novo tamanho (%d) <= tamanho original (%d). Sobrescrevendo no local.", recordId, newRecordTotalSize, originalRecordTotalSize));

                    raf.seek(originalPosition);
                    raf.write(serializedNewRecord);

                    int bytesToPad = originalRecordTotalSize - newRecordTotalSize;
                    if (bytesToPad > 0) {
                        raf.write(new byte[bytesToPad]);
                    }
                }
            }
            invertedIndexManager.updateIndexesForRecord(recordId, oldDataObject, newDataObject);
            System.out.println(String.format("Registro ID %d atualizado com sucesso.", recordId));
            return true;

        } catch (FileNotFoundException e) {
            System.err.println("Arquivo de banco de dados não encontrado: " + dbFilepath);
            return false;
        } catch (IOException | NoSuchAlgorithmException e) {
            System.err.println(String.format("Ocorreu um erro durante a atualização do registro ID %d: %s", recordId, e.getMessage()));
            e.printStackTrace();
            return false;
        }
    }

    /**
     * Fecha o DataManager, garantindo que todos os índices sejam sincronizados.
     */
    public void close() {
        invertedIndexManager.close();
    }
}


// Classe para rodar os testes do DataManager (originalmente em AccidentDataApp.java main)
class AccidentDataApp_TestRunner {
    private static void cleanUpFiles(String dbFile, String indexFile, String invPrefix) {
        new File(dbFile).delete();
        new File(indexFile).delete();
        String[] invExtensions = {"_crash_type.dat", "_injuries_total.dat", "_lighting_condition.dat", "_most_severe_injury.dat"};
        for (String ext : invExtensions) {
            new File(invPrefix + ext).delete();
        }
    }

    public static void runDeletionTests() {
        System.out.println("\n" + "=".repeat(40));
        System.out.println("           EXECUTANDO TESTES DE EXCLUSÃO         ");
        System.out.println("=".repeat(40) + "\n");

        String DB_FILE = "crash_data_delete.db";
        String INDEX_FILE = "crash_data_delete.idx";
        String INV_INDEX_PREFIX = "crash_data_inv_delete";

        cleanUpFiles(DB_FILE, INDEX_FILE, INV_INDEX_PREFIX);

        DataManager dataManager = new DataManager(DB_FILE, INDEX_FILE, INV_INDEX_PREFIX);

        String[] csvLines = {
                "01/01/2023 12:00:00 PM;STOP SIGN;CLEAR;DAYLIGHT;REAR END;NOT APPLICABLE;STRAIGHT AND LEVEL;DRY;NO DEFECTS;PEDESTRIAN/BICYCLE;N;NONE;UNSAFE SPEED;2;NO INDICATION OF INJURY,MINOR INJURY;0.0;0.0;0.0;0.0;0.0;0.0;12;1;1",
                "01/02/2023 03:30:00 PM;TRAFFIC SIGNAL;RAIN;DAWN;SIDESWIPE;NOT APPLICABLE;CURVE ON LEVEL;WET;RUT, HOLES;VEHICLE;Y;MINOR;FOLLOWING TOO CLOSELY;3;MINOR INJURY;1.0;0.0;0.0;1.0;0.0;0.0;15;2;1",
                "01/03/2023 08:15:00 AM;NONE;SNOW;DARKNESS;ANGLE;NOT APPLICABLE;CURVE ON GRADE;SNOW;NO DEFECTS;VEHICLE/TRAIN;N;SEVERE;FAILING TO YIELD RIGHT-OF-WAY;2;FATAL INJURY;1.0;1.0;0.0;0.0;0.0;0.0;8;3;1",
                "01/04/2023 09:00:00 AM;YIELD SIGN;CLEAR;DAYLIGHT;HEAD ON;NOT APPLICABLE;STRAIGHT AND LEVEL;DRY;NO DEFECTS;VEHICLE/PEDESTRIAN;N;MODERATE;IMPROPER OVERTAKING;2;NON-INCAPACITATING INJURY;1.0;0.0;1.0;0.0;0.0;0.0;9;4;1",
                "01/05/2023 10:00:00 AM;NONE;CLEAR/FOG;DAYLIGHT;REAR END;NOT APPLICABLE;STRAIGHT AND LEVEL;DRY;NO DEFECTS;PEDESTRIAN;N;NONE;UNSAFE SPEED;1;NO INDICATION OF INJURY;0.0;0.0;0.0;0.0;0.0;0.0;10;5;1"
        };

        System.out.println("Adicionando registros para o teste de exclusão...");
        for (int i = 0; i < csvLines.length; i++) {
            try {
                DataObject dataObj = DataObject.fromCsvRow(csvLines[i]);
                int recordId = dataManager.addRecord(dataObj);
                System.out.println(String.format("Registro adicionado com ID: %d, Tipo de Colisão: %s, Ferimentos: %.1f", recordId, dataObj.getCrashType(), dataObj.getInjuriesTotal()));
            } catch (IllegalArgumentException e) {
                System.err.println(String.format("Erro ao processar linha CSV %d: %s", i + 1, e.getMessage()));
            }
        }

        System.out.println("\n--- Antes da Exclusão ---");
        for (int i = 0; i < 5; i++) {
            DataObject obj = dataManager.getRecord(i);
            if (obj != null) {
                System.out.println(String.format("Registro %d: Tipo de Colisão=%s, Ferimento Mais Grave=%s", i, obj.getCrashType(), obj.getMostSevereInjury()));
            } else {
                System.out.println(String.format("Registro %d: Não encontrado (ou inválido)", i));
            }
        }

        System.out.println("\nBusca por 'PEDESTRIAN' antes da exclusão:");
        List<String> patternsPedestrian = Arrays.asList("PEDESTRIAN");
        Set<Integer> foundIdsBefore = dataManager.invertedIndexManager.searchCrashTypeWithAhoCorasick(patternsPedestrian);
        System.out.println(String.format("IDs com 'PEDESTRIAN': %s", foundIdsBefore.stream().sorted().collect(Collectors.toList())));

        System.out.println("\nBusca por 'MINOR INJURY' antes da exclusão:");
        List<Integer> minorInjuryIdsBefore = dataManager.invertedIndexManager.getRecordIdsByMostSevereInjury("MINOR INJURY");
        System.out.println(String.format("IDs com 'MINOR INJURY': %s", minorInjuryIdsBefore.stream().sorted().collect(Collectors.toList())));

        System.out.println("\n--- Realizando Exclusão do Registro ID 0 ---");
        boolean deleteSuccess = dataManager.deleteRecord(0);
        System.out.println(String.format("Exclusão do ID 0 bem-sucedida: %b", deleteSuccess));

        System.out.println("\nTentando obter o Registro ID 0 após a exclusão:");
        DataObject deletedObj = dataManager.getRecord(0);
        if (deletedObj == null) {
            System.out.println("Registro ID 0 não recuperado (conforme esperado).");
        } else {
            System.err.println(String.format("Erro: Registro ID 0 ainda recuperado: %s", deletedObj.toMap()));
        }

        System.out.println("\nBusca por 'PEDESTRIAN' após a exclusão do ID 0:");
        Set<Integer> foundIdsAfter = dataManager.invertedIndexManager.searchCrashTypeWithAhoCorasick(patternsPedestrian);
        System.out.println(String.format("IDs com 'PEDESTRIAN' (após a exclusão): %s", foundIdsAfter.stream().sorted().collect(Collectors.toList())));

        System.out.println("\nBusca por 'MINOR INJURY' após a exclusão do ID 0:");
        List<Integer> minorInjuryIdsAfter = dataManager.invertedIndexManager.getRecordIdsByMostSevereInjury("MINOR INJURY");
        System.out.println(String.format("IDs com 'MINOR INJURY': %s", minorInjuryIdsAfter.stream().sorted().collect(Collectors.toList())));

        dataManager.close();

        System.out.println("\n--- Reabrindo DataManager para verificar a persistência da exclusão ---");
        DataManager dataManagerReopened = new DataManager(DB_FILE, INDEX_FILE, INV_INDEX_PREFIX);

        System.out.println("Tentando obter o Registro ID 0 após a reabertura:");
        DataObject deletedObjReopened = dataManagerReopened.getRecord(0);
        if (deletedObjReopened == null) {
            System.out.println("Registro ID 0 não recuperado (persistência da exclusão confirmada).");
        } else {
            System.err.println(String.format("Erro: Registro ID 0 ainda recuperado após a reabertura: %s", deletedObjReopened.toMap()));
        }

        System.out.println("\nBusca por 'PEDESTRIAN' após a reabertura do DataManager:");
        Set<Integer> foundIdsReopened = dataManagerReopened.invertedIndexManager.searchCrashTypeWithAhoCorasick(patternsPedestrian);
        System.out.println(String.format("IDs com 'PEDESTRIAN' (após a reabertura): %s", foundIdsReopened.stream().sorted().collect(Collectors.toList())));

        System.out.println("\nBusca por 'MINOR INJURY' após a reabertura do DataManager:");
        List<Integer> minorInjuryIdsReopened = dataManagerReopened.invertedIndexManager.getRecordIdsByMostSevereInjury("MINOR INJURY");
        System.out.println(String.format("IDs com 'MINOR INJURY': %s", minorInjuryIdsReopened.stream().sorted().collect(Collectors.toList())));

        dataManagerReopened.close();
        System.out.println("\n" + "=".repeat(40));
        System.out.println("         TESTES DE EXCLUSÃO CONCLUÍDOS         ");
        System.out.println("=".repeat(40) + "\n");
    }

    public static void runUpdateTests() {
        System.out.println("\n" + "=".repeat(40));
        System.out.println("           EXECUTANDO TESTES DE ATUALIZAÇÃO        ");
        System.out.println("=".repeat(40) + "\n");

        String DB_FILE_UPDATE = "crash_data_update.db";
        String INDEX_FILE_UPDATE = "crash_data_update.idx";
        String INV_INDEX_PREFIX_UPDATE = "crash_data_inv_update";

        cleanUpFiles(DB_FILE_UPDATE, INDEX_FILE_UPDATE, INV_INDEX_PREFIX_UPDATE);

        DataManager dataManager = new DataManager(DB_FILE_UPDATE, INDEX_FILE_UPDATE, INV_INDEX_PREFIX_UPDATE);

        String[] csvLinesInitial = {
                "01/01/2023 12:00:00 PM;STOP SIGN;CLEAR;DAYLIGHT;REAR END;NOT APPLICABLE;STRAIGHT AND LEVEL;DRY;NO DEFECTS;PEDESTRIAN/BICYCLE;N;NONE;UNSAFE SPEED;2;NO INDICATION OF INJURY,MINOR INJURY;0.0;0.0;0.0;0.0;0.0;0.0;12;1;1",
                "01/02/2023 03:30:00 PM;TRAFFIC SIGNAL;RAIN;DAWN;SIDESWIPE;NOT APPLICABLE;CURVE ON LEVEL;WET;RUT, HOLES;VEHICLE;Y;MINOR;FOLLOWING TOO CLOSELY;3;MINOR INJURY;1.0;0.0;0.0;1.0;0.0;0.0;15;2;1",
                "01/03/2023 08:15:00 AM;NONE;SNOW;DARKNESS;ANGLE;NOT APPLICABLE;CURVE ON GRADE;SNOW;NO DEFECTS;VEHICLE/TRAIN;N;SEVERE;FAILING TO YIELD RIGHT-OF-WAY;2;FATAL INJURY;1.0;1.0;0.0;0.0;0.0;0.0;8;3;1"
        };

        System.out.println("Adicionando registros iniciais para o teste de atualização...");
        for (int i = 0; i < csvLinesInitial.length; i++) {
            try {
                DataObject dataObj = DataObject.fromCsvRow(csvLinesInitial[i]);
                int recordId = dataManager.addRecord(dataObj);
                System.out.println(String.format("Registro adicionado com ID: %d, Tipo de Colisão: %s, Ferimentos: %.1f", recordId, dataObj.getCrashType(), dataObj.getInjuriesTotal()));
            } catch (IllegalArgumentException e) {
                System.err.println(String.format("Erro ao processar linha CSV %d: %s", i + 1, e.getMessage()));
            }
        }

        System.out.println("\n--- Estado Inicial ---");
        DataObject obj0 = dataManager.getRecord(0);
        DataObject obj1 = dataManager.getRecord(1);
        DataObject obj2 = dataManager.getRecord(2);

        System.out.println(String.format("Registro 0 (Original): Tipo de Colisão=%s, Total de Ferimentos=%.1f", obj0.getCrashType(), obj0.getInjuriesTotal()));
        System.out.println(String.format("Registro 1 (Original): Tipo de Colisão=%s, Total de Ferimentos=%.1f", obj1.getCrashType(), obj1.getInjuriesTotal()));
        System.out.println(String.format("Registro 2 (Original): Tipo de Colisão=%s, Total de Ferimentos=%.1f", obj2.getCrashType(), obj2.getInjuriesTotal()));

        System.out.println("\nBusca por 'PEDESTRIAN' (original):");
        List<String> patternsPedestrian = Arrays.asList("PEDESTRIAN");
        Set<Integer> foundIdsPedestrianOriginal = dataManager.invertedIndexManager.searchCrashTypeWithAhoCorasick(patternsPedestrian);
        System.out.println(String.format("IDs com 'PEDESTRIAN': %s", foundIdsPedestrianOriginal.stream().sorted().collect(Collectors.toList())));

        System.out.println("\nBusca por 'MINOR INJURY' (original):");
        List<Integer> foundIdsMinorInjuryOriginal = dataManager.invertedIndexManager.getRecordIdsByMostSevereInjury("MINOR INJURY");
        System.out.println(String.format("IDs com 'MINOR INJURY': %s", foundIdsMinorInjuryOriginal.stream().sorted().collect(Collectors.toList())));

        System.out.println("\n--- Atualizando Registro ID 1 (Mesmo/Menor Tamanho) ---");
        String newCsvLine1 = "01/02/2023 03:30:00 PM;TRAFFIC SIGNAL;RAIN;DAWN;SIDESWIPE;NOT APPLICABLE;CURVE ON LEVEL;WET;RUT, HOLES;VEHICLE/BICYCLE;Y;SEVERE;FOLLOWING TOO CLOSELY;3;FATAL INJURY;2.0;0.0;0.0;2.0;0.0;0.0;15;2;1";
        DataObject newObjData1 = null;
        try {
            newObjData1 = DataObject.fromCsvRow(newCsvLine1);
        } catch (IllegalArgumentException e) {
            System.err.println("Erro ao analisar novos dados para o ID 1: " + e.getMessage());
        }
        boolean updateSuccess1 = dataManager.updateRecord(1, newObjData1);
        System.out.println(String.format("Atualização do ID 1 bem-sucedida: %b", updateSuccess1));

        DataObject obj1Updated = dataManager.getRecord(1);
        if (obj1Updated != null) {
            System.out.println(String.format("Registro 1 (Atualizado): Tipo de Colisão=%s, Total de Ferimentos=%.1f, Ferimento Grave=%s", obj1Updated.getCrashType(), obj1Updated.getInjuriesTotal(), obj1Updated.getMostSevereInjury()));
        }

        System.out.println("\n--- Atualizando Registro ID 0 (Maior Tamanho) ---");
        String newCsvLine0 = "01/01/2023 12:00:00 PM;STOP SIGN;CLEAR;DAYLIGHT;REAR END;NOT APPLICABLE;STRAIGHT AND LEVEL;DRY;NO DEFECTS;PEDESTRIAN/BICYCLE/ANIMAL_COLLISION;N;NONE;UNSAFE SPEED and DRIVER INATTENTION;2;FATAL INJURY;5.0;0.0;0.0;0.0;0.0;0.0;12;1;1";
        DataObject newObjData0 = null;
        try {
            newObjData0 = DataObject.fromCsvRow(newCsvLine0);
        } catch (IllegalArgumentException e) {
            System.err.println("Erro ao analisar novos dados para o ID 0: " + e.getMessage());
        }
        boolean updateSuccess0 = dataManager.updateRecord(0, newObjData0);
        System.out.println(String.format("Atualização do ID 0 bem-sucedida: %b", updateSuccess0));

        DataObject obj0Updated = dataManager.getRecord(0);
        if (obj0Updated != null) {
            System.out.println(String.format("Registro 0 (Atualizado): Tipo de Colisão=%s, Total de Ferimentos=%.1f, Ferimento Grave=%s", obj0Updated.getCrashType(), obj0Updated.getInjuriesTotal(), obj0Updated.getMostSevereInjury()));
        }

        System.out.println("\n--- Verificando Índices Invertidos Após Atualizações ---");

        System.out.println("\nBusca por 'PEDESTRIAN' (após atualização):");
        Set<Integer> foundIdsPedestrianAfter = dataManager.invertedIndexManager.searchCrashTypeWithAhoCorasick(patternsPedestrian);
        System.out.println(String.format("IDs com 'PEDESTRIAN': %s", foundIdsPedestrianAfter.stream().sorted().collect(Collectors.toList())));

        System.out.println("\nBusca por 'BICYCLE' (após atualização):");
        List<String> patternsBicycle = Arrays.asList("BICYCLE");
        Set<Integer> foundIdsBicycleAfter = dataManager.invertedIndexManager.searchCrashTypeWithAhoCorasick(patternsBicycle);
        System.out.println(String.format("IDs com 'BICYCLE': %s", foundIdsBicycleAfter.stream().sorted().collect(Collectors.toList())));

        System.out.println("\nBusca por 'MINOR INJURY' (após atualização):");
        List<Integer> foundIdsMinorInjuryAfter = dataManager.invertedIndexManager.getRecordIdsByMostSevereInjury("MINOR INJURY");
        System.out.println(String.format("IDs com 'MINOR INJURY': %s", foundIdsMinorInjuryAfter.stream().sorted().collect(Collectors.toList())));

        System.out.println("\nBusca por 'FATAL INJURY' (após atualização):");
        List<Integer> foundIdsFatalInjuryAfter = dataManager.invertedIndexManager.getRecordIdsByMostSevereInjury("FATAL INJURY");
        System.out.println(String.format("IDs com 'FATAL INJURY': %s", foundIdsFatalInjuryAfter.stream().sorted().collect(Collectors.toList())));

        dataManager.close();

        System.out.println("\n--- Reabrindo DataManager para verificar a persistência das atualizações ---");
        DataManager dataManagerReopened = new DataManager(DB_FILE_UPDATE, INDEX_FILE_UPDATE, INV_INDEX_PREFIX_UPDATE);

        DataObject obj0Reopened = dataManagerReopened.getRecord(0);
        DataObject obj1Reopened = dataManagerReopened.getRecord(1);

        if (obj0Reopened != null) {
            System.out.println(String.format("Registro 0 (Reaberto): Tipo de Colisão=%s, Total de Ferimentos=%.1f", obj0Reopened.getCrashType(), obj0Reopened.getInjuriesTotal()));
        } else {
            System.out.println("Registro 0 não encontrado após reabrir.");
        }

        if (obj1Reopened != null) {
            System.out.println(String.format("Registro 1 (Reaberto): Tipo de Colisão=%s, Total de Ferimentos=%.1f", obj1Reopened.getCrashType(), obj1Reopened.getInjuriesTotal()));
        } else {
            System.out.println("Registro 1 não encontrado após reabrir.");
        }

        System.out.println("\nBusca por 'BICYCLE' (após reabrir):");
        Set<Integer> foundIdsBicycleReopened = dataManagerReopened.invertedIndexManager.searchCrashTypeWithAhoCorasick(patternsBicycle);
        System.out.println(String.format("IDs com 'BICYCLE': %s", foundIdsBicycleReopened.stream().sorted().collect(Collectors.toList())));

        System.out.println("\nBusca por 'FATAL INJURY' (após reabrir):");
        List<Integer> foundIdsFatalInjuryReopened = dataManagerReopened.invertedIndexManager.getRecordIdsByMostSevereInjury("FATAL INJURY");
        System.out.println(String.format("IDs com 'FATAL INJURY': %s", foundIdsFatalInjuryReopened.stream().sorted().collect(Collectors.toList())));

        dataManagerReopened.close();
        System.out.println("\n" + "=".repeat(40));
        System.out.println("         TESTES DE ATUALIZAÇÃO CONCLUÍDOS         ");
        System.out.println("=".repeat(40) + "\n");
    }
}


/**
 * Classe StageOne para gerenciar dados de acidentes de trânsito, integrando com
 * o DataManager, Índice Invertido e Aho-Corasick para operações sincronizadas.
 * Esta classe fornece uma interface orientada por menu para adicionar, ler, atualizar
 * e excluir registros, garantindo que todas as alterações sejam refletidas no arquivo
 * primário .db, no arquivo de índice .idx e nos índices invertidos.
 * Esta é a versão "básica", mas ainda usa o DataManager subjacente.
 */
class StageOne {

    private static final String DB_FILE = "data/traffic_accidents.db";
    private static final String INDEX_FILE = "index/indexTrafficAccidents.idx";
    private static final String INV_INDEX_PREFIX = "inverted_index/inv_traffic_accidents";
    private static final String DEFAULT_FILE="data/amostra.csv";
    private static DataManager dataManager;

    /**
     * Inicializa o DataManager. Isso deve ser chamado uma vez quando o módulo StageOne iniciar.
     */
    public static void initializeDataManager() {
        Functions.checkDirectory("data");
        Functions.checkDirectory("index");
        Functions.checkDirectory("inverted_index");

        dataManager = new DataManager(DB_FILE, INDEX_FILE, INV_INDEX_PREFIX);
        System.out.println("DataManager inicializado para StageOne. DB: " + DB_FILE + ", Índice: " + INDEX_FILE + ", Prefixo Inv Índice: " + INV_INDEX_PREFIX);
    }

    /**
     * Ponto de entrada principal para as operações do StageOne, espelhando o Menu original.
     */
    public static void start() {
        if (dataManager == null) {
            initializeDataManager();
        }

        int op = 0;
        do {
            System.out.println("\n==================================================");
            System.out.println("\nProcessos TP AEDS III - Parte I (StageOne)\n");
            System.out.println("1) Adicionar registro(s) do CSV");
            System.out.println("2) Adicionar um novo registro manualmente");
            System.out.println("3) Ler todos os registros");
            System.out.println("4) Ler apenas um registro (por ID)");
            System.out.println("5) Atualizar um registro (por ID)");
            System.out.println("6) Apagar registro (por ID)");
            System.out.println("7) Buscar por tipo de acidente (Aho-Corasick)");
            System.out.println("\n0) Sair para o Menu Principal\n\nEscolha um valor-------> :" );
            op = Functions.only_Int();

            switch (op) {
                case 1:
                    addRecordsFromCsv();
                    break;
                case 2:
                    addNewRecordManually();
                    break;
                case 3:
                    readAllRecords();
                    break;
                case 4:
                    readSingleRecord();
                    break;
                case 5:
                    updateRecord();
                    break;
                case 6:
                    deleteRecord();
                    break;
                case 7:
                    searchByCrashType();
                    break;
                case 0:
                    System.out.println("\nVoltando ao Menu Principal.");
                    break;
                default:
                    System.out.println("\nTente novamente, escolha fora do escopo.\n");
            }
        } while (op != 0);

        dataManager.close();
    }

    /**
     * Lê registros de um arquivo CSV especificado e os adiciona ao banco de dados.
     */
    private static void addRecordsFromCsv() {
        
    	
    	System.out.println("\n--- Adicionar registros de arquivo CSV ---");
        System.out.println("Escolha a origem do arquivo CSV:");
        System.out.println("1) Procurar arquivo no sistema");
        System.out.println("2) Usar arquivo padrão da aplicação ("+DEFAULT_FILE+")");
        System.out.print("Sua escolha: ");
        int choice = Functions.only_Int();
        if (choice == -1) {
            System.out.println("Entrada inválida. Operação cancelada.");
            return;
        }

        String filePath = "";
        if (choice == 1) {
            System.out.print("Por favor, digite o caminho completo do arquivo CSV: ");
            filePath = Functions.reading();
            if (filePath == null || filePath.trim().isEmpty()) {
                System.out.println("Caminho do arquivo não fornecido. Operação cancelada.");
                return;
            }
            if (!Functions.findFile(filePath)) {
                System.out.println("Arquivo não encontrado no caminho especificado.");
                return;
            }

        } else if (choice == 2) {
            filePath = DEFAULT_FILE;
            if (!Functions.findFile(filePath)) {
                System.out.println("Arquivo padrão não encontrado: " + filePath + ". Certifique-se de que ele existe.");
                return;
            }
        } else {
            System.out.println("Opção inválida. Operação cancelada.");
            return;
        }

        long totalLines = 0;
        try (BufferedReader countBr = new BufferedReader(new java.io.FileReader(filePath))) {
            countBr.readLine(); // Skip header
            while (countBr.readLine() != null) {
                totalLines++;
            }
        } catch (IOException e) {
            System.err.println("Erro ao contar linhas no arquivo CSV: " + e.getMessage());
            totalLines = -1; // Indicate unknown total
        }

        int recordsAdded = 0;
        int progressInterval = 100; // Update every 100 records

        try (BufferedReader br = new BufferedReader(new java.io.FileReader(filePath))) {
            br.readLine(); // Pula o cabeçalho
            String line;
            System.out.println("Iniciando leitura e adição de registros...");
            while ((line = br.readLine()) != null) {
                try {
                    DataObject dataObj = DataObject.fromCsvRow(line);
                    int recordId = dataManager.addRecord(dataObj);
                    if (recordId != -1) {
                        recordsAdded++;
                        if (recordsAdded % progressInterval == 0) {
                            if (totalLines > 0) {
                                System.out.print(String.format("\rProcessando: %d/%d registros (%.1f%%)", recordsAdded, totalLines, (double)recordsAdded/totalLines * 100.0));
                            } else {
                                System.out.print(String.format("\rProcessando: %d registros...", recordsAdded));
                            }
                            System.out.flush(); // Ensure the output is immediately written
                        }
                    } else {
                        System.err.println(String.format("Falha ao adicionar registro da linha: '%s'", line));
                    }
                } catch (IllegalArgumentException e) {
                    System.err.println(String.format("Erro ao analisar linha CSV: '%s' - %s", line, e.getMessage()));
                }
            }
            System.out.println(String.format("\nImportação de CSV concluída. %d registros adicionados.", recordsAdded));
        } catch (IOException e) {
            System.err.println("Erro ao ler arquivo CSV: " + e.getMessage());
        }
    }

    /**
     * Guia o usuário para criar e adicionar um novo registro manualmente.
     */
    private static void addNewRecordManually() {
        System.out.println("\n--- Adicionar um novo registro manualmente ---");
        try {
            DataObject newObj = createNewDataObjectFromUserInput();
            if (newObj != null) {
                int recordId = dataManager.addRecord(newObj);
                if (recordId != -1) {
                    System.out.println(String.format("Novo registro adicionado com ID: %d", recordId));
                } else {
                    System.err.println("Falha ao adicionar novo registro.");
                }
            } else {
                System.out.println("Criação de novo registro cancelada ou dados inválidos.");
            }
        } catch (IOException e) {
            System.err.println("Erro durante a criação manual do registro: " + e.getMessage());
        }
    }

    /**
     * Lê e exibe todos os registros válidos do banco de dados.
     */
    private static void readAllRecords() {
        System.out.println("\n--- Lendo todos os registros ---");
        List<Integer> recordIds = dataManager.indexMap.keySet().stream().sorted().collect(Collectors.toList());
        if (recordIds.isEmpty()) {
            System.out.println("Nenhum registro encontrado no banco de dados.");
            return;
        }

        for (int id : recordIds) {
            DataObject obj = dataManager.getRecord(id);
            if (obj != null) {
                System.out.println("\n--- Registro ID: " + id + " ---");
                printDataObject(obj);
            }
        }
        System.out.println("\nLeitura de todos os registros concluída.");
    }

    /**
     * Lê e exibe um único registro especificado por sua ID.
     */
    private static void readSingleRecord() {
        System.out.print("\nDigite a ID do registro a ser lido: ");
        int id = Functions.only_Int();
        if (id == -1) {
            System.out.println("ID inválida. Operação cancelada.");
            return;
        }

        DataObject obj = dataManager.getRecord(id);
        if (obj != null) {
            System.out.println("\n--- Registro ID: " + id + " ---");
            printDataObject(obj);
        } else {
            System.out.println(String.format("Registro com ID %d não encontrado ou é inválido.", id));
        }
    }

    /**
     * Guia o usuário na atualização de um registro existente.
     */
    private static void updateRecord() {
        System.out.print("\nDigite a ID do registro a ser atualizado: ");
        int id = Functions.only_Int();
        if (id == -1) {
            System.out.println("ID inválida. Operação cancelada.");
            return;
        }

        DataObject existingObj = dataManager.getRecord(id);
        if (existingObj == null) {
            System.out.println(String.format("Registro com ID %d não encontrado ou é inválido para atualização.", id));
            return;
        }

        System.out.println(String.format("\n--- Editando Registro ID: %d ---", id));
        System.out.println("Valores Atuais:");
        printDataObject(existingObj);

        try {
            DataObject updatedObj = createNewDataObjectFromUserInput(existingObj);
            if (updatedObj != null) {
                boolean success = dataManager.updateRecord(id, updatedObj);
                if (success) {
                    System.out.println(String.format("Registro ID %d atualizado com sucesso!", id));
                } else {
                    System.err.println(String.format("Falha ao atualizar registro ID %d.", id));
                }
            } else {
                System.out.println("Atualização cancelada.");
            }
        } catch (IOException e) {
            System.err.println("Erro durante a atualização do registro: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Exclui um registro por sua ID.
     */
    private static void deleteRecord() {
        System.out.print("\nDigite a ID do registro a ser apagado: ");
        int id = Functions.only_Int();
        if (id == -1) {
            System.out.println("ID inválida. Operação cancelada.");
            return;
        }

        boolean success = dataManager.deleteRecord(id);
        if (success) {
            System.out.println(String.format("Registro ID %d apagado com sucesso!", id));
        } else {
            System.err.println(String.format("Falha ao apagar registro ID %d.", id));
        }
    }

    /**
     * Realiza uma busca por tipos de acidente usando Aho-Corasick.
     */
    private static void searchByCrashType() {
        System.out.print("\nDigite os termos de busca para tipo de acidente (separados por vírgula): ");
        String searchTermsInput = Functions.reading();
        if (searchTermsInput == null || searchTermsInput.trim().isEmpty()) {
            System.out.println("Nenhum termo de busca fornecido. Operação cancelada.");
            return;
        }
        List<String> searchPatterns = Arrays.stream(searchTermsInput.split(","))
                                            .map(String::trim)
                                            .filter(s -> !s.isEmpty())
                                            .collect(Collectors.toList());

        if (searchPatterns.isEmpty()) {
            System.out.println("Nenhum termo de busca válido foi extraído. Operação cancelada.");
            return;
        }

        System.out.println(String.format("Buscando por tipos de acidente com padrões: %s", searchPatterns));
        Set<Integer> foundIds = dataManager.invertedIndexManager.searchCrashTypeWithAhoCorasick(searchPatterns);

        printSearchResults(foundIds, "tipo de acidente", dataManager);
    }


    /**
     * Método auxiliar para obter a entrada do usuário para um novo DataObject.
     * @return Um novo DataObject preenchido com a entrada do usuário.
     */
    protected static DataObject createNewDataObjectFromUserInput() throws IOException {
        return createNewDataObjectFromUserInput(null);
    }

    protected static DataObject createNewDataObjectFromUserInput(DataObject existingObj) throws IOException {
        System.out.print("Data e Hora do Acidente (MM/DD/YYYY HH:MM:SS AM/PM): ");
        String dateTimeString = promptForInput("Data e Hora do Acidente", existingObj != null ? existingObj.getDefaultTimeString() : null);

        System.out.print("Dispositivo de Controle de Tráfego: ");
        String trafficControlDevice = promptForInput("Dispositivo de Controle de Tráfego", existingObj != null ? existingObj.getTrafficControlDevice() : null);

        System.out.print("Condição Climática: ");
        String weatherCondition = promptForInput("Condição Climática", existingObj != null ? existingObj.getWeatherCondition() : null);

        System.out.print("Condição de Iluminação (separado por vírgulas se múltiplos): ");
        String lightingCondition = promptForInput("Condição de Iluminação", existingObj != null ? String.join(",", existingObj.getLightingCondition()) : null);

        System.out.print("Primeiro Tipo de Colisão: ");
        String firstCrashType = promptForInput("Primeiro Tipo de Colisão", existingObj != null ? existingObj.getFirstCrashType() : null);

        System.out.print("Tipo de Via de Tráfego: ");
        String trafficwayType = promptForInput("Tipo de Via de Tráfego", existingObj != null ? existingObj.getTrafficwayType() : null);

        System.out.print("Alinhamento: ");
        String alignment = promptForInput("Alinhamento", existingObj != null ? existingObj.getAlignment() : null);

        System.out.print("Condição da Superfície da Via: ");
        String roadwaySurfaceCond = promptForInput("Condição da Superfície da Via", existingObj != null ? existingObj.getRoadwaySurfaceCond() : null);

        System.out.print("Defeito na Estrada: ");
        String roadDefect = promptForInput("Defeito na Estrada", existingObj != null ? existingObj.getRoadDefect() : null);

        System.out.print("Tipo de Acidente (separado por vírgulas se múltiplos): ");
        String crashType = promptForInput("Tipo de Acidente", existingObj != null ? String.join(",", existingObj.getCrashType()) : null);

        System.out.print("Interseção Relacionada (S/N): ");
        String intersectionRelatedIStr = promptForInput("Interseção Relacionada (S/N)", existingObj != null ? Functions.getStringFromBoolean(existingObj.getIntersectionRelatedI()) : null);

        System.out.print("Danos (Ex: '$500 OU MENOS', '$501 - $1,500', 'ACIMA $1,500'): ");
        String damage = promptForInput("Danos", existingObj != null ? existingObj.getDamage() : null);

        System.out.print("Causa Contributiva Primária: ");
        String primContributoryCause = promptForInput("Causa Contributiva Primária", existingObj != null ? existingObj.getPrimContributoryCause() : null);

        System.out.print("Número de Unidades Envolvidas: ");
        int numUnits = promptForIntInput("Número de Unidades Envolvidas", existingObj != null ? existingObj.getNumUnits() : 0);

        System.out.print("Ferimento Mais Grave (separado por vírgulas se múltiplos): ");
        String mostSevereInjury = promptForInput("Ferimento Mais Grave", existingObj != null ? String.join(",", existingObj.getMostSevereInjury()) : null);

        System.out.print("Total de Ferimentos: ");
        double injuriesTotal = promptForDoubleInput("Total de Ferimentos", existingObj != null ? existingObj.getInjuriesTotal() : 0.0);

        System.out.print("Ferimentos Fatais: ");
        double injuriesFatal = promptForDoubleInput("Ferimentos Fatais", existingObj != null ? existingObj.getInjuriesFatal() : 0.0);

        System.out.print("Lesões Incapacitantes: ");
        double injuriesIncapacitating = promptForDoubleInput("Lesões Incapacitantes", existingObj != null ? existingObj.getInjuriesIncapacitating() : 0.0);

        System.out.print("Lesões Não Incapacitantes: ");
        double injuriesNonIncapacitating = promptForDoubleInput("Lesões Não Incapacitantes", existingObj != null ? existingObj.getInjuriesNonIncapacitating() : 0.0);

        System.out.print("Lesões Reportadas Não Evidentes: ");
        double injuriesReportedNotEvident = promptForDoubleInput("Lesões Reportadas Não Evidentes", existingObj != null ? existingObj.getInjuriesReportedNotEvident() : 0.0);

        System.out.print("Lesões Sem Indicação: ");
        double injuriesNoIndication = promptForDoubleInput("Lesões Sem Indicação", existingObj != null ? existingObj.getInjuriesNoIndication() : 0.0);

        System.out.print("Hora do Acidente (0-23): ");
        int crashHour = promptForIntInput("Hora do Acidente (0-23)", existingObj != null ? existingObj.getCrashHour() : 0);

        int crashDayOfWeek = 0; // Será calculado dentro do DataObject se crashDate for válido
        int crashMonth = 0;     // Será calculado dentro do DataObject se crashDate for válido

        try {
            return new DataObject(
                    dateTimeString, trafficControlDevice, weatherCondition, lightingCondition,
                    firstCrashType, trafficwayType, alignment, roadwaySurfaceCond,
                    roadDefect, crashType, intersectionRelatedIStr, damage,
                    primContributoryCause, numUnits, mostSevereInjury,
                    injuriesTotal, injuriesFatal, injuriesIncapacitating,
                    injuriesNonIncapacitating, injuriesReportedNotEvident,
                    injuriesNoIndication, crashHour, crashDayOfWeek, crashMonth
            );
        } catch (IllegalArgumentException e) {
            System.err.println("Erro ao criar DataObject: " + e.getMessage());
            return null;
        }
    }


    private static String promptForInput(String prompt, String defaultValue) {
        if (defaultValue != null && !defaultValue.isEmpty()) {
            System.out.print(String.format("%s (%s) [Enter para manter]: ", prompt, defaultValue));
        } else {
            System.out.print(prompt + ": ");
        }
        String input = Functions.reading();
        return input.isEmpty() ? defaultValue : input;
    }

    private static int promptForIntInput(String prompt, int defaultValue) {
        String inputStr = promptForInput(prompt, String.valueOf(defaultValue));
        try {
            return Integer.parseInt(inputStr);
        } catch (NumberFormatException e) {
            System.out.println("Entrada inválida, usando valor padrão: " + defaultValue);
            return defaultValue;
        }
    }

    private static double promptForDoubleInput(String prompt, double defaultValue) {
        String inputStr = promptForInput(prompt, String.valueOf(defaultValue));
        try {
            return Double.parseDouble(inputStr);
        } catch (NumberFormatException e) {
            System.out.println("Entrada inválida, usando valor padrão: " + defaultValue);
            return defaultValue;
        }
    }


    /**
     * Método auxiliar para imprimir detalhes do DataObject.
     */
    protected static void printDataObject(DataObject obj) {
        System.out.println("  Data/Hora: " + obj.getDefaultTimeString());
        System.out.println("  Dispositivo Controle: " + obj.getTrafficControlDevice());
        System.out.println("  Condição Climática: " + obj.getWeatherCondition());
        System.out.println("  Condição Iluminação: " + String.join(", ", obj.getLightingCondition()));
        System.out.println("  Primeiro Tipo Colisão: " + obj.getFirstCrashType());
        System.out.println("  Tipo Via Tráfego: " + obj.getTrafficwayType());
        System.out.println("  Alinhamento: " + obj.getAlignment());
        System.out.println("  Condição Superfície: " + obj.getRoadwaySurfaceCond());
        System.out.println("  Defeito Estrada: " + obj.getRoadDefect());
        System.out.println("  Tipo Acidente: " + String.join(", ", obj.getCrashType()));
        System.out.println("  Interseção Relacionada: " + Functions.getStringFromBoolean(obj.getIntersectionRelatedI()));
        System.out.println("  Dano: " + obj.getDamage());
        System.out.println("  Causa Contributiva Primária: " + obj.getPrimContributoryCause());
        System.out.println("  Número Unidades: " + obj.getNumUnits());
        System.out.println("  Ferimento Mais Grave: " + String.join(", ", obj.getMostSevereInjury()));
        System.out.println("  Ferimentos Total: " + obj.getInjuriesTotal());
        System.out.println("  Ferimentos Fatais: " + obj.getInjuriesFatal());
        System.out.println("  Lesões Incapacitantes: " + obj.getInjuriesIncapacitating());
        System.out.println("  Lesões Não Incapacitantes: " + obj.getInjuriesNonIncapacitating());
        System.out.println("  Lesões Reportadas Não Evidentes: " + obj.getInjuriesReportedNotEvident());
        System.out.println("  Lesões Sem Indicação: " + obj.getInjuriesNoIndication());
        System.out.println("  Hora Acidente: " + obj.getCrashHour());
        System.out.println("  Dia Semana Acidente: " + obj.getCrashDayOfWeek());
        System.out.println("  Mês Acidente: " + obj.getCrashMonth());
    }

    /**
     * Helper method to display search results.
     */
    protected static void printSearchResults(Iterable<Integer> foundIds, String searchType, DataManager dataManager) {
        List<Integer> sortedIds = new java.util.ArrayList<>();
        foundIds.forEach(sortedIds::add);
        sortedIds.sort(Integer::compareTo);

        if (sortedIds.isEmpty()) {
            System.out.println(String.format("Nenhum registro encontrado para o %s fornecido.", searchType));
        } else {
            System.out.println(String.format("\nRegistros encontrados (IDs para %s): %s", searchType, sortedIds));
            System.out.println("\nDetalhes dos registros encontrados:");
            for (int id : sortedIds) {
                DataObject obj = dataManager.getRecord(id);
                if (obj != null) {
                    System.out.println(String.format("\n--- Registro ID: %d ---", id));
                    printDataObject(obj);
                }
            }
        }
    }
}

/**
 * StageTwo class para gerenciar dados de acidentes de trânsito com otimizações completas.
 * Esta classe usa o DataManager, o índice sequencial, índices invertidos tipo B-tree,
 * e Aho-Corasick para operações CRUD eficientes e busca avançada.
 * Ele fornece uma interface orientada por menu para interagir com os dados.
 */
class StageTwo {

    private static final String DB_FILE = "data/traffic_accidents_opt.db";
    private static final String INDEX_FILE = "index/indexTrafficAccidents_opt.idx";
    private static final String INV_INDEX_PREFIX = "inverted_index/inv_traffic_accidents_opt";
    private static final String DEFAULT_FILE="data/traffic_accidents_pt_br_rev2.csv";
    
    private static DataManager dataManager;

    /**
     * Inicializa o DataManager para operações otimizadas.
     * Este método deve ser chamado uma vez quando o módulo StageTwo iniciar.
     */
    public static void initializeDataManager() {
        Functions.checkDirectory("data");
        Functions.checkDirectory("index");
        Functions.checkDirectory("inverted_index");

        dataManager = new DataManager(DB_FILE, INDEX_FILE, INV_INDEX_PREFIX);
        System.out.println("DataManager Otimizado inicializado para StageTwo. DB: " + DB_FILE + ", Índice: " + INDEX_FILE + ", Prefixo Inv Índice: " + INV_INDEX_PREFIX);
    }

    /**
     * Ponto de entrada principal para as operações do StageTwo.
     * Isso fornece um menu para funcionalidades CRUD e de busca otimizadas.
     */
    public static void start() {
        if (dataManager == null) {
            initializeDataManager();
        }

        int op = 0;
        do {
            System.out.println("\n==================================================");
            System.out.println("\nProcessos TP AEDS III - Parte II (Otimizado: CRUD e Buscas)\n");
            System.out.println("1) Adicionar registro(s) do CSV");
            System.out.println("2) Adicionar um novo registro manualmente");
            System.out.println("3) Ler todos os registros");
            System.out.println("4) Ler apenas um registro (por ID)");
            System.out.println("5) Atualizar um registro (por ID)");
            System.out.println("6) Apagar registro (por ID)");
            System.out.println("7) Buscar por Tipo de Acidente (Aho-Corasick)");
            System.out.println("8) Buscar por Total de Ferimentos");
            System.out.println("9) Buscar por Condição de Iluminação");
            System.out.println("10) Buscar por Ferimento Mais Grave");
            System.out.println("\n0) Sair para o Menu Principal\n\nEscolha um valor-------> :" );
            op = Functions.only_Int();

            long startTime, endTime;

            switch (op) {
                case 1:
                    startTime = System.nanoTime();
                    addRecordsFromCsv();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de adição de CSV: %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 2:
                    startTime = System.nanoTime();
                    addNewRecordManually();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de adição manual: %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 3:
                    startTime = System.nanoTime();
                    readAllRecords();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de leitura de todos: %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 4:
                    startTime = System.nanoTime();
                    readSingleRecord();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de leitura de registro único (indexado): %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 5:
                    startTime = System.nanoTime();
                    updateRecord();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de atualização: %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 6:
                    startTime = System.nanoTime();
                    deleteRecord();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de exclusão (lógica): %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 7:
                    startTime = System.nanoTime();
                    searchByCrashType();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de busca por tipo de acidente (Aho-Corasick): %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 8:
                    startTime = System.nanoTime();
                    searchByInjuriesTotal();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de busca por total de ferimentos: %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 9:
                    startTime = System.nanoTime();
                    searchByLightingCondition();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de busca por condição de iluminação: %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 10:
                    startTime = System.nanoTime();
                    searchByMostSevereInjury();
                    endTime = System.nanoTime();
                    System.out.println(String.format("Tempo de busca por ferimento mais grave: %.3f ms", (endTime - startTime) / 1_000_000.0));
                    break;
                case 0:
                    System.out.println("\nVoltando ao Menu Principal.");
                    break;
                default:
                    System.out.println("\nTente novamente, escolha fora do escopo.\n");
            }
        } while (op != 0);

        dataManager.close();
    }

    /**
     * Lê registros de um arquivo CSV especificado e os adiciona ao banco de dados.
     */
    private static void addRecordsFromCsv() {
        System.out.println("\n--- Adicionar registros de arquivo CSV (Otimizado) ---");
        System.out.println("Esta operação adiciona registros e os indexa automaticamente.");
        System.out.println("Escolha a origem do arquivo CSV:");
        System.out.println("1) Procurar arquivo no sistema");
        System.out.println("2) Usar arquivo padrão da aplicação ("+DEFAULT_FILE+")");
        System.out.print("Sua escolha: ");
        int choice = Functions.only_Int();
        if (choice == -1) {
            System.out.println("Entrada inválida. Operação cancelada.");
            return;
        }

        String filePath = "";
        if (choice == 1) {
            System.out.print("Por favor, digite o caminho completo do arquivo CSV: ");
            filePath = Functions.reading();
            if (filePath == null || filePath.trim().isEmpty()) {
                System.out.println("Caminho do arquivo não fornecido. Operação cancelada.");
                return;
            }
            if (!Functions.findFile(filePath)) {
                System.out.println("Arquivo não encontrado no caminho especificado.");
                return;
            }

        } else if (choice == 2) {
            filePath = DEFAULT_FILE;
            if (!Functions.findFile(filePath)) {
                System.out.println("Arquivo padrão não encontrado: " + filePath + ". Certifique-se de que ele existe.");
                return;
            }
        } else {
            System.out.println("Opção inválida. Operação cancelada.");
            return;
        }

        long totalLines = 0;
        try (BufferedReader countBr = new BufferedReader(new java.io.FileReader(filePath))) {
            countBr.readLine(); // Skip header
            while (countBr.readLine() != null) {
                totalLines++;
            }
        } catch (IOException e) {
            System.err.println("Erro ao contar linhas no arquivo CSV: " + e.getMessage());
            totalLines = -1; // Indicate unknown total
        }

        int recordsAdded = 0;
        int progressInterval = 100; // Update every 100 records

        try (BufferedReader br = new BufferedReader(new java.io.FileReader(filePath))) {
            br.readLine(); // Pula o cabeçalho
            String line;
            System.out.println("Iniciando leitura e adição de registros...");
            while ((line = br.readLine()) != null) {
                try {
                    DataObject dataObj = DataObject.fromCsvRow(line);
                    int recordId = dataManager.addRecord(dataObj);
                    if (recordId != -1) {
                        recordsAdded++;
                        if (recordsAdded % progressInterval == 0) {
                             if (totalLines > 0) {
                                System.out.print(String.format("\rProcessando: %d/%d registros (%.1f%%)", recordsAdded, totalLines, (double)recordsAdded/totalLines * 100.0));
                            } else {
                                System.out.print(String.format("\rProcessando: %d registros...", recordsAdded));
                            }
                            System.out.flush(); // Ensure the output is immediately written
                        }
                    } else {
                        System.err.println(String.format("Falha ao adicionar registro da linha: '%s'", line));
                    }
                } catch (IllegalArgumentException e) {
                    System.err.println(String.format("Erro ao analisar linha CSV: '%s' - %s", line, e.getMessage()));
                }
            }
            System.out.println(String.format("\nImportação de CSV concluída. %d registros adicionados e indexados.", recordsAdded));
        } catch (IOException e) {
            System.err.println("Erro ao ler arquivo CSV: " + e.getMessage());
        }
    }

    /**
     * Guia o usuário para criar e adicionar um novo registro manualmente.
     */
    private static void addNewRecordManually() {
        System.out.println("\n--- Adicionar um novo registro manualmente (Otimizado) ---");
        System.out.println("O novo registro será automaticamente indexado.");
        try {
            DataObject newObj = StageOne.createNewDataObjectFromUserInput();
            if (newObj != null) {
                int recordId = dataManager.addRecord(newObj);
                if (recordId != -1) {
                    System.out.println(String.format("Novo registro adicionado com ID: %d", recordId));
                } else {
                    System.err.println("Falha ao adicionar novo registro.");
                }
            } else {
                System.out.println("Criação de novo registro cancelada ou dados inválidos.");
            }
        } catch (IOException e) {
            System.err.println("Erro durante a criação manual do registro: " + e.getMessage());
        }
    }

    /**
     * Lê e exibe todos os registros válidos do banco de dados usando o índice otimizado.
     */
    private static void readAllRecords() {
        System.out.println("\n--- Lendo todos os registros (Otimizado) ---");
        System.out.println("Utilizando índice sequencial para recuperação rápida.");
        List<Integer> recordIds = dataManager.indexMap.keySet().stream().sorted().collect(Collectors.toList());
        if (recordIds.isEmpty()) {
            System.out.println("Nenhum registro encontrado no banco de dados.");
            return;
        }

        for (int id : recordIds) {
            DataObject obj = dataManager.getRecord(id);
            if (obj != null) {
                System.out.println(String.format("\n--- Registro ID: %d ---", id));
                StageOne.printDataObject(obj);
            }
        }
        System.out.println("\nLeitura de todos os registros concluída.");
    }

    /**
     * Lê e exibe um único registro especificado por sua ID usando o índice otimizado.
     */
    private static void readSingleRecord() {
        System.out.print("\nDigite a ID do registro a ser lido (uso de índice sequencial): ");
        int id = Functions.only_Int();
        if (id == -1) {
            System.out.println("ID inválida. Operação cancelada.");
            return;
        }

        DataObject obj = dataManager.getRecord(id);
        if (obj != null) {
            System.out.println(String.format("\n--- Registro ID: %d ---", id));
            StageOne.printDataObject(obj);
        } else {
            System.out.println(String.format("Registro com ID %d não encontrado ou é inválido.", id));
        }
    }

    /**
     * Guia o usuário na atualização de um registro existente, garantindo a sincronização do índice.
     */
    private static void updateRecord() {
        System.out.print("\nDigite a ID do registro a ser atualizado: ");
        int id = Functions.only_Int();
        if (id == -1) {
            System.out.println("ID inválida. Operação cancelada.");
            return;
        }

        DataObject existingObj = dataManager.getRecord(id);
        if (existingObj == null) {
            System.out.println(String.format("Registro com ID %d não encontrado ou é inválido para atualização.", id));
            return;
        }

        System.out.println(String.format("\n--- Editando Registro ID: %d (Otimizado: Sincroniza Índices) ---", id));
        System.out.println("Valores Atuais:");
        StageOne.printDataObject(existingObj);

        try {
            DataObject updatedObj = StageOne.createNewDataObjectFromUserInput(existingObj);
            if (updatedObj != null) {
                boolean success = dataManager.updateRecord(id, updatedObj);
                if (success) {
                    System.out.println(String.format("Registro ID %d atualizado com sucesso e índices sincronizados!", id));
                } else {
                    System.err.println(String.format("Falha ao atualizar registro ID %d.", id));
                }
            } else {
                System.out.println("Atualização cancelada.");
            }
        } catch (IOException e) {
            System.err.println("Erro durante a atualização do registro: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Exclui um registro por sua ID, garantindo a sincronização do índice.
     */
    private static void deleteRecord() {
        System.out.print("\nDigite a ID do registro a ser apagado (Otimizado: Exclusão Lógica e Sincronização de Índices): ");
        int id = Functions.only_Int();
        if (id == -1) {
            System.out.println("ID inválida. Operação cancelada.");
            return;
        }

        boolean success = dataManager.deleteRecord(id);
        if (success) {
            System.out.println(String.format("Registro ID %d apagado com sucesso e removido dos índices!", id));
        } else {
            System.err.println(String.format("Falha ao apagar registro ID %d.", id));
        }
    }

    /**
     * Realiza uma busca por tipos de acidente usando Aho-Corasick, aproveitando o índice invertido.
     */
    private static void searchByCrashType() {
        System.out.print("\nDigite os termos de busca para tipo de acidente (separados por vírgula, ex: BICYCLE,VEHICLE). Usando Aho-Corasick: ");
        String searchTermsInput = Functions.reading();
        if (searchTermsInput == null || searchTermsInput.trim().isEmpty()) {
            System.out.println("Nenhum termo de busca fornecido. Operação cancelada.");
            return;
        }
        List<String> searchPatterns = Arrays.stream(searchTermsInput.split(","))
                                            .map(String::trim)
                                            .filter(s -> !s.isEmpty())
                                            .collect(Collectors.toList());

        if (searchPatterns.isEmpty()) {
            System.out.println("Nenhum termo de busca válido foi extraído. Operação cancelada.");
            return;
        }

        System.out.println(String.format("Buscando por tipos de acidente com padrões: %s", searchPatterns));
        Set<Integer> foundIds = dataManager.invertedIndexManager.searchCrashTypeWithAhoCorasick(searchPatterns);

        StageOne.printSearchResults(foundIds, "tipo de acidente", dataManager);
    }

    /**
     * Realiza uma busca pelo total de ferimentos usando o índice invertido.
     */
    private static void searchByInjuriesTotal() {
        System.out.print("\nDigite o valor exato para o total de ferimentos a ser buscado (ex: 1.0, 5.0): ");
        double searchValue = Functions.only_Float();
        if (searchValue == -1) {
            System.out.println("Valor de ferimentos inválido. Operação cancelada.");
            return;
        }

        System.out.println(String.format("Buscando registros com Total de Ferimentos = %.1f", searchValue));
        List<Integer> foundIds = dataManager.invertedIndexManager.getRecordIdsByInjuriesTotal(searchValue);

        StageOne.printSearchResults(foundIds, "total de ferimentos", dataManager);
    }

    /**
     * Realiza uma busca pela condição de iluminação usando o índice invertido.
     */
    private static void searchByLightingCondition() {
        System.out.print("\nDigite a condição de iluminação para busca (ex: DAYLIGHT, DARKNESS): ");
        String searchValue = Functions.reading();
        if (searchValue == null || searchValue.trim().isEmpty()) {
            System.out.println("Nenhuma condição de iluminação fornecida. Operação cancelada.");
            return;
        }

        System.out.println(String.format("Buscando registros com Condição de Iluminação = '%s'", searchValue));
        List<Integer> foundIds = dataManager.invertedIndexManager.getRecordIdsByLightingCondition(searchValue);

        StageOne.printSearchResults(foundIds, "condição de iluminação", dataManager);
    }

    /**
     * Realiza uma busca pelo ferimento mais grave usando o índice invertido.
     */
    private static void searchByMostSevereInjury() {
        System.out.print("\nDigite o tipo de ferimento mais grave para busca (ex: FATAL INJURY, MINOR INJURY): ");
        String searchValue = Functions.reading();
        if (searchValue == null || searchValue.trim().isEmpty()) {
            System.out.println("Nenhum tipo de ferimento fornecido. Operação cancelada.");
            return;
        }

        System.out.println(String.format("Buscando registros com Ferimento Mais Grave = '%s'", searchValue));
        List<Integer> foundIds = dataManager.invertedIndexManager.getRecordIdsByMostSevereInjury(searchValue);

        StageOne.printSearchResults(foundIds, "ferimento mais grave", dataManager);
    }
}


/**
 * Classe StageThree gerencia processos de compressão e descompressão usando
 * os algoritmos Huffman, LZW e LZ78. Ele fornece uma interface orientada por menu
 * para o usuário selecionar e executar essas operações em arquivos especificados.
 */
class StageThree {

    /**
     * Inicia o menu de compressão/descompressão do StageThree.
     * Este método apresentará opções para diferentes algoritmos de compressão
     * e guiará o usuário através de seus respectivos processos.
     */
    public static void start() {
        int op = 0;
        do {
            System.out.println("\n==================================================");
            System.out.println("\nProcessos TP AEDS III - Parte III (Compressão/Descompressão)\n");
            System.out.println("1) Processos Huffman (Baseado no arquivo CSV/Texto)");
            System.out.println("2) Processos LZW (Baseado no arquivo CSV/Texto)");
            System.out.println("3) Processos LZ78 Adaptado (Baseado em qualquer arquivo/byte)");
            System.out.println("\n0) Sair para o Menu Principal\n\nEscolha um valor-------> :" );
            op = Functions.only_Int();

            switch (op) {
                case 1:
                    runHuffmanProcesses();
                    break;
                case 2:
                    runLZWProcesses();
                    break;
                case 3:
                    runLZ78UnifiedProcesses();
                    break;
                case 0:
                    System.out.println("\nVoltando ao Menu Principal.");
                    break;
                default:
                    System.out.println("\nTente novamente, escolha fora do escopo.\n");
            }
        } while (op != 0);
    }

    /**
     * Gerencia os processos de compressão e descompressão Huffman.
     */
    private static void runHuffmanProcesses() {
        System.out.println("\n--- Processos Huffman ---");
        System.out.println("1) Comprimir Arquivo");
        System.out.println("2) Descomprimir Arquivo");
        System.out.print("Escolha uma opção: ");
        int choice = Functions.only_Int();
        if (choice == -1) {
            System.out.println("Entrada inválida. Retornando.");
            return;
        }

        System.out.print("Digite o caminho completo do arquivo de entrada: ");
        String inputFilePath = Functions.reading();
        if (inputFilePath == null || inputFilePath.trim().isEmpty()) {
            System.out.println("Caminho do arquivo não fornecido. Retornando.");
            return;
        }
        if (!new File(inputFilePath).exists()) {
            System.out.println("Erro: Arquivo de entrada não encontrado em " + inputFilePath);
            return;
        }

        if (choice == 1) {
            System.out.print("Digite o nome para o arquivo de saída comprimido (ex: meu_arquivo.huff): ");
            String outputFileName = Functions.reading();
            if (outputFileName == null || outputFileName.trim().isEmpty()) {
                System.out.println("Nome do arquivo de saída não fornecido. Retornando.");
                return;
            }
            File outputFile = new File(outputFileName);
            File parentDir = outputFile.getParentFile();
            if (parentDir != null && !parentDir.exists()) {
                parentDir.mkdirs();
            }

            Huffman.compressProcess(inputFilePath, outputFileName);

        } else if (choice == 2) {
            System.out.print("Digite o nome para o arquivo de saída descomprimido (ex: meu_arquivo_decomp.txt): ");
            String outputFileName = Functions.reading();
            if (outputFileName == null || outputFileName.trim().isEmpty()) {
                System.out.println("Nome do arquivo de saída não fornecido. Retornando.");
                return;
            }
            File outputFile = new File(outputFileName);
            File parentDir = outputFile.getParentFile();
            if (parentDir != null && !parentDir.exists()) {
                parentDir.mkdirs();
            }

            Huffman.decompressProcess(inputFilePath, inputFilePath.replace(".", "_compressed.") + "huff", outputFileName);

        } else {
            System.out.println("Opção inválida.");
        }
    }

    /**
     * Gerencia os processos de compressão e descompressão LZW.
     */
    private static void runLZWProcesses() {
        System.out.println("\n--- Processos LZW ---");
        System.out.println("1) Comprimir Arquivo");
        System.out.println("2) Descomprimir Arquivo");
        System.out.print("Escolha uma opção: ");
        int choice = Functions.only_Int();
        if (choice == -1) {
            System.out.println("Entrada inválida. Retornando.");
            return;
        }

        System.out.print("Digite o caminho completo do arquivo de entrada: ");
        String inputFilePath = Functions.reading();
        if (inputFilePath == null || inputFilePath.trim().isEmpty()) {
            System.out.println("Caminho do arquivo não fornecido. Retornando.");
            return;
        }
        if (!new File(inputFilePath).exists()) {
            System.out.println("Erro: Arquivo de entrada não encontrado em " + inputFilePath);
            return;
        }

        if (choice == 1) {
            System.out.print("Digite o nome para o arquivo de saída comprimido (ex: meu_arquivo.lzw): ");
            String outputFileName = Functions.reading();
            if (outputFileName == null || outputFileName.trim().isEmpty()) {
                System.out.println("Nome do arquivo de saída não fornecido. Retornando.");
                return;
            }
            File outputFile = new File(outputFileName);
            File parentDir = outputFile.getParentFile();
            if (parentDir != null && !parentDir.exists()) {
                parentDir.mkdirs();
            }

            LZWC.compressProcess(inputFilePath, outputFileName);

        } else if (choice == 2) {
            System.out.print("Digite o nome para o arquivo de saída descomprimido (ex: meu_arquivo_decomp.txt): ");
            String outputFileName = Functions.reading();
            if (outputFileName == null || outputFileName.trim().isEmpty()) {
                System.out.println("Nome do arquivo de saída não fornecido. Retornando.");
                return;
            }
            File outputFile = new File(outputFileName);
            File parentDir = outputFile.getParentFile();
            if (parentDir != null && !parentDir.exists()) {
                parentDir.mkdirs();
            }

            LZWC.decompressProcess(inputFilePath, inputFilePath.replace(".", "_compressed.") + "lzw", outputFileName);

        } else {
            System.out.println("Opção inválida.");
        }
    }

    /**
     * Gerencia os processos de compressão e descompressão LZ78 Unificado.
     * Esta versão (do LZ78Unified) é geralmente mais robusta para vários fluxos de bytes.
     */
    private static void runLZ78UnifiedProcesses() {
        System.out.println("\n--- Processos LZ78 Adaptado (UTF-8, qualquer fluxo de bytes) ---");
        System.out.println("1) Comprimir Arquivo");
        System.out.println("2) Descomprimir Arquivo");
        System.out.println("3) Rodar demonstração com arquivo de exemplo (Português-BR)");
        System.out.print("Escolha uma opção: ");
        int choice = Functions.only_Int();
        if (choice == -1) {
            System.out.println("Entrada inválida. Retornando.");
            return;
        }

        if (choice == 3) {
            LZ78Unified.createSampleData();
            return;
        }

        System.out.print("Digite o caminho completo do arquivo de entrada: ");
        String inputFilePath = Functions.reading();
        if (inputFilePath == null || inputFilePath.trim().isEmpty()) {
            System.out.println("Caminho do arquivo não fornecido. Retornando.");
            return;
        }
        if (!new File(inputFilePath).exists()) {
            System.out.println("Erro: Arquivo de entrada não encontrado em " + inputFilePath);
            return;
        }

        File lzwDir = new File("LZW");
        if (!lzwDir.exists()) {
            lzwDir.mkdirs();
        }

        if (choice == 1) {
            System.out.print("Digite o nome para o arquivo de saída comprimido (ex: meu_arquivo.lz78, será salvo em LZW/): ");
            String outputFileName = Functions.reading();
            if (outputFileName == null || outputFileName.trim().isEmpty()) {
                System.out.println("Nome do arquivo de saída não fornecido. Retornando.");
                return;
            }
            String fullOutputPath = "LZW/" + outputFileName;
            LZ78Unified.compressProcess(inputFilePath, fullOutputPath);

        } else if (choice == 2) {
            System.out.print("Digite o caminho completo do arquivo comprimido LZ78 (.lz78) para descompressão (ex: LZW/meu_arquivo.lz78): ");
            String compressedFilePath = Functions.reading();
            if (compressedFilePath == null || compressedFilePath.trim().isEmpty()) {
                System.out.println("Caminho do arquivo comprimido não fornecido. Retornando.");
                return;
            }
            if (!new File(compressedFilePath).exists()) {
                System.out.println("Erro: Arquivo comprimido não encontrado em " + compressedFilePath);
                return;
            }

            System.out.print("Digite o nome para o arquivo de saída descomprimido (ex: meu_arquivo_decomp.txt): ");
            String outputFileName = Functions.reading();
            if (outputFileName == null || outputFileName.trim().isEmpty()) {
                System.out.println("Nome do arquivo de saída não fornecido. Retornando.");
                return;
            }
            File outputFile = new File(outputFileName);
            File parentDir = outputFile.getParentFile();
            if (parentDir != null && !parentDir.exists()) {
                parentDir.mkdirs();
            }

            LZ78Unified.decompressProcess(inputFilePath, compressedFilePath, outputFileName);

        } else {
            System.out.println("Opção inválida.");
        }
    }
}


// =========================================================================
// CLASSES DE COMPRESSÃO (Originalmente de estagio3)
// =========================================================================

/**
 * Implementação do algoritmo de compressão Huffman.
 */
class Huffman {
    // --- Node Class for Huffman Tree ---
    static class Node {
        char character;
        int frequency;
        Node left;
        Node right;

        public Node(char character, int frequency) {
            this.character = character;
            this.frequency = frequency;
            this.left = null;
            this.right = null;
        }

        public Node(int frequency, Node left, Node right) {
            this.character = '\0';
            this.frequency = frequency;
            this.left = left;
            this.right = right;
        }

        public boolean isLeaf() {
            return left == null && right == null;
        }
    }

    // --- Comparator for PriorityQueue (Min-Heap) ---
    static class NodeComparator implements Comparator<Node> {
        @Override
        public int compare(Node n1, Node n2) {
            return Integer.compare(n1.frequency, n2.frequency);
        }
    }

    // --- HuffmanContext Class (for encapsulation) ---
    static class HuffmanContext {
        Node huffmanTreeRoot;
        Map<Character, String> huffmanCodes;
        Map<Character, CodeMetadata> decompressionMetadata;
        int totalOriginalChars;

        public HuffmanContext() {
            huffmanTreeRoot = null;
            huffmanCodes = new HashMap<>();
            decompressionMetadata = new HashMap<>();
            totalOriginalChars = 0;
        }
    }

    // --- CodeMetadata Class (for storing data for decompression tree) ---
    static class CodeMetadata {
        char character;
        int length;
        int decimalCode;

        public CodeMetadata(char character, int length, int decimalCode) {
            this.character = character;
            this.length = length;
            this.decimalCode = decimalCode;
        }
    }

    // --- Huffman Tree Building ---
    public static Node buildHuffmanTree(Map<Character, Integer> frequencies) {
        PriorityQueue<Node> pq = new PriorityQueue<>(new NodeComparator());

        for (Map.Entry<Character, Integer> entry : frequencies.entrySet()) {
            pq.add(new Node(entry.getKey(), entry.getValue()));
        }

        while (pq.size() > 1) {
            Node left = pq.poll();
            Node right = pq.poll();
            Node parent = new Node(left.frequency + right.frequency, left, right);
            pq.add(parent);
        }

        return pq.poll();
    }

    private static void generateHuffmanCodes(Node node, String code, HuffmanContext context) {
        if (node.isLeaf()) {
            context.huffmanCodes.put(node.character, code);
            context.decompressionMetadata.put(node.character,
                    new CodeMetadata(node.character, code.length(), binaryStringToDecimal(code)));
        } else {
            generateHuffmanCodes(node.left, code + "0", context);
            generateHuffmanCodes(node.right, code + "1", context);
        }
    }

    // --- Compression ---
    public static void compressFile(String inputFilePath, String outputFilePath) throws IOException {
        HuffmanContext context = new HuffmanContext();

        Map<Character, Integer> frequencies = new HashMap<>();
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath))) {
            int byteRead;
            while ((byteRead = bis.read()) != -1) {
                char c = (char) byteRead;
                frequencies.put(c, frequencies.getOrDefault(c, 0) + 1);
                context.totalOriginalChars++;
            }
        }
        System.out.println("-----------------------------------------------------------------------------");
        frequencies.forEach((key, value) -> {
            System.out.println("chave: " + key + ", valor: " + value);
        });
        System.out.println("-----------------------------------------------------------------------------");
        if (context.totalOriginalChars == 0) {
            System.out.println("Arquivo de entrada vazio. Criando um arquivo comprimido vazio.");
            new FileOutputStream(outputFilePath).close();
            return;
        }

        context.huffmanTreeRoot = buildHuffmanTree(frequencies);
        generateHuffmanCodes(context.huffmanTreeRoot, "", context);

        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath));
             DataOutputStream dos = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(outputFilePath)))) {

            dos.writeInt(context.totalOriginalChars);
            dos.writeInt(context.decompressionMetadata.size());
            for (CodeMetadata meta : context.decompressionMetadata.values()) {
                dos.writeChar(meta.character);
                dos.writeInt(meta.length);
                dos.writeInt(meta.decimalCode);
            }

            BitSet bitSet = new BitSet();
            int bitIndex = 0;

            int byteRead;
            while ((byteRead = bis.read()) != -1) {
                char c = (char) byteRead;
                String code = context.huffmanCodes.get(c);
                if (code == null) {
                    throw new IllegalStateException("Nenhum código Huffman encontrado para o caractere: " + c);
                }
                for (char bitChar : code.toCharArray()) {
                    if (bitChar == '1') {
                        bitSet.set(bitIndex);
                    }
                    bitIndex++;
                }
            }
            dos.write(bitSet.toByteArray());
        }
        System.out.println("Arquivo comprimido com sucesso: " + outputFilePath);
    }

    // --- Decompression ---
    public static void decompressFile(String inputFilePath, String outputFilePath) throws IOException {
        HuffmanContext context = new HuffmanContext();
        Node decompressionTreeRoot = null;

        try (DataInputStream dis = new DataInputStream(new BufferedInputStream(new FileInputStream(inputFilePath)));
             BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream(outputFilePath))) {

            context.totalOriginalChars = dis.readInt();
            int uniqueCharsCount = dis.readInt();

            if (context.totalOriginalChars == 0) {
                System.out.println("Arquivo comprimido indica que o arquivo original estava vazio. Criando arquivo descomprimido vazio.");
                return;
            }

            decompressionTreeRoot = new Node('\0', 0);
            Node currentRebuildNode;

            for (int i = 0; i < uniqueCharsCount; i++) {
                char character = dis.readChar();
                int length = dis.readInt();
                int decimalCode = dis.readInt();

                String binaryCode = decimalToBinaryString(decimalCode, length);

                currentRebuildNode = decompressionTreeRoot;
                for (char bitChar : binaryCode.toCharArray()) {
                    if (bitChar == '0') {
                        if (currentRebuildNode.left == null) {
                            currentRebuildNode.left = new Node('\0', 0);
                        }
                        currentRebuildNode = currentRebuildNode.left;
                    } else { // '1'
                        if (currentRebuildNode.right == null) {
                            currentRebuildNode.right = new Node('\0', 0);
                        }
                        currentRebuildNode = currentRebuildNode.right;
                    }
                }
                currentRebuildNode.character = character;
            }

            Node currentNode = decompressionTreeRoot;
            int charactersDecompressed = 0;
            byte[] buffer = new byte[1024];
            int bytesRead;

            while (charactersDecompressed < context.totalOriginalChars && (bytesRead = dis.read(buffer)) != -1) {
                BitSet receivedBitSet = BitSet.valueOf(buffer);

                for (int i = 0; i < bytesRead * 8; i++) {
                    if (charactersDecompressed >= context.totalOriginalChars) {
                        break;
                    }

                    boolean bit = receivedBitSet.get(i);
                    if (!bit) {
                        currentNode = currentNode.left;
                    } else {
                        currentNode = currentNode.right;
                    }

                    if (currentNode == null) {
                        throw new IllegalStateException("Código Huffman inválido encontrado durante a descompressão.");
                    }

                    if (currentNode.isLeaf()) {
                        bos.write(currentNode.character);
                        charactersDecompressed++;
                        currentNode = decompressionTreeRoot;
                    }
                }
            }
        } finally {
            // No explicit close needed for try-with-resources
        }
        System.out.println("O arquivo escolhido foi " + inputFilePath);
        System.out.println("Arquivo descomprimido com sucesso como: " + outputFilePath);
    }

    // --- Utility Methods ---
    private static int binaryStringToDecimal(String binaryString) {
        if (binaryString == null || binaryString.isEmpty()) {
            return 0;
        }
        return Integer.parseInt(binaryString, 2);
    }

    private static String decimalToBinaryString(int decimalValue, int length) {
        String binaryString = Integer.toBinaryString(decimalValue);
        return String.format("%" + length + "s", binaryString).replace(' ', '0');
    }

    public static void processing(){
        String inputFilename = "sample.txt";
        String compressedFilename = "sample_compressed.huff";
        String decompressedFilename = "sample_decompressed.txt";

        try (FileWriter writer = new FileWriter(inputFilename)) {
            writer.write("isso é uma string de teste para codificação e compressão huffman. este é outro teste.");
            System.out.println("Arquivo de entrada dummy criado: " + inputFilename);
        } catch (IOException e) {
            System.err.println("Erro ao criar arquivo de entrada dummy: " + e.getMessage());
            return;
        }
        compressProcess(inputFilename,compressedFilename);
        decompressProcess(inputFilename,compressedFilename,decompressedFilename);
    }
    public static void compressProcess(String inputFilename, String compressedFilename){
        String[] description=compressedFilename.split("\\.");

        int counterHuffman = 0;
        File folder = new File(".");
        File[] listOfFiles = folder.listFiles();

        if (listOfFiles != null) {
            for (File file : listOfFiles) {
                if (file.isFile() && file.getName().startsWith(description[0]) && file.getName().endsWith("."+description[1])) {
                    counterHuffman++;
                }
            }
        }

        if (counterHuffman == 0) {
            counterHuffman = 1;
        } else {
            counterHuffman++;
        }

        compressedFilename = compressedFilename.replace("."+description[1], "_" + counterHuffman + "."+description[1]);

        try {
            long tempoInicial = System.currentTimeMillis();
            compressFile(inputFilename, compressedFilename);
            long tempoFinal=System.currentTimeMillis();
            System.out.println(String.format("A compressão Huffman foi realizada em %.2fs", (tempoFinal - tempoInicial)/1000.0));
            long sizeOriginal=getSize(inputFilename);
            long sizeCompress=getSize(compressedFilename);
            float percentHuffman=((float)sizeCompress/(float)sizeOriginal)*100;
            System.out.println(String.format("Tamanho de (%s): %d bytes", inputFilename, sizeOriginal));
            System.out.println(String.format("Tamanho de (%s): %d bytes", compressedFilename, sizeCompress));
            System.out.println(String.format("Porcentagem de compressão: %.2f%% do arquivo original.", percentHuffman));

        } catch (IOException e) {
            System.err.println("A compressão falhou: " + e.getMessage());
            e.printStackTrace();
        }
    }
    public static void decompressProcess(String inputFilename, String compressedFilename, String decompressedFilename) {
        List<File> huffmanFiles = new ArrayList<>();

        String[] description=compressedFilename.split("\\.");

        File folder = new File(".");
        File[] listOfFiles = folder.listFiles();

        if (listOfFiles != null) {
            for (File file : listOfFiles) {
                if (file.isFile() && file.getName().startsWith(description[0]) && file.getName().endsWith("."+description[1])) {
                    huffmanFiles.add(file);
                }
            }
        }
        //Nenhum arquivo Huffman comprimido encontrado correspondente a 'test_1<_compressed*.huff>.huff'.
        if (huffmanFiles.isEmpty()) {
            System.out.println(String.format("Nenhum arquivo Huffman comprimido encontrado correspondente a '%s*.%s'.", description[0], description[1]));
            System.out.println("Por favor, execute a compressão primeiro para criar alguns arquivos.");
            return;
        }

        huffmanFiles.sort(Comparator.comparing(File::getName));

        System.out.println("\n--- Arquivos Huffman Comprimidos Disponíveis para Descompressão ---");
        for (int i = 0; i < huffmanFiles.size(); i++) {
            System.out.println((i + 1) + ". " + huffmanFiles.get(i).getName());
        }

        int choice = -1;
        String selectedCompressedFilePath = null;
        while (selectedCompressedFilePath == null) {
            System.out.print("Digite o número do arquivo para descomprimir: ");
            try {
                 choice = Functions.only_Int();
                if (choice > 0 && choice <= huffmanFiles.size()) {
                    selectedCompressedFilePath = huffmanFiles.get(choice - 1).getName();
                } else {
                    System.out.println(String.format("Escolha inválida. Por favor, digite um número entre 1 e %d.", huffmanFiles.size()));
                }
            } catch (NumberFormatException e) {
                System.out.println("Entrada inválida. Por favor, digite um número.");
            }
        }
        System.out.println();
        try {
            long tempoInicial = System.currentTimeMillis();
            decompressFile(selectedCompressedFilePath, decompressedFilename);
            long tempoFinal=System.currentTimeMillis();

            System.out.println(String.format("A descompressão Huffman foi realizada em %.2fs", (tempoFinal - tempoInicial)/1000.0));
        } catch (IOException e) {
            System.err.println("A descompressão falhou: " + e.getMessage());
            e.printStackTrace();
        } finally {
            // No explicit close needed for try-with-resources
        }

        System.out.println("\n--- Verificação ---");
        System.out.println(String.format("Agora você pode comparar '%s' e '%s' para integridade.", inputFilename, decompressedFilename));
        System.out.println();
        long sizeOriginal=getSize(inputFilename);
        long sizeCompress=getSize(selectedCompressedFilePath);
        long sizeDecompress=getSize(decompressedFilename);
        float percentHuffman=((float)sizeDecompress/(float)sizeOriginal)*100;

        System.out.println(String.format("Tamanho de (%s): %d bytes", inputFilename, sizeOriginal));
        System.out.println(String.format("Tamanho de (%s): %d bytes", selectedCompressedFilePath, sizeCompress));
        System.out.println(String.format("Tamanho de (%s): %d bytes", decompressedFilename, sizeDecompress));
        System.out.println();
        System.out.println(String.format("Porcentagem de recuperação da descompressão do arquivo original é: %.2f%%.", percentHuffman));
    }
    public static long getSize(String filename) {
        File file = new File(filename);
        return file.length();
    }
}

/**
 * Implementação do algoritmo de compressão LZW (Lempel-Ziv-Welch).
 */
class LZWC {
    private static final int MAX_DICTIONARY_SIZE = 1 << 24;

    public void compress(String inputFilePath, String outputFilePath) throws IOException {
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath));
             DataOutputStream dos = new DataOutputStream(new FileOutputStream(outputFilePath))) {

            Map<String, Integer> dictionary = new HashMap<>();
            int dictionarySize = 256;

            for (int i = 0; i < dictionarySize; i++) {
                dictionary.put("" + (char) i, i);
            }

            String currentSequence = "";
            int nextCode = dictionarySize;

            int character;
            while ((character = bis.read()) != -1) {
                String newSequence = currentSequence + (char) character;

                if (dictionary.containsKey(newSequence)) {
                    currentSequence = newSequence;
                } else {
                    dos.writeInt(dictionary.get(currentSequence));

                    if (nextCode < MAX_DICTIONARY_SIZE) {
                        dictionary.put(newSequence, nextCode++);
                    }
                    currentSequence = "" + (char) character;
                }
            }

            if (!currentSequence.isEmpty()) {
                dos.writeInt(dictionary.get(currentSequence));
            }

            System.out.println("Compressão concluída. Tamanho do dicionário: " + dictionary.size());
        }
    }
    public static void processing(){
        String inputFilename = "sample.txt";
        String compressedFilename = "sample_compressed.lzw";
        String decompressedFilename = "sample_decompressed.txt";

        try (FileWriter writer = new FileWriter(inputFilename)) {
            writer.write("isto é uma string de teste para codificação e compressão LZW. este é outro teste.");
            System.out.println("Arquivo de entrada dummy criado: " + inputFilename);
        } catch (IOException e) {
            System.err.println("Erro ao criar arquivo de entrada dummy: " + e.getMessage());
            return;
        }
        compressProcess(inputFilename,compressedFilename);
        decompressProcess(inputFilename,compressedFilename,decompressedFilename);
    }
    public static void compressProcess(String inputFilename, String compressedFilename){
        LZWC compressor = new LZWC();

        String[] description=compressedFilename.split("\\.");

        int counterLZW = 0;
        File folder = new File(".");
        File[] listOfFiles = folder.listFiles();

        if (listOfFiles != null) {
            for (File file : listOfFiles) {
                if (file.isFile() && file.getName().startsWith(description[0]) && file.getName().endsWith("."+description[1])) {
                    counterLZW++;
                }
            }
        }

        if (counterLZW == 0) {
            counterLZW = 1;
        } else {
            counterLZW++;
        }
        compressedFilename = compressedFilename.replace("."+description[1], "_" + counterLZW + "."+description[1]);

        try {
            long tempoInicial = System.currentTimeMillis();
            compressor.compress(inputFilename, compressedFilename);
            long tempoFinal = System.currentTimeMillis();
            System.out.println(String.format("A compressão LZW foi realizada em %.2fs", (tempoFinal - tempoInicial)/1000.0));
            long sizeOriginal=getSize(inputFilename);
            long sizeCompress=getSize(compressedFilename);
            float percentLZW=((float)sizeCompress/(float)sizeOriginal)*100;
            System.out.println(String.format("Tamanho de (%s): %d bytes", inputFilename, sizeOriginal));
            System.out.println(String.format("Tamanho de (%s): %d bytes", compressedFilename, sizeCompress));
            System.out.println(String.format("Porcentagem de compressão: %.2f%% do arquivo original.", percentLZW));

       } catch (IOException e) {
            System.err.println("A compressão falhou: " + e.getMessage());
            e.printStackTrace();
        }
    }
    public static void decompressProcess(String inputFilename, String compressedFilename, String decompressedFilename) {
        List<File> lzwFiles = new ArrayList<>();
        LZWD decompressor = new LZWD();

        String[] description=compressedFilename.split("\\.");

        File folder = new File(".");
        File[] listOfFiles = folder.listFiles();

        if (listOfFiles != null) {
            for (File file : listOfFiles) {
                if (file.isFile() && file.getName().startsWith(description[0]) && file.getName().endsWith("."+description[1])) {
                    lzwFiles.add(file);
                }
            }
        }

        if (lzwFiles.isEmpty()) {
            System.out.println(String.format("Nenhum arquivo LZW comprimido encontrado correspondente a '%s*.%s'.", description[0], description[1]));
            System.out.println("Por favor, execute a compressão primeiro para criar alguns arquivos.");
            return;
        }

        lzwFiles.sort(Comparator.comparing(File::getName));

        System.out.println("\n--- Arquivos LZW Comprimidos Disponíveis para Descompressão ---");
        for (int i = 0; i < lzwFiles.size(); i++) {
            System.out.println((i + 1) + ". " + lzwFiles.get(i).getName());
        }

        int choice = -1;
        String selectedCompressedFilePath = null;
        while (selectedCompressedFilePath == null) {
            System.out.print("Digite o número do arquivo para descomprimir: ");
            try {
                choice = Functions.only_Int();
                if (choice > 0 && choice <= lzwFiles.size()) {
                    selectedCompressedFilePath = lzwFiles.get(choice - 1).getName();
                } else {
                    System.out.println(String.format("Escolha inválida. Por favor, digite um número entre 1 e %d.", lzwFiles.size()));
                }
            } catch (NumberFormatException e) {
                System.out.println("Entrada inválida. Por favor, digite um número.");
            }
        }
        System.out.println();
        try {
            long tempoInicial = System.currentTimeMillis();
            decompressor.decompress(selectedCompressedFilePath, decompressedFilename);
            long tempoFinal=System.currentTimeMillis();

            System.out.println(String.format("A descompressão LZW foi realizada em %.2fs", (tempoFinal - tempoInicial)/1000.0));
        } catch (IOException e) {
            System.err.println("A descompressão falhou: " + e.getMessage());
            e.printStackTrace();
        } finally {
            // No explicit close needed for try-with-resources
        }
        System.out.println("\n--- Verificação ---");
        System.out.println(String.format("Agora você pode comparar '%s' e '%s' para integridade.", inputFilename, decompressedFilename));
        System.out.println();
        long sizeOriginal=getSize(inputFilename);
        long sizeCompress=getSize(selectedCompressedFilePath);
        long sizeDecompress=getSize(decompressedFilename);
        float percentHuffman=((float)sizeDecompress/(float)sizeOriginal)*100;

        System.out.println(String.format("Tamanho de (%s): %d bytes", inputFilename, sizeOriginal));
        System.out.println(String.format("Tamanho de (%s): %d bytes", selectedCompressedFilePath, sizeCompress));
        System.out.println(String.format("Tamanho de (%s): %d bytes", decompressedFilename, sizeDecompress));
        System.out.println();
        System.out.println(String.format("Porcentagem de recuperação da descompressão do arquivo original é: %.2f%%.", percentHuffman));
    }
    public static long getSize(String filename) {
        File file = new File(filename);
        return file.length();
    }
}

/**
 * Implementação do algoritmo de descompressão LZW (Lempel-Ziv-Welch).
 */
class LZWD {

    private static final int MAX_DICTIONARY_SIZE = 1 << 24;

    public void decompress(String inputFilePath, String outputFilePath) throws IOException {
        try (DataInputStream dis = new DataInputStream(new FileInputStream(inputFilePath));
             BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream(outputFilePath))) {

            List<String> dictionary = new ArrayList<>();
            int dictionarySize = 256;

            for (int i = 0; i < dictionarySize; i++) {
                dictionary.add("" + (char) i);
            }

            int currentCode;
            int previousCode;
            String currentSequence;

            if (dis.available() > 0) {
                previousCode = dis.readInt();
                currentSequence = dictionary.get(previousCode);
                bos.write(currentSequence.getBytes());
            } else {
                System.out.println("Arquivo de entrada vazio.");
                return;
            }

            int nextCode = dictionarySize;

            while (dis.available() > 0) {
                currentCode = dis.readInt();

                String entry;
                if (dictionary.size() > currentCode) {
                    entry = dictionary.get(currentCode);
                } else if (currentCode == dictionary.size()) {
                    entry = dictionary.get(previousCode) + dictionary.get(previousCode).charAt(0);
                } else {
                    throw new IllegalStateException("Código comprimido inválido: " + currentCode);
                }

                bos.write(entry.getBytes());

                if (nextCode < MAX_DICTIONARY_SIZE) {
                    dictionary.add(dictionary.get(previousCode) + entry.charAt(0));
                    nextCode++;
                }
                previousCode = currentCode;
            }
            System.out.println("O arquivo escolhido foi " + inputFilePath);
            System.out.println("Arquivo descomprimido com sucesso como: " + outputFilePath);
            System.out.println("Descompressão concluída. Tamanho do dicionário: " + dictionary.size());
        }
    }
}

/**
 * Implementação unificada do algoritmo LZ78 para compressão e descompressão.
 * Adaptado para lidar com fluxos de bytes arbitrários (incluindo UTF-8 multi-byte).
 */
class LZ78Unified {
    // --- Constantes ---
    private static final int INITIAL_DICTIONARY_SIZE = 256;
    private static final int MAX_DICTIONARY_SIZE = 65536;
    private static final int MAX_CODE_BITS = (int) Math.ceil(Math.log(MAX_DICTIONARY_SIZE) / Math.log(2));
    private static final int BUFFER_SIZE = 8192;

    private static final int RESET_CODE = 0;
    private static final int DICTIONARY_SIZE_HEADER_BITS = 20;
    private static final double DICT_RESET_USAGE_RATIO = 0.8;

    // --- Private Nested Class for Trie Node (Compression Dictionary) ---
    private static class TrieNode {
        Map<Byte, TrieNode> children;
        int code;

        public TrieNode() {
            children = new HashMap<>();
            code = -1;
        }
    }

    // --- Private Static Nested Class for Bit Output Stream ---
    private static class BitOutputStream implements AutoCloseable {
        private BufferedOutputStream out;
        private int currentByte;
        private int bitsInCurrentByte;

        public BitOutputStream(OutputStream os) {
            this.out = new BufferedOutputStream(os);
            this.currentByte = 0;
            this.bitsInCurrentByte = 0;
        }

        public void writeBits(int value, int numBits) throws IOException {
            if (numBits <= 0 || numBits > 32) {
                throw new IllegalArgumentException("O número de bits deve estar entre 1 e 32.");
            }
            if (numBits < 32 && (value < 0 || value >= (1 << numBits))) {
                 throw new IllegalArgumentException(String.format("O valor %d não cabe em %d bits.", value, numBits));
            }

            for (int i = numBits - 1; i >= 0; i--) {
                boolean bit = ((value >> i) & 1) == 1;
                if (bit) {
                    currentByte |= (1 << (7 - bitsInCurrentByte));
                }
                bitsInCurrentByte++;
                if (bitsInCurrentByte == 8) {
                    out.write(currentByte);
                    currentByte = 0;
                    bitsInCurrentByte = 0;
                }
            }
        }

        public void writeByte(byte b) throws IOException {
            if (bitsInCurrentByte > 0) {
                out.write(currentByte);
                currentByte = 0;
                bitsInCurrentByte = 0;
            }
            out.write(b);
        }

        @Override
        public void close() throws IOException {
            if (bitsInCurrentByte > 0) {
                out.write(currentByte);
            }
            out.close();
        }
    }

    // --- Private Static Nested Class for Bit Input Stream ---
    private static class BitInputStream implements AutoCloseable {
        private BufferedInputStream in;
        private int currentByte;
        private int bitsInCurrentByte;
        private boolean eofReached = false;

        public BitInputStream(InputStream is) {
            this.in = new BufferedInputStream(is);
            this.currentByte = 0;
            this.bitsInCurrentByte = 0;
        }

        private int readBit() throws IOException {
            if (bitsInCurrentByte == 0) {
                int read = in.read();
                if (read == -1) {
                    eofReached = true;
                    return -1;
                }
                currentByte = read;
                bitsInCurrentByte = 8;
            }

            int bit = (currentByte >> (bitsInCurrentByte - 1)) & 1;
            bitsInCurrentByte--;
            return bit;
        }

        public int readBits(int numBits) throws IOException {
            if (numBits <= 0 || numBits > 32) {
                throw new IllegalArgumentException("O número de bits deve estar entre 1 e 32.");
            }
            if (eofReached) {
                throw new EOFException("Tentativa de ler bits após o fim do stream.");
            }

            int value = 0;
            for (int i = 0; i < numBits; i++) {
                int bit = readBit();
                if (bit == -1) {
                    eofReached = true;
                    throw new EOFException("Fim inesperado do stream ao ler " + numBits + " bits.");
                }
                value = (value << 1) | bit;
            }
            return value;
        }

        public byte readByte() throws IOException {
            if (bitsInCurrentByte > 0) {
                currentByte = 0;
                bitsInCurrentByte = 0;
            }
            int b = in.read();
            if (b == -1) {
                eofReached = true;
                throw new EOFException("Fim inesperado do stream ao ler um byte.");
            }
            return (byte) b;
        }

        public boolean isEOF() {
            if (bitsInCurrentByte == 0 && !eofReached) {
                try {
                    in.mark(1);
                    if (in.read() == -1) {
                        eofReached = true;
                    }
                    in.reset();
                } catch (IOException e) {
                    // Ignorar
                }
            }
            return eofReached && bitsInCurrentByte == 0;
        }

        @Override
        public void close() throws IOException {
            in.close();
        }
    }

    // --- Compression Method ---
    public void compress(String inputFilePath, String outputFilePath) throws IOException {
        TrieNode root = new TrieNode();
        int nextCode;

        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(inputFilePath), BUFFER_SIZE);
             BitOutputStream bos = new BitOutputStream(new FileOutputStream(outputFilePath))) {

            bos.writeBits(MAX_DICTIONARY_SIZE, DICTIONARY_SIZE_HEADER_BITS);

            nextCode = initializeCompressionDictionary(root);

            int currentCodeBits = 9;

            TrieNode currentNode = root;
            int byteRead;

            while ((byteRead = bis.read()) != -1) {
                byte currentByte = (byte) byteRead;

                TrieNode nextNode = currentNode.children.get(currentByte);

                if (nextNode != null) {
                    currentNode = nextNode;
                } else {
                    bos.writeBits(currentNode.code, currentCodeBits);
                    bos.writeByte(currentByte);

                    if (nextCode < MAX_DICTIONARY_SIZE) {
                        TrieNode newNode = new TrieNode();
                        newNode.code = nextCode++;
                        currentNode.children.put(currentByte, newNode);

                        if (nextCode > (1 << currentCodeBits) && currentCodeBits < MAX_CODE_BITS) {
                            currentCodeBits++;
                        }
                    }

                    if (nextCode >= MAX_DICTIONARY_SIZE * DICT_RESET_USAGE_RATIO && nextCode < MAX_DICTIONARY_SIZE) {
                        bos.writeBits(RESET_CODE, currentCodeBits);
                        root = new TrieNode();
                        nextCode = initializeCompressionDictionary(root);
                        currentCodeBits = 9;
                    }

                    currentNode = root.children.get(currentByte);
                }
            }

            if (currentNode != root && currentNode.code != -1) {
                bos.writeBits(currentNode.code, currentCodeBits);
            }
        }
    }

    private int initializeCompressionDictionary(TrieNode root) {
        root.children.clear();
        int codeCounter = 1;
        for (int i = 0; i < INITIAL_DICTIONARY_SIZE; i++) {
            TrieNode node = new TrieNode();
            node.code = codeCounter++;
            root.children.put((byte) i, node);
        }
        return codeCounter;
    }

    // --- Decompression Method ---
    public void decompress(String inputFilePath, String outputFilePath) throws IOException {
        List<byte[]> dictionary = new ArrayList<>();
        int nextCode;

        try (BitInputStream bis = new BitInputStream(new FileInputStream(inputFilePath));
             BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream(outputFilePath), BUFFER_SIZE)) {

            int maxDictSizeFromHeader = bis.readBits(DICTIONARY_SIZE_HEADER_BITS);

            nextCode = initializeDecompressionDictionary(dictionary);

            int currentCodeBits = 9;

            byte[] previousSequence = null;
            boolean isFirstCodeOfSegment = true;

            while (true) {
                int code;
                try {
                    code = bis.readBits(currentCodeBits);
                } catch (EOFException e) {
                    break;
                }

                if (code == RESET_CODE) {
                    nextCode = initializeDecompressionDictionary(dictionary);
                    currentCodeBits = 9;
                    previousSequence = null;
                    isFirstCodeOfSegment = true;
                    continue;
                }

                byte newByte;
                try {
                    newByte = bis.readByte();
                } catch (EOFException e) {
                    if (code < dictionary.size()) {
                        byte[] sequence = dictionary.get(code);
                        bos.write(sequence);
                    } else {
                        throw new IOException("Erro de descompressão: EOF inesperado após o código " + code +
                                ". Possível arquivo corrompido ou erro de lógica de compressão para a última sequência.");
                    }
                    break;
                }

                byte[] decodedSequence;
                if (code < dictionary.size()) {
                    decodedSequence = dictionary.get(code);
                } else {
                    if (isFirstCodeOfSegment) {
                        throw new IOException("Erro de descompressão: O primeiro código do segmento (" + code + ") é inválido. Esperado 1-" + INITIAL_DICTIONARY_SIZE + ".");
                    }
                    if (previousSequence == null) {
                        throw new IOException("Erro de descompressão: Código inválido " + code + " (previousSequence é nulo, mas não é o primeiro código do segmento).");
                    }
                    decodedSequence = Arrays.copyOf(previousSequence, previousSequence.length + 1);
                    decodedSequence[previousSequence.length] = newByte;
                }

                bos.write(decodedSequence);

                if (nextCode < maxDictSizeFromHeader) {
                    byte[] newEntry = Arrays.copyOf(decodedSequence, decodedSequence.length + 1);
                    newEntry[decodedSequence.length] = newByte;
                    dictionary.add(newEntry);
                    nextCode++;

                    if (nextCode > (1 << currentCodeBits) && currentCodeBits < MAX_CODE_BITS) {
                        currentCodeBits++;
                    }
                }

                previousSequence = decodedSequence;
                isFirstCodeOfSegment = false;
            }
        }
    }

    private int initializeDecompressionDictionary(List<byte[]> dictionary) {
        dictionary.clear();
        dictionary.add(null); // Code 0 is unused or reserved for RESET
        int codeCounter = 1;
        for (int i = 0; i < INITIAL_DICTIONARY_SIZE; i++) {
            dictionary.add(new byte[]{(byte) i});
            codeCounter++;
        }
        return codeCounter;
    }

    public static void compressProcess(String inputFile, String compressedFile) {
        LZ78Unified lz78 = new LZ78Unified();
        System.out.println("Processo de Compressão ---------------------------------------------------------");
        try {
            long startTime = System.currentTimeMillis();
            lz78.compress(inputFile, compressedFile);
            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Compressão bem-sucedida! Tempo gasto: %dms", (endTime - startTime)));
            long inputSize = getSize(inputFile);
            long compressedSize = getSize(compressedFile);
            System.out.println(String.format("Tamanho de entrada: %d bytes", inputSize));
            System.out.println(String.format("Tamanho comprimido: %d bytes", compressedSize));
            if (inputSize > 0) {
                float compressionPercentage = ((float) compressedSize / inputSize) * 100;
                System.out.println(String.format("Porcentagem de compressão: %.2f%% do arquivo original.", compressionPercentage));
            } else {
                System.out.println("Não é possível calcular a porcentagem de compressão para um arquivo de entrada vazio.");
            }
        } catch (IOException e) {
            System.err.println("A compressão falhou: " + e.getMessage());
            e.printStackTrace();
        }
    }
    public static void decompressProcess(String inputFile,String compressedFile, String decompressedFile) {
        LZ78Unified lz78 = new LZ78Unified();
        System.out.println("\nProcesso de Descompressão -------------------------------------------------------");
        try {
            long startTime = System.currentTimeMillis();
            lz78.decompress(compressedFile, decompressedFile);
            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Descompressão bem-sucedida! Tempo gasto: %dms", (endTime - startTime)));
            long decompressedSize = getSize(decompressedFile);
            System.out.println(String.format("Tamanho descomprimido: %d bytes", decompressedSize));
        } catch (IOException e) {
            System.err.println("A descompressão falhou: " + e.getMessage());
            e.printStackTrace();
        }

        try {
            if (getSize(inputFile) < 1000000) { // Check size before attempting byte-by-byte comparison
                byte[] original = Files.readAllBytes(Paths.get(inputFile));
                byte[] decompressed = Files.readAllBytes(Paths.get(decompressedFile));
                if (Arrays.equals(original, decompressed)) {
                    System.out.println("\nVerificação: Os arquivos original e descomprimido são idênticos.");
                } else {
                    System.err.println("\nVerificação: Incompatibilidade entre os arquivos original e descomprimido!");
                }
            } else {
                System.out.println(String.format("Pulando a verificação byte a byte para arquivos grandes (>%dMB).", (1000000 / (1024 * 1024))));
            }
        } catch (IOException e) {
            System.err.println("Erro durante a verificação: " + e.getMessage());
        }
        System.out.println("----------- Processo Concluído ----------------------------------------------------");
    }

    public static void createSampleData() {
         String filePath = "LZW/brazilian_portuguese_sample.txt";
         String compressedFile = "LZW/brazilian_portuguese_sample.lz78";
         String decompressedFile = "LZW/brazilian_portuguese_sample_decompressed.txt";

        try {
             File lzwDir = new File("LZW");
             if (!lzwDir.exists()) {
                 lzwDir.mkdirs();
             }

            try (OutputStreamWriter writer = new OutputStreamWriter(new FileOutputStream(filePath), StandardCharsets.UTF_8)) {
                String data = "Olá! Este é um exemplo de texto em português do Brasil para compressão LZ78. " +
                              "A compressão de dados é uma área fascinante. " +
                              "Vamos ver como o algoritmo lida com caracteres como 'ç', 'ã', 'é', 'í', 'ó', 'ú'. " +
                              "Repetindo a frase para melhor compressão: ";
                for (int i = 0; i < 2; i++) {
                    writer.write(data);
                }
                writer.write("FIM_DO_ARQUIVO_MARCADOR_XYZ.");
            }
            compressProcess(filePath, compressedFile);
            decompressProcess(filePath, compressedFile,  decompressedFile);
        } catch (IOException e) {
            System.err.println("Erro ao criar o arquivo de dados de exemplo: " + e.getMessage());
            e.printStackTrace();
        }
    }
    public static long getSize(String filename) {
        File file = new File(filename);
        if (file.exists()) {
            return file.length();
        }
        return -1;
    }
}

// =========================================================================
// CLASSES DE UTILIDADE (Originalmente de Functions.java, FileExplorer.java)
// =========================================================================

/**
 * Classe de Funções Utilitárias para tratamento de erros e conversões de entrada.
 * (Originalmente estagio1.leitura.Functions)
 */
class Functions {
    private static Scanner reader = new Scanner(System.in);

    public static int only_Int() {
        while (!reader.hasNextInt()) {
            System.out.println("Entrada inválida. Por favor, digite um número inteiro.");
            reader.next();
        }
        int value = reader.nextInt();
        reader.nextLine(); // Consome a quebra de linha restante
        return value;
    }

    public static float only_Float() {
        while (!reader.hasNextFloat()) {
            System.out.println("Entrada inválida. Por favor, digite um número flutuante.");
            reader.next();
        }
        float value = reader.nextFloat();
        reader.nextLine(); // Consome a quebra de linha restante
        return value;
    }

    public static double only_Double() {
        while (!reader.hasNextDouble()) {
            System.out.println("Entrada inválida. Por favor, digite um número decimal.");
            reader.next();
        }
        double value = reader.nextDouble();
        reader.nextLine(); // Consome a quebra de linha restante
        return value;
    }

    public static long only_Long() {
        while (!reader.hasNextLong()) {
            System.out.println("Entrada inválida. Por favor, digite um número longo.");
            reader.next();
        }
        long value = reader.nextLong();
        reader.nextLine(); // Consome a quebra de linha restante
        return value;
    }

    public static String reading() {
        return reader.nextLine();
    }

    public static int getYearNow() {
        return LocalDate.now().getYear();
    }

    public static boolean findFile(String Path) {
        File file = new File(Path);
        return file.exists();
    }

    public static void checkDirectory(String Path) {
        File directory = new File(Path);
        if (!directory.exists()) {
            directory.mkdirs();
        }
    }

    public static boolean getBooleanFromString(String root) {
        return root != null && root.trim().equalsIgnoreCase("S");
    }

    public static String getStringFromBoolean(boolean request) {
        return request ? "S" : "N";
    }

    public static String dateToString(String datetime) {
        // Usando Locale.US para garantir a consistência com o padrão de entrada
        SimpleDateFormat FORMATTER = new SimpleDateFormat("MM/dd/yyyy hh:mm:ss aa", Locale.US);
        try {
            return String.format("Data de Registro: %s\nHorario --------: %s",
                                 new SimpleDateFormat("dd/MM/yyyy", Locale.getDefault()).format(FORMATTER.parse(datetime)),
                                 new SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(FORMATTER.parse(datetime)));
        } catch (ParseException e) {
            e.printStackTrace();
            return "Data Inválida";
        }
    }

    public static int getDayWeek(LocalDate date) {
        return date.getDayOfWeek().getValue();
    }

    public static int getNumMonth(LocalDate date) {
        return date.getMonthValue();
    }

    public static int getCountList() {
        int count = 0;
        while (count < 1) {
            System.out.println("\nPor favor, digite a quantidade de itens a ser listada:");
            count = only_Int();
            if (count < 1) {
                System.out.println("A quantidade deve ser pelo menos 1.");
            }
        }
        return count;
    }

    public static List<String> generateStringList(String enunciado, int count) {
        List<String> result = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            System.out.println(enunciado + (i + 1) + ": ");
            result.add(reading());
        }
        return result;
    }
}


// =========================================================================
// StageFour: Criptografia de Dados (Adaptado de Crypto_UI.py)
// =========================================================================

class StageFour {

    protected static final Path DOCUMENTS_PATH = Paths.get(System.getProperty("user.home"), "Documents");
    protected static final Path DATA_FOLDER = DOCUMENTS_PATH.resolve("Data");
    protected static final Path COMPRESSED_FOLDER = DATA_FOLDER.resolve("Compress");
    protected static final Path TEMP_FOLDER = DATA_FOLDER.resolve("Temp");

    private static final Map<String, Path> PREDEFINED_FILES = new HashMap<>();

    static {
        Functions.checkDirectory(DATA_FOLDER.toString());
        Functions.checkDirectory(COMPRESSED_FOLDER.toString());
        Functions.checkDirectory(TEMP_FOLDER.toString());

        PREDEFINED_FILES.put("Arquivo de Dados (.db)", DATA_FOLDER.resolve("Arquivo de Dados.db"));
        PREDEFINED_FILES.put("Arquivo de Índice (.idx)", DATA_FOLDER.resolve("Arquivo de Indice.idx"));
        PREDEFINED_FILES.put("Arquivo de Árvore B (.btr)", DATA_FOLDER.resolve("Arquivo de Arvore B.btr"));

        for (Map.Entry<String, Path> entry : PREDEFINED_FILES.entrySet()) {
            if (!Files.exists(entry.getValue())) {
                try {
                    Files.write(entry.getValue(), String.format("Conteúdo de exemplo para %s", entry.getKey()).getBytes());
                    System.out.println("Criado arquivo dummy: " + entry.getValue());
                } catch (IOException e) {
                    System.err.println("Erro ao criar arquivo dummy: " + entry.getValue() + " - " + e.getMessage());
                }
            }
        }
    }


    public static void start() {
        int op = 0;
        do {
            System.out.println("\n==================================================");
            System.out.println("\nProcessos TP AEDS III - Parte IV (Criptografia de Dados)\n");
            System.out.println("1) Blowfish Criptografar");
            System.out.println("2) Blowfish Descriptografar");
            System.out.println("3) Gerar Chaves RSA");
            System.out.println("4) Híbrida (AES + RSA) Criptografar");
            System.out.println("5) Híbrida (AES + RSA) Descriptografar");
            System.out.println("6) Vigenere + Caesar (APÊNDICE) - Criptografar/Descriptografar"); // New option
            System.out.println("\n0) Sair para o Menu Principal\n\nEscolha um valor-------> :" );
            op = Functions.only_Int();

            try {
                switch (op) {
                    case 1:
                        blowfishEncryptOperation();
                        break;
                    case 2:
                        blowfishDecryptOperation();
                        break;
                    case 3:
                        generateRsaKeysOperation();
                        break;
                    case 4:
                        hybridEncryptOperation();
                        break;
                    case 5:
                        hybridDecryptOperation();
                        break;
                    case 6: // New case for Apendice
                        StageFourApendice.start();
                        break;
                    case 0:
                        System.out.println("\nVoltando ao Menu Principal.");
                        break;
                    default:
                        System.out.println("\nTente novamente, escolha fora do escopo.\n");
                }
            } catch (Exception e) {
                System.err.println("Ocorreu um erro: " + e.getMessage());
                e.printStackTrace();
            }
        } while (op != 0);
    }

    protected static String selectFileSource(String operationType) {
        System.out.println(String.format("Selecione a fonte do arquivo para %s:", operationType));
        System.out.println("1) Arquivo Pré-definido");
        System.out.println("2) Caminho do Arquivo (digitar)");
        System.out.print("Sua escolha: ");
        int choice = Functions.only_Int();

        if (choice == 1) {
            System.out.println("Arquivos pré-definidos disponíveis:");
            List<String> fileLabels = new ArrayList<>(PREDEFINED_FILES.keySet());
            for (int i = 0; i < fileLabels.size(); i++) {
                System.out.println(String.format("%d) %s (%s)", i + 1, fileLabels.get(i), PREDEFINED_FILES.get(fileLabels.get(i))));
            }
            System.out.print("Selecione o número do arquivo pré-definido: ");
            int fileChoice = Functions.only_Int();
            if (fileChoice > 0 && fileChoice <= fileLabels.size()) {
                Path selectedPath = PREDEFINED_FILES.get(fileLabels.get(fileChoice - 1));
                if (Files.exists(selectedPath)) {
                    System.out.println("Arquivo selecionado: " + selectedPath);
                    return selectedPath.toString();
                } else {
                    System.out.println("Erro: Arquivo pré-definido não encontrado. Por favor, verifique.");
                }
            } else {
                System.out.println("Escolha inválida.");
            }
        } else if (choice == 2) {
            System.out.print("Digite o caminho completo do arquivo: ");
            String filePath = Functions.reading();
            if (filePath != null && !filePath.trim().isEmpty() && Files.exists(Paths.get(filePath))) {
                return filePath;
            } else {
                System.out.println("Arquivo não encontrado ou caminho inválido.");
            }
        } else {
            System.out.println("Escolha inválida.");
        }
        return null;
    }


    private static void blowfishEncryptOperation() throws Exception {
        System.out.println("\n--- Criptografia Blowfish ---");

        String inputFilePathStr = selectFileSource("criptografar com Blowfish");
        if (inputFilePathStr == null) return;
        Path inputFilePath = Paths.get(inputFilePathStr);

        System.out.print("Nome do arquivo de saída (ex: arquivo.enc.bf): ");
        String outputFileName = Functions.reading();
        if (outputFileName == null || outputFileName.trim().isEmpty()) {
            System.out.println("Nome do arquivo de saída não fornecido.");
            return;
        }
        Path outputPath = TEMP_FOLDER.resolve(outputFileName);

        System.out.print("Senha para Blowfish: ");
        String password = Functions.reading();
        if (password == null || password.isEmpty()) {
            System.out.println("Senha não pode ser vazia.");
            return;
        }

        System.out.println("Criptografando...");
        long startTime = System.currentTimeMillis();
        try {
            BlowfishCipher.blowfishEncryptFile(inputFilePath.toString(), outputPath.toString(), password);
            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Arquivo criptografado com sucesso em '%s'!", outputPath.toString()));
            System.out.println(String.format("Tempo gasto: %.2f ms", (endTime - startTime) / 1.0));
        } catch (Exception e) {
            System.err.println("Erro na criptografia Blowfish: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static void blowfishDecryptOperation() throws Exception {
        System.out.println("\n--- Descriptografia Blowfish ---");

        System.out.print("Digite o caminho completo do arquivo criptografado (ex: arquivo.enc.bf): ");
        String inputFilePathStr = Functions.reading();
        if (inputFilePathStr == null || inputFilePathStr.trim().isEmpty() || !Files.exists(Paths.get(inputFilePathStr))) {
            System.out.println("Arquivo não encontrado ou caminho inválido.");
            return;
        }
        Path inputFilePath = Paths.get(inputFilePathStr);

        System.out.print("Nome do arquivo de saída (ex: arquivo.dec.bf): ");
        String outputFileName = Functions.reading();
        if (outputFileName == null || outputFileName.trim().isEmpty()) {
            System.out.println("Nome do arquivo de saída não fornecido.");
            return;
        }
        Path outputPath = TEMP_FOLDER.resolve(outputFileName);

        System.out.print("Senha para Blowfish: ");
        String password = Functions.reading();
        if (password == null || password.isEmpty()) {
            System.out.println("Senha não pode ser vazia.");
            return;
        }

        System.out.println("Descriptografando...");
        long startTime = System.currentTimeMillis();
        try {
            BlowfishCipher.blowfishDecryptFile(inputFilePath.toString(), outputPath.toString(), password);
            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Arquivo descriptografado com sucesso em '%s'!", outputPath.toString()));
            System.out.println(String.format("Tempo gasto: %.2f ms", (endTime - startTime) / 1.0));
        } catch (Exception e) {
            System.err.println("Erro na descriptografia Blowfish: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static void generateRsaKeysOperation() throws Exception {
        System.out.println("\n--- Geração de Chaves RSA ---");
        System.out.print("Nome base para os arquivos de chave (ex: minhas_chaves): ");
        String keyName = Functions.reading();
        if (keyName == null || keyName.trim().isEmpty()) {
            keyName = "minhas_chaves";
        }

        System.out.print("Tamanho da chave RSA (bits - 1024, 2048, 4096): ");
        int keySize = Functions.only_Int();
        if (keySize != 1024 && keySize != 2048 && keySize != 4096) {
            System.out.println("Tamanho de chave inválido. Usando 2048 bits como padrão.");
            keySize = 2048;
        }

        System.out.println("Gerando chaves RSA...");
        long startTime = System.currentTimeMillis();
        try {
            CryptographyHandler.generate_rsa_keys(keyName, keySize);
            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Chaves RSA geradas com sucesso em '%s/'!", TEMP_FOLDER.toString()));
            System.out.println(String.format("Tempo gasto: %.2f ms", (endTime - startTime) / 1.0));
            System.out.println(String.format("Verifique os arquivos '%s_public.pem' e '%s_private.pem' em '%s'.", keyName, keyName, TEMP_FOLDER.toString()));
        } catch (Exception e) {
            System.err.println("Erro ao gerar chaves RSA: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static void hybridEncryptOperation() throws Exception {
        System.out.println("\n--- Criptografia Híbrida (AES + RSA) ---");

        String inputFilePathStr = selectFileSource("criptografar hibridamente");
        if (inputFilePathStr == null) return;
        Path inputFilePath = Paths.get(inputFilePathStr);

        System.out.print("Digite o caminho completo para a chave pública (.pem): ");
        String publicKeyPathStr = Functions.reading();
        if (publicKeyPathStr == null || publicKeyPathStr.trim().isEmpty() || !Files.exists(Paths.get(publicKeyPathStr))) {
            System.out.println("Chave pública não encontrada ou caminho inválido.");
            return;
        }
        Path publicKeyPath = Paths.get(publicKeyPathStr);

        System.out.print("Nome do arquivo de saída (ex: arquivo.enc.aes_rsa): ");
        String outputFileName = Functions.reading();
        if (outputFileName == null || outputFileName.trim().isEmpty()) {
            System.out.println("Nome do arquivo de saída não fornecido.");
            return;
        }
        Path outputPath = TEMP_FOLDER.resolve(outputFileName);

        System.out.println("Criptografando hibridamente...");
        long startTime = System.currentTimeMillis();
        try {
            CryptographyHandler.hybrid_encrypt_file(inputFilePath.toString(), publicKeyPath.toString(), outputPath.toString());
            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Arquivo criptografado hibridamente com sucesso em '%s'!", outputPath.toString()));
            System.out.println(String.format("Tempo gasto: %.2f ms", (endTime - startTime) / 1.0));
        } catch (Exception e) {
            System.err.println("Erro na criptografia híbrida: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static void hybridDecryptOperation() throws Exception {
        System.out.println("\n--- Descriptografia Híbrida (AES + RSA) ---");

        System.out.print("Digite o caminho completo do arquivo criptografado hibridamente (ex: arquivo.enc.aes_rsa): ");
        String inputFilePathStr = Functions.reading();
        if (inputFilePathStr == null || inputFilePathStr.trim().isEmpty() || !Files.exists(Paths.get(inputFilePathStr))) {
            System.out.println("Arquivo criptografado não encontrado ou caminho inválido.");
            return;
        }
        Path inputFilePath = Paths.get(inputFilePathStr);

        System.out.print("Digite o caminho completo para a chave privada (.pem): ");
        String privateKeyPathStr = Functions.reading();
        if (privateKeyPathStr == null || privateKeyPathStr.trim().isEmpty() || !Files.exists(Paths.get(privateKeyPathStr))) {
            System.out.println("Chave privada não encontrada ou caminho inválido.");
            return;
        }
        Path privateKeyPath = Paths.get(privateKeyPathStr);


        System.out.print("Nome do arquivo de saída (ex: arquivo.dec.aes_rsa): ");
        String outputFileName = Functions.reading();
        if (outputFileName == null || outputFileName.trim().isEmpty()) {
            System.out.println("Nome do arquivo de saída não fornecido.");
            return;
        }
        Path outputPath = TEMP_FOLDER.resolve(outputFileName);

        System.out.println("Descriptografando hibridamente...");
        long startTime = System.currentTimeMillis();
        try {
            CryptographyHandler.hybrid_decrypt_file(inputFilePath.toString(), privateKeyPath.toString(), outputPath.toString());
            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Arquivo descriptografado hibridamente com sucesso em '%s'!", outputPath.toString()));
            System.out.println(String.format("Tempo gasto: %.2f ms", (endTime - startTime) / 1.0));
        } catch (Exception e) {
            System.err.println("Erro na descriptografia híbrida: " + e.getMessage());
            e.printStackTrace();
        }
    }
}


// =========================================================================
// Blowfish Implementation (Custom based on Python logic)
// =========================================================================
class BlowfishCipher {

    private static final int[] P_INIT = {
            0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344, 0xA4093822, 0x299F31D0,
            0x082EFA98, 0xEC4E6C89, 0x452821E6, 0x38D01377, 0xBE5466CF, 0x34E90C6C,
            0xC0AC29B7, 0xC97C50DD, 0x3F84D5B5, 0xB5470917, 0x9216D5D9, 0x8979FB1B
    };

    private static final int[][] S_INIT = {
            {
                    0xD1310BA6, 0x98DFB5AC, 0x2FFD72DB, 0xD01ADFB7, 0xB8E1AFED, 0x6A267E96,
                    0xBA7C9045, 0xF12C7F99, 0x24A19947, 0xB3916CF7, 0x0801F2E2, 0x858EFC16,
                    0x636920D8, 0x71574E69, 0xA458FE3E, 0x1BBEB41B
            },
            {
                    0xE01BECD3, 0x86FA67DB, 0xF9D50F25, 0xBA7C9045, 0xF12C7F99, 0x24A19947,
                    0xB3916CF7, 0x0801F2E2, 0x858EFC16, 0x636920D8, 0x71574E69, 0xA458FE3E,
                    0x1BBEB41B, 0xE01BECD3, 0x86FA67DB, 0xF9D50F25
            },
            {
                    0x26027E2D, 0x94B7E38C, 0x0119E153, 0x858ECDBA, 0x98DFB5AC, 0x2FFD72DB,
                    0xD01ADFB7, 0xB8E1AFED, 0x6A267E96, 0xBA7C9045, 0xF12C7F99, 0x24A19947,
                    0xB3916CF7, 0x0801F2E2, 0x858EFC16, 0x636920D8
            },
            {
                    0x71574E69, 0xA458FE3E, 0x1BBEB41B, 0xE01BECD3, 0x86FA67DB, 0xF9D50F25,
                    0xBA7C9045, 0xF12C7F99, 0x24A19947, 0xB3916CF7, 0x0801F2E2, 0x858EFC16,
                    0x636920D8, 0x71574E69, 0xA458FE3E, 0x1BBEB41B
            }
    };

    private int[] P;
    private int[][] S;

    public BlowfishCipher(byte[] key) {
        this.P = Arrays.copyOf(P_INIT, P_INIT.length);
        this.S = new int[4][];
        for (int i = 0; i < 4; i++) {
            this.S[i] = Arrays.copyOf(S_INIT[i], S_INIT[i].length);
        }

        int keyLen = key.length;
        int j = 0;
        for (int i = 0; i < 18; i++) {
            int chunk = 0;
            for (int k = 0; k < 4; k++) {
                if (j + k < keyLen) {
                    chunk = (chunk << 8) | (key[j + k] & 0xFF);
                } else {
                    chunk = chunk << 8;
                }
            }
            this.P[i] ^= chunk;
            j = (j + 4) % keyLen;
        }

        long L = 0;
        long R = 0;
        for (int i = 0; i < 18; i += 2) {
            long[] encryptedBlock = encryptBlock((int)L, (int)R);
            L = encryptedBlock[0];
            R = encryptedBlock[1];
            this.P[i] = (int)L;
            this.P[i+1] = (int)R;
        }

        for (int i = 0; i < 4; i++) {
            for (int j_inner = 0; j_inner < 256; j_inner += 2) {
                long[] encryptedBlock = encryptBlock((int)L, (int)R);
                L = encryptedBlock[0];
                R = encryptedBlock[1];
                this.S[i][j_inner] = (int)L;
                this.S[i][j_inner+1] = (int)R;
            }
        }
    }

    private int feistel(int x) {
        long h = ((long)S[0][(x >> 24) & 0xFF] + S[1][(x >> 16) & 0xFF]) & 0xFFFFFFFFL;
        h ^= (S[2][(x >> 8) & 0xFF]) & 0xFFFFFFFFL;
        h = (h + (S[3][x & 0xFF] & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
        return (int)h;
    }

    private long[] encryptBlock(int L_in, int R_in) {
        long L = L_in & 0xFFFFFFFFL;
        long R = R_in & 0xFFFFFFFFL;

        for (int i = 0; i < 16; i++) {
            L ^= (P[i] & 0xFFFFFFFFL);
            R ^= (feistel((int)L) & 0xFFFFFFFFL);
            long temp = L;
            L = R;
            R = temp;
        }
        R ^= (P[16] & 0xFFFFFFFFL);
        L ^= (P[17] & 0xFFFFFFFFL);
        return new long[]{L, R};
    }

    private long[] decryptBlock(int L_in, int R_in) {
        long L = L_in & 0xFFFFFFFFL;
        long R = R_in & 0xFFFFFFFFL;

        for (int i = 17; i > 1; i--) {
            L ^= (P[i] & 0xFFFFFFFFL);
            R ^= (feistel((int)L) & 0xFFFFFFFFL);
            long temp = L;
            L = R;
            R = temp;
        }
        R ^= (P[1] & 0xFFFFFFFFL);
        L ^= (P[0] & 0xFFFFFFFFL);
        return new long[]{L, R};
    }

    public byte[] encrypt(byte[] data) {
        int paddingLen = 8 - (data.length % 8);
        byte[] paddedData = Arrays.copyOf(data, data.length + paddingLen);
        for (int i = 0; i < paddingLen; i++) {
            paddedData[data.length + i] = (byte) paddingLen;
        }

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        ByteBuffer blockBuffer = ByteBuffer.allocate(8);
        blockBuffer.order(ByteOrder.BIG_ENDIAN);

        for (int i = 0; i < paddedData.length; i += 8) {
            blockBuffer.clear();
            blockBuffer.put(paddedData, i, 8);
            blockBuffer.flip();
            int L = blockBuffer.getInt();
            int R = blockBuffer.getInt();

            long[] encrypted = encryptBlock(L, R);
            try {
                bos.write(ByteBuffer.allocate(8).order(ByteOrder.BIG_ENDIAN).putInt((int)encrypted[0]).putInt((int)encrypted[1]).array());
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return bos.toByteArray();
    }

    public byte[] decrypt(byte[] data) throws ValueError {
        if (data.length % 8 != 0) {
            throw new ValueError("Dados criptografados têm tamanho inválido (não múltiplo de 8).");
        }

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        ByteBuffer blockBuffer = ByteBuffer.allocate(8);
        blockBuffer.order(ByteOrder.BIG_ENDIAN);

        for (int i = 0; i < data.length; i += 8) {
            blockBuffer.clear();
            blockBuffer.put(data, i, 8);
            blockBuffer.flip();
            int L = blockBuffer.getInt();
            int R = blockBuffer.getInt();

            long[] decrypted = decryptBlock(L, R);
            try {
                bos.write(ByteBuffer.allocate(8).order(ByteOrder.BIG_ENDIAN).putInt((int)decrypted[0]).putInt((int)decrypted[1]).array());
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        byte[] decryptedData = bos.toByteArray();

        if (decryptedData.length == 0) {
            throw new ValueError("Dados descriptografados vazios. Senha incorreta ou arquivo corrompido?");
        }

        int paddingLen = decryptedData[decryptedData.length - 1] & 0xFF;
        if (paddingLen > 8 || paddingLen == 0) {
            throw new ValueError("Padding incorreto ou dados corrompidos. Senha incorreta ou arquivo não Blowfish?");
        }

        for (int i = 1; i <= paddingLen; i++) {
            if ((decryptedData[decryptedData.length - i] & 0xFF) != paddingLen) {
                throw new ValueError("Integridade do padding violada. Senha incorreta ou arquivo corrompido.");
            }
        }

        return Arrays.copyOf(decryptedData, decryptedData.length - paddingLen);
    }

    static class ValueError extends Exception {
        public ValueError(String message) {
            super(message);
        }
    }


    public static byte[] deriveKeyPbkdf2(String password, byte[] salt, int dkLen, int iterations) throws Exception {
        SecretKeyFactory skf = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, iterations, dkLen * 8);
        SecretKey key = skf.generateSecret(spec);
        return key.getEncoded();
    }

    public static void blowfishEncryptFile(String inputFilePath, String outputFilePath, String password) throws Exception {
        byte[] salt = new byte[16];
        new Random().nextBytes(salt);

        byte[] key = deriveKeyPbkdf2(password, salt, 32, 10000);

        BlowfishCipher cipher = new BlowfishCipher(key);
        byte[] plaintext = Files.readAllBytes(Paths.get(inputFilePath));

        byte[] ciphertext = cipher.encrypt(plaintext);

        try (FileOutputStream fos = new FileOutputStream(outputFilePath)) {
            fos.write(salt);
            fos.write(ciphertext);
        }
    }

    public static void blowfishDecryptFile(String inputFilePath, String outputFilePath, String password) throws Exception {
        byte[] salt;
        byte[] ciphertext;

        try (FileInputStream fis = new FileInputStream(inputFilePath)) {
            salt = new byte[16];
            if (fis.read(salt) != 16) {
                throw new IOException("Arquivo de entrada muito curto para conter o salt.");
            }
            ciphertext = fis.readAllBytes();
        }

        byte[] key = deriveKeyPbkdf2(password, salt, 32, 10000);
        BlowfishCipher cipher = new BlowfishCipher(key);

        byte[] plaintext = cipher.decrypt(ciphertext);

        Files.write(Paths.get(outputFilePath), plaintext);
    }
}


// =========================================================================
// Hybrid Crypto (AES + RSA) Implementation
// =========================================================================
class CryptographyHandler {
    public static void generate_rsa_keys(String keyName, int keySize) throws Exception {
        KeyPairGenerator keyGen = KeyPairGenerator.getInstance("RSA");
        keyGen.initialize(keySize);
        KeyPair pair = keyGen.generateKeyPair();
        PrivateKey privateKey = pair.getPrivate();
        PublicKey publicKey = pair.getPublic();

        Path privateKeyPath = StageFour.TEMP_FOLDER.resolve(keyName + "_private.pem");
        Path publicKeyPath = StageFour.TEMP_FOLDER.resolve(keyName + "_public.pem");

        try (FileWriter writer = new FileWriter(privateKeyPath.toFile())) {
            writer.write("-----BEGIN RSA PRIVATE KEY-----\n");
            writer.write(Base64.getMimeEncoder().encodeToString(privateKey.getEncoded()));
            writer.write("\n-----END RSA PRIVATE KEY-----\n");
        }

        try (FileWriter writer = new FileWriter(publicKeyPath.toFile())) {
            writer.write("-----BEGIN PUBLIC KEY-----\n");
            writer.write(Base64.getMimeEncoder().encodeToString(publicKey.getEncoded()));
            writer.write("\n-----END PUBLIC KEY-----\n");
        }
    }

    public static void hybrid_encrypt_file(String inputFilePath, String publicKeyFilePath, String outputFilePath) throws Exception {
        byte[] plaintext = Files.readAllBytes(Paths.get(inputFilePath));

        byte[] publicKeyBytes = Files.readAllBytes(Paths.get(publicKeyFilePath));
        String publicKeyPEM = new String(publicKeyBytes, StandardCharsets.UTF_8)
                                .replace("-----BEGIN PUBLIC KEY-----", "")
                                .replace("-----END PUBLIC KEY-----", "")
                                .replaceAll("\\s", "");
        byte[] decodedPublicKey = Base64.getDecoder().decode(publicKeyPEM);
        X509EncodedKeySpec pubSpec = new X509EncodedKeySpec(decodedPublicKey);
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        PublicKey publicKey = keyFactory.generatePublic(pubSpec);

        KeyGenerator aesKeyGen = KeyGenerator.getInstance("AES");
        aesKeyGen.init(256); // 256-bit AES key
        SecretKey sessionKey = aesKeyGen.generateKey();

        Cipher rsaCipher = Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding");
        rsaCipher.init(Cipher.ENCRYPT_MODE, publicKey, new OAEPParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, new javax.crypto.spec.PSource.PSpecified(new byte[0])));
        byte[] encryptedSessionKey = rsaCipher.doFinal(sessionKey.getEncoded());

        byte[] iv = new byte[16]; // IV para AES GCM é de 16 bytes (128 bits)
        new Random().nextBytes(iv);
        
        Cipher aesCipher = Cipher.getInstance("AES/GCM/NoPadding");
        GCMParameterSpec gcmSpec = new GCMParameterSpec(128, iv); // 128-bit authentication tag
        aesCipher.init(Cipher.ENCRYPT_MODE, sessionKey, gcmSpec);
        
        byte[] ciphertextWithTag = aesCipher.doFinal(plaintext); // doFinal já inclui o tag no ciphertext para GCM

        try (FileOutputStream fos = new FileOutputStream(outputFilePath)) {
            // Escrever a chave de sessão criptografada
            fos.write(encryptedSessionKey);
            // Escrever o IV
            fos.write(iv);
            // O ciphertext já contém a tag de autenticação para GCM, então escrevemos tudo junto
            fos.write(ciphertextWithTag);
        }
    }

    public static void hybrid_decrypt_file(String inputFilePath, String privateKeyFilePath, String outputFilePath) throws Exception {
        byte[] privateKeyBytes = Files.readAllBytes(Paths.get(privateKeyFilePath));
        String privateKeyPEM = new String(privateKeyBytes, StandardCharsets.UTF_8)
                                 .replace("-----BEGIN RSA PRIVATE KEY-----", "")
                                 .replace("-----END RSA PRIVATE KEY-----", "")
                                 .replaceAll("\\s", "");
        byte[] decodedPrivateKey = Base64.getDecoder().decode(privateKeyPEM);
        PKCS8EncodedKeySpec privSpec = new PKCS8EncodedKeySpec(decodedPrivateKey);
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        PrivateKey privateKey = keyFactory.generatePrivate(privSpec);

        byte[] encryptedSessionKey;
        byte[] iv;
        byte[] ciphertextWithTag; // Para GCM, o ciphertext e o tag são lidos juntos

        try (FileInputStream fis = new FileInputStream(inputFilePath)) {
            // Obter o tamanho do módulo da chave privada para ler a chave de sessão criptografada
            if (!(privateKey instanceof RSAPrivateKey)) {
                throw new IllegalArgumentException("Chave privada não é uma chave RSA válida.");
            }
            int rsaKeySizeBytes = ((RSAPrivateKey) privateKey).getModulus().bitLength() / 8; // CORRIGIDO

            encryptedSessionKey = new byte[rsaKeySizeBytes];
            if (fis.read(encryptedSessionKey) != rsaKeySizeBytes) {
                throw new IOException("Arquivo criptografado muito curto para conter a chave de sessão criptografada.");
            }
            
            iv = new byte[16]; // IV para AES GCM
            if (fis.read(iv) != 16) {
                throw new IOException("Arquivo criptografado muito curto para conter o IV.");
            }

            ciphertextWithTag = fis.readAllBytes(); // O restante do arquivo é o ciphertext com a tag
        }

        Cipher rsaCipher = Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding");
        rsaCipher.init(Cipher.DECRYPT_MODE, privateKey, new OAEPParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, new javax.crypto.spec.PSource.PSpecified(new byte[0])));
        byte[] decryptedSessionKeyBytes = rsaCipher.doFinal(encryptedSessionKey);
        SecretKey sessionKey = new SecretKeySpec(decryptedSessionKeyBytes, "AES");

        Cipher aesCipher = Cipher.getInstance("AES/GCM/NoPadding");
        GCMParameterSpec gcmSpec = new GCMParameterSpec(128, iv); // 128 bits para o tag
        aesCipher.init(Cipher.DECRYPT_MODE, sessionKey, gcmSpec);

        byte[] plaintext = aesCipher.doFinal(ciphertextWithTag); // doFinal espera ciphertext e tag juntos

        Files.write(Paths.get(outputFilePath), plaintext);
    }
}


// =========================================================================
// Compression Helpers (BitStreams - Used by Huffman and LZ78Unified)
// =========================================================================
// Essas classes são auxiliares internas e não precisam ser públicas ou separadas
// por convenção, mas estão aqui para fins de exemplo e unificação.
// Em um projeto real, seriam classes internas ou privadas aninhadas.


// =========================================================================
// StageFourApendice: Vigenere + Caesar Cipher (Custom Implementation)
// =========================================================================

/**
 * Representa os dados da chave para as operações de criptografia/descriptografia Vigenere-Caesar.
 */
class KeyFileInfo {
    public String password;
    public int padding;
    public String originalFilename;

    public KeyFileInfo(String password, int padding, String originalFilename) {
        this.password = password;
        this.padding = padding;
        this.originalFilename = originalFilename;
    }
}

class StageFourApendice {

    protected static final Path TEMP_FOLDER = StageFour.TEMP_FOLDER; // Reutiliza a pasta temporária do StageFour

    /**
     * Inicia o menu para as operações de criptografia/descriptografia Vigenere + Caesar.
     */
    public static void start() {
        // AVISO CRÍTICO DE SEGURANÇA
        System.err.println("\n" + "=".repeat(80));
        System.err.println("!!! AVISO DE SEGURANÇA CRÍTICO !!!");
        System.err.println("Os métodos de criptografia Vigenere e Caesar são APENAS para fins educacionais e de demonstração.");
        System.err.println("**ELES NÃO SÃO SEGUROS PARA PROTEGER DADOS CONFIDENCIAIS EM UM AMBIENTE REAL.**");
        System.err.println("São facilmente quebrados e vulneráveis a ataques criptoanalíticos.");
        System.err.println("USE AS OPÇÕES DE CRIPTOGRAFIA HÍBRIDA (AES + RSA) PARA SEGURANÇA REAL.");
        System.err.println("=".repeat(80) + "\n");

        int op = 0;
        do {
            System.out.println("\n--- Vigenere + Caesar Cipher (APÊNDICE) ---");
            System.out.println("1) Criptografar Arquivo");
            System.out.println("2) Descriptografar Arquivo");
            System.out.println("\n0) Voltar ao Menu de Criptografia\n\nEscolha um valor-------> :" );
            op = Functions.only_Int();

            try {
                switch (op) {
                    case 1:
                        encryptFileOperation();
                        break;
                    case 2:
                        decryptFileOperation();
                        break;
                    case 0:
                        System.out.println("\nVoltando ao Menu de Criptografia.");
                        break;
                    default:
                        System.out.println("\nTente novamente, escolha fora do escopo.\\n");
                }
            } catch (Exception e) {
                System.err.println("Ocorreu um erro na operação Vigenere/Caesar: " + e.getMessage());
                e.printStackTrace();
            }
        } while (op != 0);
    }

    /**
     * Criptografa dados usando os cifradores Vigenere e Caesar.
     * Equivalent to Python's `hybrid_encrypt`.
     * @param data Os bytes de dados a serem criptografados.
     * @param password A senha para o cifrador Vigenere.
     * @param padding O valor de padding para o cifrador Caesar (0-255).
     * @return Os bytes de dados criptografados.
     */
    public static byte[] hybridEncrypt(byte[] data, String password, int padding) {
        byte[] keyBytes = password.getBytes(StandardCharsets.UTF_8);
        byte[] encryptedVigenere = new byte[data.length];

        // Criptografia Vigenere
        for (int i = 0; i < data.length; i++) {
            int byteValue = data[i] & 0xFF; // Converte para unsigned int (0-255)
            int shift = keyBytes[i % keyBytes.length] & 0xFF; // Converte para unsigned int (0-255)
            encryptedVigenere[i] = (byte) ((byteValue + shift) % 256);
        }

        // Criptografia Caesar
        byte[] encryptedCaesar = new byte[encryptedVigenere.length];
        for (int i = 0; i < encryptedVigenere.length; i++) {
            int byteValue = encryptedVigenere[i] & 0xFF;
            encryptedCaesar[i] = (byte) ((byteValue + padding) % 256);
        }
        return encryptedCaesar;
    }

    /**
     * Descriptografa dados usando os cifradores Caesar e Vigenere (na ordem inversa).
     * Equivalent to Python's `hybrid_decrypt`.
     * @param data Os bytes de dados a serem descriptografados.
     * @param password A senha para o cifrador Vigenere.
     * @param padding O valor de padding usado no cifrador Caesar.
     * @return Os bytes de dados descriptografados.
     */
    public static byte[] hybridDecrypt(byte[] data, String password, int padding) {
        byte[] keyBytes = password.getBytes(StandardCharsets.UTF_8);
        byte[] decryptedCaesar = new byte[data.length];

        // Descriptografia Caesar
        for (int i = 0; i < data.length; i++) {
            int byteValue = data[i] & 0xFF;
            decryptedCaesar[i] = (byte) ((byteValue - padding + 256) % 256); // Adiciona 256 para garantir resultado positivo antes do módulo
        }

        // Descriptografia Vigenere
        byte[] decryptedVigenere = new byte[decryptedCaesar.length];
        for (int i = 0; i < decryptedCaesar.length; i++) {
            int byteValue = decryptedCaesar[i] & 0xFF;
            int shift = keyBytes[i % keyBytes.length] & 0xFF;
            decryptedVigenere[i] = (byte) ((byteValue - shift + 256) % 256);
        }
        return decryptedVigenere;
    }

    /**
     * Gera o conteúdo do arquivo de chave como uma String.
     * Equivalent to Python's `create_key_file`.
     * @param password A senha.
     * @param padding O valor de padding.
     * @param filename O nome do arquivo original.
     * @return Uma String formatada para o arquivo de chave.
     */
    public static String createKeyFileContent(String password, int padding, String filename) {
        return String.format("password: %s\npadding: %d\nfilename: %s", password, padding, filename);
    }

    /**
     * Analisa um arquivo de chave e extrai a senha, o padding e o nome do arquivo original.
     * Equivalent to Python's `parse_key_file`.
     * @param keyFilePath O caminho para o arquivo de chave.
     * @return Um objeto KeyFileInfo contendo os dados da chave.
     * @throws IOException Se ocorrer um erro de leitura do arquivo.
     * @throws IllegalArgumentException Se o formato do arquivo de chave for inválido.
     */
    public static KeyFileInfo parseKeyFile(String keyFilePath) throws IOException, IllegalArgumentException {
        String password = null;
        Integer padding = null;
        String filename = null;

        List<String> lines = Files.readAllLines(Paths.get(keyFilePath), StandardCharsets.UTF_8);
        for (String line : lines) {
            if (line.startsWith("password:")) {
                password = line.substring("password: ".length());
            } else if (line.startsWith("padding:")) {
                padding = Integer.parseInt(line.substring("padding: ".length()));
            } else if (line.startsWith("filename:")) {
                filename = line.substring("filename: ".length());
            }
        }

        if (password == null || padding == null || filename == null) {
            throw new IllegalArgumentException("Arquivo de chave inválido: faltam informações essenciais.");
        }
        return new KeyFileInfo(password, padding, filename);
    }

    /**
     * Operação de criptografia Vigenere + Caesar através da interface do console.
     */
    private static void encryptFileOperation() throws Exception {
        System.out.println("\n--- Criptografia Vigenere + Caesar ---");

        String inputFilePathStr = StageFour.selectFileSource("criptografar com Vigenere + Caesar");
        if (inputFilePathStr == null) return;
        Path inputFilePath = Paths.get(inputFilePathStr);

        System.out.print("Senha de Criptografia (deixe em branco para auto-gerar): ");
        String password = Functions.reading();
        if (password.trim().isEmpty()) {
            password = generateRandomString(16);
            System.out.println("Senha auto-gerada: " + password);
        }

        System.out.print("Valor de Padding (0-255, 0 para auto-gerar): ");
        int padding = Functions.only_Int();
        if (padding == 0) {
            padding = new Random().nextInt(255) + 1; // 1-255
            System.out.println("Padding auto-gerado: " + padding);
        } else if (padding < 0 || padding > 255) {
            System.out.println("Valor de padding inválido. Usando 0 para auto-gerar.");
            padding = new Random().nextInt(255) + 1;
            System.out.println("Padding auto-gerado: " + padding);
        }

        System.out.print("Nome do arquivo de saída criptografado (ex: meu_arquivo.enc): ");
        String outputFileName = Functions.reading();
        if (outputFileName == null || outputFileName.trim().isEmpty()) {
            outputFileName = inputFilePath.getFileName().toString() + ".enc";
            System.out.println("Usando nome de arquivo padrão: " + outputFileName);
        }
        Path outputPath = TEMP_FOLDER.resolve(outputFileName);

        System.out.print("Nome do arquivo de chave (ex: meu_arquivo.key): ");
        String keyFileName = Functions.reading();
        if (keyFileName == null || keyFileName.trim().isEmpty()) {
            keyFileName = inputFilePath.getFileName().toString() + ".key";
            System.out.println("Usando nome de arquivo de chave padrão: " + keyFileName);
        }
        Path keyPath = TEMP_FOLDER.resolve(keyFileName);

        System.out.println("Criptografando...");
        long startTime = System.currentTimeMillis();

        try {
            byte[] originalData = Files.readAllBytes(inputFilePath);
            byte[] encryptedData = hybridEncrypt(originalData, password, padding);
            Files.write(outputPath, encryptedData);

            String keyContent = createKeyFileContent(password, padding, inputFilePath.getFileName().toString());
            Files.write(keyPath, keyContent.getBytes(StandardCharsets.UTF_8));

            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Arquivo criptografado com sucesso em '%s'!", outputPath.toString()));
            System.out.println(String.format("Arquivo de chave salvo em '%s'!", keyPath.toString()));
            System.out.println(String.format("Tempo gasto: %.2f ms", (endTime - startTime) / 1.0));
        } catch (IOException e) {
            System.err.println("Erro durante a criptografia do arquivo: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Operação de descriptografia Vigenere + Caesar através da interface do console.
     */
    private static void decryptFileOperation() throws Exception {
        System.out.println("\n--- Descriptografia Vigenere + Caesar ---");

        System.out.print("Digite o caminho completo do arquivo criptografado (extensão .enc esperada): ");
        String encryptedFilePathStr = Functions.reading();
        if (encryptedFilePathStr == null || encryptedFilePathStr.trim().isEmpty() || !Files.exists(Paths.get(encryptedFilePathStr))) {
            System.out.println("Arquivo criptografado não encontrado ou caminho inválido.");
            return;
        }
        Path encryptedPath = Paths.get(encryptedFilePathStr);

        System.out.print("Digite o caminho completo do arquivo de chave (extensão .key esperada): ");
        String keyFilePathStr = Functions.reading();
        if (keyFilePathStr == null || keyFilePathStr.trim().isEmpty() || !Files.exists(Paths.get(keyFilePathStr))) {
            System.out.println("Arquivo de chave não encontrado ou caminho inválido.");
            return;
        }
        Path keyPath = Paths.get(keyFilePathStr);

        System.out.print("Nome do arquivo de saída descriptografado (ex: original_nome.db): ");
        String outputFileName = Functions.reading();
        if (outputFileName == null || outputFileName.trim().isEmpty()) {
            System.out.println("Nome do arquivo de saída não fornecido. Será inferido do arquivo de chave.");
        }
        
        System.out.println("Descriptografando...");
        long startTime = System.currentTimeMillis();

        try {
            KeyFileInfo keyInfo = parseKeyFile(keyPath.toString());
            if (outputFileName.trim().isEmpty()) { // Use inferred name if not provided
                outputFileName = keyInfo.originalFilename;
            }
            Path outputPath = TEMP_FOLDER.resolve(outputFileName);


            byte[] encryptedData = Files.readAllBytes(encryptedPath);
            byte[] decryptedData = hybridDecrypt(encryptedData, keyInfo.password, keyInfo.padding);
            Files.write(outputPath, decryptedData);

            long endTime = System.currentTimeMillis();
            System.out.println(String.format("Arquivo descriptografado com sucesso em '%s'!", outputPath.toString()));
            System.out.println(String.format("Tempo gasto: %.2f ms", (endTime - startTime) / 1.0));
            System.out.println("Lembre-se de armazenar seus arquivos de chave em local seguro!");
        } catch (IOException e) {
            System.err.println("Erro durante a descriptografia do arquivo: " + e.getMessage());
            e.printStackTrace();
        } catch (IllegalArgumentException e) {
            System.err.println("Erro no formato do arquivo de chave: " + e.getMessage());
        }
    }

    // Helper to generate random string for password
    private static String generateRandomString(int length) {
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        StringBuilder sb = new StringBuilder(length);
        Random random = new Random();
        for (int i = 0; i < length; i++) {
            sb.append(chars.charAt(random.nextInt(chars.length())));
        }
        return sb.toString();
    }
}

