"""
Programa que es comunica amb l'Arduinio via port serie, agafa la informació, l'enriqueix del JSON que ve del Fronius i ho mostra per pantalla, escriu a fitxer, etc.

PS_Rpi_1.0  Primera versió oficial.
PS_Rpi_1.1  Inclou tema sal. Nivell 11.

Proves empíriques (Hall, suma): No és el mateix de pujada que de baixada (hi ha certa histèresi)

Nivell 0-0:  350-550 (amb picos 650) /3 mostres: igual
Nivell 1-60: 4.500-7.500 (de pujada igual que N0) /3 mostres: igual (N0)
Nivell 2-70: 9.000-11.000  (de pujada igual que N0) /3 mostres: igual (N0)
Nivell 3-80: 13.000-16.000 OK, es comença a sentir soroll. /3 mostres: 14k-15k
Nivell 4-90: 16.500-21.000 OK. /3 mostres: 17k-18k
Nivell 5-100: 21.000-25.000 OK. /3 mostres: 22k-23k
Nivell 6-120: 27.000-32.000 OK. /3 mostres: 28k-32k comença a oscil.lar
Nivell 7-140: 35.000-40-000 OK. /3 37k-37k mostres: ja no osci.la...(??)
Nivell 8-160: 43.000-47.000 OK. Patró molt clar. /3 mostres: 44k-46k oscil.la clarament
Nivell 9-180: 49.000-51-000 OK. Patró claríssim. /3 mostres: igual
"""

import urllib.request
import json
import serial
import syslog
import time
import os

#-----------------------------------------------------------------------
#Inicialitzacions

port = '/dev/ttyUSB0' #A l'arrencar la Rpi el primer connectat agafa el UB0, després USB1, etc.
arduino = serial.Serial(port,9600,timeout=1)
time.sleep(3) #Pensem que s'està ressetejant l'Arduino ara.

Nivell=0
NivellAnt=0

#     Nivell             0     1     2     3     4     5     6    7      8     9    10    11
Hora_min_nivell   = [    0,    7,    8,    8,    8,    8,    8,    8,    8,    8,   11,   11]  # durant aquestes hores, ni ho intentis...
Hora_max_nivell   = [   21,   21,   21,   21,   21,   21,   21,   21,   21,   21,   17,   17]
Nivells_Servo     = [  "0", "60", "70", "80", "90","100","120","140","160","180","180","180"]  # graus del Servomotor
Nivells_Piscina   = ["OFF","OFF","OFF","OFF","OFF","OFF","OFF","OFF","OFF","OFF", "ON", "ON"]  # Piscina engegada o parada
Nivells_Sal       = ["OFF","OFF","OFF","OFF","OFF","OFF","OFF","OFF","OFF","OFF","OFF", "ON"]  # Sal engegada o parada

# Horaris
Inici_Piscina = 10
Fi_Piscina    = 19

Tempsinicial=time.time()
Segonstimestamp=0
Estatanteriorpiscina="OFF"
Estatanteriorsal="OFF"
MaxHall=35500  # Màxima lectura del Hall 100% de potència (sembla que varia si movem el sensor o algo...)
HallOffset=0 # Valor de reset.
Sunrise="00:00"
EffectiveSunrise="00:00"
EffectiveSunset="24:00"
Sunset="24:00"

#------------------------------------------------------------------------
# Funcions auxiliars

def format_hm(segons):
    return str(segons//3600).rjust(2,"0")+":"+str(int(segons%3600/60)).rjust(2,"0")

def horaminuts_a_minuts(hora):
    valors=hora.split(":")
    return int(valors[0])*60+int(valors[1])

#-----------------------------------------------------------------------
#Comencen les funcions

def Llegeix_dades():
    global Solar
    global Generat
    global Grid
    global Data
    global Hora
    global HoraInt
    global LecturaHall
    global HallOffset

    #Agafem dades del Fronius
    with urllib.request.urlopen("http://192.168.1.36/solar_api/v1/GetInverterRealtimeData.cgi?Scope=System") as url:
        objjson = json.loads(url.read().decode())
        Solar=objjson["Body"]["Data"]["PAC"]["Values"]["1"]
        Generat=objjson["Body"]["Data"]["DAY_ENERGY"]["Values"]["1"]

    # Agafem dades del Meter
    with urllib.request.urlopen("http://192.168.1.36/solar_api/v1/GetMeterRealtimeData.cgi?Scope=System") as url:
        objjson = json.loads(url.read().decode())
        Grid=int(objjson["Body"]["Data"]["0"]["PowerReal_P_Sum"])
        TimeStamp=objjson["Head"]["Timestamp"]
        Data=TimeStamp[8:10]+"-"+TimeStamp[5:7]+"-"+TimeStamp[0:4]
        Hora=TimeStamp[11:13]+":"+TimeStamp[14:16]
        HoraInt=int(TimeStamp[11:13])

    # Demanem dades del Hall a l'Arduino
    missatge="Hall"+"\n"
    arduino.write(missatge.encode('utf-8'))
    diuArduino=str(arduino.readline())[2:-5]

    if "Hall" not in diuArduino:
        Error="si"
    else:
        LecturaHall=diuArduino[5:-1]
        if HallOffset==0:
            HallOffset=int(int(LecturaHall.split('.')[0])*0.7)
        LecturaHall=int(LecturaHall.split('.')[0])-HallOffset

def Avalua_Sunrise_Sunset():
    global Solar
    global Hora
    global Sunrise
    global EffectiveSunrise
    global EffectiveSunset
    global Sunset

    if Solar>0 and Sunrise=="00:00":
        Sunrise=Hora
    if Solar>500 and EffectiveSunrise=="00:00":
        EffectiveSunrise=Hora
    if Solar>500:
        EffectiveSunset=Hora  #Vaig actualitzant fins que no actualizaré més.
    if Solar >0 and EffectiveSunset!="24:00":
        Sunset=Hora

def Avalua_Nivell():
    global Nivell
    global NivellAnt
    global Estatanteriorpiscina
    global Estatanteriorsal

    Estatanteriorpiscina=Nivells_Piscina[Nivell]
    Estatanteriorsal=Nivells_Sal[Nivell]
    NivellAnt=Nivell

    if Grid<0 and Nivell<11:
        if HoraInt>=Hora_min_nivell[Nivell+1] and HoraInt<=Hora_max_nivell[Nivell+1]: #Incrementem el temps si l'hora ho permet
            Nivell=Nivell+1
    if Grid>0 and Nivell>0:
        Nivell=Nivell-1


def Envia_Instruccions_Arduino():
    global Nivell
    global Arduino
    global Error
    global PiscinaForced
    global SalForced
    global LlumsForced
    global ServoForced
    global ValorPiscina
    global ValorSal
    global ValorServo
    global ValorLlums

    Error="no"

    # Piscina --------------------------
    if PiscinaForced=="":
        ValorPiscina=Nivells_Piscina[Nivell]
    else:
        ValorPiscina=PiscinaForced
    missatge="Piscina-"+ValorPiscina+"\n"
    arduino.write(missatge.encode('utf-8'))
    diuArduino=str(arduino.readline())[2:-5]
    if "ACK" not in diuArduino:
        Error="si"

    # Sal --------------------------
    if SalForced=="":
        ValorSal=Nivells_Sal[Nivell]
    else:
        ValorSal=SalForced
    missatge="Sal-"+ValorSal+"\n"
    arduino.write(missatge.encode('utf-8'))
    diuArduino=str(arduino.readline())[2:-5]
    if "ACK" not in diuArduino:
        Error="si"

    # Llums (sempre són forced) --------------------------
    ValorLlums=LlumsForced
    missatge="Llums-"+ValorLlums+"\n"
    arduino.write(missatge.encode('utf-8'))
    diuArduino=str(arduino.readline())[2:-5]
    if "ACK" not in diuArduino:
        Error="si"

    # Servo --------------------------
    if ServoForced=="":
        ValorServo=Nivells_Servo[Nivell]
    else:
        ValorServo=ServoForced
    missatge="Servo-"+ValorServo+"\n"
    arduino.write(missatge.encode('utf-8'))
    diuArduino=str(arduino.readline())[2:-5]
    if Error == "no":
            if "ACK" not in diuArduino:
                Error="si"


def Informa():
    global Data
    global DataInicial
    global Hora
    global Nivell
    global Solar
    global Generat
    global Grid
    global Tempsinicial
    global Segonstimestamp
    global Acumulatpiscinasegons
    global Acumulatsalsegons
    global ValorPiscina
    global ValorServo
    global PiscinaForced
    global SalForced
    global Sunrise
    global EffectiveSunrise
    global EffectiveSunset
    global Sunset

    #Calculem temps acumulat Piscina i Sal
    Segonsactuals=int(time.time()-Tempsinicial)
    print("---piscinaForced-->"+PiscinaForced+"<--")
    if Estatanteriorpiscina=="ON" or PiscinaForced=="ON":
        Acumulatpiscinasegons=Acumulatpiscinasegons+Segonsactuals-Segonstimestamp
    if Estatanteriorsal=="ON"  or SalForced=="ON":
        Acumulatsalsegons=Acumulatsalsegons+Segonsactuals-Segonstimestamp
    Segonstimestamp=Segonsactuals

    #Creem la tirallonga a imprimir
    tiraaimprimir="Data="+Data+"|Hora="+Hora+"|Ver=PS_Rpi_1.1"
    tiraaimprimir=tiraaimprimir+"|Acum="+str(Generat)
    tiraaimprimir=tiraaimprimir+"|Grid="+str(Grid)
    tiraaimprimir=tiraaimprimir+"|Solar="+str(Solar)
    tiraaimprimir=tiraaimprimir+"|Termo1="+str(100*LecturaHall//MaxHall)+"%"
    tiraaimprimir=tiraaimprimir+"|Niv="+str(NivellAnt)+"_"+str(Nivell)
    tiraaimprimir=tiraaimprimir+"|Servo1="+ValorServo+"_"
    if ServoForced!="":
        tiraaimprimir=tiraaimprimir+"F"
    tiraaimprimir=tiraaimprimir+"|Pisc="+ValorPiscina+"_"+format_hm(Acumulatpiscinasegons)+"_"
    if PiscinaForced!="":
        tiraaimprimir=tiraaimprimir+"F"
    tiraaimprimir=tiraaimprimir+"|Sal="+ValorSal+"_"+format_hm(Acumulatsalsegons)+"_"
    if SalForced!="":
        tiraaimprimir=tiraaimprimir+"F"
    tiraaimprimir=tiraaimprimir+"|Llums="+ValorLlums


    #Controlem error
    if Error=="si":
        tiraaimprimir=tiraaimprimir+"    ****** ERROR DE COMUNICACIÓ AMB ARDUINO ******"

    print(tiraaimprimir)

    fitxer = open("./sortida/PS_log_total.txt", "a") #a fitxer
    fitxer.write(tiraaimprimir+"\n")
    fitxer.close()

    fitxer = open("./sortida/avui.txt", "a") #a fitxer
    fitxer.write(tiraaimprimir+"\n")
    fitxer.close()

def Canvi_Data():
    global DataInicial
    global Acumulatpiscinasegons
    global Acumulatsalsegons
    global Sunrise
    global EffectiveSunrise
    global EffectiveSunset
    global Sunset

    tiraaimprimir="Data="+DataInicial+"|Piscina="+format_hm(Acumulatpiscinasegons)
    tiraaimprimir=tiraaimprimir+"|Sal="+format_hm(Acumulatsalsegons)
    tiraaimprimir=tiraaimprimir+"|Sunrise="+ Sunrise+"|EffectiveSunrise="+ EffectiveSunrise+"|EffectiveSunset="+ EffectiveSunset+"|Sunset="+ Sunset
    tiraaimprimir=tiraaimprimir+"\n"

    fitxer = open("./sortida/totals.txt", "a") #a fitxer
    fitxer.write(tiraaimprimir)
    fitxer.close()

    fitxer = open("./sortida/avui.txt", "w") #a fitxer
    fitxer.write("---------- "+Data+" ---------\n")
    fitxer.close()

    # calculem sunrise/sunset u10d
    u10dsunrise="24:00"
    u10defsunrise="24:00"
    u10defsunset="00:00"
    u10dsunset="00:00"

    fitxer = open("./sortida/totals.txt", "r") #Té moltes línies, només volem les últimes 10
    numlinies=0

    for linia in fitxer:
        numlinies=numlinies+1

    fitxer.seek(0)  #torna el "punter" al principi
    for linia in fitxer:
        numlinies=numlinies-1
        if numlinies<10:
            linia=linia.replace(" ","")
            linia=linia.replace("\n","")
            valors = dict(x.split("=") for x in linia.split("|"))
            sunrise=valors["Sunrise"]
            efsunrise=valors["EffectiveSunrise"]
            efsunset=valors["EffectiveSunset"]
            sunset=valors["Sunset"]

            if horaminuts_a_minuts(sunrise)<horaminuts_a_minuts(u10dsunrise):
                u10dsunrise=sunrise
            if horaminuts_a_minuts(efsunrise)<horaminuts_a_minuts(u10defsunrise):
                u10defsunrise=efsunrise
            if horaminuts_a_minuts(efsunset)>horaminuts_a_minuts(u10defsunset):
                u10defsunset=efsunset
            if horaminuts_a_minuts(sunset)>horaminuts_a_minuts(u10dsunset):
                u10dsunset=sunset
    fitxer.close()

    fitxer = open("./sortida/u10dss.tmp", "w") #a fitxer
    fitxer.write("u10dsunrise="+u10dsunrise+"|u10defsunrise="+u10defsunrise+"|u10defsunset="+u10defsunset+"|u10dsunset="+u10dsunset+"\n")
    fitxer.close()

    # ressetegem totes les variables
    Acumulatpiscinasegons=0
    Acumulatsalsegons=0
    Sunrise="00:00"
    EffectiveSunrise="00:00"
    EffectiveSunset="24:00"
    Sunset="24:00"

def Guarda_Estat():
    global Data
    global Acumulatpiscinasegons
    global Acumulatsalsegons
    global Sunrise
    global EffectiveSunrise
    global EffectiveSunset
    global Sunset

    fitxer = open("./sortida/estat.tmp", "w") #a fitxer
    fitxer.write("Data="+Data+"|Acumulatpiscinasegons="+str(Acumulatpiscinasegons)+"|Acumulatsalsegons="+str(Acumulatsalsegons)+"|Sunrise="+ str(Sunrise)+"|EffectiveSunrise="+ str(EffectiveSunrise)+"|EffectiveSunset="+ str(EffectiveSunset)+"|Sunset="+ str(Sunset)+"\n")
    fitxer.close()

def Recupera_Estat():
    global Data
    global Acumulatpiscinasegons
    global Acumulatsalsegons
    global Sunrise
    global EffectiveSunrise
    global EffectiveSunset
    global Sunset

    Acumulatpiscinasegons=0
    Acumulatsalsegons=0

    if os.path.exists("./sortida/estat.tmp"):
        fitxer = open("./sortida/estat.tmp", "r")
        for linia in fitxer:
            pass
        linia=linia.replace(" ","")
        linia=linia.replace("\n","")
        valors = dict(x.split("=") for x in linia.split("|"))

        if Data == valors["Data"]:
            Acumulatpiscinasegons=int(valors["Acumulatpiscinasegons"])
            Acumulatsalsegons=int(valors["Acumulatsalsegons"])
            Sunrise=valors["Sunrise"]
            EffectiveSunrise=valors["EffectiveSunrise"]
            EffectiveSunset=valors["EffectiveSunset"]
            Sunset=valors["Sunset"]

        fitxer.close()

def Llegeix_forced():
    global PiscinaForced
    global ServoForced
    global SalForced
    global LlumsForced

    PiscinaForced=""
    ServoForced=""
    SalForced=""
    LlumsForced=""

    if os.path.exists("./forced.txt"):
        fitxer = open("./forced.txt", "r")
        for linia in fitxer:
            x = linia.split("=")
            if x[0]=="Piscina":
                PiscinaForced= x[1][:-1]
            if x[0]=="Servo":
                ServoForced= x[1][:-1]
            if x[0]=="Sal":
                SalForced= x[1][:-1]
            if x[0]=="Llums":
                LlumsForced= x[1][:-1]
        fitxer.close()

#-----------------------------------------------------------------------
#Programa principal


count = 0
while 1:
    Llegeix_dades()
    if count == 0 :             #S'ha ressetejat la Raspberry?
        DataInicial = Data
        Recupera_Estat()
    count = count +1
    if DataInicial != Data :    # Són les 00:01 de la nit??
        Canvi_Data()
        DataInicial = Data
    Llegeix_forced()
    Avalua_Nivell()
    Envia_Instruccions_Arduino() #Tasca principal, és o realment actua.
    Informa()
    Avalua_Sunrise_Sunset()
    Guarda_Estat() #Per si se'n va la llum o algo...
    time.sleep(60)
