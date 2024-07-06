# from api.py
from api import time_diff
# for wikimedia api requests
import requests

# to convert from html to plaintext
from bs4 import BeautifulSoup
import re

# to parse time to get userage from user account creation date
import datetime


def getdata(fromrev, torev):
    # set up
    # get data
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS_DATA = {
        'action': "compare",
        'format': "json",
        'fromrev': fromrev,
        'torev': torev
    }
    PARAMS_METADATA = {
        'action': "compare",
        'format': 'json',
        'fromrev': fromrev,
        'torev': torev,
        'prop': 'diffsize|user|comment|parsedcomment'
    }
    PARAMS_REVISION = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "revids": fromrev,
        "rvprop": "size",
    }

    # collect edit data
    R = S.get(url=URL, params=PARAMS_DATA)
    DATA = R.json()

    # collect metadata
    R = S.get(url=URL, params=PARAMS_METADATA)
    DATA_METADATA = R.json()

    # collect fromrev size in bytes
    R = S.get(url=URL, params=PARAMS_REVISION)
    DATA_REVISION = R.json()

    revisions = DATA_REVISION.get("query", {}).get("pages", {}).values()
    for page in revisions:
        for rev in page.get("revisions", []):
            fromrev_size = rev.get("size")

    # check for errors
    if ('error' in DATA_METADATA):
        return "ERROR: " + DATA_METADATA['error']['code']

    # collect metadata available in 'compare'
    diffsize = DATA_METADATA['compare']['diffsize']
    user = DATA_METADATA['compare']['touser']

    # collect editor info
    PARAMS_USERINFO = {
        "action": "query",
        "format": "json",
        "list": "users",
        "ususers": user,
        "usprop": "blockinfo|groups|editcount|registration|emailable|gender"
    }
    R = S.get(url=URL, params=PARAMS_USERINFO)
    DATA_USERINFO = R.json()

    # check if user is registered or not
    # also collect other metadata
    if (DATA_METADATA["compare"]["touserid"] == 0):
        user_editcount = 0
        user_gender = "unknown"
        user_age = 0
        user_isautoconfirmed = False
        user_isextendedconfirmed = False
        user_issysop = False
        user_isanon = True
    else:
        user_editcount = DATA_USERINFO["query"]["users"][0]["editcount"]
        user_gender = DATA_USERINFO["query"]["users"][0]["gender"]
        user_creationdate = DATA_USERINFO["query"]["users"][0]["registration"]

        if (user_creationdate is None):
            user_age = -1
        else:
            user_creationdate = user_creationdate[0:10]
            d = datetime.date.fromisoformat(user_creationdate)
            # chooses to compare user date against July 1st, 2050
            # meaning that this will break for accounts created past 07012050
            d_compare = datetime.date(2050, 7, 1)
            user_age = time_diff(d, d_compare)

        user_isautoconfirmed = True if DATA_USERINFO["query"]["users"][0][
            "groups"].count("autoconfirmed") >= 1 else False
        user_isextendedconfirmed = True if (
            DATA_USERINFO["query"]["users"][0]["groups"].count(
                "extendedconfirmed")
            >= 1 or user_isautoconfirmed) else False
        user_issysop = True if (
            DATA_USERINFO["query"]["users"][0]["groups"].count("sysop") >= 1
            or user_isextendedconfirmed) else False
        user_isanon = False
    user_comment = DATA_METADATA['compare']['tocomment']
    user_comment = re.sub(r'\/*.*?\*/', '', user_comment)

    # parse edit data
    def html_to_plain_text(html_content):
        # init BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        # get text
        text = soup.get_text()

        # break into lines, remove leading and trailing space on each line
        lines = (line.strip() for line in text.splitlines())

        # drop blank lines
        text = '\n'.join(line for line in lines if line)

        return text

    # convert from html to readable plaintext
    # also replace diffmarkers with easier to parse symbols (-, +, ==)

    html_content = DATA["compare"]["*"]
    html_content = html_content.replace(
        '<td class="diff-marker" data-marker="−"></td>', '\n-\n')
    html_content = html_content.replace(
        '<td class="diff-marker" data-marker="+"></td>', '\n+\n')
    html_content = html_content.replace(
        '<td class="diff-marker"></td>', '\n==\n')
    plain_text_content = html_to_plain_text(html_content)

    plain_text_content = plain_text_content.splitlines()

    edit_diff_add = []
    edit_diff_remove = []
    cnt = 0

    def is_valid_text(text):
        if (text == "+" or text == "-" or text[:2] == "==" or
                (text[-1:] == ":" and text[:4] == "Line")):
            return False
        return True

    # split into edit_diff_add and edit_diff_remove

    while (cnt < len(plain_text_content)):
        if (plain_text_content[cnt] == "-" and
                is_valid_text(plain_text_content[cnt+1])):
            edit_diff_remove.append(plain_text_content[cnt+1])
            if (len(plain_text_content) < cnt+2 and plain_text_content[cnt+2] == "+" and
                    is_valid_text(plain_text_content[cnt+3])):
                edit_diff_add.append(plain_text_content[cnt+3])
                cnt += 4
            else:
                edit_diff_add.append("")
            cnt += 2
        elif (plain_text_content[cnt] == "+" and
              is_valid_text(plain_text_content[cnt+1])):
            edit_diff_add.append(plain_text_content[cnt+1])
            cnt += 2
        else:
            cnt += 1

    # normalize text

    sub_ref_pattern = r'<ref name=".*?">.*?</ref>'
    sub_square_brackets_pattern = r'\[\[.*?\]\]'
    for i in range(0, len(edit_diff_add)):
        edit_diff_add[i] = re.sub(sub_ref_pattern, "", edit_diff_add[i])
        edit_diff_add[i] = re.sub(
            sub_square_brackets_pattern, "", edit_diff_add[i])
    for i in range(0, len(edit_diff_remove)):
        edit_diff_remove[i] = re.sub(sub_ref_pattern, "", edit_diff_remove[i])
        edit_diff_remove[i] = re.sub(
            sub_square_brackets_pattern, "", edit_diff_remove[i])

    replace_list = ['(', ')', '[', ']', '&nbsp', '{', '}', '|', '=', '  ', '.']
    remove_list = [' !', ' .', ' ,', '″', '″']

    for i in range(0, len(edit_diff_add)):
        for j in replace_list:
            # replace from replace_list, remove duplicate spaces
            edit_diff_add[i] = edit_diff_add[i].replace(j, ' ')
            edit_diff_add[i] = edit_diff_add[i].replace('  ', ' ')
            edit_diff_add[i] = edit_diff_add[i].replace("'", '')

    for i in range(0, len(edit_diff_add)):
        for j in remove_list:
            # remove from remove_list: remove punctuation
            edit_diff_add[i] = edit_diff_add[i].replace(j, '')

    for i in range(0, len(edit_diff_remove)):
        for j in replace_list:
            # replace from replace_list, remove duplicate spaces
            edit_diff_remove[i] = edit_diff_remove[i].replace(j, ' ')
            edit_diff_remove[i] = edit_diff_remove[i].replace('  ', ' ')
            edit_diff_remove[i] = edit_diff_remove[i].replace("'", '')

    for i in range(0, len(edit_diff_remove)):
        for j in remove_list:
            # remove from remove_list: remove punctuation
            edit_diff_remove[i] = edit_diff_remove[i].replace(j, '')

    # find diff
    # first split into list of list of words
    word_matrix_add = []
    for i in range(0, len(edit_diff_add)):
        word_matrix_add.append(edit_diff_add[i].split())

    # remove words with len <= 1
    for i in range(0, len(word_matrix_add)):
        word_matrix_add[i] = [j for j in word_matrix_add[i] if len(j) > 1]

    # do the same for edit_diff_remove
    word_matrix_remove = []
    for i in range(0, len(edit_diff_remove)):
        word_matrix_remove.append(edit_diff_remove[i].split())

    for i in range(0, len(word_matrix_remove)):
        word_matrix_remove[i] = [
            j for j in word_matrix_remove[i] if len(j) > 1]

    if (len(word_matrix_remove) > len(word_matrix_add)):
        for i in range(len(word_matrix_remove) - len(word_matrix_add)):
            word_matrix_add.append([])
    elif (len(word_matrix_remove) < len(word_matrix_add)):
        for i in range(len(word_matrix_add) - len(word_matrix_remove)):
            word_matrix_remove.append([])

    # find words added/removed

    # added:
    words_added = []
    for i in range(len(word_matrix_add)):
        tmps = set(word_matrix_remove[i])
        words_added.append([x for x in word_matrix_add[i] if x not in tmps])

    # removed:
    words_removed = []
    for i in range(len(word_matrix_remove)):
        tmps = set(word_matrix_add[i])
        words_removed.append(
            [x for x in word_matrix_remove[i] if x not in tmps])

    # filter out empty strings
    words_added = [x for x in words_added if x]
    words_removed = [x for x in words_removed if x]

    # organize array to return
    # organize metadata
    final_ret = []
    metadata = [diffsize, user_editcount, user_gender, user_age,
                user_isanon, user_isautoconfirmed, user_isextendedconfirmed,
                user_issysop, user_comment, fromrev_size]
    final_ret += metadata
    final_ret.append(words_added)
    final_ret.append(words_removed)
    # final_ret organization:
    # [diffsize, user_editcount, user_gender, user_age,
    #   user_isanon, user_isautoconfirmed,
    #   user_isextendedconfirmed, user_issysop, user_comment, fromrev_size,
    #   [<words>added], [<words_removed>]]

    return final_ret
