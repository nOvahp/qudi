# -*- coding: utf-8 -*-
"""
This file contains the Qudi thread manager class.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

from qtpy import QtCore
from .util.mutex import RecursiveMutex
from functools import partial
import logging
logger = logging.getLogger(__name__)


class ThreadManager(QtCore.QAbstractTableModel):
    """ This class keeps track of all the QThreads that are needed somewhere. The registered
    threads are stored in a static variable and thus are shared across all instances of this class.

    Using this class is thread-safe.
    """

    _lock = RecursiveMutex()
    _threads = list()
    _thread_names = list()

    @property
    def thread_names(self):
        with self._lock:
            return self._thread_names.copy()

    def get_new_thread(self, name):
        """ Create and return a new QThread with objectName <name>

        @param str name: unique name of thread

        @return QThread: new thread, none if failed
        """
        with self._lock:
            logger.debug('Creating thread: "{0}".'.format(name))
            if name in self._thread_names:
                return None
            thread = QtCore.QThread()
            thread.setObjectName(name)
            self.register_thread(thread)
        return thread

    @QtCore.Slot(QtCore.QThread)
    def register_thread(self, thread):
        """ Add QThread to ThreadManager.

        @param QtCore.QThread thread: thread to register with unique objectName
        """
        with self._lock:
            name = thread.objectName()
            if name in self._thread_names:
                if self.get_thread_by_name(name) is thread:
                    return None
                raise Exception('Different thread with name "{0}" already registered in '
                                'ThreadManager'.format(name))

            row = len(self._threads)
            self.beginInsertRows(QtCore.QModelIndex(), row, row)
            self._threads.append(thread)
            self._thread_names.append(name)
            thread.finished.connect(
                partial(self.unregister_thread, name=name), QtCore.Qt.QueuedConnection)
            self.endInsertRows()

    @QtCore.Slot(str)
    @QtCore.Slot(QtCore.QThread)
    def unregister_thread(self, name):
        """ Remove thread from ThreadManager.

        @param str name: unique thread name
        """
        with self._lock:
            if isinstance(name, QtCore.QThread):
                name = name.objectName()
            if name in self._thread_names:
                index = self._thread_names.index(name)
                if self._threads[index].isRunning():
                    self.quit_thread(name)
                    return
                logger.debug('Cleaning up thread {0}.'.format(name))
                self.beginRemoveRows(QtCore.QModelIndex(), index, index)
                del self._threads[index]
                del self._thread_names[index]
                self.endRemoveRows()

    @QtCore.Slot(str)
    @QtCore.Slot(QtCore.QThread)
    def quit_thread(self, name):
        """ Stop event loop of QThread.

        @param str name: unique thread name
        """
        with self._lock:
            if isinstance(name, QtCore.QThread):
                thread = name
            else:
                thread = self.get_thread_by_name(name)
            if thread is None:
                logger.debug('You tried quitting a nonexistent thread {0}.'.format(name))
            else:
                logger.debug('Quitting thread {0}.'.format(name))
                thread.quit()

    @QtCore.Slot(str)
    @QtCore.Slot(str, int)
    @QtCore.Slot(QtCore.QThread)
    @QtCore.Slot(QtCore.QThread, int)
    def join_thread(self, name, time=None):
        """ Wait for stop of QThread event loop.

        @param str name: unique thread name
        @param int time: timeout for waiting in msec
        """
        with self._lock:
            if isinstance(name, QtCore.QThread):
                thread = name
            else:
                thread = self.get_thread_by_name(name)
            if thread is None:
                logger.debug('You tried waiting for a nonexistent thread {0}.'.format(name))
            else:
                logger.debug('Waiting for thread {0} to end.'.format(name))
                if time is None:
                    thread.wait()
                else:
                    thread.wait(time)

    @QtCore.Slot()
    @QtCore.Slot(int)
    def quit_all_threads(self, thread_timeout=10000):
        """ Stop event loop of all QThreads.
        """
        with self._lock:
            logger.debug('Quit all threads.')
            for thread in self._threads:
                thread.quit()
                if not thread.wait(int(thread_timeout)):
                    logger.error('Waiting for thread {0} timed out.'.format(thread.objectName()))

    @classmethod
    def get_thread_by_name(cls, name):
        """ Get registered QThread instance by its objectName

        @param str name: objectName of the QThread to return
        @return QThread: The registered thread object
        """
        with cls._lock:
            if name in cls._thread_names:
                index = cls._thread_names.index(name)
                return cls._threads[index]
            return None

    # QAbstractTableModel interface methods follow below
    def rowCount(self, parent=None):
        """
        Gives the number of threads registered.

        @return int: number of threads
        """
        with self._lock:
            return len(self._threads)

    def columnCount(self, parent=None):
        """
        Gives the number of data fields of a thread.

        @return int: number of thread data fields
        """
        return 2

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        Data for the table view headers.

        @param int section: column/row index to get header data for
        @param QtCore.Qt.Orientation orientation: orientation of header (horizontal or vertical)
        @param QtCore.ItemDataRole role: data access role

        @return str: header data for given column/row and role
        """
        with self._lock:
            if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return 'Name'
                elif section == 1:
                    return 'Thread'
            return None

    def data(self, index, role):
        """
        Get data from model for a given cell. Data can have a role that affects display.

        @param QtCore.QModelIndex index: cell for which data is requested
        @param QtCore.Qt.ItemDataRole role: data access role of request

        @return QVariant: data for given cell and role
        """
        with self._lock:
            if index.isValid() and role == QtCore.Qt.DisplayRole and 0 <= index.row() < self.rowCount():
                if index.column() == 0:
                    return self._thread_names[index.row()]
                elif index.column() == 1:
                    return self._threads[index.row()]
            return None

    def flags(self, index):
        """ Determines what can be done with entry cells in the table view.

          @param QModelIndex index: cell fo which the flags are requested

          @return Qt.ItemFlags: actins allowed fotr this cell
        """
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
