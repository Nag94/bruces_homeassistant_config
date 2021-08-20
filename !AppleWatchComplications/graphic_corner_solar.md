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
{% if states('sun.sun') == 'below_horizon'%}{{ states('sensor.forecastsolar_today') | int }}/{{ 
(states('sensor.forecastsolar_tomorrow') | float) | int }}{% 
else %}☀️ {{ states('sensor.solar_production') | float }}{% endif %}
```
* Trailing: 
```
{{ states('sensor.forecastsolar_today') | int }}
```
* Gauge: 
```
{{[ (states('sensor.solar_production_daily_kw') | float) / (states('sensor.forecastsolar_today') | float) ,1] | min }}
```

