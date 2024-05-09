from datetime import date
import sqlite3, logging

class BotParser():
    def __init__(self, DATABASE: str):
        # Status Constants
        self.CONNECTING, self.UPDATED, self.INACTIVE_ONE_WEEK, self.INACTIVE_TWO_WEEKS, self.INACTIVE_THREE_WEKS, self.CLOSED = range(-1, 5)
        # TODO - Date Constant
        self.TODAY       = date.today()
        # Database
        self.connection  = sqlite3.connect(DATABASE, check_same_thread = False)
        self.cursor      = self.connection.cursor()

    """
    users       .STATUS = [0 - Free, 1 - Taken, 2 - Inactive, 3 - Deleted / Cancelled]
    users       .ADMON  = [0 - False, 1 - True]
    connections .STATUS = [-1 - Connecting, 0 - Updated, 1 - Inactive1w, 2 - Inactive2w, 3 - Closed]
    chats       .STATUS = [-1 - Connecting, 0 - Updated, 1 - Inactive1w, 2 - Inactive2w, 3 - Closed]

    DEPRECTATED:
    prayer      .STATUS = [0 - Unanswered, 1 - Answered, 2 - Ignore]
    
    IMPORTANT:
    - DATE IS FORMATED YYYY-MM-DD
    """

    def number_of_users(self, including_linked = False) -> int:
        query = " WHERE status = 0;"
        q_result = self.cursor.execute("SELECT COUNT(id) FROM users" + (query if including_linked else ";"))
        return q_result.fetchall()[0][0]

    def number_of_connections(self, discriminate = False, desired_status = 0) -> int:
        query = f" AND status = {desired_status};"
        q_result = self.cursor.execute("SELECT COUNT(connection_id) FROM connections WHERE status <> 3" + (query if discriminate else ";"))
        return q_result.fetchall()[0][0]

    def return_chat_member_count(self, chat_id: int) -> int:
        q_result = self.cursor.execute("SELECT member_count FROM chats WHERE chat_id = ?;", (chat_id,))
        q_result = q_result.fetchall()
        return q_result[0][0]
    
    def return_chats(self, discriminate = False, desired_status = 0) -> list:
        query = f" AND status = {desired_status};"
        q_result = self.cursor.execute("SELECT * FROM chats WHERE status <> 4" + (query if discriminate else ";"))
        return q_result.fetchall()
    
    def return_chats_by_streak(self) -> list:
        q_result = self.cursor.execute("SELECT streak, COUNT(*) FROM chats WHERE status <> 4 GROUP BY status;")
        return q_result.fetchall()
    
    def return_connections(self, discriminate = False, desired_status = 0) -> list:
        query = f" AND status = {desired_status};"
        q_result = self.cursor.execute("SELECT * FROM connections WHERE status <> 4" + (query if discriminate else ";"))
        return q_result.fetchall()

    def return_connections_by_status(self) -> list:
        q_result = self.cursor.execute("SELECT status, COUNT(*) FROM connections WHERE status <> 4 GROUP BY status;")
        return q_result.fetchall()

    def return_last_updated_date_on_chat(self, chat_id: int) -> int:
        query = self.cursor.execute("SELECT date_updated FROM chats WHERE chat_id = ?", (chat_id,))
        query = query.fetchall()
        return True if query[0][0] == date.today().strftime('%Y-%m-%d') else False

    def return_users(self, field: str = 'user_id', discriminate = False, desired_status: int = -1, desired_gender: int = -1) -> list:
        query = f" AND status = {desired_status};"
        q_result = self.cursor.execute("SELECT * FROM users WHERE status <> 4" + (query if discriminate else ";"))
        q_result = q_result.fetchall()
        return q_result

    def return_user_count(self) -> list:
        query = self.cursor.execute("SELECT COUNT(*) FROM users WHERE status <> 4;")
        return query.fetchall()

    def return_users_in_connections(self, chat_id: int) -> list:
        q_result = self.cursor.execute("SELECT user_id FROM connections WHERE chat_id = ? AND status <> 3;", (chat_id,))
        q_result = q_result.fetchall()
        return q_result

    def insert_user(self, user_id: int, user_name: str) -> bool:
        try:
            q_result = self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, 0, 0);", (user_id, user_name, self.TODAY.strftime('%y%m%d'),))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError as e:
            return False
    
    def insert_chat(self, chat_id: int, member_count: int) -> bool:
        self.cursor.execute("INSERT INTO chats VALUES (?, ?, ?, ?, ?, ?)", (chat_id, self.TODAY.strftime('%Y-%m-%d'), self.TODAY.strftime('%Y-%m-%d'), member_count, 0, -1))
        self.connection.commit()
        return True

    def insert_connection(self, user_id: int, chat_id: int) -> bool:
        self.cursor.execute("INSERT INTO connections (chat_id, user_id, date_creation, date_updated, status) VALUES (?, ?, ?, ?, ?);", (chat_id, user_id, self.TODAY.strftime('%Y-%m-%d'), self.TODAY.strftime('%Y-%m-%d'), 1))
        self.update_user_status(user_id, 1)
        self.connection.commit()
        return True
    
    def is_user(self, user_id: int) -> bool:
        q_result = self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?;", (user_id,))
        q_result = q_result.fetchall()
        return 1 if len(q_result) else 0

    def is_administrator(self, user_id: int) -> bool:
        q_result = self.cursor.execute("SELECT is_admin FROM users WHERE user_id = ?;", (user_id,))
        q_result = q_result.fetchall()
        return q_result[0][0]

    def is_in_connection(self, user_id: int, chat_id: int) -> bool:
        q_result = self.cursor.execute("SELECT connection_id FROM connections WHERE user_id = ? AND chat_id = ?;", (user_id, chat_id,))
        q_result = q_result.fetchall()
        if(len(q_result)):
            return 1
        return 0

    def was_active_today(self, user_id: int) -> bool:
        q_result = self.cursor.execute("SELECT date_updated FROM connections WHERE user_id = ?;", (user_id,))
        q_result = q_result.fetchall()
        for row in q_result:
            if(row[0] == date.today().strftime('%Y-%m-%d')):
                return True
        return False
   
    # TODO - Reset streak
    def update_chat_streak(self, chat_id: int) -> int:
        null     = self.cursor.execute("UPDATE chats SET streak = (SELECT streak FROM chats WHERE chat_id = ?) + 1 WHERE chat_id = ?", (chat_id, chat_id))
        self.connection.commit()
        q_result = self.cursor.execute("SELECT streak FROM chats WHERE chat_id = ?;", (chat_id,)) 
        q_result = q_result.fetchall()
        return q_result[0][0]

    def update_user_activeness_today(self, user_id: int, chat_id: int) -> bool:
        try:
            today = date.today().strftime('%Y-%m-%d')
            q_result = self.cursor.execute("UPDATE connections SET date_updated = ? WHERE user_id = ? AND chat_id = ?;", (today,  user_id, chat_id))
            q_result = self.cursor.execute("UPDATE connections SET status = 0 WHERE user_id = ? AND chat_id = ?;", (user_id, chat_id))
            self.connection.commit()
            return True
        except Exception as e:
            raise
    
    def update_user_status(self, user_id: int, status: int = 0) -> bool:
        try:
            q_result = self.cursor.execute("UPDATE users SET status = ? WHERE user_id = ?;", (status, user_id))
            self.connection.commit()
            return True
        except Exception as e:
            raise

    def update_user_in_connection(self, chat_id: int, user_id: int, status: int = 0) -> bool:
        q_result = self.cursor.execute("UPDATE connections SET status = ? WHERE chat_id = ? AND user_id = ?;", (status, chat_id, user_id))
        self.connection.commit()
        return True

    def update_chat(self, chat_id: int, status: int = 0) -> bool:
        q_result = self.cursor.execute("UPDATE chats SET status = ? WHERE chat_id = ?;", (status, chat_id))
        self.connection.commit()
        return True

    def update_chat_members(self, chat_id: int, new_number: int = 0) -> bool:
        q_result = self.cursor.execute("UPDATE chats SET member_count = ? WHERE chat_id = ?;", (new_number, chat_id))
        self.connection.commit()
        return True

    def update_connections_status(self, chat_id: int, status: int = 0) -> bool:
        try:
            if(status == 0): # Bot wants to update chat to "TODAY"
                all_active_today = True
                users = self.return_users_in_connections(chat_id)
                for user_id in users:
                    if(not self.was_active_today(user_id[0])):
                        all_active_today = False
                if(all_active_today):
                    q_result = self.cursor.execute("UPDATE chats SET status = 0 WHERE chat_id = ?;", (chat_id, ))
                    q_result = self.cursor.execute("UPDATE chats SET date_updated = ? WHERE chat_id = ?;", (date.today().strftime('%y%m%d'), chat_id))
                    q_result = self.cursor.execute("UPDATE connections SET status = 0 WHERE chat_id = ?;", (chat_id, ))
                    q_result = self.cursor.execute("UPDATE connections SET date_updated = ? WHERE chat_id = ?;", (date.today().strftime('%y%m%d'), chat_id))
                    self.connection.commit()
                return all_active_today
            else: 
                q_result = self.cursor.execute("UPDATE connections SET status = ? WHERE chat_id = ?;", (status, chat_id))
            self.connection.commit()
            return True
        except Exception as e:
            raise

