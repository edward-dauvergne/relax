###############################################################################
#                                                                             #
# Copyright (C) 2009-2014 Edward d'Auvergne                                   #
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
"""Module for relax version information."""

# Dependencies.
import dep_check

# Python module imports.
from os import F_OK, access, sep
from re import search
PIPE, Popen = None, None
if dep_check.subprocess_module:
    from subprocess import PIPE, Popen

# relax module imports.
from status import Status; status = Status()


version = "repository checkout"
repo_revision = None
repo_url = None


def revision():
    """Attempt to retrieve the SVN revision number, if this is a checked out copy.

    @return:    The SVN revision number, or None if unsuccessful.
    @rtype:     None or str
    """

    # Return the global variable, if set.
    global repo_revision
    if repo_revision != None:
        return repo_revision

    # Does the base directory exist (i.e. is this a checked out copy).
    if not access(status.install_path+sep+'.svn', F_OK) and not access(status.install_path+sep+'.git', F_OK):
        return

    # Python 2.3 and earlier.
    if Popen == None:
        return

    # Try to run 'svn info', reading the output if there are no errors.
    pipe = Popen('svn info %s' % status.install_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)
    if not pipe.stderr.readlines():
        # Loop over the output lines.
        for line in pipe.stdout.readlines():
            # Decode Python 3 byte arrays.
            if hasattr(line, 'decode'):
                line = line.decode()

            # Split up the line.
            row = line.split()

            # Store revision as the global variable and return it.
            if len(row) and row[0] == 'Revision:':
                repo_revision = str(row[1])
                return repo_revision

    # Try git-svn, reading the output if there are no errors.
    pipe = Popen('cd %s; git svn info' % status.install_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)
    if not pipe.stderr.readlines():
        # Loop over the output lines.
        for line in pipe.stdout.readlines():
            # Decode Python 3 byte arrays.
            if hasattr(line, 'decode'):
                line = line.decode()

            # Split up the line.
            row = line.split()

            # Store revision as the global variable and return it.
            if len(row) and row[0] == 'Revision:':
                repo_revision = str(row[1])
                return repo_revision


def url():
    """Attempt to retrieve the SVN URL, if this is a checked out copy.

    @return:    The SVN URL, or None if unsuccessful.
    @rtype:     None or str
    """

    # Return the global variable, if set.
    global repo_url
    if repo_url != None:
        return repo_url

    # Does the base directory exist (i.e. is this a checked out copy).
    if not access(status.install_path+sep+'.svn', F_OK) and not access(status.install_path+sep+'.git', F_OK):
        return

    # Python 2.3 and earlier.
    if Popen == None:
        return

    # Try to run 'svn info', reading the output if there are no errors.
    pipe = Popen('svn info %s' % status.install_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)
    if not pipe.stderr.readlines():
        # Loop over the output lines.
        for line in pipe.stdout.readlines():
            # Decode Python 3 byte arrays.
            if hasattr(line, 'decode'):
                line = line.decode()

            # Split up the line.
            row = line.split()

            # Store URL as the global variable and return it.
            if len(row) and row[0] == 'URL:':
                repo_url = str(row[1])
                return repo_url

    # Try git-svn, reading the output if there are no errors.
    pipe = Popen('cd %s; git svn info' % status.install_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)
    if not pipe.stderr.readlines():
        # Loop over the output lines.
        for line in pipe.stdout.readlines():
            # Decode Python 3 byte arrays.
            if hasattr(line, 'decode'):
                line = line.decode()

            # Split up the line.
            row = line.split()

            # Store URL as the global variable and return it.
            if len(row) and row[0] == 'URL:':
                repo_url = str(row[1])
                return repo_url


def version_full():
    """Return the full relax version, including all SVN info for repository versions.

    @return:    The relax version string.
    @rtype:     str
    """

    # The relax version.
    ver = version

    # Repository version.
    if ver == 'repository checkout':
        # Get the SVN revision and URL.
        svn_rev = revision()
        svn_url = url()

        # Change the version string.
        if svn_rev:
            ver = version + " r" + svn_rev
        if svn_url:
            ver = ver + " " + svn_url

    # Return the version.
    return ver
