###############################################################################
#                                                                             #
# Copyright (C) 2007 Gary S Thompson (https://gna.org/users/varioustoxins)    #
# Copyright (C) 2011-2013 Edward d'Auvergne                                   #
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
"""Module containing a Processor base class to be used by any multi-processor fabric.

This is used by the mpi4py clustering code.  It can also be used by any new implementation
including, for example:

    - Other implementations using different python MPI libraries (pypar, etc.).
    - Use of ssh tunnels for parallel programming.
    - Use of the twisted frame work for communication (http://twistedmatrix.com/projects/).
    - The parallel virtual machine (pvm) via pypvm (http://pypvm.sourceforge.net).
"""

# Python module imports.
from copy import copy
import math
import sys

# multi module imports.
from multi.misc import raise_unimplemented, Result, Result_string, Verbosity; verbosity = Verbosity()
from multi.processor import Processor
from multi.result_commands import Batched_result_command, Result_command, Result_exception


class Multi_processor(Processor):
    """The multi-processor base class."""

    def __init__(self, processor_size, callback):
        super(Multi_processor, self).__init__(processor_size=processor_size, callback=callback)

        self.do_quit = False

        #FIXME un clone from uniprocessor
        #command queue and memo queue
        self.command_queue = []
        self.memo_map = {}

        self.batched_returns = True
        self.result_list = None


    #TODO: move up a level
    def add_to_queue(self, command, memo=None):
        self.command_queue.append(command)
        if memo != None:
            command.set_memo_id(memo)
            self.memo_map[memo.memo_id()] = memo


    #TODO: move up a level
    def chunk_queue(self, queue):
        lqueue = copy(queue)
        result = []
        processors = self.processor_size()
        chunks = processors * self.grainyness
        chunk_size = int(math.floor(float(len(queue)) / float(chunks)))

        if chunk_size < 1:
            result = queue
        else:
            for i in range(chunks):
                result.append(lqueue[:chunk_size])
                del lqueue[:chunk_size]
            for i, elem in enumerate(lqueue):
                result[i].append(elem)
        return result


    # FIXME move to lower level
    def on_master(self):
        if self.rank() == 0:
            return True


    # FIXME move to lower level
    def on_slave(self):
        return not self.on_master()


    def post_run(self):

        super(Multi_processor, self).post_run()


    def pre_run(self):
        """Method called before starting the application main loop"""

        # Execute the base class method.
        super(Multi_processor, self).pre_run()


    #FIXME: fill out generic result processing move to processor
    def process_result(self, result):
        if isinstance(result, Result):
            if isinstance(result, Result_command):
                memo = None
                if result.memo_id != None:
                    memo = self.memo_map[result.memo_id]
                result.run(self, memo)
                if result.memo_id != None and result.completed:
                    del self.memo_map[result.memo_id]

            elif isinstance(result, Result_string):
                #FIXME can't cope with multiple lines
                sys.stdout.write(result.string)
        else:
            message = 'Unexpected result type \n%s \nvalue%s' %(result.__class__.__name__, result)
            raise Exception(message)


    #TODO: move up a level add send and revieve virtual functions
    def return_object(self, result):
        result_object = None
        #raise Exception('dummy')
        if isinstance(result, Result_exception):
            result_object = result
        elif self.batched_returns:
            is_batch_result = isinstance(result, Batched_result_command)

            if is_batch_result:
                result_object = result
            else:
                if self.result_list != None:
                    self.result_list.append(result)
        else:
            result_object = result

        if result_object != None:
            #FIXME check is used?
            result_object.rank = self.rank()
            self.return_result_command(result_object=result_object)


    def return_result_command(self, result_object):
        raise_unimplemented(self.slave_queue_result)


    def slave_receive_commands(self):
        raise_unimplemented(self.slave_receive_commands)



class Too_few_slaves_exception(Exception):
    def __init__(self):
        msg = 'master slave processing requires at least 2 processors to run you only provided 1, exiting....'
        Exception.__init__(self, msg)
