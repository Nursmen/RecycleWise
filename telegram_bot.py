from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import requests
from huggingface_hub import InferenceClient
import dotenv


dotenv.load_dotenv()
API_KEY = os.getenv("API_KEY")


client = InferenceClient(api_key=API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! Send us a photo and we will tell where to put your trash!")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    f = update.message.photo[-1].file_id  
    file_info = await context.bot.get_file(f) 
    
    download_path = os.path.join("downloads", f"{f}.jpg") 
    os.makedirs(os.path.dirname(download_path), exist_ok=True)  
    await file_info.download_to_drive(download_path)  

    
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {"Authorization": "Bearer " + API_KEY}

    def query(filename):
        with open(filename, "rb") as f:
            data = f.read()
        response = requests.post(API_URL, headers=headers, data=data)
        return response.json()

    output = query(download_path)[0]['generated_text']
    print(output)

    messages = [
	{
		"role": "user",
		"content": f"I have three recycling bens: for plastic, grass, paper. In what bin do I put {output}? Asnwer with only one word"
    }
    ]

    completion = client.chat.completions.create(
        model="Qwen/Qwen2.5-Coder-32B-Instruct", 
        messages=messages, 
        max_tokens=500
    )

    result = completion.choices[0].message.content
    print(result)

    if "plastic" in result.lower():
        result = "Put it inside a green recycling bin for plastic"
    elif 'g' in result.lower():
        result = "Put it inside a blue recycling bin for glass"
    else:
        result = "Put it inside a red recycling bin for paper"

    await update.message.reply_text(f"{result}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Извините, я пока понимаю только изображения.")

# Main function
def main():
    application = ApplicationBuilder().token("8017734805:AAFn8oFHWIIXbBHBQUlqgqyl07lK3eCMZVY").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.ALL, unknown))

    application.run_polling()

if __name__ == "__main__":
    main()
