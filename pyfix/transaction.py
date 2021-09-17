
class TransactionResource(object):
    def __init__(self, action):
        self.action = action
    #   回调函数...
    def commit(self):
        if self.action != None:
            self.action()

# 事务
class Transaction(TransactionResource):

    def __init__(self):
        self.resources = []
        TransactionResource.__init__(self, None)

    def addResource(self, resource):
        # 添加要参与的事务
        self.resources.append(resource)
        pass

    def commit(self):
        for resource in self.resources:
            resource.commit()
            #  批量提交事务

# 优先级事务 从高到低执行...
class PriorityTransaction(TransactionResource):
    def __init__(self):
        self.resources = []
        TransactionResource.__init__(self, None)

    def addResource(self, resource, priority):
        self.resources.append((priority, resource))

    def commit(self):
        # TODO: sort the resources...
        # High --> Low (so you can always make something higher priority)
        for resource in self.resources:
            resource.commit()
