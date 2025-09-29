import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

# Credenciales desde variable de entorno
google_creds = os.getenv("GOOGLE_CREDS_JSON")
creds_dict = json.loads(google_creds)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import os, json
from oauth2client.service_account import ServiceAccountCredentials

google_creds = os.getenv("GOOGLE_CREDS_JSON")
creds_dict = json.loads(google_creds)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# === Configuración de logs ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# === Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("vivid-router-463420-q1-a3ced18081ce.json", scope)
client = gspread.authorize(creds)
sheet = client.open("CRM WolfTech Servicios").sheet1  # Cambia "WolfTech CRM" por el nombre exacto de tu sheet

# === Estados de la conversación ===
TELEFONO, CONTACTO, NOMBRE_EMPRESA, SERVICIO, FORMA_CONTACTO, CONFIRMAR = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola, soy NOVA de WolfTech.\nTe ayudaré a registrar tus datos. Empecemos.\n📱 ¿Cuál es tu *número de teléfono*?")
    return TELEFONO

async def telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefono"] = update.message.text
    await update.message.reply_text("¿Cómo te llamas o quién es el contacto principal?")
    return CONTACTO

async def contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contacto"] = update.message.text
    await update.message.reply_text("¿Cuál es el nombre de tu empresa (o tuyo personal)?")
    return NOMBRE_EMPRESA

async def nombre_empresa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre_empresa"] = update.message.text
    reply_keyboard = [["Cámaras", "Redes", "Energía", "Aires"]]
    await update.message.reply_text("¿Qué servicio te interesa?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SERVICIO

async def servicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["servicio"] = update.message.text

    # Mensajes cálidos según servicio
    mensajes_servicio = {
        "Cámaras": "🔒 Perfecto, las cámaras de seguridad de WolfTech protegen tu espacio con equipos modernos y garantía en la instalación.",
        "Redes": "🌐 Genial, nuestras redes están diseñadas para que trabajes sin caídas ni dolores de cabeza.",
        "Energía": "⚡ Excelente, los sistemas de respaldo garantizan que tu operación nunca se detenga.",
        "Aires": "❄️ Muy bien, contamos con venta, instalación y mantenimiento para mantener tu ambiente fresco y confiable."
    }

    mensaje_extra = mensajes_servicio.get(context.user_data["servicio"], "")
    await update.message.reply_text(f"{mensaje_extra}\n\n¿Cómo prefieres que te contactemos? (WhatsApp, llamada, email)")
    return FORMA_CONTACTO

    context.user_data["servicio"] = update.message.text
    await update.message.reply_text("¿Cómo prefieres que te contactemos? (WhatsApp, llamada, email)")
    return FORMA_CONTACTO

async def forma_contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["forma_contacto"] = update.message.text

    datos = f"""
📋 Por favor confirma:
📱 Teléfono: {context.user_data['telefono']}
👤 Contacto: {context.user_data['contacto']}
🏢 Nombre/Empresa: {context.user_data['nombre_empresa']}
🔧 Servicio: {context.user_data['servicio']}
📨 Forma de contacto: {context.user_data['forma_contacto']}
¿Es correcto? (sí / no)
"""
    await update.message.reply_text(datos)
    return CONFIRMAR

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() in ["si", "sí", "correcto"]:
        sheet.append_row([
            context.user_data["telefono"],
            context.user_data["contacto"],
            context.user_data["nombre_empresa"],
            context.user_data["servicio"],
            context.user_data["forma_contacto"],
        ])
        await update.message.reply_text("✅ Tus datos fueron guardados. ¡Gracias por confiar en WolfTech!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Registro cancelado. Puedes volver a empezar con /start")
        return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Proceso cancelado. Usa /start para comenzar de nuevo.")
    return ConversationHandler.END

async def forma_contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["forma_contacto"] = update.message.text
    await update.message.reply_text("📅 ¿Qué día te viene mejor para la visita o contacto?")
    return FECHA_CONTACTO

async def fecha_contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["fecha_contacto"] = update.message.text

    datos = f"""
📋 Por favor confirma:
📱 Teléfono: {context.user_data['telefono']}
👤 Contacto: {context.user_data['contacto']}
🏢 Nombre/Empresa: {context.user_data['nombre_empresa']}
🔧 Servicio: {context.user_data['servicio']}
📨 Forma de contacto: {context.user_data['forma_contacto']}
📅 Día de contacto: {context.user_data['fecha_contacto']}
¿Es correcto? (sí / no)
"""
    await update.message.reply_text(datos)
    return CONFIRMAR

def main():
    app = Application.builder().token("8391739062:AAHtIkZEXQZAHge7_E9mVjXbFV0z56es4QI").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, telefono)],
            CONTACTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, contacto)],
            NOMBRE_EMPRESA: [MessageHandler(filters.TEXT & ~filters.COMMAND, nombre_empresa)],
            SERVICIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, servicio)],
            FORMA_CONTACTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, forma_contacto)],
            CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
