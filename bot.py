import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import os, json

# === Configuración de logs ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === Google Sheets (credenciales desde Render) ===
google_creds = os.getenv("GOOGLE_CREDS_JSON")
if not google_creds:
    raise ValueError("❌ No se encontró la variable de entorno GOOGLE_CREDS_JSON")

creds_dict = json.loads(google_creds)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

try:
    sheet = client.open("CRM WolfTech Servicios").sheet1
except Exception as e:
    raise RuntimeError(f"❌ Error al abrir la hoja de cálculo: {e}")

# === Estados de la conversación ===
TELEFONO, CONTACTO, NOMBRE_EMPRESA, SERVICIO, FORMA_CONTACTO, FECHA_CONTACTO, CONFIRMAR = range(7)

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola, soy NOVA de WolfTech.\n"
        "Te ayudaré a registrar tus datos. Empecemos.\n\n"
        "📱 ¿Cuál es tu *número de teléfono*?"
    )
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
    await update.message.reply_text(
        "¿Qué servicio te interesa?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SERVICIO

async def servicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["servicio"] = update.message.text

    mensajes_servicio = {
        "Cámaras": "🔒 Perfecto, nuestras cámaras protegen tu espacio con tecnología moderna.",
        "Redes": "🌐 Genial, diseñamos redes estables y rápidas, cero dolores de cabeza.",
        "Energía": "⚡ Excelente, nuestros sistemas de respaldo garantizan continuidad.",
        "Aires": "❄️ Muy bien, venta, instalación y mantenimiento de aires con garantía."
    }
    mensaje_extra = mensajes_servicio.get(context.user_data["servicio"], "")

    await update.message.reply_text(
        f"{mensaje_extra}\n\n¿Cómo prefieres que te contactemos? (WhatsApp, llamada, email)"
    )
    return FORMA_CONTACTO

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
🏢 Empresa: {context.user_data['nombre_empresa']}
🔧 Servicio: {context.user_data['servicio']}
📨 Contacto: {context.user_data['forma_contacto']}
📅 Día: {context.user_data['fecha_contacto']}
¿Es correcto? (sí / no)
"""
    await update.message.reply_text(datos)
    return CONFIRMAR

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() in ["si", "sí", "correcto"]:
        try:
            sheet.append_row([
                context.user_data["telefono"],
                context.user_data["contacto"],
                context.user_data["nombre_empresa"],
                context.user_data["servicio"],
                context.user_data["forma_contacto"],
                context.user_data["fecha_contacto"],
            ])
            await update.message.reply_text("✅ Tus datos fueron guardados. ¡Gracias por confiar en WolfTech!")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Hubo un error al guardar en Google Sheets: {e}")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Registro cancelado. Puedes reiniciar con /start")
        return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Proceso cancelado. Usa /start para comenzar de nuevo.")
    return ConversationHandler.END

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("❌ No se encontró la variable de entorno TELEGRAM_TOKEN")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, telefono)],
            CONTACTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, contacto)],
            NOMBRE_EMPRESA: [MessageHandler(filters.TEXT & ~filters.COMMAND, nombre_empresa)],
            SERVICIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, servicio)],
            FORMA_CONTACTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, forma_contacto)],
            FECHA_CONTACTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, fecha_contacto)],
            CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
