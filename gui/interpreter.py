###############################################################################
#                                                                             #
# Copyright (C) 2011-2014 Edward d'Auvergne                                   #
#                                                                             #
# This file is part of the program relax (http://www.nmr-relax.com).          #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

# Module docstring.
"""A threaded version of the relax interpreter for use by the GUI."""

# Python module imports.
import sys
from threading import Thread
from time import sleep
from traceback import print_exc
import wx

# relax module imports.
from gui.errors import gui_raise
from lib.compat import Queue
from lib.errors import AllRelaxErrors
from prompt import interpreter
from status import Status; status = Status()
from user_functions.data import Uf_info; uf_info = Uf_info()


class Interpreter(object):
    """The threaded interpreter."""

    # Class variable for storing the class instance (for the singleton).
    _instance = None

    def __new__(self, *args, **kargs):
        """Replacement method for implementing the singleton design pattern."""

        # First instantiation.
        if self._instance is None:
            # Instantiate.
            self._instance = object.__new__(self, *args, **kargs)

            # Load a copy of the relax interpreter.
            self._instance._interpreter = interpreter.Interpreter(show_script=False, raise_relax_error=True)
            self._instance._interpreter.populate_self()
            self._instance._interpreter.on(verbose=False)

            # Start the interpreter thread for asynchronous operations.
            self._instance._interpreter_thread = Interpreter_thread()
            self._instance._interpreter_thread.start()

            # Hack to turn off ANSI escape characters in GUI mode.
            self._instance._interpreter.prompt_colour_off()

        # Already instantiated, so return the instance.
        return self._instance


    def _get_backend(self, uf):
        """Return the user function object corresponding to the given string.

        @param uf:  The name of the user function.
        @type uf:   str
        @return:    The user function object.
        @rtype:     func
        """

        # Get the user function info object.
        info = uf_info.get_uf(uf)

        # Return the backend.
        return info.backend


    def apply(self, uf, *args, **kwds):
        """Apply a user function for synchronous execution.

        @param uf:      The user function as a string.
        @type uf:       str
        @param args:    The user function arguments.
        @type args:     any arguments
        @param kwds:    The user function keyword arguments.
        @type kwds:     any keyword arguments
        @return:        Whether the user function was successfully applied or not.
        @rtype:         bool
        """

        # Debugging.
        if status.debug:
            sys.stdout.write("debug> GUI interpreter:  Applying the %s user function for synchronous execution.\n" % uf)

        # Get the user function backend.
        fn = self._get_backend(uf)

        # Execute the user function.
        try:
            fn(*args, **kwds)

        # Catch all RelaxErrors.
        except AllRelaxErrors:
            instance = sys.exc_info()[1]

            # Display a dialog with the error.
            gui_raise(instance, raise_flag=False)

            # Return as a failure.
            return False

        # Notify all observers that a user function has completed.
        status.observers.gui_uf.notify()

        # Return success.
        return True


    def empty(self):
        """Determine if the interpreter thread queue is empty.

        This is a wrapper method for the thread method.
        """

        # Return the queue empty state.
        return self._interpreter_thread.empty()


    def exit(self):
        """Cause the thread to exit once all currently queued user functions are processed.

        This is a wrapper method for the thread method.
        """

        # Call the thread's method.
        return self._interpreter_thread.exit()


    def flush(self):
        """Return only once the queue is empty.

        This is a wrapper method for the interpreter thread.
        """

        # Debugging.
        if status.debug:
            sys.stdout.write("debug> GUI interpreter:  Flushing.\n")

        # Wait a little while to prevent races with the reading of the queue.
        sleep(0.05)

        # Loop until empty.
        while not self._interpreter_thread.empty():
            # Wait a bit for the queue to empty.
            sleep(0.05)

            # Wait until execution is complete.
            while status.exec_lock.locked():
                sleep(0.1)

        # Debugging.
        if status.debug:
            sys.stdout.write("debug> GUI interpreter:  Flushed.\n")


    def join(self):
        """Wrapper method for the Queue.join() method."""

        # Call the thread's method.
        self._interpreter_thread.join()


    def queue(self, uf, *args, **kwds):
        """Queue up a user function.

        This is a wrapper method for the interpreter thread.

        @param uf:      The user function as a string.
        @type uf:       str
        @param args:    The user function arguments.
        @type args:     any arguments
        @param kwds:    The user function keyword arguments.
        @type kwds:     any keyword arguments
        @return:        Whether the user function was successfully applied or not (though as this is asynchronous, this cannot be checked so True will always be returned.
        @rtype:         bool
        """

        # Debugging.
        if status.debug:
            sys.stdout.write("debug> GUI interpreter:  Queuing the %s user function for asynchronous execution.\n" % uf)

        # Get the user function.
        fn = self._get_backend(uf)

        # Call the thread's method.
        self._interpreter_thread.queue(fn, *args, **kwds)

        # Cannot judge if the user function was successful.
        return True



class Interpreter_thread(Thread):
    """The threaded interpreter."""

    def __init__(self):
        """Initialise the object."""

        # Set up the thread object.
        Thread.__init__(self)

        # Set the thread to be daemonic so that relax can exit.
        self.daemon = True

        # Create a queue object for the user function calls.
        self._queue = Queue()

        # The list of user functions still in the queue.
        self._uf_list = []

        # A flag for exiting the thread.
        self._exit = False


    def empty(self):
        """Is the queue empty?"""

        # Execution is locked.
        if status.exec_lock.locked():
            return False

        # There are still queued calls.
        elif len(self._uf_list):
            return False

        # The queue is empty.
        else:
            return True


    def exit(self):
        """Cause the thread to exit once all currently queued user functions are processed."""

        # First set the flag.
        self._exit = True

        # Then queue a dummy user function.
        self._queue.put([None, None, None])


    def join(self):
        """Wrapper method for the Queue.join() method."""

        # Join the queue.
        self._queue.join()


    def queue(self, fn, *args, **kwds):
        """Queue up a user function for asynchronous execution.

        @param fn:      The user function as a string.
        @type fn:       str
        @param args:    The user function arguments.
        @type args:     any arguments
        @param kwds:    The user function keyword arguments.
        @type kwds:     any keyword arguments
        """

        # Add the user function name to the list.
        self._uf_list.append(repr(fn))

        # Place the user function and its args onto the queue.
        self._queue.put([fn, args, kwds])


    def run(self):
        """Execute the thread."""

        # Loop until told to exit.
        while not self._exit:
            # Get the user function from the queue.
            fn, args, kwds = self._queue.get()

            # No user function.
            if fn == None:
                continue

            # Execution lock.
            status.exec_lock.acquire('gui', mode='interpreter thread')

            # Execute the user function, catching errors (the nested try-except statements within the try-finally statements are for Python 2.4 and earlier support).
            try:
                try:
                    fn(*args, **kwds)

                # Catch all RelaxErrors.
                except AllRelaxErrors:
                    instance = sys.exc_info()[1]

                    # Display a dialog with the error.
                    wx.CallAfter(gui_raise, instance, raise_flag=False)

                # Handle all other errors.
                except:
                    # Print the exception.
                    print_exc()

            # Release the lock.
            finally:
                # Signal that the queue item has been processed.
                self._queue.task_done()

                # Release the execution lock.
                status.exec_lock.release()

                # Remove the user function from the list.
                self._uf_list.pop(self._uf_list.index(repr(fn)))

            # Notify all observers that a user function has completed.
            status.observers.gui_uf.notify()
