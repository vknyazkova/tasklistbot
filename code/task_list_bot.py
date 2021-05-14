import telebot
import sqlite3
import re
import datetime

from telebot import types
from keyboa import Keyboa

import keyboards
from bd import DbHandler




TOKEN = '1704625083:AAF2ae6sw25H1TpVWp7NkuT5Zl8KZUP9u2E'

bot = telebot.TeleBot(TOKEN)



################################   start  ############################
@bot.message_handler(commands= ['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Hi, I\'m a planner bot. I can do this, this and this.')
    db = DbHandler()
    db.add_user(message.chat.id)




##############################  show tasks  ############################
@bot.message_handler(commands= ['tasks'])
def show_tasks(message):
    db = DbHandler()
    check_missed_deadlines(message.chat.id)
    records = db.select_tasks(message.chat.id)
    # 0 - task, 1 - state_id, 2 - task_id, 3 - deadline
    if len(records) > 0:
        to_print = 'Your tasks:\n'
        i = 1
        for record in records:
            to_print += str(i) + '\. '
            # in progress
            if record[1] == 1:
                to_print += record[0] + '\u23F3'
            # done
            elif record[1] == 3:
                to_print += '~' + record[0] + '~'
            # to do
            else:
                to_print += record[0]
            # with deadline 
            if record[3]:
                to_print += ' ' + record[3].replace('-', '\.')
            to_print += '\n'
            db.add_gener_num(record[2], i)
            i += 1

        buttons = [{'change progress': 'change_progress'}, {'add new task': 'new_task'}, 
                   {'edit': 'edit'}, {'delete': 'delete'}, {'change deadline': 'change_deadline'}]
        keyboard = Keyboa(items=buttons, items_in_row = 2).keyboard
        bot.send_message(message.chat.id, to_print, reply_markup=keyboard, parse_mode='MarkdownV2')
    else:
        buttons = [{'add task': 'new_task'}]
        keyboard = Keyboa(items=buttons, items_in_row=2).keyboard

        bot.send_message(message.chat.id, 'You have 0 tasks, do you want to add some?', reply_markup=keyboard)
  
        


#####################################  all callbacks   ###################################  
@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    db = DbHandler()
    if call.data == 'new_task':
        instruction = 'Enter your tasks \(each task with a new string\)'
        task_query = bot.send_message(call.message.chat.id, instruction, parse_mode = 'MarkdownV2')
        bot.register_next_step_handler(task_query, add_new_task)

    else:
        selected_button = call.data
        kb_tasks_generated_num = Keyboa(items=db.get_task_generated_num(call.message.chat.id), back_marker='@'+selected_button, items_in_row=5, copy_text_to_callback=True).keyboard
        replies = {'edit':'select task you want to edit', 'delete':'select task you want to delete', 
               'change_progress':'select task to change progress', 'change_deadline':'select task for changing deadline'}
        print(call.data)

        if call.data in replies:
            bot.send_message(call.message.chat.id, replies[call.data], reply_markup=kb_tasks_generated_num)

        elif call.data.split('@')[0].isalnum():
            choice_info = call.data.split('@')

            if choice_info[1] == 'delete':
                bot.send_message(call.message.chat.id, 'successfully deleted')
                db.delete_task(call.message.chat.id, choice_info[0])

            elif choice_info[1] == 'change_progress':
                db.add_selected_number(call.message.chat.id, choice_info[0])
                keyboard = keyboards.progress_keyboard()
                send = bot.send_message(call.message.chat.id, 'select progress', reply_markup=keyboard)
                bot.register_next_step_handler(send, change_state)

            elif choice_info[1] == 'edit':
                db.add_selected_number(call.message.chat.id, choice_info[0])
                send = bot.send_message(call.message.chat.id, 'change to')
                bot.register_next_step_handler(send, edit_task)

            elif choice_info[1] == 'change_deadline':
                db.add_selected_number(call.message.chat.id, choice_info[0])
                keyboard = keyboards.create_year_keyboard()
                bot.send_message(call.message.chat.id, 'select year', reply_markup=keyboard)
    

            elif choice_info[1] == 'year':
                db.add_deadline(call.message.chat.id, choice_info[0])
                keyboard = keyboards.create_months_keyboard()
                bot.edit_message_text(text='select month', chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=keyboard)

            elif choice_info[1] == 'month':
                date = (choice_info[0])
                if len(choice_info[0]) == 1:
                    date = '0' + choice_info[0]
                db.update_deadline(call.message.chat.id, '-' + date)
                date = db.get_deadline(db.selected_task_id(call.message.chat.id))
                keyboard = keyboards.create_days_keyboard(date)
                bot.edit_message_text(text='select day', chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=keyboard)

            elif choice_info[1] == 'day':
                date = (choice_info[0])
                if len(choice_info[0]) == 1:
                    date = '0' + choice_info[0]
                db.update_deadline(call.message.chat.id, '-' + date)
                send = bot.send_message(call.message.chat.id, 'enter_time')
                bot.register_next_step_handler(send, add_time)





#################################  add task  ##############################
def add_new_task(message):
    db = DbHandler()
    tasks = message.text.split('\n')
    for task in tasks:
        db.add_task(message.chat.id, task)
    
    bot.send_message(message.chat.id, 'successfully added')




#############################  change progress  #########################
def change_state(message):
    db = DbHandler()
    state_id = 0
    states = {'to do':'2', 'in progress':'1', 'done':'3'}
    if message.text in states:
        db.change_task_state(message.chat.id, states[message.text])
        bot.send_message(message.chat.id, 'progress was saved', reply_markup=types.ReplyKeyboardRemove())
    else:
        send = bot.send_message(message.chat.id, 'plese press one of the button')
        bot.register_next_step_handler(send, change_state)
        return
 
def add_time(message):
    db = DbHandler()
    print(message.text)
    if re.match('(([0-1][0-9]|2[0-3]):[0-5][0-9])', message.text).group():
        db.update_deadline(message.chat.id, ' ' + message.text)
        bot.send_message(message.chat.id, 'deadline successfully added')


##################################### edit task  #############################
def edit_task(message):
    db = DbHandler()
    db.edit_task(message.chat.id, message.text)
    bot.send_message(message.chat.id, 'task was successfully edited')

def check_missed_deadlines(user_id):
    db = DbHandler()
    deadlines = db.get_all_deadlines(user_id)
    print(deadlines)
    for deadline in deadlines:
            deadline_date = datetime.datetime.fromisoformat(deadline[0])
            if deadline_date < datetime.datetime.today():
                db.add_missed_deadlines(user_id)

def main():
    bot.polling(none_stop=True, interval=0)

if __name__ == '__main__':

    main()