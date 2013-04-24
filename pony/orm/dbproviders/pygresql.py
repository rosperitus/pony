import re
from itertools import imap
from binascii import unhexlify

from pony.orm.dbproviders._postgres import *

import pgdb

char2oct = {}
for i in range(256):
    ch = chr(i)
    if 31 < i < 127:
        char2oct[ch] = ch
    else: char2oct[ch] = '\\' + ('00'+oct(i))[-3:]
char2oct['\\'] = '\\\\'

oct_re = re.compile(r'\\[0-7]{3}')

class PyGreSQLValue(sqlbuilding.Value):
    def __unicode__(self):
        value = self.value
        if isinstance(value, buffer):
            return "'%s'::bytea" % "".join(imap(char2oct.__getitem__, val))
        return sqlbuilding.Value.__unicode__(self)

class PyGreSQLBuilder(PGSQLBuilder):
    make_value = PyGreSQLValue

class PyGreSQLBlobConverter(PGBlobConverter):
    def py2sql(converter, val):
        db_val = "".join(imap(char2oct.__getitem__, val))
        return db_val
    def sql2py(converter, val):
        if val.startswith('\\x'): val = unhexlify(val[2:])
        else: val = oct_re.sub(lambda match: chr(int(match.group(0)[-3:], 8)), val.replace('\\\\', '\\'))
        return buffer(val)

class PyGreSQLDateConverter(dbapiprovider.DateConverter):
    def py2sql(converter, val):
        return datetime(val.year, val.month, val.day)
    def sql2py(converter, val):
        return datetime.strptime(val, '%Y-%m-%d').date()
    
class PyGreSQLDatetimeConverter(PGDatetimeConverter):
    def sql2py(converter, val):
        return timestamp2datetime(val)

class PyGreSQLProvider(PGProvider):
    dbapi_module = pgdb
    sqlbuilder_cls = PyGreSQLBuilder

    converter_classes = [
        (bool, dbapiprovider.BoolConverter),
        (unicode, PGUnicodeConverter),
        (str, PGStrConverter),
        (long, PGLongConverter),
        (int, dbapiprovider.IntConverter),
        (float, PGRealConverter),
        (Decimal, dbapiprovider.DecimalConverter),
        (buffer, PyGreSQLBlobConverter),
        (datetime, PyGreSQLDatetimeConverter),
        (date, PyGreSQLDateConverter)
    ]

provider_cls = PyGreSQLProvider
