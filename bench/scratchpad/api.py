
import ollama
import sys
import io

def dump_help_to_file():
	help_text = io.StringIO()
	sys_stdout = sys.stdout
	try:
		sys.stdout = help_text
		help(ollama)
	finally:
		sys.stdout = sys_stdout
	with open('scratchpad/ollama_api_help.txt', 'w', encoding='utf-8') as f:
		f.write(help_text.getvalue())

if __name__ == "__main__":
	dump_help_to_file()