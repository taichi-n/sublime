import sublime
import sublime_plugin
import random
import re

class LoremIpsumCommand(sublime_plugin.TextCommand):

    def run(self, edit, qty=10):

        selections = self.view.sel()
        for selection in selections:

            # always start with Lorem ipsum for first outpur lorem
            para = "Lorem ipsum "

            # words from the original Lorum ipsum text
            words = "dolor sit amet consectetur adipisicing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua Ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur Excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum".split()

            # get preceding numbers (possibly with decimal separation) if available
            lastchars = self.view.substr(sublime.Region(selection.begin()-20, selection.end()))
            last = re.search("(|(\d+)(\.\d+)?)$", lastchars).group(0)

            m = str(last).split(".")

            if re.search("\d", last) and (
                (len(m) > 1 and (int(m[0]) * int(m[1])) < 1000)
                or (len(m) == 1 and int(m[0]) < 1000)
            ):
                selection = sublime.Region(selection.begin() - len(str(last)), selection.end())
            else:
                # if they wasked for too much lorem, just give 'em one - for their own safety!
                last = 1
            # could give error instead - but who wants to think that much about lorem?
            # else:
            #     print("[ERROR] too much lorem ipsum - try a smaller number")

            m = str(last).split(".")
            paras = int(m[0])

            if len(m) > 1:
                qty = int(m[1])

            for i in list(range(0, paras)):
                from random import choice
                para += choice(words).capitalize() + " "
                for x in list(range(random.randint(int(qty - qty/3)-2, int(qty + qty/3)-2))):
                    para += choice(words) + " "
                para += choice(words) + "."
                if i != paras and paras > 1:
                    para += "\n\n"

            # erase region
            self.view.erase(edit, selection)

            last = self.view.substr(sublime.Region(selection.begin()-1, selection.end()))
            if last == ".":
                para = " " + para

            # insert para before current cursor position
            self.view.insert(edit, selection.begin(), para)

            self.view.end_edit(edit)

