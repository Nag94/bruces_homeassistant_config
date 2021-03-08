# Hot Tub

## Graphic Corner

* Template: Gauge Text
* Show When Locked: True

* Leading: 
```
20
```
* Outer: 
```
{% if states('sensor.hottub_summary') == 'heat' %}🔥{% 
elif states('sensor.hottub_summary') == 'scheduled' %}⏱{% 
elif states('sensor.hottub_summary') == 'reached' %}✅{% 
elif states('sensor.hottub_summary') == 'off' %}❄️{% 
endif %}{{ states('input_number.hottub_water_temp') | int}}°c
```
* Trailing: 
```
{{ states('input_number.hottub_water_target') | int }} 
```
* Gauge: 
```
{{ [(states('sensor.hottub_water_temp') | float - 20.0) /
(states('input_number.hottub_water_target') | float -20.0),1]|min}} 
```








