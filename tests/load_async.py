import unittest
import webtest
import threading
import app_frontend
import backend
import frontend
import frontend.session
import common.base
import frontend.submission_manager
import Queue
from tests import *
import time
import json
import uuid

class AsyncSubmitter(threading.Thread):
    """ Launch a sync submission """

    def __init__(self, queue, tid):
        threading.Thread.__init__(self)
        self.queue = queue
        self.tid = tid
    
    def assertion(self, stmtstr, stmt):
        self.queue.put((stmtstr, stmt))
    
    def run(self):
        print "\033[1;34m--> STARTING THREAD " + str(self.tid) + "\033[0m"
        t0 = time.time()
        
        resp = appt.post('/course/test/task1', {"@action":"submit", "unittest/decimal": "2"})
        print resp.body
        js = json.loads(resp.body)
        assert "status" in js and "submissionid" in js and js["status"] == "ok"
        sub_id = js["submissionid"]
        
        for tries in range(0, 100):
            time.sleep(1)
            resp = appt.post('/course/test/task1', {"@action":"check", "submissionid":sub_id})
            js = json.loads(resp.body)
            assert "status" in js and "status" != "error"
            if js["status"] == "done":
                self.assertion('"result" in js and js["result"] != "error"', "result" in js and js["result"] != "error")
                break
        
        t1 = time.time() - t0
        print "\033[1;34m--> FINISHING THREAD " + str(self.tid) + " in " + str(t1) + "seconds\033[0m"

class Watcher(threading.Thread):
    """ Launch a sync submission """

    def __init__(self):
        threading.Thread.__init__(self)
        self.cont = True
    
    def stop(self):
        self.cont = False
    
    def run(self):
        while self.cont:
            resp = appt.get('/tests/stats')
            print "\033[1;33m--> Waiting jobs : " + resp.body +  "\033[0m"
            time.sleep(1)

class load_async(unittest.TestCase):
    def setUp(self):
        frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
        self.jm = frontend.submission_manager.get_job_manager()
        self.queue = Queue.Queue()
        self.thqueue = Queue.Queue()
        
    def test_async_load(self):
        '''Tests some number of task launching'''
        print "\033[1m-> load-sync: lot of async submissions\033[0m"
        
        # Start resource watcher
        watchth = Watcher()
        watchth.start()
        
        # Launch threads
        for x in range(0, 10):
            th = AsyncSubmitter(self.queue, x)
            self.thqueue.put(th)
            th.start()
        
        # Join threads
        while not self.thqueue.empty():
            item = self.thqueue.get()
            item.join()
        
        # Stop resource watcher
        watchth.stop()
        watchth.join()
          
    def tearDown(self):
        while not self.queue.empty():
            item = self.queue.get()
            assert item[1], item[1]

if __name__ == "__main__":
    unittest.main()
