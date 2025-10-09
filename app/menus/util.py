import app.menus.banner as banner
from html.parser import HTMLParser
import os
import re
import textwrap

ascii_art = banner.load("https://me.mashu.lol/mebanner870.png", globals())

# ANSI escape codes for colors and styles
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    if ascii_art:
        ascii_art.to_terminal(columns=55)

def print_header(title: str):
    """Prints a stylized header with borders."""
    width = 55
    border_top = f"{Style.MAGENTA}╔{'═' * (width - 2)}╗{Style.RESET}"
    border_bottom = f"{Style.MAGENTA}╚{'═' * (width - 2)}╝{Style.RESET}"
    
    # Strip ANSI codes for accurate length calculation for centering
    clean_title = strip_ansi(title)
    
    # Calculate padding for centering
    padding_total = (width - 2) - len(clean_title)
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left

    print(border_top)
    print(f"{Style.MAGENTA}║{' ' * padding_left}{Style.BOLD}{Style.CYAN}{title}{Style.RESET}{' ' * padding_right}║{Style.RESET}")
    print(border_bottom)


def pause():
    input("\nPress enter to continue...")

class HTMLToText(HTMLParser):
    def __init__(self, width=80):
        super().__init__()
        self.width = width
        self.result = []
        self.in_li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True
        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "li":
            self.in_li = False
            self.result.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_li:
                self.result.append(f"- {text}")
            else:
                self.result.append(text)

    def get_text(self):
        # Join and clean multiple newlines
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        # Wrap lines nicely
        return "\n".join(textwrap.wrap(text, width=self.width, replace_whitespace=False))

def display_html(html_text, width=80):
    parser = HTMLToText(width=width)
    parser.feed(html_text)
    return parser.get_text()

def strip_ansi(text):
    """Removes ANSI escape codes from a string."""
    ansi_escape = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def print_bordered_line(text, width, border_color=Style.MAGENTA):
    """Prints a line of text within a bordered box, handling ANSI color codes."""
    # The visible length of the text, without ANSI codes
    visible_len = len(strip_ansi(text))
    
    # Calculate the required padding
    padding = width - 2 - visible_len
    
    # Construct the line
    line = f"{border_color}║ {text}{' ' * padding}{border_color}║{Style.RESET}"
    print(line)
