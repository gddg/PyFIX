import logging

class FIXSession:
    def __init__(self, key, targetCompId, senderCompId):
        self.key = key
        self.senderCompId = senderCompId
        self.targetCompId = targetCompId

        self.sndSeqNum = 0
        self.nextExpectedMsgSeqNum = 1
    '''验证对手方'''
    def validateCompIds(self, targetCompId, senderCompId):
        return self.senderCompId == senderCompId and self.targetCompId == targetCompId

    '''获取新序号'''
    def allocateSndSeqNo(self):
        self.sndSeqNum += 1
        return str(self.sndSeqNum)

    '''验证收到的序号'''
    def validateRecvSeqNo(self, seqNo):
        if self.nextExpectedMsgSeqNum < int(seqNo):
            logging.warning("SeqNum from client unexpected (Rcvd: %s Expected: %s)" % (seqNo, self.nextExpectedMsgSeqNum))
            return (False, self.nextExpectedMsgSeqNum)
        else:
            return (True, seqNo)

    '''设置下一个序号,为后续验证做准备'''
    def setRecvSeqNo(self, seqNo):
        # if self.nextExpectedMsgSeqNum != int(seqNo):
        #     logging.warning("SeqNum from client unexpected (Rcvd: %s Expected: %s)" % (seqNo, self.nextExpectedMsgSeqNum))
        self.nextExpectedMsgSeqNum = int(seqNo) + 1

