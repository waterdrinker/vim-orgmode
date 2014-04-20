# -*- coding: utf-8 -*-

import vim
from orgmode._vim import echo, echom, echoe, ORGMODE, apply_count, repeat, insert_at_cursor, indent_orgmode
from orgmode.menu import Submenu, Separator, ActionEntry, add_cmd_mapping_menu
from orgmode.keybinding import Keybinding, Plug, Command
from orgmode.liborgmode.checkboxes import Checkbox


class EditCheckbox(object):
	u"""
	Checkbox plugin.
	"""

	def __init__(self):
		u""" Initialize plugin """
		object.__init__(self)
		# menu entries this plugin should create
		self.menu = ORGMODE.orgmenu + Submenu(u'EditCheckbox')

		# key bindings for this plugin
		# key bindings are also registered through the menu so only additional
		# bindings should be put in this variable
		self.keybindings = []

		# commands for this plugin
		self.commands = []

	@classmethod
	def new_checkbox(cls, below=None):
		d = ORGMODE.get_document()
		h = d.current_heading()
		if h is None:
			return
		# init checkboxes for current heading
		h.init_checkboxes()
		c = h.current_checkbox()

		# default checkbox level
		level = h.level
		# if no checkbox is found, insert at current line with indent level=1
		if c is None:
			start = h.start
			if h.checkboxes:
				level = h.first_checkbox.level
		else:
			level = c.level
			if below:
				start = c.end_of_last_child
			else:
				start = c.start

		vim.current.window.cursor = (start + 1, 0)

		if below:
			vim.command("normal o")
		else:
			vim.command("normal O")

		new_checkbox = Checkbox(level=level)
		insert_at_cursor(str(new_checkbox))
		vim.command("call feedkeys('a')")

	@classmethod
	def toggle(cls, checkbox=None):
		u"""
		Toggle the checkbox given in the parameter.
		If the checkbox is not given, it will toggle the current checkbox.
		"""
		d = ORGMODE.get_document()
		current_heading = d.current_heading()
		# init checkboxes for current heading
		if current_heading is None:
			return
		current_heading = current_heading.init_checkboxes()

		if checkbox is None:
			# get current_checkbox
			c = current_heading.current_checkbox()
			# no checkbox found
			if c is None:
				cls.update_checkboxes_status()
				return
		else:
			c = checkbox

		if c.status == Checkbox.STATUS_OFF:
			# set checkbox status on if all children are on
			if not c.children or c.are_children_all(Checkbox.STATUS_ON):
				c.toggle()
				d.write_checkbox(c)

		elif c.status == Checkbox.STATUS_ON:
			if not c.children or c.is_child_one(Checkbox.STATUS_OFF):
				c.toggle()
				d.write_checkbox(c)

		elif c.status == Checkbox.STATUS_INT:
			# can't toggle intermediate state directly according to emacs orgmode
			pass
		# update checkboxes status
		cls.update_checkboxes_status()

	@classmethod
	def _update_subtasks(cls):
		d = ORGMODE.get_document()
		h = d.current_heading()
		# init checkboxes for current heading
		h.init_checkboxes()
		# update heading subtask info
		c = h.first_checkbox
		if c is None:
			return
		total, on = c.all_siblings_status()
		h.update_subtasks(total, on)
		# update all checkboxes under current heading
		cls._update_checkboxes_subtasks(c)

	@classmethod
	def _update_checkboxes_subtasks(cls, checkbox):
		# update checkboxes
		for c in checkbox.all_siblings():
			if c.children:
				total, on = c.first_child.all_siblings_status()
				c.update_subtasks(total, on)
				cls._update_checkboxes_subtasks(c.first_child)

	@classmethod
	def update_checkboxes_status(cls):
		d = ORGMODE.get_document()
		h = d.current_heading()
		# init checkboxes for current heading
		h.init_checkboxes()

		cls._update_checkboxes_status(h.first_checkbox)
		cls._update_subtasks()

	@classmethod
	def _update_checkboxes_status(cls, checkbox=None):
		u""" helper function for update checkboxes status
			:checkbox: The first checkbox of this indent level
			:return: The status of the parent checkbox
		"""
		if checkbox is None:
			return

		status_off, status_on, status_int, total = 0, 0, 0, 0
		# update all top level checkboxes' status
		for c in checkbox.all_siblings():
			current_status = c.status
			# if this checkbox is not leaf, its status should determine by all its children
			if c.children:
				current_status = cls._update_checkboxes_status(c.first_child)

			# don't update status if the checkbox has no status
			if c.status is None:
				current_status = None
			# the checkbox needs to have status
			else:
				total +=  1

			# count number of status in this checkbox level
			if current_status == Checkbox.STATUS_OFF:
				status_off += 1
			elif current_status == Checkbox.STATUS_ON:
				status_on += 1
			elif current_status == Checkbox.STATUS_INT:
				status_int += 1

			# write status if any update
			if current_status is not None and c.status != current_status:
				c.status = current_status
				d = ORGMODE.get_document()
				d.write_checkbox(c)

		parent_status = Checkbox.STATUS_INT
		# all silbing checkboxes are off status
		if status_off == total:
			parent_status = Checkbox.STATUS_OFF
		# all silbing checkboxes are on status
		elif status_on == total:
			parent_status = Checkbox.STATUS_ON
		# one silbing checkbox is on or int status
		elif status_on != 0 or status_int != 0:
			parent_status = Checkbox.STATUS_INT
		# other cases
		else:
			parent_status = None

		return parent_status

	def register(self):
		u"""
		Registration of the plugin.

		Key bindings and other initialization should be done here.
		"""
		add_cmd_mapping_menu(
			self,
			name=u'OrgCheckBoxNewAbove',
			function=u':py ORGMODE.plugins[u"EditCheckbox"].new_checkbox()<CR>',
			key_mapping=u'<localleader>cN',
			menu_desrc=u'New CheckBox Above'
		)
		add_cmd_mapping_menu(
			self,
			name=u'OrgCheckBoxNewBelow',
			function=u':py ORGMODE.plugins[u"EditCheckbox"].new_checkbox(below=True)<CR>',
			key_mapping=u'<localleader>cn',
			menu_desrc=u'New CheckBox Below'
		)
		add_cmd_mapping_menu(
			self,
			name=u'OrgCheckBoxToggle',
			function=u':silent! py ORGMODE.plugins[u"EditCheckbox"].toggle()<CR>',
			key_mapping=u'<localleader>cc',
			menu_desrc=u'Toggle Checkbox'
		)
		add_cmd_mapping_menu(
			self,
			name=u'OrgCheckBoxUpdate',
			function=u':silent! py ORGMODE.plugins[u"EditCheckbox"].update_checkboxes_status()<CR>',
			key_mapping=u'<localleader>c#',
			menu_desrc=u'Update Subtasks'
		)

# vim: set noexpandtab:
