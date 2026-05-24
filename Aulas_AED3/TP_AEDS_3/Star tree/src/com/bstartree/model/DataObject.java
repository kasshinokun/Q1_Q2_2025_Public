package com.bstartree.model;

import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Classe de domínio para registros de acidentes
 * Compatível com a estrutura solicitada
 */
public class DataObject {
    
    // Formatters (conforme especificado)
    private final SimpleDateFormat LOCALDATEFORMATTER = 
            new SimpleDateFormat("dd/MM/yyyy hh:mm:ss aa", Locale.getDefault());
    private final DateTimeFormatter DATEFORMATTER = 
            DateTimeFormatter.ofPattern("dd/MM/yyyy");
    private final SimpleDateFormat HOURFORMATER = 
            new SimpleDateFormat("HH:mm:ss", Locale.getDefault());
    
    // Campos do registro
    private int ID_registro;                      // ID do Registro (chave)
    private String crash_date;
    private LocalDate data;
    private String traffic_control_device;    
    private String weather_condition;
    private List<String> lighting_condition;
    private String first_crash_type;
    private String trafficway_type;    
    private String alignment;    
    private String roadway_surface_cond;    
    private String road_defect;    
    private List<String> crash_type;
    private boolean intersection_related_i;
    private String damage;
    private String prim_contributory_cause;
    private int num_units;
    private List<String> most_severe_injury;
    private float injuries_total;
    private float injuries_fatal;
    private float injuries_incapacitating;
    private float injuries_non_incapacitating;
    private float injuries_reported_not_evident;
    private float injuries_no_indication;
    private int crash_hour;
    private int crash_day_of_week;
    private int crash_month;
    
    // Construtor padrão
    public DataObject() {
        this.lighting_condition = new ArrayList<>();
        this.crash_type = new ArrayList<>();
        this.most_severe_injury = new ArrayList<>();
    }
    
    // Getters e Setters
    public int getID_registro() { return ID_registro; }
    public void setID_registro(int id) { this.ID_registro = id; }
    
    public String getCrash_date() { return crash_date; }
    public void setCrash_date(String crash_date) { this.crash_date = crash_date; }
    
    public LocalDate getData() { return data; }
    public void setData(LocalDate data) { this.data = data; }
    
    public String getTraffic_control_device() { return traffic_control_device; }
    public void setTraffic_control_device(String traffic_control_device) { 
        this.traffic_control_device = traffic_control_device; 
    }
    
    public String getWeather_condition() { return weather_condition; }
    public void setWeather_condition(String weather_condition) { 
        this.weather_condition = weather_condition; 
    }
    
    public List<String> getLighting_condition() { return lighting_condition; }
    public void setLighting_condition(List<String> lighting_condition) { 
        this.lighting_condition = lighting_condition != null ? lighting_condition : new ArrayList<>(); 
    }
    
    public String getFirst_crash_type() { return first_crash_type; }
    public void setFirst_crash_type(String first_crash_type) { 
        this.first_crash_type = first_crash_type; 
    }
    
    public String getTrafficway_type() { return trafficway_type; }
    public void setTrafficway_type(String trafficway_type) { 
        this.trafficway_type = trafficway_type; 
    }
    
    public String getAlignment() { return alignment; }
    public void setAlignment(String alignment) { this.alignment = alignment; }
    
    public String getRoadway_surface_cond() { return roadway_surface_cond; }
    public void setRoadway_surface_cond(String roadway_surface_cond) { 
        this.roadway_surface_cond = roadway_surface_cond; 
    }
    
    public String getRoad_defect() { return road_defect; }
    public void setRoad_defect(String road_defect) { this.road_defect = road_defect; }
    
    public List<String> getCrash_type() { return crash_type; }
    public void setCrash_type(List<String> crash_type) { 
        this.crash_type = crash_type != null ? crash_type : new ArrayList<>(); 
    }
    
    public boolean isIntersection_related_i() { return intersection_related_i; }
    public void setIntersection_related_i(boolean intersection_related_i) { 
        this.intersection_related_i = intersection_related_i; 
    }
    
    public String getDamage() { return damage; }
    public void setDamage(String damage) { this.damage = damage; }
    
    public String getPrim_contributory_cause() { return prim_contributory_cause; }
    public void setPrim_contributory_cause(String prim_contributory_cause) { 
        this.prim_contributory_cause = prim_contributory_cause; 
    }
    
    public int getNum_units() { return num_units; }
    public void setNum_units(int num_units) { this.num_units = num_units; }
    
    public List<String> getMost_severe_injury() { return most_severe_injury; }
    public void setMost_severe_injury(List<String> most_severe_injury) { 
        this.most_severe_injury = most_severe_injury != null ? most_severe_injury : new ArrayList<>(); 
    }
    
    public float getInjuries_total() { return injuries_total; }
    public void setInjuries_total(float injuries_total) { this.injuries_total = injuries_total; }
    
    public float getInjuries_fatal() { return injuries_fatal; }
    public void setInjuries_fatal(float injuries_fatal) { this.injuries_fatal = injuries_fatal; }
    
    public float getInjuries_incapacitating() { return injuries_incapacitating; }
    public void setInjuries_incapacitating(float injuries_incapacitating) { 
        this.injuries_incapacitating = injuries_incapacitating; 
    }
    
    public float getInjuries_non_incapacitating() { return injuries_non_incapacitating; }
    public void setInjuries_non_incapacitating(float injuries_non_incapacitating) { 
        this.injuries_non_incapacitating = injuries_non_incapacitating; 
    }
    
    public float getInjuries_reported_not_evident() { return injuries_reported_not_evident; }
    public void setInjuries_reported_not_evident(float injuries_reported_not_evident) { 
        this.injuries_reported_not_evident = injuries_reported_not_evident; 
    }
    
    public float getInjuries_no_indication() { return injuries_no_indication; }
    public void setInjuries_no_indication(float injuries_no_indication) { 
        this.injuries_no_indication = injuries_no_indication; 
    }
    
    public int getCrash_hour() { return crash_hour; }
    public void setCrash_hour(int crash_hour) { this.crash_hour = crash_hour; }
    
    public int getCrash_day_of_week() { return crash_day_of_week; }
    public void setCrash_day_of_week(int crash_day_of_week) { 
        this.crash_day_of_week = crash_day_of_week; 
    }
    
    public int getCrash_month() { return crash_month; }
    public void setCrash_month(int crash_month) { this.crash_month = crash_month; }
    
    // Métodos utilitários
    public String formatDate(LocalDate date) {
        return date != null ? date.format(DATEFORMATTER) : null;
    }
    
    public String formatTime(int hour) {
        try {
            return HOURFORMATER.format(new java.util.Date(0, 0, 0, hour, 0, 0));
        } catch (Exception e) {
            return String.format("%02d:00:00", hour);
        }
    }
    
    @Override
    public String toString() {
        return String.format("DataObject{ID=%d, Date=%s, Type=%s}",
                ID_registro, crash_date, first_crash_type);
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof DataObject)) return false;
        DataObject that = (DataObject) o;
        return ID_registro == that.ID_registro;
    }
    
    @Override
    public int hashCode() {
        return Integer.hashCode(ID_registro);
    }
}
