import sublime
import sublime_plugin
import re
from .utils import SqlUtil


settings = {}


def plugin_loaded():
    global settings
    settings = sublime.load_settings('my-sublime-utils.sublime-settings')


class PluginMixin():
    def get_selection(self):
        selections = []
        for region in self.view.sel():
            if not region.empty():
                selections.append(region)
        if len(selections) == 0:
            # select whole document
            selections.append(sublime.Region(0, self.view.size()))
        return selections


class Mattmc3ConvertCsvToInsertSqlCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        util = SqlUtil()

        values_chunk_size = settings.get("values_chunk_size")

        for region in self.view.sel():
            selection = region
            if region.empty():
                # select whole document
                selection = sublime.Region(0, self.view.size())

            csvdata = self.view.substr(selection)

            try:
                insertsql = util.csv_to_inserts(csvdata, chunk_size=values_chunk_size)
            except Exception as ex:
                sublime.error_message(__name__ + ": csv_to_inserts failed : " + str(ex))
                return

            # Create a new output window
            new_view = self.view.window().new_file()
            new_view.set_name('SQL Output')
            new_view.set_scratch(True)
            new_view.set_syntax_file("Packages/SQL/SQL.tmLanguage")
            new_view.run_command('mattmc3_set_output', {'output': insertsql})


class Mattmc3ReplaceSmartQuotes(sublime_plugin.TextCommand):
    def run(self, edit):
        replacements = [
            (re.compile(r'“|”'), '"'),
            (re.compile(r'‘|’'), "'"),
        ]

        for region in self.view.sel():
            selection = region
            if region.empty():
                # select whole document
                selection = sublime.Region(0, self.view.size())

            text = self.view.substr(selection)
            for pat, replacewith in replacements:
                text = pat.sub(replacewith, text)

            self.view.replace(edit, selection, text)


class Mattmc3ReformatMssqlCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        util = SqlUtil()

        for region in self.view.sel():
            selection = region
            if region.empty():
                # select whole document
                selection = sublime.Region(0, self.view.size())

            sql = self.view.substr(selection)

            formatsql = util.reformat_mssql(sql)

            # Replace the SQL
            self.view.replace(edit, selection, formatsql)


class Mattmc3ReplaceObjectScriptDate(sublime_plugin.TextCommand, PluginMixin):
    def run(self, edit):
        for selection in self.get_selection():
            sql = self.view.substr(selection)
            script_date_pattern = r"Script\sDate:\s\d+\/\d+/\d+\s\d+:\d+:\d+\s[AP]M\s\*{6}\/"
            script_date_replacement = "Script Date: 1/1/2000 12:00:00 AM ******/"
            new_sql = re.sub(script_date_pattern, script_date_replacement, sql)
            self.view.replace(edit, selection, new_sql)


class Mattmc3TsqlMakeMergeStatement(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            selection = region
            if region.empty():
                # select whole document
                selection = sublime.Region(0, self.view.size())

        column_text = self.view.substr(selection)
        column_text = column_text.replace(",", "\n")
        columns = [c.strip() for c in column_text.split("\n")]
        columns = [c for c in columns if c != ""]

        double_indent = "\n        ,"
        join = "target.{} = source.{}".format(columns[0], columns[0])
        insert_cols = double_indent.join(columns)
        values_cols = double_indent.join("source.{}".format(c) for c in columns)
        where_cols = "\n    or ".join("target.{0} <> source.{0}".format(c) for c in columns[1:])
        set_cols = double_indent.join("target.{0} = source.{0}".format(c) for c in columns[1:])

        merge_tmpl = '''merge {{table_name}} as target
using (select * from #t) as source
on ({join})
when not matched by target then
    insert (
         {insert_cols}
    )
    values (
        {values_cols}
    )
when matched and (
    {where_cols}
) then
    update set
         {set_cols}
-- output deleted.*, $action, inserted.* into #merge_result
;'''
        result = merge_tmpl.format(join=join,
                                   insert_cols=insert_cols,
                                   values_cols=values_cols,
                                   where_cols=where_cols,
                                   set_cols=set_cols)
        # self.view.insert(edit, 0, result)
        self.view.replace(edit, selection, result)


class Mattmc3SetOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        if 'output' in args:
            self.view.replace(edit, sublime.Region(0, self.view.size()), args['output'])
