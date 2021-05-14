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
    #check_missed_deadlines(message.chat.id)
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
            db.add_gener_num_tasks(record[2], i)
            i += 1

        keyboard = keyboards.tasks_keyboard()
        bot.send_message(message.chat.id, to_print, reply_markup=keyboard, parse_mode='MarkdownV2')
    else:
        buttons = [{'add task': 'new_task'}]
        keyboard = Keyboa(items=buttons, items_in_row=2).keyboard

        bot.send_message(message.chat.id, 'You have 0 tasks, do you want to add some?', reply_markup=keyboard)
  
  
#######################################  show habits  ###############################
@bot.message_handler(commands=["habits"])
def habits(message):
    db = DbHandler()
    keyboard_habits = keyboards.habits_keyboard()
    #to_print = create_list(message.chat.id, 'habits')
    records = db.select_habits(message.chat.id)
    if len(records) > 0:
        to_print = 'Your habits:\n'
        i = 1
        for record in records:
            to_print += str(i) + '\. '
            if record[4] == 1:
                to_print += '~' + record[2] + '~\n'
            else:
                to_print += record[2] + "\n"
            db.add_gener_num_habits(record[0], i)
            i += 1
        bot.send_message(message.chat.id, to_print, reply_markup=keyboard_habits, parse_mode="MarkdownV2")
    else:
        kb_habits = Keyboa(items=[{"Add new habit":"new_habit"}]).keyboard
        bot.send_message(message.chat.id, "You don't have any habits yet", reply_markup=kb_habits)


####################################  show goals  ######################
@bot.message_handler(commands=["goals"])
def show_goals(message):
    db = DbHandler()
    keyboard_goals = keyboards.goals_keyboard()
    records = db.select_goals(message.chat.id)
    if len(records) > 0:
        to_print = 'Your goals:\n'
        i = 1
        for record in records:
            to_print += str(i) + '\. '
            if record[4] == 1:
                to_print += '~' + record[2] + '~\n'
            else:
                to_print += record[2] + "\n"
            db.add_gener_num_goals(record[0], i)
            i += 1
        bot.send_message(message.chat.id, to_print, reply_markup=keyboard_goals, parse_mode="MarkdownV2")
    else:
        kb_goals = Keyboa(items=[{'add new goal':'new_goal'}]).keyboard
        bot.send_message(message.chat.id, "You don't have any goals yet", reply_markup=kb_goals)
        
########################################################################
def create_list(user_id, function):
    if function == 'habits':
        db = DbHandler()
        records = db.select_habits(user_id)
    elif function == 'goals':
        db = DbHandler()
        records = db.select_goals(user_id)
    if len(records) > 0:
        to_print1 = f'Your {function}:\n'
        i = 1
        for record in records:
            to_print1 += str(i) + '\. '
            if record[4] == 1:
                to_print1 += '~' + record[2] + '~\n'
            else:
                to_print1 += record[2] + "\n"
            db.add_gener_num_habits(record[0], i)
            i += 1
    else:
        to_print1 = None
    return to_print1

#####################################  add habits  ###################
def add_habits(message):
    db = DbHandler()
    for i in message.text.split('\n'):
        db.add_habit(message.chat.id, i)
    bot.send_message(message.chat.id, "Habits added!")

################################## add goals  ############################
def add_goals(message):
    db = DbHandler()
    for i in message.text.split('\n'):
        db.add_goal(message.chat.id, i)
    bot.send_message(message.chat.id, "Goal added!")


#####################################  all callbacks   ###################################  
@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    db = DbHandler()
    if call.data == 'new_task':
        instruction = 'Enter your tasks \(each task with a new string\)'
        task_query = bot.send_message(call.message.chat.id, instruction, parse_mode = 'MarkdownV2')
        bot.register_next_step_handler(task_query, add_new_task)
    elif call.data == 'new_habit':
        sent =bot.send_message(call.message.chat.id, 'What habit would you like to add?')
        bot.register_next_step_handler(sent, add_habits)
    elif call.data == 'new_goal':
        send = bot.send_message(call.message.chat.id, 'What goal would you like to add?')
        bot.register_next_step_handler(send, add_goals)
    else:
        selected_button = call.data
        replies = {'edit_task':'select task you want to edit', 'delete_task':'select task you want to delete', 
               'progress_task':'select task to change progress', 'changedeadline_task':'select task for changing deadline',
               'edit_habit':'select habit you want to edit', 'delete_habit':'selecthabit you want to delete',
               'progress_habit':'select habit to mark as done','edit_goal':'select goal you want to edit',
               'delete_goal':'select goal you want to delete', 'progress_goal':'select goal to mark as reached'}
        print(call.data)

        if call.data in replies:
            if call.data.split('_')[1] == 'task':
                kb_tasks_generated_num = Keyboa(items=db.get_task_generated_num(call.message.chat.id), back_marker='@'+selected_button, items_in_row=5, copy_text_to_callback=True).keyboard
                bot.send_message(call.message.chat.id, replies[call.data], reply_markup=kb_tasks_generated_num)
            if call.data.split('_')[1] == 'habit':
                kb_habits_generated_num = Keyboa(items=db.get_habit_generated_num(call.message.chat.id), back_marker='@'+selected_button, items_in_row=5, copy_text_to_callback=True).keyboard
                bot.send_message(call.message.chat.id, replies[call.data], reply_markup=kb_habits_generated_num)
            if call.data.split('_')[1] == 'goal':
                buttons=db.get_goal_generated_num(call.message.chat.id)
                print(buttons)
                kb_goals_generated_num = Keyboa(items=buttons, back_marker='@'+selected_button, items_in_row=5, copy_text_to_callback=True).keyboard
                bot.send_message(call.message.chat.id, replies[call.data], reply_markup=kb_goals_generated_num)

        elif call.data.split('@')[0].isalnum():
            choice_info = call.data.split('@')

            if choice_info[1] == 'delete_task':
                bot.send_message(call.message.chat.id, 'successfully deleted')
                db.delete_task(call.message.chat.id, choice_info[0])


            elif choice_info[1] == 'progress_task':
                db.add_selected_number(call.message.chat.id, choice_info[0])
                keyboard = keyboards.progress_keyboard()
                send = bot.send_message(call.message.chat.id, 'select progress', reply_markup=keyboard)
                bot.register_next_step_handler(send, change_state)

            elif choice_info[1] == 'edit_task':
                db.add_selected_number(call.message.chat.id, choice_info[0])
                send = bot.send_message(call.message.chat.id, 'change to')
                bot.register_next_step_handler(send, edit_task)

            elif choice_info[1] == 'changedeadline_task':
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

            elif choice_info[1] == 'edit_habit':
                db.add_selected_number(call.message.chat.id, choice_info[0])
                send = bot.send_message(call.message.chat.id, 'change to')
                bot.register_next_step_handler(send, edit_habit)

            elif choice_info[1] == 'edit_goal':
                db.add_selected_number(call.message.chat.id, choice_info[0])
                send = bot.send_message(call.message.chat.id, 'change to')
                bot.register_next_step_handler(send, edit_goal)

            elif choice_info[1] == 'delete_habit':
                bot.send_message(call.message.chat.id, 'successfully deleted')
                db.delete_habit(call.message.chat.id, choice_info[0])

            elif choice_info[1] == 'delete_goal':
                bot.send_message(call.message.chat.id, 'successfully deleted')
                db.delete_goal(call.message.chat.id, choice_info[0])

            elif choice_info[1] == 'progress_habit':
                db.change_progress_habit(call.message.chat.id, choice_info[0])
                bot.send_message(call.message.chat.id, 'progress changed')

            elif choice_info[1] == 'progress_goal':
                db.change_progress_goal(call.message.chat.id, choice_info[0])
                bot.send_message(call.message.chat.id, 'progress changed')



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
    bot.send_message(message.chat.id, 'task successfully edited')

def check_missed_deadlines(user_id):
    db = DbHandler()
    deadlines = db.get_all_deadlines(user_id)
    print(deadlines)
    for deadline in deadlines:
            deadline_date = datetime.datetime.fromisoformat(deadline[0])
            if deadline_date < datetime.datetime.today():
                db.add_missed_deadlines(user_id)

#################################  edit habit  ############################3
def edit_habit(message):
    db = DbHandler()
    db.edit_habit(message.chat.id, message.text)
    bot.send_message(message.chat.id, 'habit successfully edited')
        #edit_message('habits')

################################  edit goal  ###################
def edit_goal(message):
    db = DbHandler()
    db.edit_goal(message.chat.id, message.text)
    bot.send_message(message.chat.id, 'goal successfully edited')

def main():
    bot.polling(none_stop=True, interval=0)

if __name__ == '__main__':

    main()