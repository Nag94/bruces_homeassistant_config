# Solar

## Graphic Corner

* Template: Gauge Text
* Show When Locked: True
* Leading: 
```
0
```
* Outer: 
```
{% if states('sun.sun') == 'below_horizon'%}🌙 {{ 
(states('sensor.solar_production_daily') | float) | round(1) }}{% 
else %}☀️ {{ (states('sensor.solaredge_ac_power_output') | float / 
1000.0 ) | round(1) }}{% endif %}
```
* Trailing: 
```
8
```
* Gauge: 
```
{{ states('sensor.solaredge_ac_power_output') | float/ 8000.0 }}
```

