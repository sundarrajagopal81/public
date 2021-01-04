package com.languagelatte.simplechaos.properties;

import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;

public class ChaosPropertiesDefaultImpl implements ChaosProperties {

  private final Map<String, String> properties = new HashMap<>();

  @Override
  public void loadProperties() {

    for (Entry<String, String> entry : SimpleChaosConstants.defaultValueMap.entrySet()) {

      String systemValue = System.getProperty(entry.getKey());

      if (isValidPropertyValue(entry.getKey(), systemValue)) {
        this.properties.put(entry.getKey(), systemValue);
      } else {
        this.properties.put(entry.getKey(), entry.getValue());
      }
    }
  }

  // @Override
  // public void loadProperties(Map<String, String> properties) {
  //   loadProperties();

  //   for (Entry<String, String> e : properties.entrySet()) {
  //     if (isValidPropertyValue(e.getKey(), e.getValue())) {
  //       this.properties.put(e.getKey(), e.getValue());
  //     }
  //   }
  // }

  // @Override
  // public void loadProperties(Properties properties) {
  //   loadProperties();

  //   for (Entry<Object, Object> e : properties.entrySet()) {

  //     if (isValidPropertyValue(e.getKey().toString(), e.getValue().toString())) {
  //       this.properties.put(e.getKey().toString(), e.getValue().toString());
  //     }
  //   }
  // }

  @Override
  public Boolean getBooleanProperty(String key) {
    return Boolean.valueOf(properties.get(key));
  }

  @Override
  public Double getDoubleProperty(String key) {
    return Double.valueOf(properties.get(key));
  }

  @Override
  public Integer getIntProperty(String key) {
    return Integer.valueOf(properties.get(key));
  }

  @Override
  public String getStringProperty(String key) {
    // Dirty hack to prevent nullaway from complaining.
    return String.valueOf(properties.get(key));
  }
}