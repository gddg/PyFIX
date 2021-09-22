from enum import Enum
import datetime
import os
from select import select, error
import errno
import time


class EventType(Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    TIMEOUT = 4
    READWRITE = READ | WRITE


class EventRegistration(object):
    def __init__(self, callback, closure=None):
        self.callback = callback  # 回调函数..
        self.closure = closure  # 回调参数,当时环境..


# 时间类型注册器
class TimerEventRegistration(EventRegistration):
    # 内部类
    class TimeoutState(Enum):
        NONE = 0
        START = 1
        PROGRESS = 2

    def __init__(self, callback, timeout, closure=None):
        EventRegistration.__init__(self, callback, closure)
        print("callback",callback)
        print("closure",closure)
        self.timeout = timeout
        self.timeoutState = TimerEventRegistration.TimeoutState.START
        self.timeLeft = timeout  # 约定时间
        self.lastTime = None

    def reset(self):
        self.timeLeft = self.timeout
        # 重置超时时间,可能已经过了一段时间了,重新设置初始化时候的超时时间.

    def __str__(self):
        return "TimerEvent interval: %s, remaining: %s" % (self.timeout, self.timeLeft)


# 文件描述符事件 socket/udp/file
class FileDescriptorEventRegistration(EventRegistration):
    def __init__(self, callback, fileDescriptor, eventType, closure=None):
        EventRegistration.__init__(self, callback, closure)
        self.fd = fileDescriptor
        self.eventType = eventType

    def __str__(self):
        return "FileDescriptorEvent fd: %s, type: %s" % (self.fd, self.eventType.name)


class _Event(object):
    def __init__(self, fd, filter):
        self.fd = fd  #
        self.filter = filter  # EventType事件类型


# 抽象类
class EventLoop(object):
    def add(self, event):
        pass

    def remove(self, event):
        pass

    def run(self, timeout):
        pass


# select模型,循环
class SelectEventLoop(EventLoop):
    def __init__(self):
        self.readSet = []
        self.writeSet = []

    def add(self, event):
        if (event.filter.value & EventType.READ.value) == EventType.READ.value:
            self.readSet.append(event.fd)
        if (event.filter.value & EventType.WRITE.value) == EventType.WRITE.value:
            self.writeSet.append(event.fd)

    def remove(self, event):
        if event.filter.value & EventType.READ.value == EventType.READ.value:
            self.readSet.remove(event.fd)
        if event.filter.value & EventType.WRITE.value == EventType.WRITE.value:
            self.writeSet.remove(event.fd)

    # 返回event[] (fd,事件)
    def run(self, timeout):
        # 如果什么事情都没有,就睡到时间返回空
        if len(self.readSet) == 0 and len(self.writeSet) == 0:
            time.sleep(timeout)
            return []
        else:
            while True:
                try:
                    readReady, writeReady, exceptReady = select(self.readSet, self.writeSet, [], timeout)
                    events = []
                    # 读取输出事件
                    for r in readReady:
                        events.append(_Event(r, EventType.READ))
                    for r in writeReady:
                        events.append(_Event(r, EventType.WRITE))
                    return events
                except error as why:
                    if os.name == 'posix':
                        if why[0] != errno.EAGAIN and why[0] != errno.EINTR:
                            # 这2个事件可以恢复,其他不可以.
                            break
                    else:
                        if why[0] == errno.WSAEADDRINUSE:
                            break


class EventManager(object):
    def __init__(self):
        self.eventLoop = SelectEventLoop()
        self.handlers = []

    def waitForEvent(self):
        self.waitForEventWithTimeout(None)

    # 多久后叫醒循环...
    def waitForEventWithTimeout(self, timeout):
        if not self.handlers:
            raise RuntimeError("Failed to start event loop without any handlers")
        # 找时间定时器,最近唤醒时间
        timeout = self._setTimeout(timeout)
        # 走loop,唤醒的event
        events = self.eventLoop.run(timeout)
        self._serviceEvents(events)

    def _setTimeout(self, timeout):
        nowTime = datetime.datetime.utcnow()
        duration = timeout

        for handler in self.handlers:
            # 遍历时间handle,如果是start状态,那么改为进行状态..
            if type(handler) is TimerEventRegistration:
                if handler.timeoutState == TimerEventRegistration.TimeoutState.START:
                    handler.timeoutState = TimerEventRegistration.TimeoutState.PROGRESS
                # 更新一下句柄=最近的时间
                handler.lastTime = nowTime
                # 找到句柄的剩余时间比较短,反馈这个时间给select,唤醒.
                if duration is None or handler.timeLeft < duration:
                    duration = handler.timeLeft
        return duration

    def _serviceEvents(self, events):
        nowTime = datetime.datetime.utcnow()
        for handler in self.handlers:
            if isinstance(handler, FileDescriptorEventRegistration):
                for event in events:
                    if event.fd == handler.fd:
                        # handle*event. handle 关注事件和发生事件
                        type = handler.eventType.value & event.filter.value
                        if type != EventType.NONE:
                            handler.callback(type, handler.closure)
            elif isinstance(handler, TimerEventRegistration):
                if handler.timeoutState == TimerEventRegistration.TimeoutState.PROGRESS:
                    elapsedTime = nowTime - handler.lastTime
                    handler.timeLeft -= elapsedTime.total_seconds()  # timeout-elapsed
                    # 计算是否超时timeout.  引发时间事件..
                    if handler.timeLeft <= 0.0:
                        handler.timeLeft = handler.timeout
                        handler.callback(EventType.TIMEOUT, handler.closure)
                        print("TimeOut...这里超时器不删除..%s"%handler)

    # [外部调用]注册句柄...
    def registerHandler(self, handler):
        if isinstance(handler, TimerEventRegistration):
            pass
            # 时间事件没有句柄..
        elif isinstance(handler, FileDescriptorEventRegistration):
            # fd添加关注读和写..
            self.eventLoop.add(_Event(handler.fd, handler.eventType))
        else:
            raise RuntimeError("Trying to register invalid handler")
        # 追加到总handle
        self.handlers.append(handler)

    # [外部调用]移除句柄...
    def unregisterHandler(self, handler):
        if self.isRegistered(handler):
            self.handlers.remove(handler)  # 容器中移除
            if isinstance(handler, FileDescriptorEventRegistration):
                self.eventLoop.remove(_Event(handler.fd, handler.eventType))

    def isRegistered(self, handler):
        # 遍历handle 是否在这里面.
        return handler in self.handlers
