from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler
)

from dotenv import load_dotenv

from database import (
    init_db,
    save_application,
    get_applications,
    update_status
)

from excel import export_to_excel

import re
import os
from datetime import datetime


# =========================
# НАСТРОЙКИ
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 997497221

NAME, PHONE, SERVICE, DESCRIPTION = range(4)


# =========================
# КЛАВИАТУРА УСЛУГ
# =========================

keyboard = [
    ["📄 Создание КП"],
    ["🤖 ИИ-автоматизация"],
    ["📊 CRM"],
    ["💬 Другое"]
]

reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True
)


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        "Добро пожаловать! 👋\n\n"
        "Выберите услугу, которая вас интересует:",
        reply_markup=reply_markup
    )

    return SERVICE


# =========================
# УСЛУГА
# =========================

async def get_service(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["service"] = update.message.text.strip()

    await update.message.reply_text(
        "Отлично! 👌\n\n"
        "Как вас зовут?",
        reply_markup=ReplyKeyboardRemove()
    )

    return NAME


# =========================
# ИМЯ
# =========================

async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["name"] = update.message.text.strip()

    await update.message.reply_text(
        "Спасибо! Теперь введите ваш номер телефона."
    )

    return PHONE


# =========================
# ТЕЛЕФОН
# =========================

async def get_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    phone = update.message.text.strip()

    if not re.fullmatch(r"\+?\d{10,15}", phone):

        await update.message.reply_text(
            "❌ Неверный номер телефона.\n\n"
            "Введите номер в формате:\n"
            "+77771234567"
        )

        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text(
        "Отлично! 👍\n\n"
        "Теперь кратко опишите, что вам нужно.\n\n"
        "Например:\n"
        "«Хочу автоматизировать обработку заявок клиентов»"
    )

    return DESCRIPTION


# =========================
# ОПИСАНИЕ
# =========================

async def get_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["description"] = update.message.text.strip()

    confirm_keyboard = [
        [
            InlineKeyboardButton(
                "✅ Отправить",
                callback_data="confirm"
            ),
            InlineKeyboardButton(
                "✏️ Заполнить заново",
                callback_data="restart"
            )
        ]
    ]

    confirm_markup = InlineKeyboardMarkup(
        confirm_keyboard
    )

    await update.message.reply_text(
        "📋 <b>Проверьте данные заявки</b>\n\n"

        f"👤 <b>Имя:</b> "
        f"{context.user_data['name']}\n"

        f"📞 <b>Телефон:</b> "
        f"{context.user_data['phone']}\n"

        f"💼 <b>Услуга:</b> "
        f"{context.user_data['service']}\n"

        f"📝 <b>Задача:</b> "
        f"{context.user_data['description']}\n\n"

        "Всё верно?",

        parse_mode="HTML",
        reply_markup=confirm_markup
    )

    return DESCRIPTION


# =========================
# ПОДТВЕРЖДЕНИЕ
# =========================

async def confirm_application(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    # -------------------------
    # ЗАПОЛНИТЬ ЗАНОВО
    # -------------------------

    if query.data == "restart":

        context.user_data.clear()

        await query.message.edit_text(
            "Начнём заполнение заявки заново. 👌"
        )

        await query.message.reply_text(
            "Выберите услугу, которая вас интересует:",
            reply_markup=reply_markup
        )

        return SERVICE

    # -------------------------
    # ОТПРАВИТЬ
    # -------------------------

    if query.data == "confirm":

        date = datetime.now().strftime(
            "%d.%m.%Y %H:%M"
        )

        context.user_data["date"] = date

        save_application(
            date,
            context.user_data["name"],
            context.user_data["phone"],
            context.user_data["service"],
            context.user_data["description"]
        )

        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=(
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📥 <b>НОВАЯ ЗАЯВКА</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                f"👤 <b>Клиент:</b> "
                f"{context.user_data['name']}\n"

                f"📞 <b>Телефон:</b> "
                f"{context.user_data['phone']}\n"

                f"💼 <b>Услуга:</b> "
                f"{context.user_data['service']}\n"

                f"📝 <b>Задача:</b> "
                f"{context.user_data['description']}\n"

                f"🕒 <b>Дата:</b> "
                f"{date}\n"

                "━━━━━━━━━━━━━━━━━━━━━━"
            ),

            parse_mode="HTML"
        )

        await query.message.edit_text(
            "✅ <b>Заявка успешно отправлена!</b>\n\n"
            "Спасибо! Мы свяжемся с вами "
            "в ближайшее время.",
            parse_mode="HTML"
        )

        context.user_data.clear()

        return ConversationHandler.END


# =========================
# ОТМЕНА
# =========================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        "Заявка отменена.\n\n"
        "Если захотите начать заново, "
        "используйте команду /start."
    )

    return ConversationHandler.END


# =========================
# CHAT ID
# =========================

async def id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"Ваш Chat ID: {update.effective_chat.id}"
    )

async def filter_applications(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    applications = get_applications()

    status_map = {
        "filter_new": "Новая",
        "filter_work": "В работе",
        "filter_done": "Завершена",
        "filter_reject": "Отказ"
    }

    selected_status = status_map.get(query.data)

    filtered = [
        app for app in applications
        if app[6] == selected_status
    ]

    if not filtered:
        await query.message.edit_text(
            f"📭 Заявок со статусом «{selected_status}» нет."
        )
        return

    await query.message.edit_text(
        f"📋 <b>{selected_status.upper()}</b>\n\n"
        f"Найдено заявок: <b>{len(filtered)}</b>",
        parse_mode="HTML"
    )

    for app in filtered:

        application_id = app[0]

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 В работу",
                    callback_data=f"status_{application_id}_В работе"
                ),
                InlineKeyboardButton(
                    "✅ Завершить",
                    callback_data=f"status_{application_id}_Завершена"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Отказать",
                    callback_data=f"status_{application_id}_Отказ"
                )
            ]
        ]

        markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=ADMIN_ID,

            text=(
                f"📌 <b>Заявка №{app[0]}</b>\n\n"
                f"🕒 <b>Дата:</b> {app[1]}\n"
                f"👤 <b>Клиент:</b> {app[2]}\n"
                f"📞 <b>Телефон:</b> {app[3]}\n"
                f"💼 <b>Услуга:</b> {app[4]}\n"
                f"📝 <b>Задача:</b> {app[5]}\n"
                f"📊 <b>Статус:</b> {app[6]}"
            ),

            parse_mode="HTML",
            reply_markup=markup
        )

# =========================
# ПОКАЗ ЗАЯВОК
# =========================

async def show_applications(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ У вас нет доступа."
        )
        return

    applications = get_applications()

    if not applications:
        await update.message.reply_text(
            "📭 Заявок пока нет."
        )
        return

    new_count = sum(1 for app in applications if app[6] == "Новая")
    work_count = sum(1 for app in applications if app[6] == "В работе")
    done_count = sum(1 for app in applications if app[6] == "Завершена")
    reject_count = sum(1 for app in applications if app[6] == "Отказ")

    keyboard = [
        [
            InlineKeyboardButton(
                f"🆕 Новые ({new_count})",
                callback_data="filter_new"
            )
        ],
        [
            InlineKeyboardButton(
                f"🔄 В работе ({work_count})",
                callback_data="filter_work"
            )
        ],
        [
            InlineKeyboardButton(
                f"✅ Завершены ({done_count})",
                callback_data="filter_done"
            )
        ],
        [
            InlineKeyboardButton(
                f"❌ Отказы ({reject_count})",
                callback_data="filter_reject"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Экспорт в Excel",
                callback_data="admin_export"
            )
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📋 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"🆕 Новые: <b>{new_count}</b>\n"
        f"🔄 В работе: <b>{work_count}</b>\n"
        f"✅ Завершены: <b>{done_count}</b>\n"
        f"❌ Отказы: <b>{reject_count}</b>\n\n"
        "Выберите раздел:",
        parse_mode="HTML",
        reply_markup=markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ <b>Помощь</b>\n\n"
        "/start — создать заявку\n"
        "/applications — посмотреть заявки\n"
        "/export — выгрузить заявки в Excel\n"
        "/cancel — отменить заполнение",
        parse_mode="HTML"
    )


async def error_handler(update, context):
    print(f"Ошибка: {context.error}")

    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Произошла техническая ошибка. Попробуйте ещё раз."
            )
        except Exception:
            pass

# =========================
# ИЗМЕНЕНИЕ СТАТУСА
# =========================

async def change_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ Нет доступа.",
            show_alert=True
        )

        return

    await query.answer()

    parts = query.data.split(
        "_",
        2
    )

    application_id = int(parts[1])

    new_status = parts[2]

    update_status(
        application_id,
        new_status
    )

    applications = get_applications()

    application = None

    for item in applications:

        if item[0] == application_id:

            application = item

            break

    if application is None:

        await query.message.edit_text(
            "❌ Заявка не найдена."
        )

        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 В работе",
                callback_data=(
                    f"status_{application_id}_В работе"
                )
            ),

            InlineKeyboardButton(
                "✅ Завершена",
                callback_data=(
                    f"status_{application_id}_Завершена"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "❌ Отказ",
                callback_data=(
                    f"status_{application_id}_Отказ"
                )
            )
        ]
    ]

    markup = InlineKeyboardMarkup(
        keyboard
    )

    await query.edit_message_text(

        f"📌 <b>Заявка №{application[0]}</b>\n\n"

        f"🕒 <b>Дата:</b> {application[1]}\n"

        f"👤 <b>Клиент:</b> {application[2]}\n"

        f"📞 <b>Телефон:</b> {application[3]}\n"

        f"💼 <b>Услуга:</b> {application[4]}\n"

        f"📝 <b>Задача:</b> {application[5]}\n"

        f"📊 <b>Статус:</b> {application[6]}",

        parse_mode="HTML",

        reply_markup=markup
    )


# =========================
# EXPORT В EXCEL
# =========================

async def export(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_chat.id != ADMIN_ID:

        await update.message.reply_text(
            "⛔ У вас нет доступа."
        )

        return

    applications = get_applications()

    if not applications:

        await update.message.reply_text(
            "📭 Заявок пока нет."
        )

        return

    file_name = export_to_excel(
        applications
    )

    await update.message.reply_document(
        document=file_name,
        caption="📊 Все заявки"
    )


# =========================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ
# =========================

init_db()


# =========================
# СОЗДАНИЕ ПРИЛОЖЕНИЯ
# =========================

app = Application.builder().token(
    BOT_TOKEN
).build()


# =========================
# CONVERSATION
# =========================

entry_points = [
    CommandHandler(
        "start",
        start
    )
]


states = {

    SERVICE: [
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            get_service
        )
    ],

    NAME: [
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            get_name
        )
    ],

    PHONE: [
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            get_phone
        )
    ],

    DESCRIPTION: [

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            get_description
        ),

        CallbackQueryHandler(
            confirm_application,
            pattern=r"^(confirm|restart)$"
        )
    ]
}


fallbacks = [
    CommandHandler(
        "cancel",
        cancel
    )
]


conv_handler = ConversationHandler(

    entry_points=entry_points,

    states=states,

    fallbacks=fallbacks
)


app.add_handler(
    conv_handler
)


# =========================
# ADMIN COMMANDS
# =========================

app.add_handler(
    CommandHandler(
        "applications",
        show_applications
    )
)

app.add_handler(
    CallbackQueryHandler(
        filter_applications,
        pattern=r"^filter_(new|work|done|reject)$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        change_status,
        pattern=r"^status_\d+_.+$"
    )
)

app.add_handler(
    CommandHandler(
        "id",
        id
    )
)

app.add_handler(
    CommandHandler(
        "export",
        export
    )
)

app.add_error_handler(error_handler)


# =========================
# ЗАПУСК
# =========================

print("Бот запущен...")

app.add_handler(
    CommandHandler("help", help_command)
)

app.run_polling()