import re
import requests

apiBase = "https://adarsha.dharma-treasure.org/api/kdbs/{name}/pbs?size=10&lastId={pbs}"


def formatLines(lines):
    formatedLines = []
    volume = lines.pop(0)
    formatedLines.append(volume)
    page = lines.pop(0)
    side = lines.pop(0)
    formatedLines.append(f"[{page}{side}]")
    sutra_id = lines.pop(0)
    formatedLines.append(f"{sutra_id}")

    for line in lines:
        formatedLines.append(f"{line}")
    return formatedLines


def extractLines(page):
    # [volume, page, side, l1, ..., l7]

    lines = []
    vol = page["pbId"]
    volume = int(re.search('(\d+?)-', vol).group(1))
    """ lines.append(volume)
    pageNum = int(re.search('"pbId":"\d+?-\d+?-(\d+?)[a-z]', page).group(1))
    lines.append(pageNum)
    side = re.search('"pbId":"\d+?-\d+?-\d+?([a-z])', page).group(1)
    lines.append(side)
    biography_id = re.search('"BiographyId":(\d+)', page).group(1)
    lines.append(biography_id)
    text = re.search('"text":"(.+?)"', page).group(1)
    text = re.sub("\s+", " ", text)
    ls = list(filter(None, text.split("\\n")))
    lines += ls """
    return volume


def item_generator(things):
    # ...because writelines() is such a tease
    for item in things:
        yield item
        yield "\n"

def normalizeUni(strNFC):
    strNFC = strNFC.replace("\u0F00", "\u0F68\u0F7C\u0F7E")  # ༀ
    strNFC = strNFC.replace("\u0F43", "\u0F42\u0FB7")  # གྷ
    strNFC = strNFC.replace("\u0F48", "\u0F47\u0FB7")  # ཈
    strNFC = strNFC.replace("\u0F4D", "\u0F4C\u0FB7")  # ཌྷ
    strNFC = strNFC.replace("\u0F52", "\u0F51\u0FB7")  # དྷ
    strNFC = strNFC.replace("\u0F57", "\u0F56\u0FB7")  # བྷ
    strNFC = strNFC.replace("\u0F5C", "\u0F5B\u0FB7")  # ཛྷ
    strNFC = strNFC.replace("\u0F69", "\u0F40\u0FB5")  # ཀྵ
    strNFC = strNFC.replace("\u0F73", "\u0F71\u0F72")  # ཱི
    strNFC = strNFC.replace("\u0F75", "\u0F71\u0F74")  # ཱུ
    strNFC = strNFC.replace("\u0F76", "\u0FB2\u0F80")  # ྲྀ
    strNFC = strNFC.replace("\u0F77", "\u0FB2\u0F71\u0F80")  # ཷ
    strNFC = strNFC.replace("\u0F78", "\u0FB3\u0F80")  # ླྀ
    strNFC = strNFC.replace("\u0F79", "\u0FB3\u0F71\u0F80")  # ཹ
    strNFC = strNFC.replace("\u0F81", "\u0F71\u0F80")  # ཱྀ
    strNFC = strNFC.replace("\u0F93", "\u0F92\u0FB7")  # ྒྷ
    strNFC = strNFC.replace("\u0F9D", "\u0F9C\u0FB7")  # ྜྷ
    strNFC = strNFC.replace("\u0FA2", "\u0FA1\u0FB7")  # ྡྷ
    strNFC = strNFC.replace("\u0FA7", "\u0FA6\u0FB7")  # ྦྷ
    strNFC = strNFC.replace("\u0FAC", "\u0FAB\u0FB7")  # ྫྷ
    strNFC = strNFC.replace("\u0FB9", "\u0F90\u0FB5")  # ྐྵ
    return strNFC

def testUrl(work, pbs):
    # check if url has text
    url = apiBase.format(name=work[0], pbs=pbs)
    response = requests.get(url)
    if response.text == '{"total":0,"data":[]}':
        # print(response.text)
        status = False
    else:
        status = True
    return status
