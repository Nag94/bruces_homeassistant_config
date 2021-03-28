# Solar


Live production figure, Gauge shows daily forecast
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
(states('sensor.solcast_forecast_tomorrow') | float) | round(1) }}{% 
else %}☀️ {{ (states('sensor.solaredge_ac_power_output') | float / 
1000.0 ) | round(1) }}{% endif %}
```
* Trailing: 
```
{{ states('input_number.solcast_latest_today_forecast') | int }}
```
* Gauge: 
```
{{ (states('sensor.solar_production_daily') | float) / (states('input_number.solcast_latest_today_forecast') | float)  }}



Live Production value and gauge showing same
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

