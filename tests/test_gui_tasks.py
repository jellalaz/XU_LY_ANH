"""Test GUI job lifecycle without opening a desktop window."""
import queue
import time
import unittest
from morpholab.gui import App
from morpholab.tasks import check_cancelled


class Widget:
    def configure(self,**kwargs): pass
    def set(self,value): self.value=value
    def after(self,*args): pass
    def destroy(self): self.destroyed=True


class GuiTasksTest(unittest.TestCase):
    def app(self):
        app=App.__new__(App)
        app.root=Widget(); app.root.destroyed=False
        app.status=Widget(); app.stop_button=Widget(); app.actions=[Widget()]
        app.events=queue.Queue(); app.busy=False; app.closing=False
        app.worker=None; app.token=None
        return app

    def test_result_returns_through_main_thread_poll(self):
        app=self.app(); values=[]
        app.job(lambda:42,values.append,'testing')
        app.worker.join(2); app.poll()
        self.assertEqual(values,[42]); self.assertFalse(app.busy)

    def test_close_cancels_worker_and_suppresses_callback(self):
        app=self.app(); values=[]
        def work():
            for _ in range(1000): check_cancelled(); time.sleep(.005)
            return 42
        app.job(work,values.append,'testing')
        app.close(); app.worker.join(2); app.poll()
        self.assertFalse(app.worker.is_alive())
        self.assertTrue(app.root.destroyed)
        self.assertEqual(values,[])


if __name__=='__main__': unittest.main()
