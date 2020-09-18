'''
Bot 0.1 Molt bàsic, aprenent.
Bot 0.2 Una mica de formateig (que no formatge)
...
Bot 0.6 Anem fent...
Bot 0.7 A veure si uso la versió 12 correctament (update,context)... Aconseguit!!
Bot 0.9 Afegim fitxer totals.txt (inclou sunrise...Sunset)
Bot 1.0 Primera versió oficial
Bot 1.1 Inclou tema sal
Bot 1.2 Remodelació dels botons
Bot 1.3 Botons nous, ip, etc.

Programa principal del bot. Coses a tenir en compte.
- Cal ternir-lo corrent des de la raspberry (amb nohup per exemple)
- No té contrasenya, qualsevol persona que descobrís per casualitat el nom del bot podria parlar amb ell
'''

import re
# Llibreries de python pels bots de Telegram
import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import time
import urllib.request
import json

def horaminuts_a_minuts(hora):
    valors=hora.split(":")
    return int(valors[0])*60+int(valors[1])

def escapa_missatge(message):
    message=message.replace("_","\_")
    message=message.replace(":","\:")
    message=message.replace(".","\.")
    message=message.replace("-","\-")
    message=message.replace("=","\=")
    message=message.replace(">","\>")
    message=message.replace("|","\|")
    message=message.replace("(","\(")
    message=message.replace(")","\)")
    message=message.replace("!","\!")
    return message

def printa_botonera(update, context,missatge):

    custom_keyboard = [['/info', '/botons', '/totals', '/help']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,resize_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id,text=escapa_missatge(missatge),reply_markup=reply_markup,parse_mode="Markdownv2")

def actualitza_forced(valor1, valor2):

    with open('../forced.txt') as f:
        lines = f.readlines()

    f = open("../forced.txt", "w")
    for linia in lines:
        trobat=re.search("^"+valor1, linia)
        if not trobat:
            f.write(linia)
    if(valor2!=""):
        f.write(valor2+"\n")
    f.close()


# Botons
def botons(update, context):

    iconbotoPiscinaON=""
    iconbotoPiscinaOFF=""
    iconbotoPiscinaAuto=""
    iconbotoSalON=""
    iconbotoSalOFF=""
    iconbotoSalAuto=""
    iconbotoLlumsON=""
    iconbotoLlumsOFF="*"
    iconServoAuto="*"
    fitxer = open("../forced.txt", "r")
    for linia in fitxer:
        if (re.search("^Piscina=ON", linia)):
            iconbotoPiscinaON="*"
        if (re.search("^Piscina=OFF", linia)):
            iconbotoPiscinaOFF="*"
        if (re.search("^Sal=ON", linia)):
            iconbotoSalON="*"
        if (re.search("^Sal=OFF", linia)):
            iconbotoSalOFF="*"
        if (re.search("^Llums=ON", linia)):
            iconbotoLlumsON="*"
            iconbotoLlumsOFF=""
        if (re.search("^Servo=", linia)):
            iconServoAuto=""
    fitxer.close()
    if iconbotoPiscinaON=="" and iconbotoPiscinaOFF=="":
        iconbotoPiscinaAuto=" *"
    if iconbotoSalON=="" and iconbotoSalOFF=="":
        iconbotoSalAuto="*"

    keyboard = [[InlineKeyboardButton("Piscina ON"+iconbotoPiscinaON, callback_data='Piscina_ON'),
                 InlineKeyboardButton("Piscina OFF"+iconbotoPiscinaOFF, callback_data='Piscina_OFF'),
                 InlineKeyboardButton("Piscina Auto"+iconbotoPiscinaAuto, callback_data='Piscina_auto')],
                 [InlineKeyboardButton("Sal ON"+iconbotoSalON, callback_data='Sal_ON'),
                 InlineKeyboardButton("Sal OFF"+iconbotoSalOFF, callback_data='Sal_OFF'),
                 InlineKeyboardButton("Sal Auto"+iconbotoSalAuto, callback_data='Sal_auto')],
                [InlineKeyboardButton("Llums ON"+iconbotoLlumsON, callback_data='Llums_ON'),
                 InlineKeyboardButton("Llums OFF"+iconbotoLlumsOFF, callback_data='Llums_OFF'),],
                 [InlineKeyboardButton("Servo 0", callback_data='Servo_0'),
                  InlineKeyboardButton("Servo 90", callback_data='Servo_90'),
                  InlineKeyboardButton("Servo 180", callback_data='Servo_180')],
                 [InlineKeyboardButton("Servo auto"+iconServoAuto, callback_data='Servo_auto')],
                 [InlineKeyboardButton("Sortir", callback_data='Sortir')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Què vols fer?', reply_markup=reply_markup)

# Resposta botons
def resposta_botons(update, context):
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    query.edit_message_text(text="Has triat: {}".format(query.data))

    if (query.data=="Piscina_ON"):
        actualitza_forced("Piscina","Piscina=ON")
    if (query.data=="Piscina_OFF"):
        actualitza_forced("Piscina","Piscina=OFF")
    if (query.data=="Piscina_auto"):
        actualitza_forced("Piscina","")
    if (query.data=="Sal_ON"):
        actualitza_forced("Sal","Sal=ON")
    if (query.data=="Sal_OFF"):
        actualitza_forced("Sal","Sal=OFF")
    if (query.data=="Sal_auto"):
        actualitza_forced("Sal","")
    if (query.data=="Llums_ON"):
        actualitza_forced("Llums","Llums=ON")
    if (query.data=="Llums_OFF"):
        actualitza_forced("Llums","Llums=OFF")
    if (query.data=="Llums_auto"):
        actualitza_forced("Llums","")
    if (query.data=="Servo_0"):
        actualitza_forced("Servo","Servo=0")
    if (query.data=="Servo_90"):
        actualitza_forced("Servo","Servo=90")
    if (query.data=="Servo_180"):
        actualitza_forced("Servo","Servo=180")
    if (query.data=="Servo_auto"):
        actualitza_forced("Servo","")
    if (query.data=="Sortir"):
        context.bot.send_message(chat_id=update.effective_chat.id, text="deu...",  parse_mode="Markdown")

# Comanda /help
def comanda_help(update, context):
    message = '''
    Programeta que mostra com va el tema de les plaques solars i permet fer alguns ajustos al fitxer forced.txt.
    \U0001F60E (ulleres)
    I això és tot! ( _de moment..._ )
    '''

    with urllib.request.urlopen("https://api.ipify.org/?format=json") as url:
        objjson = json.loads(url.read().decode())
        ippublica=objjson["ip"]

    user = update.message.from_user
    if (user["first_name"]+user["last_name"])=="RamonRos":
        message=message+"\n  "+ippublica+"  \n"

    printa_botonera(update, context,message)


# Comanda /list.Llista les darreres entrades del fitxer 'avui.txt'
def comanda_list(update, context):
    fitxer = open("../sortida/avui.txt", "r")
    liniest=0
    for linia in fitxer:
        liniest=liniest+1
    fitxer.close()
    fitxer = open("../sortida/avui.txt", "r")
    linies=0
    message="```\n"
    for linia in fitxer:
        if linies>liniest-62:
            linia=linia.replace(" ","")
            linia=linia.replace("\n","")
            valors = dict(x.split("=") for x in linia.split("|"))

            message=message+valors["Hora"]
            message=message+" GS="+valors["Grid"]+"/"+valors["Solar"]
            message=message+" N="+valors["Niv"]
            message=message+" T1="+valors["Termo1"]
            message=message+" P="+valors["Pisc"].split("_")[0]+" "+valors["Pisc"].split("_")[2]
            message=message+" S="+valors["Sal"].split("_")[0]+" "+valors["Sal"].split("_")[2]
            message=message+" Ll="+valors["Llums"]
            message=message+"\n"

        linies=linies+1
    fitxer.close()
    message=message+"```\n"

    #context.bot.send_message(chat_id=update.effective_chat.id, text=escapa_missatge(message), parse_mode="Markdownv2")
    printa_botonera(update, context,message)

# Comanda /totals.Llista les darreres entrades del fitxer 'totals.txt'
def comanda_totals(update, context):
    fitxer = open("../sortida/totals.txt", "r")
    liniest=0
    for linia in fitxer:
        liniest=liniest+1
    fitxer.close()
    fitxer = open("../sortida/totals.txt", "r")
    linies=0
    message="```\n"
    for linia in fitxer:
        if linies>liniest-32:
            linia=linia.replace(" ","")
            linia=linia.replace("Data=","")
            linia=linia.replace("-20","-")
            linia=linia.replace("|Piscina=","|P=")
            linia=linia.replace("|Sal=","|S=")
            linia=linia.replace("|Sunrise=","|Sr=")
            linia=linia.replace("|EffectiveSunrise=","|ESr=")
            linia=linia.replace("|EffectiveSunset=","|ESs=")
            linia=linia.replace("|Sunset=","|Ss=")
            linia=linia.replace("|"," ")
            message=message+linia
        linies=linies+1
    fitxer.close()
    message=message+"```\n"

    context.bot.send_message(chat_id=update.effective_chat.id, text=escapa_missatge(message), parse_mode="Markdownv2")
    printa_botonera(update, context)



#Retorna la icona adequada segons si el nivell puja o baixa
def icona_nivell(n1,n2):

    if n1<n2:
        return " \U00002197" # El nivell està pujant
    if n1>n2:
        return " \U00002198" # El nivell està baixant
    if n1==n2:
        return " \U000027A1" # El nivell no ha variat.

#Retorna la icona adequada segons si el termo està ja a tope o no (si ho intuim...)
def icona_termo(nivell,pct):

    if int(nivell)>3 and pct=="0%":
        return " \U0001F51D" # El termo està a tope i ja no admet més
    else:
        return ""

#Retorna la icona si els llums estan engegats.
def icona_llums(estat):

    if estat=="ON":
        return " \U0001F4A1" # Llums ON
    else:
        return ""

#Retorna la icona adequada segons els valors Grid/Solar
def icona_grid_solar(grid, solar):
    global hora

    hora=int(hora[0:2])
    grid=int(grid)
    solar=int(solar)
    sunrise=8  #provisional, algun dia s'hauria de fer real i dinàmic
    sunset=20    #provisional, algun dia s'hauria de fer real i dinàmic

    if hora<=sunrise or hora>=sunset:
        print("\n---> cas a")
        return " \U000026AA" # Blanc
    if grid <=0:
        print("\n---> cas b")
        return " \U0001F7E2" # Verd
    ratio=solar/grid
    if ratio >0.7:
        print("\n---> cas b")
        return " \U0001F7E2" # Verd
    if ratio >0.4:
        print("\n---> cas c")
        return " \U0001F7E0" # Taronja
    if ratio >0.05:
        print("\n---> cas d")
        return " \U0001F7E1" # Groc
    if ratio >=0:
        print("\n---> cas e")
        return " \U0001F534" # Vermell
    else: #No hauria d'arribar mai aquí...
        print("\n---> cas error ")
        return " \U00002753" # Interrogant

# Comanda /info.La bàsica, diu l'estat i mostra les comandes.
def comanda_info(update, context):
    global hora

    fitxer = open("../sortida/avui.txt", "r")
    for linia in fitxer: #linia quedarà la darrera entrada del fitxer
        pass
    fitxer.close()
    linia=linia.replace(" ","")
    linia=linia.replace("\n","")
    valors = dict(x.split("=") for x in linia.split("|"))

    message= "*Estat actual:*  "

    #Comprovem que l'hora estigui sincronitzada (que tot vagi bé)
    hora=valors["Hora"]
    horaa=int(hora[0:2])*60+int(hora[3:5])
    horab=int(time.strftime("%H:%M")[0:2])*60+int(time.strftime("%H:%M")[3:5])
    if abs(horaa-horab)>3:
        message=message+"("+hora+")  \U000026A0 \n" #warning emoji

    message=message+"``` \n"
    message=message+"\nGrid/Solar: "+str(valors["Grid"]+ "/"+valors["Solar"]).rjust(13) +icona_grid_solar(valors["Grid"],valors["Solar"])
    message=message+"\nTermo1: "+valors["Termo1"].rjust(17)+icona_termo(valors["Niv"].split("_")[1],valors["Termo1"])
    message=message+"\nNivell: "+valors["Niv"].split("_")[1].rjust(17) +icona_nivell(valors["Niv"].split("_")[0],valors["Niv"].split("_")[1])
    message=message+"\nServo1: "+(valors["Servo1"].split("_")[0]).rjust(17)
    if (valors["Servo1"].split("_")[1] == "F"):
        message=message+" Forc."
    message=message+"\nPiscina: "+ (valors["Pisc"].split("_")[1]).rjust(9) + (valors["Pisc"].split("_")[0]).rjust(7)
    if (valors["Pisc"].split("_")[2] == "F"):
        message=message+" Forc."
    message=message+"\nSal: "+ (valors["Sal"].split("_")[1]).rjust(13) + (valors["Sal"].split("_")[0]).rjust(7)
    if (valors["Sal"].split("_")[2] == "F"):
        message=message+" Forc."
    message=message+"\nLlums: "+valors["Llums"].rjust(18)+ icona_llums(valors["Llums"])
    message=message+"\n ```"

    # Ara la part Sunrise/sunset

    hora=time.strftime("%H:%M")

    message=message+"\n*Sortida/Posta de sol efectiva*\n ``` \n       >0W  >500W <500W  <0W "

    #u10d  últims 10 dies
    fitxer = open("../sortida/u10dss.tmp", "r") #té 1 sola línia
    linia=fitxer.readline()
    fitxer.close()

    linia=linia.replace(" ","")
    linia=linia.replace("\n","")
    valors = dict(x.split("=") for x in linia.split("|"))

    message=message+"\nu10d: "
    message=message+valors["u10dsunrise"]
    message=message+" "+valors["u10defsunrise"]
    message=message+" "+valors["u10defsunset"]
    message=message+" "+valors["u10dsunset"]

    # Avui
    fitxer = open("../sortida/estat.tmp", "r") #té 1 sola línia
    linia=fitxer.readline()
    fitxer.close()

    linia=linia.replace(" ","")
    linia=linia.replace("\n","")
    valors2 = dict(x.split("=") for x in linia.split("|"))

    message=message+"\nAvui: "
    if valors2["Sunrise"]!="00:00":
        message=message+valors2["Sunrise"]
    if valors2["EffectiveSunrise"]!="00:00":
        message=message+" "+valors2["EffectiveSunrise"]
    if horaminuts_a_minuts(hora)>horaminuts_a_minuts(valors["u10defsunset"])-30:
        message=message+" "+valors2["EffectiveSunset"]
    if horaminuts_a_minuts(hora)>horaminuts_a_minuts(valors2["Sunset"])+2:
        message=message+" "+valors2["Sunset"]
    message=message+"```\n"

    #context.bot.send_message(chat_id=update.effective_chat.id, text=escapa_missatge(message), parse_mode="Markdownv2")

    printa_botonera(update,context,message)


# --------------------------- comencem --------------------------------------------

# Token privat del bot esta a "token.txt"
TOKEN = open('token.txt').read().strip()

# Coses necessaries del Telegram
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Llista de les possbiles comandes. Quan rep de l'usuari un "/algo"
# mira en la llista i executa la funcio corresponent si hi es
dispatcher.add_handler(CommandHandler('start', comanda_info))
dispatcher.add_handler(CommandHandler('info', comanda_info))
dispatcher.add_handler(CommandHandler('list', comanda_list))
dispatcher.add_handler(CommandHandler('totals', comanda_totals))
dispatcher.add_handler(CommandHandler('help', comanda_help))
dispatcher.add_handler(CommandHandler('botons', botons))
dispatcher.add_handler(CallbackQueryHandler(resposta_botons))

# Inicia el bot
updater.start_polling()
