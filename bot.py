import time
from telegram import *
from telegram.ext import *
#from imgurpython import ImgurClient
import pyimgur
import sqlite3
import os

#id censurato per privacy
IMGUR_ID = "xxxxxxxxxxx"

im = pyimgur.Imgur(IMGUR_ID)


conn = sqlite3.connect('db/database.db', check_same_thread=False)
cursor = conn.cursor()

def updateStudente(id: int):
	cursor.execute('INSERT INTO studenti (id, status, count) VALUES (?, ?, ?)', (id, 0, 0))
	conn.commit()

def updateIdDocente(id: int):
	cursor.execute('INSERT INTO docenti (id, status) VALUES (?, ?)', (id,0))
	conn.commit()

#telegram bot token censurato per privacy
updater = Updater(token="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
dispatcher = updater.dispatcher

print("[BOT STARTED]")

def start(update: Update, context: CallbackContext):
    print("[" + str(update.message.chat_id) + "] STARTED THE BOT")
    update.message.reply_text("Sei uno Studente o un Docente?")


#restituisce id
def consegne(update, context):
    print("[" + str(update.message.chat_id) + "] CONSEGNE")
    if len(cursor.execute("SELECT id FROM docenti WHERE id = ?",(update.message.chat_id,)).fetchall()) != 0: #se sono docente
        list = cursor.execute("SELECT id_studente, dataora FROM consegne").fetchall() #faccio lista di ID e date
        if len(list) == 0:
            update.message.reply_text("Nessuna consegna entro 24 ore dall'esecuzione del comando")
        else:
            update.message.reply_text("🔎 Di seguito gli ID degli studenti che hanno consegnato entro un giorno dall'esecuzione del comando."
                                      + "\n\n👀 Per vedere la consegna di uno studente, esegua il comando /leggi")  
            for item in list:
                if (time.time() - item[1] < 86400): #se la differenza è minore di 24h
                    #update.message.reply_text(" ".join(map(str, item)))
                    date = cursor.execute("SELECT dataora FROM consegne WHERE id_studente = ?", (item[0],)).fetchone()[0]
                    update.message.reply_text("*" + str(item[0]) + "*" 
                                            + "\n⏰ Mandato alle " + time.strftime("%H:%M:%S", time.localtime(date))
                                            + " del " + time.strftime("%d/%m/%Y", time.localtime(date)), parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text("Non puoi fare questa operazione")

#legge consegne tramite id
def leggi(update, context):
    print("[" + str(update.message.chat_id) + "] LEGGI")

    if len(cursor.execute("SELECT id FROM docenti WHERE id = ?",(update.message.chat_id,)).fetchall()) != 0:
        cursor.execute("UPDATE docenti SET status = 1 WHERE id = ?",(update.message.chat_id,))
        conn.commit()
        update.message.reply_text("🤨 Inserisci l'ID dello studente di cui leggere la consegna:")
    else:
        update.message.reply_text("Non puoi fare questa operazione")

def listaDocenti(update, context):
    print("[" + str(update.message.chat_id) + "] LISTA DOCENTI")

    if len(cursor.execute("SELECT id FROM studenti WHERE id = ?",(update.message.chat_id,)).fetchall()) != 0:
        list = cursor.execute("SELECT id FROM docenti").fetchall()
        if len(list) == 0:
            update.message.reply_text("Nessun docente registrato")
        else:
            for i in list:
                update.message.reply_text(" ".join(map(str, i)))
    else:
        update.message.reply_text("Non puoi fare questa operazione")

def consegna(update, context):
    print("[" + str(update.message.chat_id) + "] CONSEGNA")

    if len(cursor.execute("SELECT id FROM studenti WHERE id = ?",(update.message.chat_id,)).fetchall()) != 0:
        update.message.reply_text("📎 Invia le foto della consegna ✋*individualmente*\n👍 Una volta finito scrivi \"fatto\".", parse_mode=ParseMode.MARKDOWN)
        cursor.execute('UPDATE studenti SET status = 1 WHERE id = (?)', (update.message.chat_id,))
        cursor.execute('UPDATE studenti SET count = 0 WHERE id = (?)', (update.message.chat_id,))
        album = im.create_album(title=("Consegne di "+str(update.message.chat_id)))
        cursor.execute('INSERT INTO consegne (id_studente, album_link, album_hash) VALUES (?,?,?)', (update.message.chat_id, album.link, album.deletehash))
        #cursor.execute('UPDATE studenti SET album_link = (?) WHERE id = (?)', (album.link ,update.message.chat_id))
        #cursor.execute('UPDATE studenti SET album_hash = (?) WHERE id = (?)', (album.deletehash ,update.message.chat_id))
        conn.commit()

    else:
        update.message.reply_text("Non puoi fare questa operazione")

def messageHandler(update, context):
    print("[" + str(update.message.chat_id) + "] MESSAGE: \"" + update.message.text + "\"")
    if update.message.text.lower() == "studente":
        cursor.execute('DELETE FROM docenti WHERE id = (?)', (update.message.chat_id,)) #elimino l'id dai docenti
        updateStudente(update.message.chat_id)
        update.message.reply_text("Sei stato registrato come Studente")
        update.message.reply_text("I tuoi comandi disponibili sono: \n📖 /listadocenti - per vedere tutti i docenti \n📨 /consegna - per consegnare un compito")
    if update.message.text.lower() == "docente":
        cursor.execute('DELETE FROM studenti WHERE id = (?)', (update.message.chat_id,)) #elimino l'id dagli studenti
        updateIdDocente(update.message.chat_id)
        update.message.reply_text("Sei stato registrato come Docente")
        update.message.reply_text("I tuoi comandi disponibili sono: \n✉️ /consegne - per vedere tutti gli studenti che hanno consegnato \n🔎 /leggi - per vedere la consegna di qualche studente")
    if update.message.text.lower() == "fatto" and cursor.execute("SELECT status FROM studenti WHERE id = ?",(update.message.chat_id,)).fetchone()[0] == 1 and len(cursor.execute("SELECT id_studente FROM consegne WHERE id_studente = ?",(update.message.chat_id,)).fetchone()) != 0:
        cursor.execute('UPDATE consegne SET dataora = ? WHERE id_studente = ?', (time.time(), update.message.chat_id))
        cursor.execute('UPDATE studenti SET status = 0 WHERE id = (?)', (update.message.chat_id,))
        conn.commit()
        update.message.reply_text("🎉 Questo è il tuo album: " + cursor.execute('SELECT album_link FROM consegne WHERE id_studente = (?)', (update.message.chat_id,)).fetchone()[0])
    if  len(cursor.execute("SELECT id FROM docenti WHERE id = ?",(update.message.chat_id,)).fetchall()) != 0:  #se sono docente
        if cursor.execute("SELECT status FROM docenti WHERE id = ?",(update.message.chat_id,)).fetchone()[0] == 1: #se sono nello stato 1
            if cursor.execute("SELECT album_link FROM consegne WHERE id_studente = ?",(update.message.text,)).fetchone() != None and len(cursor.execute("SELECT album_link FROM consegne WHERE id_studente = ?",(update.message.text,)).fetchone()) != 0: #se lo studente ha un album
                date=cursor.execute("SELECT dataora FROM consegne WHERE id_studente = ?", (update.message.chat_id,)).fetchone()[0]
                update.message.reply_text("Album di " + str(update.message.text) + ": " 
                                          + cursor.execute("SELECT album_link FROM consegne WHERE id_studente = ?",(update.message.text,)).fetchone()[0]
                                          + "\nMandato alle " + time.strftime("%H:%M:%S", time.localtime(date))
                                          + " del " + time.strftime("%d/%m/%Y", time.localtime(date)))
                cursor.execute('UPDATE docenti SET status = 0 WHERE id = (?)', (update.message.chat_id,))
                conn.commit()
            else:
                update.message.reply_text("L'utente " + update.message.text + " non ha album caricati.")

def photoHandler(update, context):
    bot = context.bot
    if len(cursor.execute("SELECT id FROM studenti WHERE id = ?",(update.message.chat_id,)).fetchall()) != 0 and cursor.execute("SELECT status FROM studenti WHERE id = ?",(update.message.chat_id,)).fetchone()[0] == 1:
        file_id = update.message.photo[-1].file_id
        newFile = bot.getFile(file_id)

        count = cursor.execute("SELECT count FROM studenti WHERE id = ?",(update.message.chat_id,)).fetchone()[0]
        path = 'temp/'+ str(update.message.chat_id) + '-' + str(count) + '.png'
        hash = cursor.execute("SELECT album_hash FROM consegne WHERE id_studente = ?",(update.message.chat_id,)).fetchone()[0]
        newFile.download(path)
        im.upload_image(path, title=("Immagine n" + str(count+1)), album=hash)
        update.message.reply_text("✅ Upload " + str(count+1) + " completato")
        cursor.execute('UPDATE studenti SET count = count + 1 WHERE id = (?)', (update.message.chat_id,))
        conn.commit()
        os.remove(path)
    else:
        update.message.reply_text("Non puoi fare questa operazione")

dispatcher.add_handler(CommandHandler("start", start))

#COMANDI DOCENTE
dispatcher.add_handler(CommandHandler("CONSEGNE", consegne))
dispatcher.add_handler(CommandHandler("LEGGI", leggi))
#COMANDI STUDENTE
dispatcher.add_handler(CommandHandler("LISTADOCENTI", listaDocenti))
dispatcher.add_handler(CommandHandler("CONSEGNA", consegna))

dispatcher.add_handler(MessageHandler(Filters.text, messageHandler))
dispatcher.add_handler(MessageHandler(Filters.photo, photoHandler))
updater.start_polling()
