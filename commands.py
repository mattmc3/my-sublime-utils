import sublime
import sublime_plugin
import re
from .utils import SqlUtil


class Mattmc3ConvertCsvToInsertSqlCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        util = SqlUtil()

        for region in self.view.sel():
            selection = region
            if region.empty():
                # select whole document
                selection = sublime.Region(0, self.view.size())

            csvdata = self.view.substr(selection)

            try:
                insertsql = util.csv_to_inserts(csvdata)
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


class Mattmc3SetOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        if 'output' in args:
            self.view.replace(edit, sublime.Region(0, self.view.size()), args['output'])
