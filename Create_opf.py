from logging import raiseExceptions
import os
from pathlib import Path
from uuid import uuid4
import shutil
import requests
import re
from bs4 import BeautifulSoup
import json


from openpecha import config, github_utils
from openpecha.core.annotation import AnnBase, Page, Span
from openpecha.core.layer import InitialCreationEnum, Layer, LayerEnum, PechaMetaData
from openpecha.core.pecha import OpenPechaFS
from openpecha.utils import dump_yaml, load_yaml
from submodule import extractLines,normalizeUni,testUrl
from scrap import start_work
from datetime import datetime


base = "https://adarsha.dharma-treasure.org/"
workBase = "https://adarsha.dharma-treasure.org/kdbs/{name}"
apiBase = "https://adarsha.dharma-treasure.org/api/kdbs/{name}/pbs?size=10&lastId={pbs}"
prev_volume = 999
prev_Line = []

vol_sutra_map = {}
outdir = ""


def writePage(page, opf_path):

    global prev_Line,prev_volume
    volume = extractLines(page)

    if volume == prev_volume:     
        prev_Line.append(page)
    elif prev_volume != 999:
        prev_volume = "{:0>3d}".format(prev_volume)
        create_opf_repo(str(prev_volume),prev_Line,opf_path)
        prev_Line.clear()
        prev_Line.append(page)
        prev_volume = volume
    else:
        prev_Line.clear()
        prev_Line.append(page)
        prev_volume = volume


def getwork(work, opf_path):
    i = work[1]
    j = 0
    while testUrl(work, i) and j<100:
        url = apiBase.format(name=work[0], pbs=i)
        response = requests.get(url)
        text = response.text.replace("},{", "},\n{")
        text = normalizeUni(text)
        text = json.loads(text)
        pages = text["data"]
        for page in pages:
            writePage(page, opf_path)
        
        i += 10
        j+=1



def create_opf_repo(file_name, formatted_line,opf_path):
    
    global vol_sutra_map
    vol_sutra_map[file_name] = formatted_line[0]["BiographyId"]

    opf = OpenPechaFS(opf_path=opf_path)
    layers = {file_name: {LayerEnum.pagination: get_pagination_layer(formatted_line)}}

    base_text = get_base_text(formatted_line)
    bases = {file_name: base_text}
    
    opf.layers = layers
    opf.base = bases
    opf.save_base()
    opf.save_layers()

def create_index_layer(opf_path):
    global vol_sutra_map
    opf=OpenPechaFS(opf_path=opf_path)
    index = Layer(annotation_type=LayerEnum.index,annotations=get_sutra_span_map())
    opf._index = index
    opf.save_index()

def get_sutra_span_map():
    global vol_sutra_map
    page_annotations = {}
    sutra_id = sorted(set(vol_sutra_map.values()))
    for id in sutra_id:
        response = get_sutra_value(id)
        page_annotation = get_index_annotation(response.json()["data"])
        page_annotations.update(page_annotation)

    return page_annotations    



def get_index_annotation(data):

    page_span = get_page_span(data["vol"])
    meta_data = get_page_metadata(data["page"])
    page_annotation = {
        data["tname"]: Page(span=page_span,metadata=meta_data)
    }

    return page_annotation

def get_page_metadata(page):
    meta_datas = {}
    #page_group = page.split(",")
    #For test pruprose only one vol is given
    page_group = ["༼ཀ༽ 1-1-1a1~1-1-311b2"]

    for page in page_group:
        vol_name = re.search("(༼.༽) (.+)~(.+)",page).group(1)
        page_start = re.search("༼.༽ (.+)~(.+)",page).group(1)
        page_end = re.search("༼.༽ (.+)~(.+)",page).group(2)
        start_span,end_span = get_span(page_start,page_end)
        meta_data = {vol_name:Span(start=start_span,end=end_span)}
        meta_datas.update(meta_data)

    return meta_datas

def get_span(page_start,page_end):
    vol = int(re.search('(\d+?)-', page_start).group(1))
    vol ="{:0>3d}".format(vol)

    start_span = convert_span(re.search("\d+?-\d+?-(\d+?)[a-z]\d",page_start).group(1),re.search("\d+?-\d+?-\d+?([a-z])\d",page_start).group(1))
    end_span = convert_span(re.search("\d+?-\d+?-(\d+?)[a-z]\d",page_end).group(1),re.search("\d+?-\d+?-\d+?([a-z])\d",page_end).group(1))
    
    """Make the Pagination Path more general"""
    start=""
    end = ""
    pagination_path = Path(f"./opfs/layers/{vol}/Pagination.yml")
    pagination_yml =load_yaml(pagination_path)
    paginations = pagination_yml["annotations"]

    for index,pagination, in enumerate(paginations, start=1):
        if index == start_span:
            start = paginations[pagination]["span"]["start"]
        elif index == end_span:
            end = paginations[pagination]["span"]["end"]

    return (start,end)


    
def convert_span(val,mul):
    if mul =="a":
        res = int(val)*2-1
    elif mul == "b":
        res = int(val)*2
    else:
        raiseExceptions
    return res        


def get_page_span(vol):
    vol_start = re.search(".+\((\d+)-(\d+)\)",vol).group(1)
    vol_end = re.search(".+\((\d+)-(\d+)\)",vol).group(2)
    page_span = Span(start=vol_start,end=vol_end)

    return page_span



def get_pagination_layer(formatted_line):

    page_annotations = {}
    char_walker = 0

    for line in formatted_line:
        page_annotation,end = get_page_annotation(line,char_walker)
        page_annotations.update(page_annotation)
        char_walker = end+2

    pagination_layer = Layer(
        annotation_type=LayerEnum.pagination, annotations=page_annotations
    )

    return pagination_layer


def get_page_annotation(line,char_walker):
    
    metadata={}

    text = line["text"]
    imgnum = line["pbId"]
    pbid = line["id"]
    
    #tree = start_work(pbid)
    
    img_num1 = re.search('(\d+?-\d+?)-\d+?[a-z]', imgnum).group(1)
    img_num2 = get_img_num(re.search('\d+?-\d+?-(\d+?[a-z])', imgnum).group(1))
    img_link=f"https://files.dharma-treasure.org/degekangyur/degekangyur{img_num1}/{imgnum}.jpg"
    metadata["img_ref"] = img_link
    metadata["img_num"] = img_num2
    #metadata["tree"] = tree


    text_len = len(text) -1
    page_annotation = {
        uuid4().hex: Page(span=Span(start=char_walker, end=char_walker + text_len),imgnum=img_num2,reference=img_link)
    }
    return page_annotation,(char_walker + text_len)

def get_img_num(img_num):
    img_num1 = re.search("\d+?([a-z])",img_num).group(1)
    img_num2 = int(re.search("(\d+?)[a-z]",img_num).group(1))

    if img_num1 == "a":
        return img_num2*2-1
    else:
        return img_num2*2    


def get_base_text(texts):
    final_base = ""
    for text in texts:
        final_base+=text["text"].lstrip("\n")+"\n"

    return final_base


def dump_meta():
    global vol_sutra_map
    source_metadata = {
            "id": "",
            "title": "Kangyur",
            "language": "bo",
            "author": "",
            "volume": vol_sutra_map,
            "sutra": {},
        }

    sutra_id = sorted(set(vol_sutra_map.values()))

    for id in sutra_id:
        response = get_sutra_value(id)
        source_metadata["sutra"][id] = response.json()["data"]
    meta_fn = Path(f"{opf_path}/meta.yml")

    dump_yaml(source_metadata, meta_fn)

def get_sutra_value(sutra_id):
    response = requests.get(
            f"https://adarsha.dharma-treasure.org/api/kdbs/degekangyur/biographies/{sutra_id}"
        )
    return response


def call_api(work, opf_path):
    outdir = f"output/{work[0]}/"
    if os.path.exists(outdir):
        shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir)

    getwork(work, opf_path)

if __name__ == "__main__":
    # [work, starting pbs]2308063
    # work = ['degetengyur', 2843237]
    work = ["degekangyur", 2977724]
    # work = ['lhasakangyur', 2747738]
    # work = ['jiangkangyur', 2561410]
    opf_path = "./opfs"
    call_api(work, opf_path)
    dump_meta()
    create_index_layer(opf_path)
