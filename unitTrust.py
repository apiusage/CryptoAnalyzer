from content import *
from FA import *

def unitTrustList(funds, txt_file=get_prompt_path("UT_funds.txt"), placeholder="{fundURL}"):
    for fund in funds:
        gpt_prompt_copy(
            txt_file=txt_file,
            placeholder=placeholder,
            replacement=fund["url"],
            name=fund["name"]
        )

