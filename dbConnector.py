import psycopg
import datetime

class dbConnector:
    def __init__(self, host, port, dbname, user, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.connect()
        #print("initialized and connected")
    
    def __enter__(self):
        #print('entered')
        return self

    def connect(self):
        self.conn = psycopg.connect("host=" + self.host + " port=" + str(self.port) + " dbname=" + self.dbname + 
                                    " user=" + self.user + " password=" + self.password + " connect_timeout=10")
        self.cur = self.conn.cursor()

    def __del__(self):
        #self.conn.commit()
        #self.cur.close()
        #self.conn.close()
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cur.close()
        self.conn.close()
        #print("exited")
    
    def _executeSelect(self, selectStatement, param):
        self.cur.execute(selectStatement, param)
        return self.cur.fetchall()
    
    def _executeInsert(self, insertSatement, vals):
        self.cur.execute(insertSatement, vals)
        return
    
    def _executeUpdate(self, updateSatement, vals):
        self.cur.execute(updateSatement, vals)
        return


    def _buildSelectStatement(self, columns, table, wheres=[]):
        statement = 'SELECT '
        for col in columns:
            statement += col
            if columns.index(col) == len(columns) - 1:
                statement += ' FROM ' + table
            else:
                statement += ', '
        
        if len(wheres) == 0:
            return statement
        else:
            statement += ' WHERE '
            for w in wheres:
                statement += w + ' = %s'
                if wheres.index(w) != len(wheres) - 1:
                    statement += ' and '
            #print(statement)
            return statement
    
    def _buildInsertSatement(self, columns, table):
        statement = 'INSERT INTO ' + table + '('
        for col in columns:
            statement += col
            if columns.index(col) == len(columns) - 1:
                statement += ') VALUES ('
            else:
                statement += ', '
        
        for col in columns:
            if columns.index(col) == len(columns) - 1:
                statement += '%s)'
            else:
                statement += '%s, '
        
        return statement

    def _buildUpdateSatement(self, columns, table, wheres=[]):
        statement = 'UPDATE ' + table + ' SET '
        for col in columns:
            statement += col
            if columns.index(col) == len(columns) - 1:
                statement += '=%s'
            else:
                statement += '=%s, '
        
        if len(wheres) == 0:
            return statement
        else:
            statement += ' WHERE '
            for w in wheres:
                statement += w + ' = %s'
                if wheres.index(w) != len(wheres) - 1:
                    statement += ' and '
            #print(statement)
            return statement


    def selectWhere(self, columns, table, wheres=[], param=()):
        selStaement = self._buildSelectStatement(columns, table, wheres)
        return self._executeSelect(selStaement, param)

    def insertValues(self, columns, table, values):
        insStatement = self._buildInsertSatement(columns, table)
        self._executeInsert(insStatement, values)
        self.conn.commit()

    def updateValues(self, columns, table, values, wheres=[]):
        updStatement = self._buildUpdateSatement(columns, table, wheres)
        self._executeUpdate(updStatement, values)
        self.conn.commit()
    
    def insert_log(self, level, message):
        """
        Insert a log entry using the sequence directly in the SQL
        """
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        INSERT INTO backup_log (log_id, date_entered, level, message) 
        VALUES (nextval('backup_log_id_seq'), %s, %s, %s)
        """
        self.cur.execute(sql, (current_time, level, message))
        self.conn.commit()



    def close(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()  
    
