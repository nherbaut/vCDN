import sqlite3
import pickle
import time
import os
RESULTS_PATH=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../results')
class DAO:
    class __DAO:
        def __init__(self):
            conn = sqlite3.connect(os.path.join(RESULTS_PATH,'service-mapping.db'))
            #conn.execute('''DROP TABLE IF EXISTS smap''')
            conn.execute('''CREATE TABLE IF NOT EXISTS smap  (start text, end text, service blob, mapping BLOB)''')
            conn.commit()
            conn.close()

        def __str__(self):
            return repr(self)


        def save(self,service,mapping):
            conn = sqlite3.connect(os.path.join(RESULTS_PATH,'service-mapping.db'))
            conn.execute('''insert into smap values (:start,:end,:service,:mapping);''', (time.time(),time.time(),sqlite3.Binary(pickle.dumps(service)),sqlite3.Binary(pickle.dumps(mapping))))
            conn.commit()
            conn.close()

        def findall(self):
            res=[]
            conn = sqlite3.connect(os.path.join(RESULTS_PATH,'service-mapping.db'))
            curr = conn.execute('''SELECT * FROM smap''')
            for start,end,service,mapping in curr.fetchall():
                service=pickle.loads(str(service))
                mapping=pickle.loads(str(mapping))
                res.append((start,end,service,mapping))


            conn.close()
            return res



    instance = None

    def __init__(self,):
        if not DAO.instance:
            DAO.instance = DAO.__DAO()

    def __getattr__(self, name):
        return getattr(self.instance, name)


    def save(self,service,mapping):
        DAO.instance.save(service,mapping)


    def findall(self):
        return DAO.instance.findall()


