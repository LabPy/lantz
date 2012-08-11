
import logging
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
import collections

from ..log import get_logger

logger = get_logger(__name__)


MessageRole = Qt.UserRole
invindex = QtCore.QModelIndex()

from ..log import SocketListener

class LoggerModel(QtCore.QAbstractItemModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._root = TreeNode(None, '')
        self._registry = {
            '': self._root,
            }

    def columnCount(self, parent):
        return 1

    def index(self, row, column, parent):
        try:
            if not parent.isValid():
                #logger.debug('creating root index')
                result = self.createIndex(row, column, self._root)
            else:
                node = parent.internalPointer()
                #logger.debug('creating index for %r', node.path)
                result = self.createIndex(row, column, node.children[row])
        except IndexError:
            result = invindex
        return result

    def parent(self, index):
        result = invindex
        if index.isValid():
            node = index.internalPointer()
            if node.parent is not None:
                result = self.createIndex(node.parent.row, 0, node.parent)
        return result

    def rowCount(self, parent):
        if not parent.isValid():
            result = 1
        else:
            node = parent.internalPointer()
            result = len(node.children)
        return result

    def data(self, index, role=Qt.DisplayRole):
        result = None
        if index.isValid():
            node = index.internalPointer()
            if role == Qt.DisplayRole:
                try:
                    result = node.name
                    if not node.parent:
                        result = 'Root logger'
                except Exception:
                    pass
            elif role == Qt.ToolTipRole:
                result = node.path
        return result

    def headerData(self, section, orientation, role):
        result = None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            result = 'Logger name'
        return result

    def register_logger(self, name):
        if name in self._registry:
            result = self._registry[name]
        else:
            parts = name.rsplit('.', 1)
            nodename = parts[-1]
            if len(parts) == 1:
                parent = self._root
            else:
                parent = self.register_logger(parts[0])
            pindex = self.createIndex(0, 0, parent)
            names = [c.name for c in parent.children]
            pos = bisect.bisect(names, nodename)
            result = TreeNode(parent, nodename)
            self._registry[name] = result
            self.beginInsertRows(pindex, pos, pos)
            parent.children.insert(pos, result)
            self.endInsertRows()
        return result

    def clear(self):
        self._registry = {}
        self._root.children = []
        self.reset()

class Column(object):
    def __init__(self, name, title, visible=True):
        self.name = name
        self.title = title
        self.visible = visible

class LogRecordModel(QtCore.QAbstractTableModel):

    foreground_map = {
        logging.ERROR: QtGui.QColor(255, 0, 0),
        logging.CRITICAL: QtGui.QColor(255, 255, 255),
        }

    background_map = {
        logging.DEBUG: QtGui.QColor(192, 255, 255),
        logging.WARNING: QtGui.QColor(255, 255, 192),
        #logging.ERROR: QtGui.QColor(255, 192, 192),
        logging.CRITICAL: QtGui.QColor(255, 0, 0),
        }

    style_map = {
        logging.ERROR: 'bold',
        logging.CRITICAL: 'bold',
        }

    def __init__(self, parent, records, columns, capacity=0):
        super().__init__()
        self._records = records
        self._columns = columns
        self.font = parent.font()
        self._capacity = capacity

    def columnCount(self, index):
        if index.isValid():
            result = 0
        else:
            visible = [col for col in self._columns if col.visible]
            result = len(visible)
        return result

    def rowCount(self, index):
        if self._records is None or index.isValid():
            result = 0
        else:
            result = len(self._records)
        return result

    def data(self, index, role=Qt.DisplayRole):
        result = None
        if index.isValid():
            record = self._records[index.row()]
            if role == Qt.DisplayRole:
                try:
                    viscols = [c for c in self._columns if c.visible]
                    col = viscols[index.column()]
                    try:
                        v = getattr(record, col.name)
                    except AttributeError as e:
                        try:
                            v = ("%(" + col.name + ")s") % record
                        except:
                            v = "AttributeError: " + col.name
                    result = v
                except Exception as e:
                    logger.exception('Error: {}', e)
            elif role == Qt.BackgroundColorRole:
                result = self.background_map.get(record.levelno)
            elif role == Qt.TextColorRole:
                result = self.foreground_map.get(record.levelno)
            elif role == Qt.FontRole:
                QFont = QtGui.QFont
                result = None
                style = self.style_map.get(record.levelno)
                if style:
                    result = QFont(self.font)
                    if 'bold' in style:
                        result.setWeight(QFont.Bold)
                    if 'italic' in style:
                        result.setStyle(QFont.StyleItalic)
            elif role == MessageRole: # special role used for searching
                result = record.message
        return result

    def headerData(self, section, orientation, role):
        result = None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                visible = [col.title for col in self._columns if col.visible]
                result = visible[section]
            except IndexError:
                pass
        return result

    def add_record(self, record):
        pos = len(self._records)
        if self._capacity and pos >= self._capacity:
            self.beginRemoveRows(invindex, 0, 0)
            self._records.popleft()
            self.endRemoveRows()
            pos -= 1
        self.beginInsertRows(invindex, pos, pos)
        self._records.append(record)
        self.endInsertRows()

    def clear(self):
        if hasattr(self._records, 'clear'):
            self._records.clear()
        else:
            del self._records[:]
        self.reset()

    def get_record(self, pos):
        return self._records[pos]

class BaseTable(QtGui.QTableView):
    def __init__(self, parent):
        super().__init__(parent)
        self._context_items = []
        self.setupUi(self)

    def setupUi(self, w):
        pass

    @property
    def context_actions(self):
        return self._context_items

    def contextMenuEvent(self, event):
        actions = list(self.context_actions)
        if actions:
            menu = QtGui.QMenu(self)
            for action_or_menu in actions:
                if isinstance(action_or_menu, QtGui.QAction):
                    menu.addAction(action_or_menu)
                else:
                    menu.addMenu(action_or_menu)
            menu.exec_(event.globalPos())

class MasterTable(BaseTable):
    def setupUi(self, w):
        super().setupUi(w)
        self.action_cols = action = QtGui.QAction("&Columns", self)
        self._context_items.append(action)

class DetailTable(BaseTable):
    pass

class LoggerTree(QtGui.QTreeView):
    def contextMenuEvent(self, event):
        logger.debug('tree context event')

class LogTable(SocketListener):

    DEFAULT_COLUMNS = [
        Column('asctime', 'Creation time'),
        Column('name', 'Logger name'),
        Column('levelname', 'Level'),
        Column('msg', 'Message'),
        Column('funcName', 'Function', False),
        Column('pathname', 'Path name', False),
        Column('filename', 'File name', False),
        Column('lineno', 'Line no.', True),
        Column('module', 'Module', False),
        Column('process', 'Process ID', False),
        Column('processName', 'Process name', False),
        Column('thread', 'Thread ID', False),
        Column('threadName', 'Thread name', False),
        ]

    def __init__(self, parent, tcphost='0.0.0.0', udphost='0.0.0.0'):
        super().__init__(tcphost, udphost)
        self.master = MasterTable(parent)
        self.master.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.master.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.master.setObjectName("master")

        self.records = collections.deque()
        self.columns = self.DEFAULT_COLUMNS
        self.lmodel = LogRecordModel(parent, self.records, self.columns, 0)
        self.master.setModel(self.lmodel)

    def get_table(self):
        return self.master

    def process_record(self, record):
        self.lmodel.add_record(record)

    def on_record(self, record):
        self._lock.acquire()
        try:
            self.process_record(record)
        finally:
            self._lock.release()
