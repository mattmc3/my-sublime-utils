'''
SQL Tools: mattmc3
Version: 0.0.4
Revision: 20170113

TODO:
    - Settings?
    - Trim values
    - single insert vs multiple
    - values vs union all select
    - Fixed width
    - Tokenize strings, comments
'''

import csv
from io import StringIO
import re


class SqlUtil():
    def csv_to_inserts(self, csvdata):
        # remove 0x00 NULs because csv.reader chokes on it
        csvdata = csvdata.replace('\0', '?')
        data = []

        dialect = csv.Sniffer().sniff(csvdata, delimiters=",|;~\t")
        has_header = csv.Sniffer().has_header(csvdata)
        csv_io = StringIO(csvdata)
        data = list(csv.reader(csv_io, dialect=dialect))

        return self._get_dialect_str(dialect, has_header) + "\n" + self.list_to_inserts(data, has_header) + "\n"

    def list_to_inserts(self, datalist, has_header):
        result = []
        first_insert = True
        for idx, row in enumerate(datalist):
            if idx == 0:
                sql = "INSERT INTO {{some_table}}"
                if has_header:
                    sql += " (" + ", ".join(['"{}"'.format(c) for c in row]) + ")"
                result.append(sql)
                if has_header:
                    continue

            # determine whether we have the first data row
            line_prefix = "      ,"
            if first_insert:
                line_prefix = "VALUES "
                first_insert = False

            values = line_prefix + "(" + ", ".join([self._sql_escape(c) for c in row]) + ")"
            result.append(values)

        return "\n".join(result) + "\n"

    def _get_dialect_str(self, dialect, has_header):
        result = []
        result.append("-- =====================")
        result.append("-- Delimeted Dialect Details:")
        result.append("-- delimiter: {0}".format(self._show(dialect.delimiter)))
        result.append("-- double quote: {0}".format(self._show(dialect.doublequote)))
        result.append("-- escape char: {0}".format(self._show(dialect.escapechar)))
        result.append("-- line terminator: {0}".format(self._show(dialect.lineterminator)))
        result.append("-- quote char: {0}".format(self._show(dialect.quotechar)))
        result.append("-- quoting: {0}".format(self._show(dialect.quoting)))
        result.append("-- skip initial space: {0}".format(self._show(dialect.skipinitialspace)))
        result.append("-- has header: {0}".format(has_header))
        result.append("-- =====================")
        return "\n".join(result)

    def _show(self, x):
        if x is None:
            return ""
        else:
            s = str(x)
            return s.replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")

    def _sql_escape(self, s):
        if s is None:
            return "NULL"
        elif s == "":
            return "''"
        else:
            return_raw = False
            try:
                i = int(s)
                return_raw = True
            except ValueError:
                return_raw = False

            if return_raw:
                return s
            else:
                return "'{}'".format(s.replace("'", "''"))

    def reformat_mssql(self, sql):
        result = sql
        result = self._mssql_replacements(result)

        keywords = set(['select', 'insert', 'from', 'where', 'into'])

        def bracket_sub(matchobj):
            if matchobj.group(0) in keywords:
                return matchobj.group(0)
            else:
                return matchobj.group(1)

        def lower_sub(matchobj):
            return matchobj.group(0).lower()

        def knr_openparen_sub(matchobj):
            return " (\n" + matchobj.group(1)

        indent = "    "
        flags = re.S | re.M | re.X | re.I

        # fix SHOUTCASE
        result = re.sub(r'(?<!\[)\b([A-Z_][A-Z0-9_]*)\b', lower_sub, result, flags=flags)

        # K&R open paren
        result = re.sub(r'\n(\s+)\(', knr_openparen_sub, result, flags=flags)

        # K&R close paren
        result = re.sub(r'\)\n', "\n)\n", result, flags=flags)

        # strip off DB
        result = re.sub(r'\[[^\]]+\]\.(\[[^\]]+\]\.\[[^\]]+\])', r'\1', result, flags=flags)

        # remove extraneous brackets
        result = re.sub(r'\[([A-Za-z_][A-Za-z0-9_]*)\]', bracket_sub, result, flags=flags)

        # remove extraneous indents
        result = re.sub(r'^\s+values', 'values', result, flags=flags)

        # standardize indents
        while True:
            new_result = re.sub(r'^\t', indent, result, flags=flags)
            if new_result == result:
                break
            result = new_result

        # remove extra newlines
        result = re.sub(r'\n(\n+)', "\n", result, flags=flags)

        # remove extra GOs
        result = re.sub(r'GO(\nGO)+', "go", result, flags=flags)

        return result

    def _mssql_replacements(self, sql):
        result = sql
        repls = [
            (re.escape("WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]"), ""),
            (re.escape("WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]"), ""),
            (r'SET ANSI_NULLS (ON|OFF)', ""),
            (r'SET ANSI_PADDING (ON|OFF)', ""),
            (r'SET QUOTED_IDENTIFIER (ON|OFF)', ""),
            (re.escape("ON [PRIMARY]"), ""),
        ]
        for replacement in repls:
            result = re.sub(replacement[0], replacement[1], result, flags=re.IGNORECASE)
        return result
