#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

import logging
import os
import sys

from telegram import *
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from database import DataBase

DB = DataBase('data.sql')

TOKEN = os.environ.get('TOKEN')
if TOKEN == None:
  print('Define TOKEN env var!')
  sys.exit(1)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def dota(update, context):
    if len(context.args) == 0:
        keyboard = [
          [
            InlineKeyboardButton("Patches", callback_data="patches"),
            InlineKeyboardButton("Heroes", callback_data="heroes"),
            InlineKeyboardButton("Items", callback_data="items"),
            InlineKeyboardButton("Close", callback_data="close"),
          ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('What do you wanna know?', reply_markup=reply_markup)

def smart_append(line, text, lenght=4000):
    if len(line) + len(text) > 4000:
        text = text[len(line):]
        text = 'Full message too long\n' + text
    return text + line

def shorten(text):
    max_len = 4000
    if len(text) > max_len:
        text = 'Message too long...\n' + text[len(text)-max_len:]
    return text

def button(update, context):
    query = update.callback_query
    if query.data.split('_')[0] == 'close':
        query.edit_message_text('Bye')
    if query.data.split('_')[0] == 'dota':
        keyboard = [
          [
            InlineKeyboardButton("Patches", callback_data="patches"),
            InlineKeyboardButton("Heroes", callback_data="heroes"),
            InlineKeyboardButton("Items", callback_data="items"),
            InlineKeyboardButton("Close", callback_data="close"),
          ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text('What do you wanna know?', reply_markup=reply_markup)
    if query.data.split('_')[0] == 'patch':
        patch = query.data.split('_')[1]
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='patches'),]])
        text = f'Patch *{patch}*\n'
        general_info = DB.get_general_history(patch)
        heroes_affected = DB.get_heroes_affected(patch)
        items_affected = DB.get_items_affected(patch)
        if len(general_info) == 0:
            text += f"There isn't general changes in {patch}\n"
        else:
            text += "*General changes:\n*"
            i = 1
            for change in general_info:
                text += f" {i} - {change[0]}\n"
                i += 1
        if len(heroes_affected) == 0:
            text += f"There isn't heroes changed in {patch}"
        else:
            i = 1
            text += "*Heroes changed:\n*"
            for hero in heroes_affected:
                text += f" {i} - {hero[0]}\n"
                i += 1
        if len(items_affected) == 0:
            text += f"There isn't items changed in {patch}"
        else:
            i = 1
            text += "*Items changed:\n*"
            for item in items_affected:
                text += f" {i} - {item[0]}\n"
                i += 1
            
        query.edit_message_text(shorten(text), parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    if query.data.split('_')[0] == 'item':
        keyboard = [[InlineKeyboardButton("Back", callback_data='items')]]
        if 'expand' in query.data:
            expand = True
        else:
            expand = False
            keyboard[0].append(InlineKeyboardButton(
                    "Expand",
                    callback_data=f'{query.data}_expand')
            )
        reply_markup = InlineKeyboardMarkup(keyboard)

        expand = True if 'expand' in query.data else False
        item_name = query.data.split('_')[1]
        item_history = DB.get_item_history(item_name)
        text = f'*{item_name}* update history\n'
        cur_patch = ''
        for upd in item_history:
            if upd[1] is None and not expand:
                continue
            if upd[0] != cur_patch:
                no_info = '*No changes*' if upd[1] is None else ''
                text += f"\n* {upd[0]} {no_info} *\n"
                cur_patch = upd[0]
            if upd[1] is not None:
                text += f'\t\t 🔹 {upd[1]}\n'
        query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    if query.data.split('_')[0] == 'hero':
        keyboard = [[InlineKeyboardButton("Back", callback_data='heroes')]]
        if 'expand' in query.data:
            expand = True
        else:
            expand = False
            keyboard[0].append(InlineKeyboardButton(
                    "Expand",
                    callback_data=f'{query.data}_expand')
            )
        reply_markup = InlineKeyboardMarkup(keyboard)

        expand = True if 'expand' in query.data else False
        hero_name = query.data.split('_')[1]
        hero_history = DB.get_hero_history(hero_name)
        text = f'*{hero_name}* update history\n'
        cur_patch = ''
        cur_type = ''
        for upd in hero_history:
            if upd[0] != cur_patch:
                if upd[1] is None and not expand:
                    continue
                no_info = '*No changes*' if upd[1] is None else ''
                text += f"\n* {upd[0]} {no_info} *\n"
                cur_patch = upd[0]
                cur_type = ''
            if upd[1] is not None:
                if upd[1] != cur_type:
#                  text = smart_append(f"🔆*{upd[1].capitalize()}*\n", text)
                   text += f"🔆*{upd[1].capitalize()}*\n"
                   cur_type = upd[1]
#               text = smart_append(f'\t\t 🔹 {upd[2]}\n', text)
                text += f'\t\t 🔹 {upd[2]}\n'
        text = shorten(text)
        query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    if query.data.split('_')[0] == 'patches':
        patches = DB.get_patch_list()
        patches.reverse()
        keyboard = [[]]
        in_a_row = 5
        for patch in patches:
            if len(keyboard[-1]) == in_a_row:
                keyboard.append(list())
            keyboard[-1].append(InlineKeyboardButton(f"{patch}", callback_data=f"patch_{patch}"))
        keyboard.append([InlineKeyboardButton("Back", callback_data='dota')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Select patch", reply_markup=reply_markup)
    if query.data.split('_')[0] == 'heroes':
        per_page = 20
        try:
            page = int(query.data.split('_')[1])
        except:
            page = 0
        heroes = DB.get_heroes_list()
        heroes.sort()
        last_hero = page*per_page+per_page
        if len(heroes) <= last_hero - 1:
            last_hero = len(heroes)
        keyboard = [[]]
        in_a_row = 2
        for hero in heroes[page*per_page:last_hero]:
            if len(keyboard[-1]) == in_a_row:
                keyboard.append(list())
            keyboard[-1].append(InlineKeyboardButton(f"{hero}", callback_data=f"hero_{hero}"))
        keyboard.append([])
        if page != 0:
            keyboard[-1].append(
                InlineKeyboardButton("<=", callback_data=f'heroes_{page-1}'),
            )
        if len(heroes) != last_hero:
            keyboard[-1].append(
                InlineKeyboardButton("=>", callback_data=f'heroes_{page+1}'),
            )

        keyboard.append([InlineKeyboardButton("Back", callback_data='dota')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=f"Select hero {page*per_page}:{page*per_page+per_page}", reply_markup=reply_markup)
    if query.data.split('_')[0] == 'items':
        per_page = 20
        try:
            page = int(query.data.split('_')[1])
        except:
            page = 0
        items = DB.get_items_list()
        items.sort()
        keyboard = [[]]
        last_item = page*per_page+per_page
        if len(items) <= last_item - 1:
            last_item = len(items)
        in_a_row = 2
        for item in items[page*per_page:last_item]:
            if len(keyboard[-1]) == in_a_row:
                keyboard.append(list())
            keyboard[-1].append(InlineKeyboardButton(f"{item}", callback_data=f"item_{item}"))
        keyboard.append([])
        if page != 0:
            keyboard[-1].append(
                InlineKeyboardButton("<=", callback_data=f'items_{page-1}'),
            )
        if len(items) != last_item:
            keyboard[-1].append(
                InlineKeyboardButton("=>", callback_data=f'items_{page+1}'),
            )
        keyboard.append([InlineKeyboardButton("Back", callback_data='dota')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Select item", reply_markup=reply_markup)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Run bot."""
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler("dota", dota,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
