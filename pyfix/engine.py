from pyfix.event import EventManager
from pyfix.journaler import Journaler


class FIXEngine(object):
    def __init__(self, journalfile=None):
        self.eventManager = EventManager()
        self.journaller = Journaler(journalfile)
        self.sessions = {}
        # 从sql中读取回话对象.
        # We load all sessions from the journal and add to our list
        for session in self.journaller.sessions():
            self.sessions[session.key] = session

    # 验证会话号是不是允许
    def _validateSession(self, targetCompId, senderCompId):
        # this make any session we receive valid
        return True

    # 恢复发送消息
    def shouldResendMessage(self, session, msg):
        # we should resend all application messages
        return True

    # 创建回话
    def createSession(self, targetCompId, senderCompId):
        if self.findSessionByCompIds(targetCompId, senderCompId) is None:
            session = self.journaller.createSession(targetCompId, senderCompId)
            self.sessions[session.key] = session
        else:
            raise RuntimeError("Failed to add session with duplicate key")
        return session

    # 获取回话 回话key
    def getSession(self, identifier):
        try:
            return self.sessions[identifier]
        except KeyError:
            return None

    # 供内部使用_
    def _findSessionByCompIds(self, targetCompId, senderCompId):
        # 获得数组 [for if]
        sessions = [x for x in self.sessions.values() if
                    x.targetCompId == targetCompId and x.senderCompId == senderCompId]
        if sessions is not None and len(sessions) != 0:
            return sessions[0]
        return None

    def getOrCreateSessionFromCompIds(self, targetCompId, senderCompId):
        # 获取回话
        session = self._findSessionByCompIds(targetCompId, senderCompId)
        if session is None:
            # 没找到回话那么创建...
            if self._validateSession(targetCompId, senderCompId):
                session = self.createSession(targetCompId, senderCompId)
        return session
