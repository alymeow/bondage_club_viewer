import hashlib
import json
import os
import sqlite3

from tqdm import tqdm


class bc_logs:
    flag_debug = False
    flag_skip_on_same_message = False
    db_file = './instance/logs.db'
    db_memory = False

    sql_insert_logs = None

    def __init__(self, database=None, use_memory=False):
        if database:
            self.db_file = database

        print('loading database:', self.db_file)
        if use_memory:
            print("db memory load.")
            self.db_memory = True

            self._conn = sqlite3.connect(":memory:")
            self._cursor = self._conn.cursor()

            disk_db = sqlite3.connect(self.db_file)
            query = "".join(line for line in disk_db.iterdump())
            self._conn.executescript(query)
            disk_db.close()

        else:
            self._conn = sqlite3.connect(self.db_file)
            self._cursor = self._conn.cursor()

        print('db loaded')

    def db_save(self):
        if not self.db_memory:
            return

        print('db write disk')
        self._cursor.close()
        query = "".join(line for line in self._conn.iterdump())

        disk_db = sqlite3.connect(self.db_file)
        disk_db.executescript(query)
        disk_db.close()

        self._cursor = self._conn.cursor()

    def close_conn(self):
        self.db_save()
        self._cursor.close()
        self._conn.close()

    def db_execute(self, sql: str, value: tuple):
        try:
            self._cursor.execute(sql, value)
            self._conn.commit()
            if 'INSERT' in sql.upper():
                if self.flag_debug:
                    print("[insert 1 record success]")
            if 'UPDATE' in sql.upper():
                if self.flag_debug:
                    print("[update 1 record success]")
            return True
        except Exception as e:
            print("[insert/update 1 record error]", e)
            self._conn.rollback()
            return False

    def db_execute_many(self, sql: str, value: list):
        try:
            self._cursor.executemany(sql, value)
            self._conn.commit()
            if 'INSERT' in sql.upper():
                if self.flag_debug:
                    print("[insert many  records success]")
            if 'UPDATE' in sql.upper():
                if self.flag_debug:
                    print("[update many  records success]")
            return True
        except Exception as e:
            print("[insert/update many records error]", e)
            self._conn.rollback()
            return False

    def db_query_one(self, sql: str, params=None):
        try:
            if params:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)
            r = self._cursor.fetchone()
            if self.flag_debug:
                print("[select 1 record success]")
            return r
        except Exception as e:
            print("[select 1 record error]")

    def db_query_all(self, sql: str, params=None):
        try:
            if params:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)
            r = self._cursor.fetchall()
            print("[select all record success]")
            return r
        except Exception as e:
            print("[select all record error]")

    def db_set_user(self, id, name, color):
        user_data = self.db_get_user(id)
        if user_data:
            if user_data['name'] == name and user_data['color'] == color:
                return True

            sql = "UPDATE users SET name = ?, color = ? WHERE id = ?"
            return self.db_execute(sql, (name, color, id))

        else:
            sql = 'INSERT INTO users (id, name, color) VALUES (?, ?, ?)'
            return self.db_execute(sql, (id, name, color))

    def db_get_user(self, id):
        sql = 'SELECT * FROM users WHERE id = ?'
        ret = self.db_query_one(sql, (id,))
        if ret:
            return {'id': ret[0], 'name': ret[1], 'color': ret[2]}

        else:
            if self.flag_debug:
                print('[user not found]')
            return None

    def db_logs_get_hash(self, hash):
        sql = 'SELECT * FROM logs WHERE hash = ?'
        ret = self.db_query_one(sql, (hash,))
        if ret:
            return ret
        else:
            if self.flag_debug:
                print('[message not found]')
            return None

    def db_logs_insert_many(self, logs_data: list):
        tmp = []
        hash_list = []
        for data in logs_data:
            jstr = json.dumps(data, ensure_ascii=False)
            jhash = hashlib.md5(jstr.encode('utf-8', errors='ignore')).hexdigest()

            if jhash in hash_list:
                continue
            elif self.db_logs_get_hash(jhash):
                if self.flag_debug:
                    print('[message exists]', jstr)
                continue
            else:
                hash_list.append(jhash)

            target = None
            if 'target' in data.keys():
                target = data['target']

            tmp.append((data['chat_room'], data['session_id'], data['sender'], target,
                        data['content'], data['timestamp'], data['type'], jstr, jhash))

        sql = 'INSERT INTO logs (chat_room, session, sender, target, content, timestamp, type, json, hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        ret = self.db_execute_many(sql, tmp)
        if ret:
            if len(tmp) != len(logs_data):
                print('write {} records from {} logs'.format(len(tmp), len(logs_data)))
            return True
        else:
            print('write many logs failed')
            return False

    def process(self, json_file):
        with open(json_file, errors='ignore') as f:
            json_data = json.load(f)

            logs_data = []
            for line in json_data:
                if self.flag_debug:
                    for key, value in line.items():
                        print(key, '\t', value)

                data = {}

                for key, value in line.items():
                    if key == 'chatRoom':
                        data['chat_room'] = value

                    elif key == 'content':
                        data['content'] = value

                    elif key == 'sender':
                        if 'color' not in value.keys():
                            value['color'] = None
                        # usr = {'id': value['id'], 'name':value['name'], 'color':None}
                        # if 'color' in value.keys():
                        #     usr['color'] = value['color']
                        self.db_set_user(value['id'], value['name'], value['color'])
                        data['sender'] = value['id']

                    elif key == 'session':
                        data['session_id'] = value['id']

                    elif key == 'timestamp':
                        data['timestamp'] = value

                    elif key == 'type':
                        data['type'] = value

                    elif key == 'dictionary':
                        # print(value) # ignore
                        data['dictionary'] = value

                    elif key == 'characters':
                        # print(value) # ignore
                        data['characters'] = value

                    elif key == 'target':
                        data['target'] = json.dumps(value, ensure_ascii=False)

                    else:
                        print('[warning] unknown key {}'.format(key), line)
                        exit(-1)

                logs_data.append(data)

            return self.db_logs_insert_many(logs_data)


def import_logs(dir, db):
    tool = bc_logs(use_memory=False, database=db)
    for root, dirs, files in os.walk(dir):
        json_files = []
        for file in files:
            if file.split('.')[-1].lower() == 'json':
                json_files.append(file)

        if len(json_files) == 0:
            continue

        with tqdm(json_files) as tq:
            for file in tq:
                json_file = os.path.join(root, file)
                tq.set_description(json_file)
                success = tool.process(json_file)
                if success:
                    json_file_bak = os.path.join(root, file + '.bak')
                    os.rename(json_file, json_file_bak)
                else:
                    print("process failed:", json_file)

    tool.close_conn()
    print('finish')


# 用于恢复bak文件
def rename_bak(dir):
    for root, dirs, files in os.walk(dir):
        for file in files:
            if 'json.bak' in file:
                src = os.path.join(root, file)
                tgt = src.replace('json.bak', 'json')
                os.rename(src, tgt)
                print("rename:", src)


if __name__ == '__main__':
    dir = './import_logs'
    try:
        import_logs(dir=dir, db='instance/logs.db')
    except:
        rename_bak(dir=dir)
