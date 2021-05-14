import sqlite3


class DbHandler(object):
    conn = None 
    cur = None

    def __init__(self):
        self.conn = sqlite3.connect('..\\tbot_database_test.db')
        self.cur = self.conn.cursor()

    def add_user(self, user_id):
        try:
            self.cur.execute('''INSERT INTO users (user_id)
                                VALUES (?)''', (user_id,))
            self.conn.commit()
        except Exception:
            print('this id already exists')
            pass

    def select_tasks(self, user_id):
        self.cur.execute('''SELECT task, state_id, task_id, deadline 
                            FROM tasks 
                            WHERE user_id = (?)
                            ORDER BY deadline, state_id''', (user_id,))
        return self.cur.fetchall()

    def add_gener_num(self, task_id, number):
        self.cur.execute('''UPDATE tasks
                            SET
                            generated_num = (?)
                            WHERE task_id = (?)''', (number, task_id))
        self.conn.commit()

    def add_task(self, user_id, task):
        self.cur.execute('''INSERT INTO tasks (user_id, task) 
                            VALUES (?, ?)''', (user_id, task))
        self.conn.commit()

    def add_selected_number(self, user_id, number):
        self.cur.execute('''UPDATE users 
                            SET 
                            selected_number = (?) 
                            WHERE user_id = (?)''', (number, user_id))
        self.conn.commit()

    def add_deadline(self, user_id, date):
        task_id = self.selected_task_id(user_id)
        self.cur.execute('''UPDATE tasks
                            SET
                            deadline = (?)
                            WHERE task_id = (?)''', (date, task_id))
        self.conn.commit()

    def change_task_state(self, user_id, state_id):
        self.cur.execute('''SELECT tasks.task_id
                            FROM tasks
                                INNER JOIN
                                users
                            WHERE users.user_id = (?) AND users.selected_number = tasks.generated_num''', (user_id,))
        task_id = self.cur.fetchone()
        print(task_id)
        self.cur.execute('''UPDATE tasks 
                            SET 
                            state_id = (?) 
                            WHERE task_id = (?)''', (state_id, task_id[0]))
        self.conn.commit()

    def get_task_generated_num(self, user_id):
        self.cur.execute('''SELECT generated_num
                            FROM tasks
                            WHERE user_id = (?)
                            ORDER BY generated_num''', (user_id,))
        return self.cur.fetchall()


    def selected_task_id(self, user_id):
        self.cur.execute('''SELECT tasks.task_id
                            from tasks
                                inner join
                                users
                            where users.user_id = (?) and users.selected_number = tasks.generated_num''', (user_id,))
        task_id = self.cur.fetchone()
        return task_id[0]

    def edit_task(self, user_id, edited_task):
        task_id = self.selected_task_id(user_id)
        self.cur.execute('''UPDATE tasks
                            SET
                            task = (?)
                            WHERE task_id = (?)''', (edited_task, task_id))
        self.conn.commit()

    def get_deadline(self, task_id):
        self.cur.execute('''SELECT deadline
                            FROM tasks
                            WHERE task_id = (?)''', (task_id,))
        deadline, = self.cur.fetchone()
        if deadline == None:
            deadline = ''
        print(deadline)
        return deadline

    def update_deadline(self, user_id, new_info):
        task_id = self.selected_task_id(user_id)
        existing_info = self.get_deadline(task_id)
        combined_info = existing_info + new_info
        self.cur.execute('''UPDATE tasks
                            SET
                            deadline = (?)
                            WHERE task_id = (?)''', (combined_info, task_id))
        self.conn.commit()

    def edit_habit(self, user_id, edited_habit):
        self.cur.execute('''SELECT habits.habit_id
                            FROM habits
                                INNER JOIN
                                users
                            WHERE users.user_id = (?) AND users.selected_number = habits.generated_num''', (user_id,))
        habit_id = self.cur.fetchone()
        self.cur.execute('''UPDATE habits
                            SET
                            habit = (?)
                            WHERE habit_id = (?)''', (edited_habit, habit_id))
        self.conn.commit()

    def delete_task(self, user_id, gen_num):
        self.cur.execute('''DELETE FROM tasks 
                            WHERE user_id = (?) AND generated_num = (?)''', (user_id, gen_num))
        self.conn.commit()

    def get_all_deadlines(self, user_id):
        self.cur.execute('''SELECT deadline
                            FROM tasks
                            WHERE user_id=(?) AND deadline IS NOT NULL''', (user_id,))
        deadlines = self.cur.fetchall()
        return deadlines

    def add_missed_deadlines(self, user_id):
        self.cur.execute('''SELECT missed_deadlines
                            FROM users
                            WHERE user_id=(?)''', (user_id,))
        curr_number, = self.cur.fetchone()
        print(curr_number)
        self.cur.execute('''UPDATE users
                            SET
                            missed_deadlines=(?)
                            WHERE user_id=(?)''', (curr_number+1, user_id))
        self.conn.commit()
