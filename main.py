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
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatInviteLink, Update, constants
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
MAIN_LOOP, CHOOSING_MENU, GROUP_REGISTER, PRAYING, = range(4)
OPER_KEYBOARD:  Final = [["CONTACT", "ORDER MATERIAL"], ["CONFERENCE",], ["PRAY FOR ME"]]

# LOGGING
logging.basicConfig(format="MAIN APP - %(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
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
        # Get the member count
        await update.effective_chat.send_action(constants.ChatAction.TYPING)
        members = await update.effective_chat.get_member_count() - 1
        
        # Register the chat
        try:
            await update.effective_chat.send_message("(Welcome message) Beginning registry… I need everyone to send me a message to register you!")
            HANDLER.insert_chat(chat_id, members)
            return GROUP_REGISTER
        except IntegrityError as i:
            await update.effective_chat.send_message("(Chat_already_registered) Looks like you triggered /start in a registered chat! Going back to read updates.")
            return MAIN_LOOP
    else:
        await update.message.reply_text("(Welcome message) TODO",
                                        reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD,
                                                                           input_field_placeholder = "CHOOSE AN OPTION",
                                                                           resize_keyboard = True))
    return CHOOSING_MENU

#User-based functions
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

async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_chat.send_message("#TODO - This function is still in development, come back soon! ;)")
    return CHOOSING_MENU

# Group based functions
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id       = update.effective_user.id
    user_username = update.effective_user.username
    chat_id       = update.effective_chat.id
    logging.debug(f"Verifying: {user_username}")
    try:
        # Register the user if it's the first time interacting with the bot
        if(not HANDLER.is_user(user_id)):
            await update.effective_chat.send_message(f"(New_User) It's a pleasure to meet you {user_username}, recording you into the database!")
            HANDLER.insert_user(user_id, user_username)
        
        # Link user with the connection if it's not already
        if(not HANDLER.is_in_connection(user_id, chat_id)):
            HANDLER.insert_connection(user_id, chat_id)
        
        # Confirm all users are recorded in db.connections, else loop until satisfied
        connections   = HANDLER.return_users_in_connections(chat_id)
        member_count  = HANDLER.return_chat_member_count(chat_id)
        users_left    = member_count - len(connections)
        logging.debug(f'connections: {connections}')
        logging.debug(f'member_count: {member_count}')
        if(users_left == 0):
            HANDLER.update_chat(chat_id, 0)
            return MAIN_LOOP
        await update.effective_chat.send_message(f"(Lacking_Connections) I still lack {users_left} to connect with me! I can't update this chat until everyone is registered, please introduce yourselves to me!")
    except Exception as e:
        raise
    return GROUP_REGISTER

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
                MessageHandler(filters.Regex("PRAY FOR ME"),    pray),
                MessageHandler(None,                            start),
            ],
            GROUP_REGISTER: [
                MessageHandler(None, register),
            ],
            PRAYING: [],
        },
        fallbacks = [CommandHandler("stop", error)],
        allow_reentry = True
    )
    application = Application.builder().token(TOKEN).concurrent_updates(True).pool_timeout(350).connection_pool_size(700).build()
    application.add_handler(convStart)
    application.add_error_handler(error)
    application.run_polling(allowed_updates = Update.ALL_TYPES, poll_interval = 0.1)

if __name__ == "__main__":
    logging.info("Starting background thread…")
    x = threading.Thread(target = subroutine, daemon = True)
    x.start()
    logging.info("Firing up bot…")
    main()
