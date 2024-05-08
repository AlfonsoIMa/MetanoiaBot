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

import logging, threading, time, re, os
from datetime import date, datetime
from handler import BotParser as bp
from sqlite3 import IntegrityError
from tabulate import tabulate
from typing import Final
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatInviteLink, Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler,
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
MAIN_LOOP, REGISTRATION, PRAYING, CHOOSING_MENU = range(4)
OPER_KEYBOARD:  Final = [["CONTACT", "ORDER MATERIAL"], ["CONFERENCE",], ["PRAY FOR ME"]]

# LOGGING
logging.basicConfig(format="MAIN APP - %(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logging.getLogger("httpx")
logger = logging.getLogger(__name__)

# Thread subroutine - Deprecated
# def subroutine():
    

# Proper bot implementations
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id       = update.effective_user.id
    user_username = update.effective_user.username
    chat_id       = update.effective_chat.id
    logging.debug(f'\n\n\n/start has been triggered by {user_id} on {chat_id}!')
    if(user_id != chat_id):
        if(not context.bot.can_read_all_group_messages):
            logging.error(f'Group {chat_id} has no permissions to read messages! Informing {user_id}')
            await update.effective_chat.send_message("(Lack Permissions) I don't have permission to see this group's messages! Please ensure I have permissions in the settings bar of this group!")
            return MAIN_LOOP

        # Get the member count
        await update.effective_chat.send_action(constants.ChatAction.TYPING)
        members = await update.effective_chat.get_member_count() - 1
        logging.debug(f'Group {chat_id} has {members} member(s)!\n\n\n')
        
        # Register the chat
        try:
            await update.effective_chat.send_message(f"Hey {user_username} schön, dass Du dabei bist. Ich freue mich auf die gemeinsame Nachfolge Jesu! Schreib mir doch kurz eine Nachricht.")
            logging.debug(f'Registering {chat_id} with {members} member(s)!\n\n\n')
            HANDLER.insert_chat(chat_id, members)
            logging.debug(f'Succesful registration of {chat_id} with {members} member(s)! returning to REGISTRATION\n\n\n')
        except IntegrityError as i:
            logging.warning(f'IntegrityError for {chat_id} has been triggered! Defaulting to Registration for confirmation.')
            await update.effective_chat.send_message("Es scheint, als hättet ihr den Chat mehrfach gestartet. Lasst uns schauen, ob alles in Ordnung ist. Schreibt beide mal eine Nachricht.")
        logging.debug(f'\n\n\nSuccesful exit from try/catch sequence, returning to REGISTRATION')
        return REGISTRATION
    else:
        await update.message.reply_text(f"Hey {user_username} schön, dass Du dabei bist. Ich freue mich auf die verändernde Reise der Nachfolge Jesu! Schreib mir doch kurz eine Nachricht.",
                                        reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD,
                                                                           input_field_placeholder = "CHOOSE AN OPTION",
                                                                           resize_keyboard = True))
    return CHOOSING_MENU

#User-based functions
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Du hast Fragen oder Vorschläge? Schreib uns einfach eine info@metanoia\-movement\.org",
                                    reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD, input_field_placeholder = "CHOOSE AN OPTION", resize_keyboard = True), disable_web_page_preview = False, parse_mode = "MarkdownV2")
    return CHOOSING_MENU

async def order_material(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Du benötigst neues metanoia-Material?\n\n\- Bibel Journal\n\- Themenheft\n\- Geben\n\- Gehen\n\- Beten\n\nSchreib uns was du brauchst und wir schicken es dir zu\. info@metanoia\-movement\.org",
                                    reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD, input_field_placeholder = "CHOOSE AN OPTION", resize_keyboard = True), disable_web_page_preview = False, parse_mode = "MarkdownV2")
    return CHOOSING_MENU

async def conference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Für 2025 sind 4 lokale \"metanoia\-Tage\" geplant\. 2026 wollen wir vom 24\.\-26\.April die dritte Konferenz feiern\.\n\n[metanoia-website](http://www.metanoia-movement.org)",
                                    reply_markup = ReplyKeyboardMarkup(OPER_KEYBOARD, input_field_placeholder = "CHOOSE AN OPTION", resize_keyboard = True), disable_web_page_preview = False, parse_mode = "MarkdownV2")
    return CHOOSING_MENU

# TODO - implement in both group and private
async def pray(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_chat.send_message("#TODO - This function is still in development, come back soon! ;)")
    return CHOOSING_MENU

# Group based functions
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id       = update.effective_user.id
    user_username = update.effective_user.username
    chat_id       = update.effective_chat.id
    logging.debug(f"Verifying: {user_username}\n\n\n")
    try:
        # Register the user if it's the first time interacting with the bot
        if(not HANDLER.is_user(user_id)):
            await update.effective_chat.send_message(f"{user_username} hat heute noch nichts geschrieben. Schick eine Erinnerung :)")
            HANDLER.insert_user(user_id, user_username)
        
        # Link user with the connection if it's not already
        if(not HANDLER.is_in_connection(user_id, chat_id)):
            HANDLER.insert_connection(user_id, chat_id)
        
        # Confirm all users are recorded in db.connections, else loop until satisfied
        connections   = HANDLER.return_users_in_connections(chat_id)
        member_count  = HANDLER.return_chat_member_count(chat_id)
        users_left    = member_count - len(connections)
        logging.debug(f'connections: {connections}; member_count: {member_count}')
        if(users_left == 0):
            await update.effective_chat.send_message(f"Wir sind startklar! Lasst uns gemeinsam lesen und beten!")
            HANDLER.update_chat(chat_id, 1)
            return MAIN_LOOP
        # Missing n connections
        await update.effective_chat.send_message(f"Dein Jüngerschaftspartner hat noch nichts geschrieben. Wenn er seinen Namen schreibt, sind wir startklar 😉.")
    except Exception as e:
        raise
    return REGISTRATION

async def update_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    logging.debug(f"Reading updates from: {user_id}\n\n\n")
    if(chat_id != user_id):
        logging.debug(f"Method update_chat() triggered on chat {chat_id}!\n\n\n")
        try:
            logging.debug(f"Attempting updating activeness for {user_id}\n\n\n")
            HANDLER.update_user_activeness_today(user_id, chat_id)
            logging.info(f"Activenness for {user_id} today updated")
            first_pass  = HANDLER.return_current_status_on_chat(chat_id)
            updated     = HANDLER.update_connections_status(chat_id)
            if(updated):
                logging.info(f"All connections updated for {chat_id}")
                if(first_pass):
                    streak = HANDLER.update_chat_streak(chat_id)
                    await update.effective_chat.send_message(f"Ihr seid schon {streak} Tage aktiv 👍 macht weiter so 🤝🙏")
        except Exception as e:
            logging.error(e.with_traceback)
            raise
    else:
        logging.debug("Method update_chat() triggered on personal chat… Ignoring…\n\n\n")
    return MAIN_LOOP

async def update_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    logging.debug(f'Member count change for {chat_id}\n\n\n')
    members = await update.effective_chat.get_member_count() - 1
    if(members):
        logging.debug(f'Member updates for {chat_id}\n\n\n')
        members_registered = HANDLER.return_chat_member_count(chat_id)
        
        # Updating member_count in database
        HANDLER.update_chat_members(chat_id, members)
        if(members > members_registered):
            # A user joined, performing registration
            for user in update.message.new_chat_members:
                user_id = user.id
            
                if(HANDLER.is_in_connection(user_id, chat_id)):
                    logging.info(f'{user_id} rejoined {chat_id}, updating status!')
                    HANDLER.update_user_activeness_today(user_id, chat_id)
                    HANDLER.update_user_in_connection(chat_id, user_id, HANDLER.UPDATED)
                else:
                    logging.info(f'New member {user_id} on {chat_id}, performing registration')
                    HANDLER.insert_connection(user_id, chat_id)
        elif(members < members_registered):
            for user in update.message.left_chat_member:
                # A user left, changing connection status to closed
                user_id = update.message.left_chat_member.id
                logging.info(f'{user_id} left {chat_id}, updating status')
                HANDLER.update_user_in_connection(chat_id, user_id, HANDLER.CLOSED)
        else:
            await update.effective_chat.send_message("Did someone join or leave?")
    else:
        logging.info(f'No more members on {chat_id}, exitting chat')
        # All users have left the chat, deleiting registries
        HANLDER.update_connections_status(chat_id, HANDLER.CLOSED)
        HANDLER.update_chat(chat_id, HANDLER.CLOSED) 
    return MAIN_LOOP

#  OPERATOR COMMAND - Subroutines and logical implementations
async def run_operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id   = update.effective_user.id
    this_chat = update.effective_chat.id
    if(not HANDLER.is_administrator(user_id) and user_id != update.effective_chat.id):
        logging.error(f'User {user_id} tried to trigger /run without operator permissions!')
        return MAIN_LOOP
    else:
        try:
            await update.effective_chat.send_message("Running master command…")
            # Setting all connections to False to read from today
            logging.info("Resetting all activeness to False on all chats!")
            today           = date.today().strftime('%Y-%m-%d')
            all_connections = HANDLER.return_connections(discriminate = True)
            for row_fetched in all_connections:
                # Update all active connections to 1
                HANDLER.update_connections_status(row_fetched[1], 1)
                logging.debug(f'Updated {row_fetched[1]}:{row_fetched[2]} to status INACTIVE for today')
            logging.info("All activeness set to False on all chats!")
        except Exception as e:
            await update.effective_chat.send_message('error in falseness in all chats')

        try:
            # Set all chats to inactive
            all_chats = HANDLER.return_chats() 
            for row_fetched in all_chats:
                # Update status on old chats based on date and send message accordingly
                days_passed = days_between(row_fetched[2], today)
                chat_id = row_fetched[0]
                if(days_passed in range(0, 2)):
                   continue
                elif(days_passed in range(3, 7)):
                    HANDLER.update_chat(chat_id, HANDLER.INACTIVE_ONE_WEEK)
                    await context.bot.send_message(chat_id = chat_id, text = "Hey! Es sieht so aus, als hättet ihr aktuell Schwierigkeiten. Ich will euch ermutigen, macht weiter - Es lohnt sich! 🙏🏼")
                elif(days_passed in range(8, 15)):
                    HANDLER.update_chat(chat_id, HANDLER.INACTIVE_TWO_WEEKS)
                    await context.bot.send_message(chat_id = chat_id, text = "Hey! Ihr habt schon lange nichts mehr geteilt! Seid ihr noch unterwegs? Dann gebt hier doch mal wieder ein Update und startet wieder voll durch.")
                elif(days_passed in range(16, 29)):
                    HANDLER.update_chat(chat_id, HANDLER.INACTIVE_THREE_WEKS)
                    await context.bot.send_message(chat_id = chat_id, text = "Es sieht so aus, als würdet ihr aktuell nicht mehr gemeinsam Lesen und beten…")
                else:
                    HANDLER.update_chat(chat_id, HANDLER.CLOSED) 
                    HANDLER.update_connections_status(chat_id, HANDLER.CLOSED)
                    await context.bot.send_message(chat_id = chat_id, text = "Leider sehe ich immer noch keine Aktivität. Daher sende ich euch keine Updates mehr. Wenn immer ihr wieder starten wollt, aktiviert mich einfach wieder und wir gehen gemeinsam wieder los")
                    await context.bot.leave_chat(chat_id)
                # All active chats set to 1
                if(row_fetched[5] == 0):
                    HANDLER.update_chat(chat_id, 1)
                logging.debug(f'Updated {row_fetched[0]}:{row_fetched[5]} to status INACTIVE for today')
            logging.info("All activeness set to False on all chats!")
            logging.info("Succesfully reset dates")
        except Exception as e:
            await update.effective_chat.send_message('exception in messages')
        finally:
            # Sending results
            users = HANDLER.return_user_count()[0][0]
            chats = HANDLER.return_chats_by_streak()
            t_chats = f"```Chats by streak\n{tabulate(chats, headers = ['Streak', 'No. of Chats'], tablefmt = 'grid')}```"
            conns = HANDLER.return_connections_by_status()
            t_conns = f"```Users(Connections) by status\n{tabulate(conns, headers = ['Status', 'No. of Users'], tablefmt = 'grid')}```"
            with open('report.txt', 'w') as file:
                # file.write(t_users)
                file.write(t_chats)
                file.write(t_conns)
            with open('report.txt', 'rb') as file:
                context.bot.send_document(chat_id = this_chat, document = file)
            os.remove('report.txt')
            await update.effective_chat.send_message('sending tables')
            await update.effective_chat.send_message(f"I currently have {users} users registered!")
            await update.effective_chat.send_message(t_chats, parse_mode = 'MarkdownV2')
            await update.effective_chat.send_message(t_conns, parse_mode = 'MarkdownV2')
            await update.effective_chat.send_message('tables sent')
    return MAIN_LOOP

def days_between(dateOne: str, dateTwo: str) -> int:
    dOne        = datetime.strptime(dateOne, "%Y-%m-%d").date()
    dTwo        = datetime.strptime(dateTwo, "%Y-%m-%d").date()
    return (dTwo - dOne).days

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error:\n\n{context.error}\n\n{context.error.with_traceback}')
    await context.bot.send_message(chat_id = '1523978922', text = f'Update {update} caused error:\n\n{context.error}\n\n{context.error.with_traceback}')

def main() -> None:
    convStart = ConversationHandler(
        entry_points = [CommandHandler("start", start),
                        CommandHandler("pray", pray),
                        CommandHandler("run", run_operator)],
        states = {MAIN_LOOP: [MessageHandler(filters.TEXT,                          update_chat),
                              MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, update_members),
                              MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, update_members)],
                  REGISTRATION: [MessageHandler(None, register)],
                  PRAYING: [MessageHandler(None, pray)],
                  CHOOSING_MENU: [MessageHandler(filters.Regex("CONTACT"),        contact),
                                  MessageHandler(filters.Regex("ORDER MATERIAL"), order_material),
                                  MessageHandler(filters.Regex("CONFERENCE"),     conference),
                                  MessageHandler(filters.Regex("PRAY FOR ME"),    pray),
                                  MessageHandler(None,                            start)]},
        fallbacks = [CommandHandler("stop", error)],
        allow_reentry = True,
        per_user = False
    )
    # As noted per API "When using this handler, telegram.ext.ApplicationBuilder.concurrent_updates should be set to False"
    application = Application.builder().token(TOKEN).concurrent_updates(False).pool_timeout(350).connection_pool_size(700).build()
    application.add_handler(convStart)
    application.add_error_handler(error)
    application.run_polling(allowed_updates = Update.ALL_TYPES, poll_interval = 0.1)

if __name__ == "__main__":
    #logging.info("Starting background thread…")
    #x = threading.Thread(target = subroutine, daemon = True)
    #x.start()
    logging.info("Firing up bot…")
    main()
