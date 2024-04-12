# -*- coding: UTF-8 -*-
""" Coded with <3 by @PonchoIMa

Copyright © 2024 Alfonso Izaguirre

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

- Reference and credit to original authors of this software.

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# TODO - 
"""
    - /start will result in registration and automatic lookup for prayer pair.
        - if not found, notify and suggest reccommend bot to local church / community.
        - if found, pair and create group (?).
    - group logic:
        - every X days, if there are no updates, send a message asking for updates.
        - after X days, close the connection and notify the users.
    - /pray will ask for a public prayer request that everyone can see and pray for.
        - /prayers will plot the last 10 most unpopular prayer requests so that you can pray for them.
        - Prayers have to be 140 characters long.
        - It _can_ include ID.
    - General announcements
        - should give the opportunity to order new materials, register for coming events and so on. 
"""

import logging, threading, time, re
from datetime import date
from handler import BotParser as bp
from sqlite3 import IntegrityError
from typing import Final
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatInviteLink, Update, error
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.error import BadRequest, Forbidden

# DAY_OPORTUNITY_CHOSEN = 0
ADMINSTRATORS:  Final = '' # HIDDEN FOR SECURITY REASONS
TOKEN:          Final = open('key.txt').read().strip()
BOT_USERNAME:   Final = '@TheTheologianBot'
DATABASE:       Final = 'metanoia.db'
HANDLER:        Final = bp(DATABASE)
CLIENT = Application.chat_data
MAIN_LOOP, CHOOSING_MENU, CHOOSING_GENDER, GROUP_REGISTER, USER_PICKED, PRAYING, = range(6)
OPER_KEYBOARD:  Final = [["CONTACT", "ORDER MATERIAL"], ["CONFERENCE", "REGISTRATION"]]
REGI_KEYBOARD:  Final = [["REGISTER", "CANCEL"]]
GEND_KEYBOARD:  Final = [["MALE", "FEMALE"]]

# LOGGING
logging.basicConfig(format="MAIN APP - %(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx")
logger = logging.getLogger(__name__)

def commit_the_database():
    while True:
        logging.info("Updating values…")
        try:
            pass
            # TODO - COMMIT THE DATABASE?
        except Exception as e:
            pass

def subroutine():
    # EVERYDAY CHECK DATE_CHAT_UPDATED
    # TODO - GET TODAY /
    #               COMPARE TODAY WITH CONNECTIONS.DATE_UPDATED / 
    #               IF MORE THAN 7 DAYS, SEND MESSAGE_ONE /
    #               IF MORE THAN 14 DAYS, SEND MESSAGE_TOW /
    #               IF MORE THAN 30 DAYS, CLOSE AND UPDATE STATUS
    # TODO - Broadcast Group messages
    # TODO - Store / Purchase products (every day update file with links and stuff)
    # INACTIVE ALL USERS
    logging.info("Running dates to see activity today!")
    #for row_fetched in HANDLER.return_users():
    #    HANDLER.update_user_activeness_today(row_fetched[0])
    logging.info("Succesfully resetted dates")
    today = date.today().strftime('%Y-%m-%d')
    time.sleep(86400)
    pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id       = update.effective_user.id
    chat_id       = update.effective_chat.id
    if(user_id != chat_id):
        await update.message.reply_text("(Welcome group message) Invite/Cancel")
        return GROUP_REGISTER
    else:
        await update.message.reply_text("(Welcome message) TODO",
                                        reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD,
                                                                           input_field_placeholder = "CHOOSE AN OPTION",
                                                                           resize_keyboard = True))
    return CHOOSING_MENU

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Send us an email to info@metanoia\-movement\.org\n\n[Send it now\!](info@metanoia-movement.org)",
                                    reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD, input_field_placeholder = "CHOOSE AN OPTION", resize_keyboard = True), disable_web_page_preview = False, parse_mode = "MarkdownV2")
    return CHOOSING_MENU

async def order_material(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("You can order\n\n\- Bibel Journal\n\- Themenheft\n\- Geben\n\- Gehen\n\- Beten\n\nYou can order them by [writing to us](info@metanoia-movement.org)\.",
                                    reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD, input_field_placeholder = "CHOOSE AN OPTION", resize_keyboard = True), disable_web_page_preview = False, parse_mode = "MarkdownV2")
    return CHOOSING_MENU

async def conference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("This is text of our conference\n\n[This is a link to our website](http://www.metanoia-movement.org)\n\n📍 «This is the place» [This is a link to a maps place](https://maps.app.goo.gl/hFNL1f8yySwLK1116)",
                                    reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD, input_field_placeholder = "CHOOSE AN OPTION", resize_keyboard = True), disable_web_page_preview = False, parse_mode = "MarkdownV2")
    return CHOOSING_MENU

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id       = update.effective_user.id
    user_username = update.effective_user.username
    attempt       = None
    chat_id       = update.effective_chat.id
    logging.info(f"Verifying: {user_username}")
    if(not HANDLER.is_user(user_id)):
        await update.message.reply_text(f"(Hello Message) Hey {update.effective_user.first_name}! Registering into the database…")
        logging.info(f"Not found: {user_username}. Beginning registration…")
        await update.message.reply_text("Choose your sex:",
                                        reply_markup = ReplyKeyboardMarkup(GEND_KEYBOARD, input_field_placeholder = "CHOOSE AN OPTION", resize_keyboard = True))
        return CHOOSING_GENDER
    elif(HANDLER.is_free(user_id)):
        await update.message.reply_text(f"(Hello Message) Hey {update.effective_user.first_name}! You're already registered! Let's find someone for you to pray and connect!")
        pairs = HANDLER.find_pair_for(user_id)
        pairs = "\n".join([row[1] for row in pairs])
        if(user_id != chat_id):
            if(pairs != 0):
                await update.effective_chat.send_message("Please respond with @username you want to invite, \"RANDOM\" to pick a random user or \"CANCEL\" to cancel the invitation.\n\n" + str(pairs))
                return USER_PICKED
            else:
                await update.effective_chat.send_message('(Odd user) Looks like there are no available users to pair you with, but that means you have the opportunity of sharing this bot with your local church or group. Whenever someone else joins, I will make sure to pair them with you! Blessings :)')
        else:
            await update.effective_chat.send_message("It looks like we're on a personal chat, please add me to a group and trigger /start one more time there")
    else:
        await update.effective_chat.send_message('(Odd user) Looks like we are in a group conversation already… (#TODO - Get the other user to reply? confirm activity or report? maybe user misclicked?)')
        # TODO - List connection and users there.
    return MAIN_LOOP

async def gender_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE, sex: int) -> int: 
    user_id       = update.effective_user.id
    user_username = update.effective_user.username
    logging.info(f"Registering: {user_username}")
    HANDLER.insert_user(user_id, user_username, sex)
    await update.effective_chat.send_message('Succesfully registered! Going back to main menu!')
    await start(update, context)
    return CHOOSING_MENU

async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text
    logging.info(f"Connect triggered for {update.effective_user.id}!")
    try:
        link: ChatInviteLink = await update.effective_chat.create_invite_link()
        if(message.lower() == "random"): # TODO - Change methods to implement a decision based connection
            logging.info(f"User {update.effective_user.id} chose 'random'!")
            await update.effective_chat.send_message("(User found) I've found a pair for you!")
            attempt = HANDLER.insert_connection(user_id, chat_id)
            if(attempt is not None):
                link: ChatInviteLink = await update.effective_chat.create_invite_link()
                await update.effective_chat.send_message(link.invite_link)
                await context.bot.send_message(chat_id = attempt[2], text = f"You've been invited to join @ {link.invite_link}")
                await update.effective_chat.send_message("(Invitation sent) I've sent an invitation for someone to join this group, let's see if they join! :)")
            return MAIN_LOOP
        else:
            logging.info(f"User {update.effective_user.id} chose user {message}!")
            await update.effective_chat.send_message("Non random triggered!")
            HANDLER.return_user_id_from_username(message)
            await update.effective_chat.send_message(link.invite_link)
    except IndexError as e:
        await update.effective_chat.send_message(f"(User mistyped error) It appears that '{message}' is not a username in my database, can you try again (or cancel)?")
        return USER_PICKED
    except BadRequest as e:
        await update.effective_chat.send_message("(Not administrator) Looks like I'm not an administrator of this group, please make me an administrator to continue!")
        return MAIN_LOOP
    return MAIN_LOOP

async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_chat.send_message("#TODO - This function is still in development, come back soon! ;)")
    return MAIN_LOOP

async def update_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if(chat_id != user_id):
        logging.info("Method update_chat() triggered!")
        try:
            logging.info(f"Attempting updating activeness for {user_id}")
            HANDLER.update_user_activeness_today(user_id, chat_id)
            logging.debug("Activenness today updated")
            updated = HANDLER.update_connections_status(chat_id)
            if(updated):
                await update.effective_chat.send_message(f"All connections updated for {chat_id}")
                logging.debug("All connections updated")
        except Exception as e:
            logging.error(e.with_traceback)
            raise
    else:
        logging.info("Method update_chat() triggered on personal chat… Ignoring…")
    return MAIN_LOOP

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error:\n\n{context.error}\n\n{context.error.with_traceback}')
    await context.bot.send_message(chat_id = '1523978922', text = f'Update {update} caused error:\n\n{context.error}\n\n{context.error.with_traceback}')

def main() -> None:
    # updater = Updater(TOKEN, connection_pool_size = 100)
    convStart = ConversationHandler(
        entry_points = [CommandHandler("start", start), CommandHandler("pray", pray)],
        states = {
            MAIN_LOOP: [
                MessageHandler(None, update_chat),
            ],
            CHOOSING_MENU: [
                MessageHandler(filters.Regex("CONTACT"),        contact),
                MessageHandler(filters.Regex("ORDER MATERIAL"), order_material),
                MessageHandler(filters.Regex("CONFERENCE"),     conference),
                MessageHandler(filters.Regex("REGISTRATION"),   register),
            ],
            CHOOSING_GENDER: [
                MessageHandler(filters.Regex("M"),   lambda update, context: gender_chosen(update, context, 0)),
                MessageHandler(filters.Regex("F"),   lambda update, context: gender_chosen(update, context, 1)),
            ],
            GROUP_REGISTER: [
                MessageHandler(filters.Regex(re.compile("INVITE", re.IGNORECASE)), register),
                MessageHandler(filters.Regex("CANCEL"),                            start),   # TODO - What to do?
            ],
            USER_PICKED: [
                MessageHandler(filters.Regex(re.compile("CANCEL", re.IGNORECASE)), start),
                MessageHandler(filters.Regex(re.compile("RANDOM", re.IGNORECASE)), connect),
                MessageHandler(None,                                               connect),
            ],
            PRAYING: [],
        },
        fallbacks = [CommandHandler("stop", error)],
        allow_reentry = True
    )
    application = Application.builder().token(TOKEN).concurrent_updates(True).pool_timeout(350).connection_pool_size(700).build()
    application.add_handler(convStart)
    application.add_error_handler(error)
    # application.run_polling(allowed_updates = Update.ALL_TYPES, poll_interval = 0.1, pool_timeout = 10)
    application.run_polling(allowed_updates = Update.ALL_TYPES, poll_interval = 0.1)
    # updater.start_polling(poll_interval = 0.2)

if __name__ == "__main__":
    logging.info("Starting background thread…")
    x = threading.Thread(target = subroutine, daemon = True)
    x.start()
    logging.info("Firing up bot…")
    main()
