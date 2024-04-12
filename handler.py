from datetime import date
import sqlite3, logging

# TODO Method to (1) Count all users (ADMIN)
#                (1) Count all connections (ADMIN)
#                (1) Count all prayers (by status - ADMIN)
#                (1) Create user
#                (1) Create prayer request
#              a (1) Create connection
#                (1) Get list of all late connections
#       a.1, b.1 (1) Update status ANY table
#              b (1) Close connection
#              c (1) Delete users
#         a.0 !! (?) Get two free users or return false

logging.basicConfig(format="PARSER - %(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx")
logger = logging.getLogger(__name__)

class BotParser():
    def __init__(self, DATABASE: str):
        self.ID_COUNTER  = 0
        self.TODAY       = date.today()
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

    def generate_id(self) -> int:
        if(self.TODAY != date.today()):
            self.TODAY = date.today()
            self.ID_COUNTER = 0
        self.ID_COUNTER += 1
        return int(self.TODAY.strftime('%y%m%d') + str(self.ID_COUNTER).zfill(5))

    def number_of_users(self, including_linked = False) -> int:
        query = " WHERE status = 0;"
        q_result = self.cursor.execute("SELECT COUNT(id) FROM users" + (query if including_linked else ";"))
        return q_result.fetchall()[0][0]

    def number_of_connections(self, discriminate = False, desired_status = 0) -> int:
        query = f" AND status = {desired_status};"
        q_result = self.cursor.execute("SELECT COUNT(connection_id) FROM connections WHERE status <> 3" + (query if discriminate else ";"))
        return q_result.fetchall()[0][0]

    #def number_of_prayers(self, including_answered = False) -> int:
    #    query = " WHERE status = 0;"
    #    q_result = self.cursor.execute("SELECT COUNT(id) FROM prayers" + (query if including_answered else ";"))
    #    return q_result.fetchall()[0][0]
    
    def return_connections(self, discriminate = False, desired_status = 0) -> list:
        query = f" AND status = {desired_status};"
        q_result = self.cursor.execute("SELECT * FROM connections WHERE status <> 3" + (query if discriminate else ";"))
        return q_result.fetchall()

    def return_users(self, field: str = 'user_id', discriminate = False, desired_status: int = -1, desired_gender: int = -1) -> list:
        query_status = f" status = {desired_status}"
        query_gender = f" gender = {desired_gender}"
        final_query = " WHERE"
        final_query += query_status if discriminate and desired_status != -1 else ""
        final_query += (" AND" if desired_status != -1 else "") + (query_gender if discriminate and desired_gender != -1 else "")
        q_result = self.cursor.execute("SELECT ? FROM users" + (final_query if discriminate else "") + ";" , (field,))
        q_result = q_result.fetchall()
        return q_result

    def return_users_in_connections(self, chat_id: int) -> list:
        q_result = self.cursor.execute("SELECT user_id FROM connections WHERE chat_id = ?;", (chat_id,))
        q_result = q_result.fetchall()
        return q_result
    
    def return_user_id_from_username(self, username: str) -> int:
        q_result = self.cursor.execute("SELECT user_id FROM users WHERE LOWER(user_name) = LOWER(?);", (username,))
        q_result = q_result.fetchall()
        return q_result[0][0]

    def insert_user(self, user_id: int, user_name: str, gender: int) -> bool:
        try:
            q_result = self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, 0, 0);", (user_id, user_name, self.TODAY.strftime('%y%m%d'), gender))
            self.connection.commit()
            # Confirmation
            q_result = self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?;", (user_id, ))
            if(len(q_result.fetchall()) == 1):
                return True
            return False
        except sqlite3.IntegrityError as e:
            raise
        except TypeError as e:
            logging.error("TypeError found here! Probably trying to fetch users?")
    
    #def insert_prayer(self, telegram_id: int, motive: str, date: str, status: int) -> bool:
    #    q_result        = self.cursor.execute("INSERT INTO prayers VALUES (?, ?, ?, ?, ?);", (self.generate_id(), telegram_id, motive, date, status))
    #    current_prayers = self.cursor.execute("SELECT COUNT(id) FROM prayers WHERE id_person = ?;", (telegram_id, ))
    #    current_prayers = current_prayers.fetchall()
    #    self.connection.commit()
    #    q_result        = self.cursor.execute("SELECT COUNT(id) FROM prayers WHERE id_person = ?;", (telegram_id, ))
    #    q_result        = q_result.fetchall()
    #    if(q_result[0][0] == current_prayers[0][0]):
    #        return True
    #    return False
    
    def insert_connection(self, user_id: int, chat_id: int) -> list:
        user_id_pair = self.find_pair_for(user_id)
        if(self.is_free(user_id) and user_id_pair):
            logging.info("Pair found!")
            self.cursor.execute("INSERT INTO chats VALUES (?, ?, ?)", (chat_id, self.TODAY.strftime('%Y-%m-%d'), 1))
            self.cursor.execute("INSERT INTO connections (chat_id, user_id, date_creation, date_updated, status) VALUES (?, ?, ?, ?, ?);", (chat_id, user_id, self.TODAY.strftime('%Y-%m-%d'), self.TODAY.strftime('%Y-%m-%d'), 1))
            self.cursor.execute("INSERT INTO connections (chat_id, user_id, date_creation, date_updated, status) VALUES (?, ?, ?, ?, ?);", (chat_id, user_id_pair, self.TODAY.strftime('%Y-%m-%d'), self.TODAY.strftime('%Y-%m-%d'), 1))
            self.update_user_status(user_id, 1)
            self.update_user_status(user_id_pair, 1)
            self.connection.commit()
            return [chat_id, user_id, user_id_pair]
        logging.info("Couldn't find pair, returning None")
        return None
    
    #def connect(self, chat_id: int, telegram_id_second: int) -> bool:
    #    self.cursor.execute("UPDATE connections SET id_person_second = ? WHERE id = ?;", (telegram_id_second, chat_id))
    #    self.connection.commit()
    #    return True
    
    def find_pair_for(self, telegram_id_to_discriminate: int):
        q_result = self.cursor.execute("SELECT user_id, user_name FROM users WHERE status = 0 AND user_id <> ? AND gender = (SELECT gender FROM users WHERE user_id = ?);", (telegram_id_to_discriminate, telegram_id_to_discriminate))
        q_result = q_result.fetchall()
        logging.info(q_result)
        return q_result if len(q_result) else 0
     
    def is_user(self, user_id: int) -> bool:
        q_result = self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?;", (user_id,))
        q_result = q_result.fetchall()
        return 1 if len(q_result) else 0
    
    def is_free(self, user_id: int) -> bool:
        q_result = self.cursor.execute("SELECT status FROM users WHERE user_id = ?;", (user_id,))
        q_result = q_result.fetchall()
        if(int(q_result[0][0]) == 0):
            return 1
        return 0

    def was_active_today(self, user_id: int) -> bool:
        q_result = self.cursor.execute("SELECT date_updated FROM connections WHERE user_id = ?;", (user_id,))
        q_result = q_result.fetchall()
        for row in q_result:
            if(row[0] == self.TODAY.strftime('%Y-%m-%d')):
                return True
        return False
    
    def update_user_activeness_today(self, user_id: int, chat_id: int) -> bool:
        try:
            today = self.TODAY.strftime('%Y-%m-%d')
            q_result = self.cursor.execute("UPDATE connections SET date_updated = ? WHERE user_id = ? AND chat_id = ?;", (today,  user_id, chat_id))
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
                    q_result = self.cursor.execute("UPDATE connections SET status = 0 WHERE chat_id = ?;", (chat_id, ))
                    q_result = self.cursor.execute("UPDATE connections SET date_updated = ? WHERE chat_id = ?;", (self.TODAY.strftime('%y%m%d'), chat_id))
                    self.connection.commit()
                return all_active_today
            else: 
                q_result = self.cursor.execute("UPDATE connections SET status = ? WHERE chat_id = ?;", (status, chat_id))
            self.connection.commit()
            return True
        except Exception as e:
            raise

    #def update_connections_id(self, old_id: int, group_chat_id: int) -> bool:
    #    try:
    #        q_result = self.cursor.execute("UPDATE connections SET id = ? WHERE id = ?;", (group_chat_id, old_id))
    #        self.connection.commit()
    #        return True
    #    except Exception as e:
    #        raise
 
