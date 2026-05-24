package com.bstartree.io;

import com.bstartree.model.DataObject;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Serializador binário para DataObject
 * Formato compacto similar ao record format do SQLite
 */
public class Serializer {
    
    private static final DateTimeFormatter DATE_FORMATTER = 
            DateTimeFormatter.ofPattern("dd/MM/yyyy");
    
    /**
     * Serializa DataObject para array de bytes
     */
    public static byte[] serialize(DataObject obj) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DataOutputStream dos = new DataOutputStream(baos);
        
        // ID_registro (4 bytes)
        dos.writeInt(obj.getID_registro());
        
        // crash_date (UTF string com length prefix)
        writeUTFWithLength(dos, obj.getCrash_date());
        
        // data (LocalDate como string formatada)
        String dateStr = obj.getData() != null ? 
                obj.getData().format(DATE_FORMATTER) : "";
        writeUTFWithLength(dos, dateStr);
        
        // Campos string simples
        writeUTFWithLength(dos, obj.getTraffic_control_device());
        writeUTFWithLength(dos, obj.getWeather_condition());
        writeUTFWithLength(dos, obj.getFirst_crash_type());
        writeUTFWithLength(dos, obj.getTrafficway_type());
        writeUTFWithLength(dos, obj.getAlignment());
        writeUTFWithLength(dos, obj.getRoadway_surface_cond());
        writeUTFWithLength(dos, obj.getRoad_defect());
        writeUTFWithLength(dos, obj.getDamage());
        writeUTFWithLength(dos, obj.getPrim_contributory_cause());
        
        // intersection_related_i (boolean)
        dos.writeBoolean(obj.isIntersection_related_i());
        
        // num_units (int)
        dos.writeInt(obj.getNum_units());
        
        // Campos float
        dos.writeFloat(obj.getInjuries_total());
        dos.writeFloat(obj.getInjuries_fatal());
        dos.writeFloat(obj.getInjuries_incapacitating());
        dos.writeFloat(obj.getInjuries_non_incapacitating());
        dos.writeFloat(obj.getInjuries_reported_not_evident());
        dos.writeFloat(obj.getInjuries_no_indication());
        
        // Campos int de tempo
        dos.writeInt(obj.getCrash_hour());
        dos.writeInt(obj.getCrash_day_of_week());
        dos.writeInt(obj.getCrash_month());
        
        // Listas de strings (serializadas como count + elementos)
        writeStringList(dos, obj.getLighting_condition());
        writeStringList(dos, obj.getCrash_type());
        writeStringList(dos, obj.getMost_severe_injury());
        
        dos.close();
        return baos.toByteArray();
    }
    
    /**
     * Desserializa array de bytes para DataObject
     */
    public static DataObject deserialize(byte[] data) throws IOException {
        DataObject obj = new DataObject();
        ByteArrayInputStream bais = new ByteArrayInputStream(data);
        DataInputStream dis = new DataInputStream(bais);
        
        obj.setID_registro(dis.readInt());
        obj.setCrash_date(readUTFWithLength(dis));
        
        String dateStr = readUTFWithLength(dis);
        if (dateStr != null && !dateStr.isEmpty()) {
            try {
                obj.setData(LocalDate.parse(dateStr, DATE_FORMATTER));
            } catch (Exception e) {
                obj.setData(null);
            }
        }
        
        obj.setTraffic_control_device(readUTFWithLength(dis));
        obj.setWeather_condition(readUTFWithLength(dis));
        obj.setFirst_crash_type(readUTFWithLength(dis));
        obj.setTrafficway_type(readUTFWithLength(dis));
        obj.setAlignment(readUTFWithLength(dis));
        obj.setRoadway_surface_cond(readUTFWithLength(dis));
        obj.setRoad_defect(readUTFWithLength(dis));
        obj.setDamage(readUTFWithLength(dis));
        obj.setPrim_contributory_cause(readUTFWithLength(dis));
        
        obj.setIntersection_related_i(dis.readBoolean());
        obj.setNum_units(dis.readInt());
        
        obj.setInjuries_total(dis.readFloat());
        obj.setInjuries_fatal(dis.readFloat());
        obj.setInjuries_incapacitating(dis.readFloat());
        obj.setInjuries_non_incapacitating(dis.readFloat());
        obj.setInjuries_reported_not_evident(dis.readFloat());
        obj.setInjuries_no_indication(dis.readFloat());
        
        obj.setCrash_hour(dis.readInt());
        obj.setCrash_day_of_week(dis.readInt());
        obj.setCrash_month(dis.readInt());
        
        obj.setLighting_condition(readStringList(dis));
        obj.setCrash_type(readStringList(dis));
        obj.setMost_severe_injury(readStringList(dis));
        
        dis.close();
        return obj;
    }
    
    /**
     * Escreve string UTF com prefixo de length (2 bytes)
     */
    private static void writeUTFWithLength(DataOutputStream dos, String str) 
            throws IOException {
        if (str == null) {
            dos.writeShort(0);
        } else {
            byte[] bytes = str.getBytes(StandardCharsets.UTF_8);
            dos.writeShort(bytes.length);
            dos.write(bytes);
        }
    }
    
    /**
     * Lê string UTF com prefixo de length
     */
    private static String readUTFWithLength(DataInputStream dis) 
            throws IOException {
        int length = dis.readShort();
        if (length == 0) return null;
        byte[] bytes = new byte[length];
        dis.readFully(bytes);
        return new String(bytes, StandardCharsets.UTF_8);
    }
    
    /**
     * Serializa lista de strings
     */
    private static void writeStringList(DataOutputStream dos, List<String> list) 
            throws IOException {
        if (list == null) {
            dos.writeInt(0);
        } else {
            dos.writeInt(list.size());
            for (String s : list) {
                writeUTFWithLength(dos, s);
            }
        }
    }
    
    /**
     * Desserializa lista de strings
     */
    private static List<String> readStringList(DataInputStream dis) 
            throws IOException {
        int count = dis.readInt();
        if (count == 0) return new ArrayList<>();
        List<String> list = new ArrayList<>(count);
        for (int i = 0; i < count; i++) {
            list.add(readUTFWithLength(dis));
        }
        return list;
    }
    
    /**
     * Calcula tamanho estimado de um objeto serializado
     */
    public static int estimateSize(DataObject obj) {
        // Estimativa conservadora: ~500 bytes por registro
        return 512;
    }
}
