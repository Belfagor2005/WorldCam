#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    Tulip routine libraries, based on lambda's lamlib
    Author Twilight0

        License summary below, for more details please read license.txt file

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 2 of the License, or
        (at your option) any later version.
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import re, hashlib, time, os

def get(function, timeout = 10, *args, **table):
    try:
        response = None

        f = repr(function)
        f = re.sub('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', f)

        a = hashlib.md5()
        for i in args: a.update(str(i))
        a = str(a.hexdigest())
    except:
        pass

    try:
        table = table['table']
    except:
        table = 'rel_list'

    try:
        r = function(*args)
        if (r == None or r == []) and not response == None:
            return response
        elif (r == None or r == []):
            return r
    except:
        return

    try:
        return eval(r.encode('utf-8'))
    except:
        pass




