import re
import sublime
from common.config import config
from common.selection import Selection

NEEDLE_SEPARATOR = "\"\'\(\)"
NEEDLE_SEPARATOR_BEFORE = "\"\'\("
NEEDLE_SEPARATOR_AFTER = "^\"\'\)"
NEEDLE_CHARACTERS = "\.A-Za-z0-9\-\_$"
NEEDLE_INVALID_CHARACTERS = "\"\'\)=\:\(<>"
DELIMITER = "\s\:\(\[\="

def get_context(view):
	valid = True
	valid_needle = True
	position = Selection.get_position(view)

	# regions
	word_region = view.word(position)
	line_region = view.line(position)
	pre_region = sublime.Region(line_region.a, word_region.a)
	post_region = sublime.Region(word_region.b, line_region.b)

	# text
	line = view.substr(line_region)
	word = view.substr(word_region)
	pre = view.substr(pre_region)
	post = view.substr(post_region)

	needle_region = view.word(position)
	# st2: unmutable region
	needle_start = needle_region.a
	needle_end = needle_region.b

	# grab everything in 'separators'
	needle = ""
	separator = False
	pre_match = ""
	# search for a separator before current word, i.e. <">path/to/<position>
	pre_quotes = re.search("(["+NEEDLE_SEPARATOR_BEFORE+"])([^"+NEEDLE_SEPARATOR+"]*)$", pre)
	if pre_quotes:
		needle += pre_quotes.group(2) + word
		separator = pre_quotes.group(1)
		pre_match = pre_quotes.group(2)

		needle_start -= len(pre_quotes.group(2))

	else:
		# use whitespace as separator
		pre_quotes = re.search("(\s)([^"+NEEDLE_SEPARATOR+"\s]*)$", pre)
		if pre_quotes:
			needle = pre_quotes.group(2) + word
			separator = pre_quotes.group(1)
			pre_match = pre_quotes.group(2)

			needle_start -= len(pre_quotes.group(2))

	if pre_quotes:
		post_quotes = re.search("^(["+NEEDLE_SEPARATOR_AFTER+"]*)", post)
		if post_quotes:
			needle += post_quotes.group(1)
			needle_end += len(post_quotes.group(1))
		else:
			print("no post quotes found => invalid")
			valid = False

	elif not re.search("["+NEEDLE_INVALID_CHARACTERS+"]", needle):
		needle = pre + word
		needle_start = pre_region.a

	else:
		needle = word

	needle_region = sublime.Region(needle_start, needle_end)

	# grab prefix
	prefix_region = sublime.Region(line_region.a, pre_region.b - len(pre_match) - 1)
	prefix_line = view.substr(prefix_region)
	# # print("prefix line", prefix_line)

	#define? (["...", "..."]) -> before?
	# before: ABC =:([
	prefix = re.search("\s*(["+NEEDLE_CHARACTERS+"]+)["+DELIMITER+"]*$", prefix_line)
	if prefix is None:
		# validate array, like define(["...", ".CURSOR."])
		prefix = re.search("^\s*(["+NEEDLE_CHARACTERS+"]+)["+DELIMITER+"]+", prefix_line)

	if prefix:
		# print("prefix:", prefix.group(1))
		prefix = prefix.group(1)

	tag = re.search("<\s*(["+NEEDLE_CHARACTERS+"]*)\s*[^>]*$", prefix_line)
	if tag:
		tag = tag.group(1)
		# print("tag:", tag)

	style = re.search("[\s\"\'']*(["+NEEDLE_CHARACTERS+"]*)[\s\"\']*\:[^\:]*$", prefix_line)
	if style:
		style = style.group(1)
		# print("style:", style)

	if separator is False:
		# print("context", "separator undefined => invalid", needle)
		valid = False
	elif re.search("["+NEEDLE_INVALID_CHARACTERS+"]", needle):
		# print("context", "invalid characters in needle => invalid", needle)
		valid_needle = False
		valid = False
	elif prefix is None and separator.strip() == "":
		# print("context", "prefix undefined => invalid", needle)
		valid = False

	return {
		"is_valid": valid,
		"valid_needle": valid_needle,
		"needle": needle,
		"prefix": prefix,
		"tagName": tag,
		"style": style,
		"region": needle_region
	}

class Context:

	@staticmethod
	def get_context(view):
		return get_context(view)

	@staticmethod
	def check_trigger(trigger, expression):
		# returns True if the expression statements match the trigger
		for statement in set(config["TRIGGER_STATEMENTS"]).intersection(trigger):
			values = trigger.get(statement)
			# statement values may be None (or any other value...)
			if type(values) is list and not expression.get(statement) in values:
				return False
			# validate other value by comparison
			# elif not values == expression.get(statement):
			# 	return False

		return True

	@staticmethod
	def find_trigger(expression, scope, triggers):
		for trigger in triggers:
			# if the trigger is defined for the current scope
			# REQUIRED? scope = properties.get("scope").replace("//", "")
			if re.search(trigger["scope"], scope):
				# validate its statements on the current context
				if Context.check_trigger(trigger, expression):
					return trigger

		return False

	@staticmethod
	def get_rule(view):

		selection = view.sel()[0]
		position = selection.begin()
		word_region = view.word(position)

		current_scope = view.scope_name(word_region.a)
		context = get_context(view)
		rule = Context.find_rule(context, current_scope)

		return [rule, context] if rule else False
