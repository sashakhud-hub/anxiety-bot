import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class AnxietyBot:
    def __init__(self):
        """Инициализация бота"""
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        init_db()  # Создаем базу данных
        
    def setup_handlers(self):
        """Настройка обработчиков команд и кнопок"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.username} запустил бота")
        
        # Создаем кнопки для начала
        keyboard = [
            [InlineKeyboardButton("🚀 Узнать свой тип", callback_data="start_test")],
            [InlineKeyboardButton("❓ Что это такое?", callback_data="what_is_it")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "start_test":
            await self.start_test(query, context)
        elif data == "what_is_it":
            await self.show_explanation(query)
        elif data == "begin_test":
            await self.show_question(query, context, 1)
        elif data.startswith("answer_"):
            await self.handle_answer(query, context, data)
        elif data == "retake_test":
            await self.start_test(query, context)
        elif data == "share_result":
            await self.share_result(query)
        elif data == "get_techniques":
            await self.check_subscription(query, context)
        elif data == "check_subscription":
            await self.check_subscription(query, context)
    
    async def start_test(self, query, context):
        """Начало теста"""
        user_id = query.from_user.id
        # Сброс предыдущих результатов
        context.user_data.clear()
        context.user_data['answers'] = {}
        context.user_data['current_question'] = 1
        
        await self.show_question(query, context, 1)
    
    async def show_explanation(self, query):
        """Показ объяснения что такое тревожные типы"""
        keyboard = [[InlineKeyboardButton("Понятно, погнали!", callback_data="begin_test")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            EXPLANATION_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_question(self, query, context, question_num):
        """Показ вопроса теста"""
        if question_num > len(QUESTIONS):
            await self.calculate_result(query, context)
            return
        
        question_data = QUESTIONS[question_num - 1]
        
        # Создаем кнопки с вариантами ответов
        keyboard = []
        for i, option in enumerate(question_data['options']):
            callback_data = f"answer_{question_num}_{chr(65+i)}"  # A, B, C, D
            keyboard.append([InlineKeyboardButton(option, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        question_text = f"**Вопрос {question_num} из {len(QUESTIONS)}**\n\n{question_data['text']}\n\n**Твоя реакция:**"
        
        await query.edit_message_text(
            question_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_answer(self, query, context, callback_data):
        """Обработка ответа на вопрос"""
        # Парсим данные: answer_1_A
        parts = callback_data.split('_')
        question_num = int(parts[1])
        answer = parts[2]
        
        user_id = query.from_user.id
        
        # Сохраняем ответ
        context.user_data['answers'][question_num] = answer
        save_user_answer(user_id, question_num, answer)
        
        # Переходим к следующему вопросу
        next_question = question_num + 1
        await self.show_question(query, context, next_question)
    
    async def calculate_result(self, query, context):
        """Подсчет результатов и определение типа"""
        answers = context.user_data.get('answers', {})
        user_id = query.from_user.id
        
        # Подсчитываем количество каждого типа ответов
        count_a = sum(1 for answer in answers.values() if answer == 'A')
        count_b = sum(1 for answer in answers.values() if answer == 'B')
        count_c = sum(1 for answer in answers.values() if answer == 'C')
        count_d = sum(1 for answer in answers.values() if answer == 'D')
        
        # Определяем тип
        max_count = max(count_a, count_b, count_c, count_d)
        
        if count_a == max_count and count_a >= 4:
            result_type = "calm"
        elif count_b == max_count:
            result_type = "catastrophizer"
        elif count_c == max_count:
            result_type = "mind_reader"
        elif count_d == max_count:
            result_type = "perfectionist"
        else:
            result_type = "mixed"
        
        # Сохраняем результат в базу
        save_user_result(user_id, result_type, answers)
        
        await self.show_result(query, result_type)
    
    async def show_result(self, query, result_type):
        """Показ результата теста"""
        result_text = RESULTS[result_type]
        
        # Создаем кнопки
        keyboard = [
            [InlineKeyboardButton("📱 Поделиться с подругой", callback_data="share_result")],
            [InlineKeyboardButton("🔄 Пройти еще раз", callback_data="retake_test")],
            [InlineKeyboardButton("✅ Узнать секрет мыслечтения", callback_data="get_techniques")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def share_result(self, query):
        """Поделиться результатом"""
        share_text = "🔮 Я узнала свой тревожный тип! А ты знаешь какая ты тревожица?\n\nПройди тест: t.me/your_bot_username"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Пройти еще раз", callback_data="retake_test")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"**Отправь это сообщение подруге:**\n\n{share_text}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def check_subscription(self, query, context):
        """Проверка подписки на канал"""
        user_id = query.from_user.id
        
        try:
            # Проверяем подписку на канал
            chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
            
            if chat_member.status in ['member', 'administrator', 'creator']:
                # Пользователь подписан - отправляем техники
                await self.send_techniques(query)
            else:
                # Не подписан - показываем напоминание
                await self.show_subscription_reminder(query)
                
        except Exception as e:
            # Ошибка при проверке - показываем напоминание
            logger.error(f"Ошибка проверки подписки: {e}")
            await self.show_subscription_reminder(query)
    
    async def send_techniques(self, query):
        """Отправка техник подписчику"""
        keyboard = [
            [InlineKeyboardButton("💾 Сохранить технику", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("📤 Поделиться с подругой", callback_data="share_result")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            TECHNIQUES_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_subscription_reminder(self, query):
        """Показ напоминания о подписке"""
        keyboard = [
            [InlineKeyboardButton("👆 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("🔄 Я подписалась", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            SUBSCRIPTION_REMINDER,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    def run(self):
        """Запуск бота"""
        logger.info("Бот запущен!")
        self.app.run_polling()

if __name__ == '__main__':
    bot = AnxietyBot()
    bot.run()
