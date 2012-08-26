[
	{ "keys": ["ctrl+shift+n"], "command": "new_window" },
	{ "keys": ["ctrl+shift+w"], "command": "close_window" },
	{ "keys": ["ctrl+o"], "command": "prompt_open_file" },
	{ "keys": ["ctrl+shift+t"], "command": "reopen_last_file" },
	{ "keys": ["alt+o"], "command": "switch_file", "args": {"extensions": ["cpp", "cxx", "cc", "c", "hpp", "hxx", "h", "ipp", "inl", "m", "mm"]} },
	{ "keys": ["ctrl+n"], "command": "new_file" },
	{ "keys": ["ctrl+s"], "command": "save" },
	{ "keys": ["ctrl+shift+s"], "command": "prompt_save_as" },
	{ "keys": ["ctrl+f4"], "command": "close_file" },
	{ "keys": ["ctrl+w"], "command": "close" },

	{ "keys": ["ctrl+k", "ctrl+b"], "command": "toggle_side_bar" },
	{ "keys": ["f11"], "command": "toggle_full_screen" },
	{ "keys": ["shift+f11"], "command": "toggle_distraction_free" },

	{ "keys": ["backspace"], "command": "left_delete" },
	{ "keys": ["shift+backspace"], "command": "left_delete" },
	{ "keys": ["ctrl+shift+backspace"], "command": "left_delete" },
	{ "keys": ["delete"], "command": "right_delete" },
	{ "keys": ["enter"], "command": "insert", "args": {"characters": "\n"} },
	{ "keys": ["shift+enter"], "command": "insert", "args": {"characters": "\n"} },

	{ "keys": ["ctrl+z"], "command": "undo" },
	{ "keys": ["ctrl+shift+z"], "command": "redo" },
	{ "keys": ["ctrl+y"], "command": "redo_or_repeat" },
	{ "keys": ["ctrl+u"], "command": "soft_undo" },
	{ "keys": ["ctrl+shift+u"], "command": "soft_redo" },

	{ "keys": ["ctrl+shift+v"], "command": "paste_and_indent" },
	{ "keys": ["shift+delete"], "command": "cut" },
	{ "keys": ["ctrl+insert"], "command": "copy" },
	{ "keys": ["shift+insert"], "command": "paste" },
	{ "keys": ["ctrl+x"], "command": "cut" },
	{ "keys": ["ctrl+c"], "command": "copy" },
	{ "keys": ["ctrl+v"], "command": "paste" },

	{ "keys": ["left"], "command": "move", "args": {"by": "characters", "forward": false} },
	{ "keys": ["right"], "command": "move", "args": {"by": "characters", "forward": true} },
	{ "keys": ["up"], "command": "move", "args": {"by": "lines", "forward": false} },
	{ "keys": ["down"], "command": "move", "args": {"by": "lines", "forward": true} },
	{ "keys": ["shift+left"], "command": "move", "args": {"by": "characters", "forward": false, "extend": true} },
	{ "keys": ["shift+right"], "command": "move", "args": {"by": "characters", "forward": true, "extend": true} },
	{ "keys": ["shift+up"], "command": "move", "args": {"by": "lines", "forward": false, "extend": true} },
	{ "keys": ["shift+down"], "command": "move", "args": {"by": "lines", "forward": true, "extend": true} },

	{ "keys": ["ctrl+left"], "command": "move", "args": {"by": "words", "forward": false} },
	{ "keys": ["ctrl+right"], "command": "move", "args": {"by": "word_ends", "forward": true} },
	{ "keys": ["ctrl+shift+left"], "command": "move", "args": {"by": "words", "forward": false, "extend": true} },
	{ "keys": ["ctrl+shift+right"], "command": "move", "args": {"by": "word_ends", "forward": true, "extend": true} },

	{ "keys": ["alt+left"], "command": "move", "args": {"by": "subwords", "forward": false} },
	{ "keys": ["alt+right"], "command": "move", "args": {"by": "subword_ends", "forward": true} },
	{ "keys": ["alt+shift+left"], "command": "move", "args": {"by": "subwords", "forward": false, "extend": true} },
	{ "keys": ["alt+shift+right"], "command": "move", "args": {"by": "subword_ends", "forward": true, "extend": true} },

	{ "keys": ["ctrl+alt+up"], "command": "select_lines", "args": {"forward": false} },
	{ "keys": ["ctrl+alt+down"], "command": "select_lines", "args": {"forward": true} },

	{ "keys": ["pageup"], "command": "move", "args": {"by": "pages", "forward": false} },
	{ "keys": ["pagedown"], "command": "move", "args": {"by": "pages", "forward": true} },
	{ "keys": ["shift+pageup"], "command": "move", "args": {"by": "pages", "forward": false, "extend": true} },
	{ "keys": ["shift+pagedown"], "command": "move", "args": {"by": "pages", "forward": true, "extend": true} },

	{ "keys": ["home"], "command": "move_to", "args": {"to": "bol", "extend": false} },
	{ "keys": ["end"], "command": "move_to", "args": {"to": "eol", "extend": false} },
	{ "keys": ["shift+home"], "command": "move_to", "args": {"to": "bol", "extend": true} },
	{ "keys": ["shift+end"], "command": "move_to", "args": {"to": "eol", "extend": true} },
	{ "keys": ["ctrl+home"], "command": "move_to", "args": {"to": "bof", "extend": false} },
	{ "keys": ["ctrl+end"], "command": "move_to", "args": {"to": "eof", "extend": false} },
	{ "keys": ["ctrl+shift+home"], "command": "move_to", "args": {"to": "bof", "extend": true} },
	{ "keys": ["ctrl+shift+end"], "command": "move_to", "args": {"to": "eof", "extend": true} },


	{ "keys": ["ctrl+up"], "command": "scroll_lines", "args": {"amount": 1.0 } },
	{ "keys": ["ctrl+down"], "command": "scroll_lines", "args": {"amount": -1.0 } },

	{ "keys": ["ctrl+pagedown"], "command": "next_view" },
	{ "keys": ["ctrl+pageup"], "command": "prev_view" },

	{ "keys": ["ctrl+tab"], "command": "next_view_in_stack" },
	{ "keys": ["ctrl+shift+tab"], "command": "prev_view_in_stack" },

	{ "keys": ["ctrl+a"], "command": "select_all" },
	{ "keys": ["ctrl+shift+l"], "command": "split_selection_into_lines" },
	{ "keys": ["escape"], "command": "single_selection", "context":
		[
			{ "key": "num_selections", "operator": "not_equal", "operand": 1 }
		]
	},
	{ "keys": ["escape"], "command": "clear_fields", "context":
		[
			{ "key": "has_next_field", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["escape"], "command": "clear_fields", "context":
		[
			{ "key": "has_prev_field", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["escape"], "command": "hide_panel", "args": {"cancel": true},
		"context":
		[
			{ "key": "panel_visible", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["escape"], "command": "hide_overlay", "context":
		[
			{ "key": "overlay_visible", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["escape"], "command": "hide_auto_complete", "context":
		[
			{ "key": "auto_complete_visible", "operator": "equal", "operand": true }
		]
	},

	{ "keys": ["tab"], "command": "insert_best_completion", "args": {"default": "\t", "exact": true} },
	{ "keys": ["tab"], "command": "insert_best_completion", "args": {"default": "\t", "exact": false},
		"context":
		[
			{ "key": "setting.tab_completion", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["tab"], "command": "replace_completion_with_next_completion", "context":
		[
			{ "key": "last_command", "operator": "equal", "operand": "insert_best_completion" },
			{ "key": "setting.tab_completion", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["tab"], "command": "reindent", "context":
		[
			{ "key": "setting.auto_indent", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "preceding_text", "operator": "regex_match", "operand": "^$", "match_all": true },
			{ "key": "following_text", "operator": "regex_match", "operand": "^$", "match_all": true }
		]
	},
	{ "keys": ["tab"], "command": "indent", "context":
		[
			{ "key": "text", "operator": "regex_contains", "operand": "\n" }
		]
	},
	{ "keys": ["tab"], "command": "next_field", "context":
		[
			{ "key": "has_next_field", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["tab"], "command": "commit_completion", "context":
		[
			{ "key": "auto_complete_visible" },
			{ "key": "setting.auto_complete_commit_on_tab" }
		]
	},

	{ "keys": ["shift+tab"], "command": "insert", "args": {"characters": "\t"} },
	{ "keys": ["shift+tab"], "command": "unindent", "context":
		[
			{ "key": "setting.shift_tab_unindent", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["shift+tab"], "command": "unindent", "context":
		[
			{ "key": "preceding_text", "operator": "regex_match", "operand": "^[\t ]*" }
		]
	},
	{ "keys": ["shift+tab"], "command": "unindent", "context":
		[
			{ "key": "text", "operator": "regex_contains", "operand": "\n" }
		]
	},
	{ "keys": ["shift+tab"], "command": "prev_field", "context":
		[
			{ "key": "has_prev_field", "operator": "equal", "operand": true }
		]
	},

	{ "keys": ["ctrl+]"], "command": "indent" },
	{ "keys": ["ctrl+["], "command": "unindent" },

	{ "keys": ["insert"], "command": "toggle_overwrite" },

	{ "keys": ["ctrl+l"], "command": "expand_selection", "args": {"to": "line"} },
	{ "keys": ["ctrl+d"], "command": "find_under_expand" },
	{ "keys": ["ctrl+k", "ctrl+d"], "command": "find_under_expand_skip" },
	{ "keys": ["ctrl+shift+space"], "command": "expand_selection", "args": {"to": "scope"} },
	{ "keys": ["ctrl+shift+m"], "command": "expand_selection", "args": {"to": "brackets"} },
	{ "keys": ["ctrl+m"], "command": "move_to", "args": {"to": "brackets"} },
	{ "keys": ["ctrl+shift+j"], "command": "expand_selection", "args": {"to": "indentation"} },
	{ "keys": ["ctrl+shift+a"], "command": "expand_selection", "args": {"to": "tag"} },

	{ "keys": ["alt+."], "command": "close_tag" },

	{ "keys": ["ctrl+q"], "command": "toggle_record_macro" },
	{ "keys": ["ctrl+shift+q"], "command": "run_macro" },

	{ "keys": ["ctrl+enter"], "command": "run_macro_file", "args": {"file": "Packages/Default/Add Line.sublime-macro"} },
	{ "keys": ["ctrl+shift+enter"], "command": "run_macro_file", "args": {"file": "Packages/Default/Add Line Before.sublime-macro"} },
	{ "keys": ["enter"], "command": "commit_completion", "context":
		[
			{ "key": "auto_complete_visible" },
			{ "key": "setting.auto_complete_commit_on_tab", "operand": false }
		]
	},

	{ "keys": ["ctrl+p"], "command": "show_overlay", "args": {"overlay": "goto", "show_files": true} },
	{ "keys": ["ctrl+shift+p"], "command": "show_overlay", "args": {"overlay": "command_palette"} },
	{ "keys": ["ctrl+alt+p"], "command": "prompt_select_project" },
	{ "keys": ["ctrl+r"], "command": "show_overlay", "args": {"overlay": "goto", "text": "@"} },
	{ "keys": ["ctrl+g"], "command": "show_overlay", "args": {"overlay": "goto", "text": ":"} },
	{ "keys": ["ctrl+;"], "command": "show_overlay", "args": {"overlay": "goto", "text": "#"} },

	{ "keys": ["ctrl+i"], "command": "show_panel", "args": {"panel": "incremental_find", "reverse":false} },
	{ "keys": ["ctrl+shift+i"], "command": "show_panel", "args": {"panel": "incremental_find", "reverse":true} },
	{ "keys": ["ctrl+f"], "command": "show_panel", "args": {"panel": "find"} },
	{ "keys": ["ctrl+h"], "command": "show_panel", "args": {"panel": "replace"} },
	{ "keys": ["ctrl+shift+h"], "command": "replace_next" },
	{ "keys": ["f3"], "command": "find_next" },
	{ "keys": ["shift+f3"], "command": "find_prev" },
	{ "keys": ["ctrl+f3"], "command": "find_under" },
	{ "keys": ["ctrl+shift+f3"], "command": "find_under_prev" },
	{ "keys": ["alt+f3"], "command": "find_all_under" },
	{ "keys": ["ctrl+e"], "command": "slurp_find_string" },
	{ "keys": ["ctrl+shift+e"], "command": "slurp_replace_string" },
	{ "keys": ["ctrl+shift+f"], "command": "show_panel", "args": {"panel": "find_in_files"} },
	{ "keys": ["f4"], "command": "next_result" },
	{ "keys": ["shift+f4"], "command": "prev_result" },

	{ "keys": ["f6"], "command": "toggle_setting", "args": {"setting": "spell_check"} },
	{ "keys": ["ctrl+f6"], "command": "next_misspelling" },
	{ "keys": ["ctrl+shift+f6"], "command": "prev_misspelling" },

	{ "keys": ["ctrl+shift+up"], "command": "swap_line_up" },
	{ "keys": ["ctrl+shift+down"], "command": "swap_line_down" },

	{ "keys": ["ctrl+backspace"], "command": "delete_word", "args": { "forward": false } },
	{ "keys": ["ctrl+shift+backspace"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete to Hard BOL.sublime-macro"} },

	{ "keys": ["ctrl+delete"], "command": "delete_word", "args": { "forward": true } },
	{ "keys": ["ctrl+shift+delete"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete to Hard EOL.sublime-macro"} },

	{ "keys": ["ctrl+/"], "command": "toggle_comment", "args": { "block": false } },
	{ "keys": ["ctrl+shift+/"], "command": "toggle_comment", "args": { "block": true } },

	{ "keys": ["ctrl+j"], "command": "join_lines" },
	{ "keys": ["ctrl+shift+d"], "command": "duplicate_line" },

	{ "keys": ["ctrl+`"], "command": "show_panel", "args": {"panel": "console", "toggle": true} },

	{ "keys": ["ctrl+space"], "command": "auto_complete" },
	{ "keys": ["ctrl+space"], "command": "replace_completion_with_auto_complete", "context":
		[
			{ "key": "last_command", "operator": "equal", "operand": "insert_best_completion" },
			{ "key": "auto_complete_visible", "operator": "equal", "operand": false },
			{ "key": "setting.tab_completion", "operator": "equal", "operand": true }
		]
	},

	{ "keys": ["ctrl+alt+shift+p"], "command": "show_scope_name" },

	{ "keys": ["f7"], "command": "build" },
	{ "keys": ["ctrl+b"], "command": "build" },
	{ "keys": ["ctrl+shift+b"], "command": "build", "args": {"variant": "Run"} },
	{ "keys": ["ctrl+break"], "command": "exec", "args": {"kill": true} },

	{ "keys": ["ctrl+t"], "command": "transpose" },

	{ "keys": ["f9"], "command": "sort_lines", "args": {"case_sensitive": false} },
	{ "keys": ["ctrl+f9"], "command": "sort_lines", "args": {"case_sensitive": true} },

	// Auto-pair quotes
	{ "keys": ["\""], "command": "insert_snippet", "args": {"contents": "\"$0\""}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^(?:\t| |\\)|]|\\}|>|$)", "match_all": true },
			{ "key": "preceding_text", "operator": "not_regex_contains", "operand": "[\"a-zA-Z0-9_]$", "match_all": true },
			{ "key": "eol_selector", "operator": "not_equal", "operand": "string.quoted.double", "match_all": true }
		]
	},
	{ "keys": ["\""], "command": "insert_snippet", "args": {"contents": "\"${0:$SELECTION}\""}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": false, "match_all": true }
		]
	},
	{ "keys": ["\""], "command": "move", "args": {"by": "characters", "forward": true}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\"", "match_all": true }
		]
	},
	{ "keys": ["backspace"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete Left Right.sublime-macro"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "preceding_text", "operator": "regex_contains", "operand": "\"$", "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\"", "match_all": true }
		]
	},

	// Auto-pair single quotes
	{ "keys": ["'"], "command": "insert_snippet", "args": {"contents": "'$0'"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^(?:\t| |\\)|]|\\}|>|$)", "match_all": true },
			{ "key": "preceding_text", "operator": "not_regex_contains", "operand": "['a-zA-Z0-9_]$", "match_all": true },
			{ "key": "eol_selector", "operator": "not_equal", "operand": "string.quoted.single", "match_all": true }
		]
	},
	{ "keys": ["'"], "command": "insert_snippet", "args": {"contents": "'${0:$SELECTION}'"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": false, "match_all": true }
		]
	},
	{ "keys": ["'"], "command": "move", "args": {"by": "characters", "forward": true}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^'", "match_all": true }
		]
	},
	{ "keys": ["backspace"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete Left Right.sublime-macro"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "preceding_text", "operator": "regex_contains", "operand": "'$", "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^'", "match_all": true }
		]
	},

	// Auto-pair brackets
	{ "keys": ["("], "command": "insert_snippet", "args": {"contents": "($0)"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^(?:\t| |\\)|]|;|\\}|$)", "match_all": true }
		]
	},
	{ "keys": ["("], "command": "insert_snippet", "args": {"contents": "(${0:$SELECTION})"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": false, "match_all": true }
		]
	},
	{ "keys": [")"], "command": "move", "args": {"by": "characters", "forward": true}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\\)", "match_all": true }
		]
	},
	{ "keys": ["backspace"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete Left Right.sublime-macro"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "preceding_text", "operator": "regex_contains", "operand": "\\($", "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\\)", "match_all": true }
		]
	},

	// Auto-pair square brackets
	{ "keys": ["["], "command": "insert_snippet", "args": {"contents": "[$0]"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^(?:\t| |\\)|]|;|\\}|$)", "match_all": true }
		]
	},
	{ "keys": ["["], "command": "insert_snippet", "args": {"contents": "[${0:$SELECTION}]"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": false, "match_all": true }
		]
	},
	{ "keys": ["]"], "command": "move", "args": {"by": "characters", "forward": true}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\\]", "match_all": true }
		]
	},
	{ "keys": ["backspace"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete Left Right.sublime-macro"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "preceding_text", "operator": "regex_contains", "operand": "\\[$", "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\\]", "match_all": true }
		]
	},

	// Auto-pair curly brackets
	{ "keys": ["{"], "command": "insert_snippet", "args": {"contents": "{$0}"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^(?:\t| |\\)|]|\\}|$)", "match_all": true }
		]
	},
	{ "keys": ["{"], "command": "insert_snippet", "args": {"contents": "{${0:$SELECTION}}"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": false, "match_all": true }
		]
	},
	{ "keys": ["}"], "command": "move", "args": {"by": "characters", "forward": true}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\\}", "match_all": true }
		]
	},
	{ "keys": ["backspace"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete Left Right.sublime-macro"}, "context":
		[
			{ "key": "setting.auto_match_enabled", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "preceding_text", "operator": "regex_contains", "operand": "\\{$", "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\\}", "match_all": true }
		]
	},

	{ "keys": ["enter"], "command": "run_macro_file", "args": {"file": "Packages/Default/Add Line in Braces.sublime-macro"}, "context":
		[
			{ "key": "setting.auto_indent", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "preceding_text", "operator": "regex_contains", "operand": "\\{$", "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\\}", "match_all": true }
		]
	},
	{ "keys": ["shift+enter"], "command": "run_macro_file", "args": {"file": "Packages/Default/Add Line in Braces.sublime-macro"}, "context":
		[
			{ "key": "setting.auto_indent", "operator": "equal", "operand": true },
			{ "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
			{ "key": "preceding_text", "operator": "regex_contains", "operand": "\\{$", "match_all": true },
			{ "key": "following_text", "operator": "regex_contains", "operand": "^\\}", "match_all": true }
		]
	},

	{
		"keys": ["alt+shift+1"],
		"command": "set_layout",
		"args":
		{
			"cols": [0.0, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1]]
		}
	},
	{
		"keys": ["alt+shift+2"],
		"command": "set_layout",
		"args":
		{
			"cols": [0.0, 0.5, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
		}
	},
	{
		"keys": ["alt+shift+3"],
		"command": "set_layout",
		"args":
		{
			"cols": [0.0, 0.33, 0.66, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1], [2, 0, 3, 1]]
		}
	},
	{
		"keys": ["alt+shift+4"],
		"command": "set_layout",
		"args":
		{
			"cols": [0.0, 0.25, 0.5, 0.75, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1], [2, 0, 3, 1], [3, 0, 4, 1]]
		}
	},
	{
		"keys": ["alt+shift+8"],
		"command": "set_layout",
		"args":
		{
			"cols": [0.0, 1.0],
			"rows": [0.0, 0.5, 1.0],
			"cells": [[0, 0, 1, 1], [0, 1, 1, 2]]
		}
	},
	{
		"keys": ["alt+shift+9"],
		"command": "set_layout",
		"args":
		{
			"cols": [0.0, 1.0],
			"rows": [0.0, 0.33, 0.66, 1.0],
			"cells": [[0, 0, 1, 1], [0, 1, 1, 2], [0, 2, 1, 3]]
		}
	},
	{
		"keys": ["alt+shift+5"],
		"command": "set_layout",
		"args":
		{
			"cols": [0.0, 0.5, 1.0],
			"rows": [0.0, 0.5, 1.0],
			"cells":
			[
				[0, 0, 1, 1], [1, 0, 2, 1],
				[0, 1, 1, 2], [1, 1, 2, 2]
			]
		}
	},
	{ "keys": ["ctrl+1"], "command": "focus_group", "args": { "group": 0 } },
	{ "keys": ["ctrl+2"], "command": "focus_group", "args": { "group": 1 } },
	{ "keys": ["ctrl+3"], "command": "focus_group", "args": { "group": 2 } },
	{ "keys": ["ctrl+4"], "command": "focus_group", "args": { "group": 3 } },
	{ "keys": ["ctrl+shift+1"], "command": "move_to_group", "args": { "group": 0 } },
	{ "keys": ["ctrl+shift+2"], "command": "move_to_group", "args": { "group": 1 } },
	{ "keys": ["ctrl+shift+3"], "command": "move_to_group", "args": { "group": 2 } },
	{ "keys": ["ctrl+shift+4"], "command": "move_to_group", "args": { "group": 3 } },
	{ "keys": ["ctrl+0"], "command": "focus_side_bar" },

	{ "keys": ["alt+1"], "command": "select_by_index", "args": { "index": 0 } },
	{ "keys": ["alt+2"], "command": "select_by_index", "args": { "index": 1 } },
	{ "keys": ["alt+3"], "command": "select_by_index", "args": { "index": 2 } },
	{ "keys": ["alt+4"], "command": "select_by_index", "args": { "index": 3 } },
	{ "keys": ["alt+5"], "command": "select_by_index", "args": { "index": 4 } },
	{ "keys": ["alt+6"], "command": "select_by_index", "args": { "index": 5 } },
	{ "keys": ["alt+7"], "command": "select_by_index", "args": { "index": 6 } },
	{ "keys": ["alt+8"], "command": "select_by_index", "args": { "index": 7 } },
	{ "keys": ["alt+9"], "command": "select_by_index", "args": { "index": 8 } },
	{ "keys": ["alt+0"], "command": "select_by_index", "args": { "index": 9 } },

	{ "keys": ["f2"], "command": "next_bookmark" },
	{ "keys": ["shift+f2"], "command": "prev_bookmark" },
	{ "keys": ["ctrl+f2"], "command": "toggle_bookmark" },
	{ "keys": ["ctrl+shift+f2"], "command": "clear_bookmarks" },
	{ "keys": ["alt+f2"], "command": "select_all_bookmarks" },

	{ "keys": ["ctrl+shift+k"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete Line.sublime-macro"} },

	{ "keys": ["alt+q"], "command": "wrap_lines" },

	{ "keys": ["ctrl+k", "ctrl+u"], "command": "upper_case" },
	{ "keys": ["ctrl+k", "ctrl+l"], "command": "lower_case" },

	{ "keys": ["ctrl+k", "ctrl+space"], "command": "set_mark" },
	{ "keys": ["ctrl+k", "ctrl+a"], "command": "select_to_mark" },
	{ "keys": ["ctrl+k", "ctrl+w"], "command": "delete_to_mark" },
	{ "keys": ["ctrl+k", "ctrl+x"], "command": "swap_with_mark" },
	{ "keys": ["ctrl+k", "ctrl+y"], "command": "yank" },
	{ "keys": ["ctrl+k", "ctrl+k"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete to Hard EOL.sublime-macro"} },
	{ "keys": ["ctrl+k", "ctrl+backspace"], "command": "run_macro_file", "args": {"file": "Packages/Default/Delete to Hard BOL.sublime-macro"} },
	{ "keys": ["ctrl+k", "ctrl+g"], "command": "clear_bookmarks", "args": {"name": "mark"} },
	{ "keys": ["ctrl+k", "ctrl+c"], "command": "show_at_center" },

	{ "keys": ["ctrl++"], "command": "increase_font_size" },
	{ "keys": ["ctrl+="], "command": "increase_font_size" },
	{ "keys": ["ctrl+keypad_plus"], "command": "increase_font_size" },
	{ "keys": ["ctrl+-"], "command": "decrease_font_size" },
	{ "keys": ["ctrl+keypad_minus"], "command": "decrease_font_size" },

	{ "keys": ["alt+shift+w"], "command": "insert_snippet", "args": { "name": "Packages/XML/long-tag.sublime-snippet" } },

	{ "keys": ["ctrl+shift+["], "command": "fold" },
	{ "keys": ["ctrl+shift+]"], "command": "unfold" },
	{ "keys": ["ctrl+k", "ctrl+1"], "command": "fold_by_level", "args": {"level": 1} },
	{ "keys": ["ctrl+k", "ctrl+2"], "command": "fold_by_level", "args": {"level": 2} },
	{ "keys": ["ctrl+k", "ctrl+3"], "command": "fold_by_level", "args": {"level": 3} },
	{ "keys": ["ctrl+k", "ctrl+4"], "command": "fold_by_level", "args": {"level": 4} },
	{ "keys": ["ctrl+k", "ctrl+5"], "command": "fold_by_level", "args": {"level": 5} },
	{ "keys": ["ctrl+k", "ctrl+6"], "command": "fold_by_level", "args": {"level": 6} },
	{ "keys": ["ctrl+k", "ctrl+7"], "command": "fold_by_level", "args": {"level": 7} },
	{ "keys": ["ctrl+k", "ctrl+8"], "command": "fold_by_level", "args": {"level": 8} },
	{ "keys": ["ctrl+k", "ctrl+9"], "command": "fold_by_level", "args": {"level": 9} },
	{ "keys": ["ctrl+k", "ctrl+0"], "command": "unfold_all" },
	{ "keys": ["ctrl+k", "ctrl+j"], "command": "unfold_all" },
	{ "keys": ["ctrl+k", "ctrl+t"], "command": "fold_tag_attributes" },

	{ "keys": ["context_menu"], "command": "context_menu" },

	{ "keys": ["alt+c"], "command": "toggle_case_sensitive", "context":
		[
			{ "key": "setting.is_widget", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["alt+r"], "command": "toggle_regex", "context":
		[
			{ "key": "setting.is_widget", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["alt+w"], "command": "toggle_whole_word", "context":
		[
			{ "key": "setting.is_widget", "operator": "equal", "operand": true }
		]
	},
	{ "keys": ["alt+a"], "command": "toggle_preserve_case", "context":
		[
			{ "key": "setting.is_widget", "operator": "equal", "operand": true }
		]
	},

	// Find panel key bindings
	{ "keys": ["enter"], "command": "find_next", "context":
		[{"key": "panel", "operand": "find"}, {"key": "panel_has_focus"}]
	},
	{ "keys": ["shift+enter"], "command": "find_prev", "context":
		[{"key": "panel", "operand": "find"}, {"key": "panel_has_focus"}]
	},
	{ "keys": ["alt+enter"], "command": "find_all", "args": {"close_panel": true},
		 "context": [{"key": "panel", "operand": "find"}, {"key": "panel_has_focus"}]
	},

	// Replace panel key bindings
	{ "keys": ["enter"], "command": "find_next", "context":
		[{"key": "panel", "operand": "replace"}, {"key": "panel_has_focus"}]
	},
	{ "keys": ["shift+enter"], "command": "find_prev", "context":
		[{"key": "panel", "operand": "replace"}, {"key": "panel_has_focus"}]
	},
	{ "keys": ["alt+enter"], "command": "find_all", "args": {"close_panel": true},
		"context": [{"key": "panel", "operand": "replace"}, {"key": "panel_has_focus"}]
	},
	{ "keys": ["ctrl+alt+enter"], "command": "replace_all", "args": {"close_panel": true},
		 "context": [{"key": "panel", "operand": "replace"}, {"key": "panel_has_focus"}]
	},

	// Incremental find panel key bindings
	{ "keys": ["enter"], "command": "hide_panel", "context":
		[{"key": "panel", "operand": "incremental_find"}, {"key": "panel_has_focus"}]
	},
	{ "keys": ["shift+enter"], "command": "find_prev", "context":
		[{"key": "panel", "operand": "incremental_find"}, {"key": "panel_has_focus"}]
	},
	{ "keys": ["alt+enter"], "command": "find_all", "args": {"close_panel": true},
		"context": [{"key": "panel", "operand": "incremental_find"}, {"key": "panel_has_focus"}]
	}
]
