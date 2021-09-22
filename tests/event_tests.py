import datetime
import unittest
from pyfix.event import EventManager, TimerEventRegistration


class EventTimerTests(unittest.TestCase):
    def testTimerEvent(self):
        mgr = EventManager()
        endTime = None
        # 如果设置loop.wait超时> 定时器,在定时器超时时间之前就返回.超时器永远没法触发..
        # 表达式  fire 事件 ,closure 2021-09-22 05:36:59.466344
        t1 = TimerEventRegistration(lambda fire,closure:
                                    self.assertEqual(int((datetime.datetime.utcnow() - closure).total_seconds()), 3),
                                    3.0,
                                    datetime.datetime.utcnow())
        print(t1)
        mgr.registerHandler(t1)
        mgr.waitForEventWithTimeout(5.0)

    def testTimerEventReset(self):
        mgr = EventManager()
        t1 = TimerEventRegistration(
            lambda fire, closure: self.assertEqual(int((datetime.datetime.utcnow() - closure).total_seconds()), 2), 1.0,
            datetime.datetime.utcnow())
        mgr.registerHandler(t1)
        mgr.registerHandler(TimerEventRegistration(lambda fire, closure: t1.reset(), 0.9))
        # 相当于执行3次,select,每次都被0.9s定时器中断返回了.
        for i in range(0, 3):
            mgr.waitForEventWithTimeout(10.0)
