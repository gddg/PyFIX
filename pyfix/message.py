from collections import OrderedDict
from enum import Enum


# 枚举类型
class MessageDirection(Enum):
    INBOUND = 0
    OUTBOUND = 1


# 组容器
class _FIXRepeatingGroupContainer:
    def __init__(self):
        # 多个组..
        self.groups = []

    def addGroup(self, group, index):
        if index == -1:
            self.groups.append(group)
        else:
            self.groups.insert(index, group)

    def removeGroup(self, index):
        del self.groups[index]

    #  返回整个组..
    def getGroup(self, index):
        return self.groups[index]

    def __str__(self):
        return str(len(self.groups)) + "=>" + str(self.groups)

    __repr__ = __str__


class FIXContext(object):
    def __init__(self):
        # 顺序字典
        self.tags = OrderedDict()

    def setField(self, tag, value):
        self.tags[tag] = value

    def removeField(self, tag):
        try:
            del self.tags[tag]
        except KeyError:
            pass

    def getField(self, tag):
        return self.tags[tag]

    def addRepeatingGroup(self, tag, group, index=-1):
        if tag in self.tags:
            groupContainer = self.tags[tag]
            groupContainer.addGroup(group, index)
        else:
            # 首次添加容器 重复组件..
            groupContainer = _FIXRepeatingGroupContainer()
            groupContainer.addGroup(group, index)
            self.tags[tag] = groupContainer

    # 移除重复tag中..某一个组重复值
    def removeRepeatingGroupByIndex(self, tag, index=-1):
        if self.isRepeatingGroup(tag):
            try:
                if index == -1:
                    del self.tags[tag]
                    pass
                else:
                    groups = self.tags[tag]
                    groups.removeGroup(index)
            except KeyError:
                pass

    # 重复tag,返回(数量,组)
    def getRepeatingGroup(self, tag):
        if self.isRepeatingGroup(tag):
            return (len(self.tags[tag].groups), self.tags[tag].groups)
        return None

    # 在重复组中,找特定tag=特定value,把这个组挑出来.
    def getRepeatingGroupByTag(self, tag, identifierTag, identifierValue):
        if self.isRepeatingGroup(tag):
            for group in self.tags[tag].groups:
                if identifierTag in group.tags:
                    if group.getField(identifierTag) == identifierValue:
                        return group
        return None

    def getRepeatingGroupByIndex(self, tag, index):
        if self.isRepeatingGroup(tag):
            return self.tags[tag].groups[index]
        return None

    # 获取tag对象.
    def __getitem__(self, tag):
        return self.getField(tag)

    # 添加tag 和value
    def __setitem__(self, tag, value):
        self.setField(tag, value)

    # 类型检查..
    def isRepeatingGroup(self, tag):
        return type(self.tags[tag]) is _FIXRepeatingGroupContainer

    # 检查是否包含这个tag
    def __contains__(self, item):
        return item in self.tags

    def __str__(self):
        r = ""
        allTags = []
        for tag in self.tags:
            # 重复tag,有他容器负责str-value
            allTags.append("%s=%s" % (tag, self.tags[tag]))
        r += "|".join(allTags)
        return r

    def __eq__(self, other):
        # if our string representation looks the same, the objects are equivalent
        return self.__str__() == other.__str__()

    __repr__ = __str__


class FIXMessage(FIXContext):
    def __init__(self, msgType):
        self.msgType = msgType
        FIXContext.__init__(self)

    def setMsgType(self, msgType):
        self.msgType = msgType
