###############################################################################
#                                                                             #
# Copyright (C) 2007 Gary S Thompson (https://gna.org/users/varioustoxins)    #
# Copyright (C) 2010-2013 Edward d'Auvergne                                   #
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
"""The MPI processor fabric via the mpi4py Python implementation."""


# TODO: clone communicators & resize
# TODO: check exceptions on master

# Python module imports.
try:
    from mpi4py import MPI
except ImportError:
    MPI = None
import os
import sys

# relax module imports.
from multi.slave_commands import Exit_command
from multi.multi_processor_base import Multi_processor, Too_few_slaves_exception


class Mpi4py_processor(Multi_processor):
    """The mpi4py multi-processor class."""

    def __init__(self, processor_size, callback):
        """Initialise the mpi4py processor."""

        mpi_processor_size = MPI.COMM_WORLD.size-1

        if processor_size == -1:
            processor_size = mpi_processor_size

        # FIXME: needs better support in relax generates stack trace
        if mpi_processor_size == 0:
            raise Too_few_slaves_exception()

        msg = 'warning: mpi4py_processor is using 1 masters and %d slave processors you requested %d slaves\n'
        if processor_size != (mpi_processor_size):
            print(msg % (mpi_processor_size, processor_size))

        super(Mpi4py_processor, self).__init__(processor_size=mpi_processor_size, callback=callback)

        # Initialise a flag for determining if we are in the run() method or not.
        self.in_main_loop = False


    def _broadcast_command(self, command):
        for i in range(1, MPI.COMM_WORLD.size):
            if i != 0:
                MPI.COMM_WORLD.send(obj=command, dest=i)


    def _ditch_all_results(self):
        for i in range(1, MPI.COMM_WORLD.size):
            if i != 0:
                while True:
                    result = MPI.COMM_WORLD.recv(source=i)
                    if result.completed:
                        break


    def abort(self):
        MPI.COMM_WORLD.Abort()


    def assert_on_master(self):
        """Make sure that this is the master processor and not a slave.

        @raises Exception:  If not on the master processor.
        """

        # Check if this processor is a slave, and if so throw an exception.
        if self.on_slave():
            msg = 'running on slave when expected master with MPI.rank == 0, rank was %d'% self.rank()
            raise Exception(msg)


    def exit(self, status=0):
        """Exit the mpi4py processor with the given status.

        @keyword status:    The program exit status.
        @type status:       int
        """

        # Execution on the slave.
        if MPI.COMM_WORLD.rank != 0:
            # Catch sys.exit being called on an executing slave.
            if self.in_main_loop:
                raise Exception('sys.exit unexpectedly called on slave!')

            # Catch sys.exit
            else:
                sys.stderr.write('\n')
                sys.stderr.write('***********************************************\n')
                sys.stderr.write('\n')
                sys.stderr.write('warning sys.exit called before mpi4py main loop\n')
                sys.stderr.write('\n')
                sys.stderr.write('***********************************************\n')
                sys.stderr.write('\n')
                MPI.COMM_WORLD.Abort()

        # Execution on the master.
        else:
            # Slave clean up.
            if MPI.Is_initialized() and not MPI.Is_finalized() and MPI.COMM_WORLD.rank == 0:
                # Send the exit command to all slaves.
                self._broadcast_command(Exit_command())

                # Dump all results.
                self._ditch_all_results()

            # Exit the program with the given status.
            sys.exit(status)


    def get_intro_string(self):
        """Return the string to append to the end of the relax introduction string.

        @return:    The string describing this Processor fabric.
        @rtype:     str
        """

        # Get the specific MPI version.
        version_info = MPI.Get_version()

        # The vendor info.
        vendor = MPI.get_vendor()
        vendor_name = vendor[0]
        vendor_version = str(vendor[1][0])
        for i in range(1, len(vendor[1])):
            vendor_version = vendor_version + '.%i' % vendor[1][i]

        # Return the string.
        return "MPI %s.%s running via mpi4py with %i slave processors & 1 master.  Using %s %s." % (version_info[0], version_info[1], self.processor_size(), vendor_name, vendor_version)


    def get_name(self):
        return '%s-pid%s' % (MPI.Get_processor_name(), os.getpid())


    def master_queue_command(self, command, dest):
        """Slave to master processor data transfer - send the result command from the slave.

        @param command: The results command to send to the master.
        @type command:  Results_command instance
        @param dest:    The destination processor's rank.
        @type dest:     int
        """

        # Use a basic MPI send call to transfer the result command.
        MPI.COMM_WORLD.send(obj=command, dest=dest)


    def master_receive_result(self):
        """Slave to master processor data transfer - receive the result command from the slave.

        This is invoked by the master processor.

        @return:        The result command sent by the slave.
        @rtype:         Result_command instance
        """

        # Catch and return the result command.
        return MPI.COMM_WORLD.recv(source=MPI.ANY_SOURCE)


    def rank(self):
        return MPI.COMM_WORLD.rank


    def return_result_command(self, result_object):
        MPI.COMM_WORLD.send(obj=result_object, dest=0)


    def run(self):
        self.in_main_loop = True
        super(Mpi4py_processor, self).run()
        self.in_main_loop = False


    def slave_receive_commands(self):
        return MPI.COMM_WORLD.recv(source=0)
