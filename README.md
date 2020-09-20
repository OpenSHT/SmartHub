![alt text](https://github.com/OpenSHT/SmartHub/blob/master/static/images/header_tall.png?raw=true)

[OpenSHT.tech](https://opensht.tech/)
![GitHub](https://img.shields.io/github/license/OpenSHT/SmartHub?color=blue)
![GitHub issues](https://img.shields.io/github/issues/OpenSHT/SmartHub)
![GitHub top language](https://img.shields.io/github/languages/top/OpenSHT/SmartHub)
![GitHub repo size](https://img.shields.io/github/repo-size/OpenSHT/SmartHub)
![GitHub forks](https://img.shields.io/github/forks/OpenSHT/SmartHub?style=social)
![GitHub stars](https://img.shields.io/github/stars/OpenSHT/SmartHub?style=social)
![GitHub contributors](https://img.shields.io/github/contributors/OpenSHT/SmartHub)

A bit audacious to call this a smart home hub just yet, however... dream big I guess.
## Table of Contents

* [RoadMap](https://github.com/OpenSHT/SmartHub#roadmap)
* [Raspberry Pi Setup](https://github.com/OpenSHT/SmartHub#raspberry-pi-setup)
* [Troubleshooting](https://github.com/OpenSHT/SmartHub#troubleshooting)
* [Technologies](https://github.com/OpenSHT/SmartHub#technologies)
* [Requirements](https://github.com/OpenSHT/SmartHub#requirements)
* [Screenshots](https://github.com/OpenSHT/SmartHub#screenshots)

## RoadMap
#### Current Features:
<ul>
    <li>Thermostat support for modern HVAC systems that <u><b>DO NOT</b></u> have a compressor</li>
    <li><a href="https://openweathermap.org/">OpenWeatherMap</a> API integration</li>
    <li>ESP32 NodeMCU as a Serial slave feeding local and remote sensor data
        <ul>saves opening a thread to listen to a half dozen wifi devices chucking information at it</ul></li>
    <li>Support for the <b>DHT 11 / 22 / 21</b> on a GPIO connection</li>
    <li>Support for any micro-controller streaming the data as (hum,temp):</li>
    
        <64.8,23.5>
   <li>C/C++ code for the Arduino and ESP32 NodeMCU using the DHT11/22 sensor</li>
</ul>

#### Future Hub Integrations:
<ul>
    <li>Philips Hue lighting integration (just havent gotten around to it)
        <ul><a href="https://github.com/studioimaginaire/phue">phue</a></ul></li>
    <li>Wiz Smart Lighting (No good API available so may lack features)</li>
    <li>Garden monitoring & automation</li>
    <li>IOT Security Cameras (PiZero or other)</li>
</ul>

#### Features in need of <u><b>YOU!</b></u>, the open source community
<ul>
    <li>Additional smart home product I do not own such as:
        <ul>
            <li>Wyze Bulb, Lifx, TP-Link Bulbs, Sengled, ...</li>
            <li>ZigBee</li>
            <li>Z-Wave</li>
            <li>Alexa/Google Home?</li>
        </ul>
    </li>
</ul>

## Raspberry Pi Setup:

#### (Tested on RPI 3B+, 3)
1. Write the iso using 'dd':
	
		sudo dd bs=4M if=2020-05-27-raspios-buster-armhf.img of=/dev/sdb conv=fdatasync status="progress"
	
2. If using the HDMI&USB Connected TFT Touchscreens 'made' for RPi:
   
    i. With the fresh SD still plugged in, access the "/boot/config.txt" file
   
    ii. add the following options:
        
            hdmi_force_hotplug=1
            hdmi_group=2
            hdmi_mode=87
            hdmi_cvt=800 480 60 6 0 0 0
            hdmi_drive=1
            max_usb_current=1
            
    iii. Be sure to change to the appropriate resolution for the screen       
         
* NOTE: if you need ssh on first boot, place an empty file named '.ssh' in /rootfs
3. Setup Auto Update:
    
        sudo apt-get install unattended-upgrades
	
4. Configure interfaces and hostname etc...:
        
    i. Open terminal and type:
    
        sudo nano /etc/hosts
        
    ii. add the hostname 'openhub' to localhost as well as any 'static' IP you may have reseved on your router 
        
## Troubleshooting

- "Permission denied" when trying to read a serial device:
    
        - sudo chmod a+rw /dev/ttyUSB0
        
        
## Technologies
<ul>
    <li><a href="https://getbootstrap.com/">Bootstrap v4.5.2</a></li>
    <li><a href="https://hostingcrown.com/jquery-cdn">jQuery v3.4.0</a></li>
    <li><a href="https://www.chartjs.org/">Chart.js v2.93</a></li>
    <li><a href="https://rangeslider.js.org/">Rangeslider.js v2.3.0</a></li>
</ul>

## Requirements:
<ul>
    <li>Flask>=1.1.2</li>
    <li>pyserial>=3.4</li>
    <li>Flask-APScheduler>=1.11.0</li>
</ul>

## Screenshots

#### /thermostat

![alt text](https://github.com/OpenSHT/SmartHub/blob/master/screenshots/thermostat_page_tab_1.png?raw=true)

![alt text](https://github.com/OpenSHT/SmartHub/blob/master/screenshots/thermostat_page_tab_2.png?raw=true)

![alt text](https://github.com/OpenSHT/SmartHub/blob/master/screenshots/settings_page_1.png?raw=true)

![alt text](https://github.com/OpenSHT/SmartHub/blob/master/screenshots/settings_page_2.png?raw=true)
