    import pyewts

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from rdflib import ConjunctiveGraph
from rdflib.namespace import Namespace, SKOS
from uuid import uuid4


from openpecha.core.annotation import Page, Span
from openpecha.core.layer import InitialCreationEnum, Layer, LayerEnum, PechaMetaData
from openpecha.core.pecha import OpenPechaFS

from ttl_scrapper import from_yaml


BDR = Namespace("http://purl.bdrc.io/resource/")
BDO = Namespace("http://purl.bdrc.io/ontology/core/")
BDA = Namespace("http://purl.bdrc.io/admindata/")
ADM = Namespace("http://purl.bdrc.io/ontology/admin/")
BDG = Namespace("http://purl.bdrc.io/graph/")
EWTSCONV = pyewts.pyewts()

def ewtstobo(ewtsstr):
    res = EWTSCONV.toUnicode(ewtsstr)
    return res

def parse_uri(URI):
    return URI.split('/')[-1]


def get_work_id(instance_gr, instance_id):
    return str(instance_gr.value(BDR[instance_id], BDO["instanceOf"]))


def get_titles(instance_id, type_):
    titles = defaultdict(list)
    src_instance_id = f"MW{instance_id[2:]}"
    src_inst_gr = ConjunctiveGraph()
    src_inst_gr.parse(f"https://purl.bdrc.io/resource/{src_instance_id}.ttl", format="ttl")
    for title in src_inst_gr.objects(BDR[src_instance_id], SKOS[type_]):
        if title.language == "bo-x-ewts":
            titles[title.language].append(ewtstobo(title.value))
        else:
            titles[title.language].append(title.value)
    return titles


def is_restricted_in_china(instance_gr, instance_id):
    is_restricted_flag = False
    is_restricted = str(instance_gr.value(BDA[instance_id], ADM["restrictedInChina"]))
    if is_restricted == "true":
        is_restricted_flag = True
    return is_restricted_flag


def get_access_flag(instance_gr, instance_id):
    return str(instance_gr.value(BDA[instance_id], ADM["access"]))


def get_vol_title(base_file_name):
    vol_gr = ConjunctiveGraph()
    vol_gr.parse(f"./data/sub_texts/{base_file_name}.trig", format="trig")
    vol_title = ewtstobo(str(vol_gr.value(BDR[base_file_name], SKOS["prefLabel"])))
    return vol_title


def get_volume_meta(instance_gr, vol_uri):
    vol_id = parse_uri(vol_uri)
    base_file_id = parse_uri(str(instance_gr.value(BDR[vol_id], BDO['volumeHasEtext'])))
    base_file_name = parse_uri(str(instance_gr.value(BDR[base_file_id], BDO['eTextResource'])))
    vol_title = get_vol_title(base_file_name)
    vol_meta = {
        uuid4().hex: {
            'title': vol_title,
            'volume_number': str(instance_gr.value(BDR[vol_id], BDO['volumeNumber'])),
            'base_file': f'{base_file_name}.txt',
            'reference': vol_uri
        }
    }
    return vol_meta


def get_volumes_meta(instance_gr, instance_id):
    volumes_meta = {}
    volumes = instance_gr.objects(BDR[instance_id], BDO['instanceHasVolume'])
    for volume in volumes:
        vol_uri = str(volume)
        vol_meta = get_volume_meta(instance_gr, vol_uri)
        volumes_meta.update(vol_meta)
    return volumes_meta


def get_instance_language(work_uri):
    work_id = parse_uri(work_uri)
    language = 'http://purl.bdrc.io/resource/LangBo'
    work_gr = ConjunctiveGraph()
    work_gr.parse(f"https://purl.bdrc.io/resource/{work_id}.ttl", format="ttl")
    language = str(work_gr.value(BDR[work_id], BDO['language']))
    return language



def get_source_meta(instance_id):
    src_meta = {
        'work_id': None,
        'instance_id': f"http://purl.bdrc.io/resource/{instance_id}",
        'language_id': None,
        'title': None,
        'alt_title': None,
        'author': None,
        'access': None,
        'restrictedInChina': None,
        'volumes': None
    }
    instance_gr = ConjunctiveGraph()
    instance_gr.parse(f'./data/instances/{instance_id}.trig', format="trig")
    src_meta['work_id'] = get_work_id(instance_gr, instance_id)
    src_meta['language_id'] = get_instance_language(src_meta['work_id'])
    src_meta['title'] = get_titles(instance_id, type_="prefLabel")
    src_meta['alt_title'] = get_titles(instance_id, type_="altLabel")
    src_meta['access'] = get_access_flag(instance_gr, instance_id)
    src_meta['restrictedInChina'] = is_restricted_in_china(instance_gr, instance_id)
    src_meta['volumes'] = get_volumes_meta(instance_gr, instance_id)
    return src_meta


def get_metadata(instance_id):
    source_metadata = get_source_meta(instance_id)
    instance_meta = PechaMetaData(
        initial_creation_type=InitialCreationEnum.input,
        created_at=datetime.now(),
        last_modified_at=datetime.now(),
        source_metadata= source_metadata)
    return instance_meta


def get_sub_text_base(sub_text_id):
    try:
        sub_text_base = Path(f'./data/etext-content/{sub_text_id}.txt').read_text(encoding='utf-8')
    except Exception:
        sub_text_base = ''
    return sub_text_base

def get_base_layer(instance_id, instance_mapping):
    bases = {}
    sub_text_ids = instance_mapping.get(instance_id, [])
    if sub_text_ids:
        for sub_text_id in sub_text_ids:
            bases[sub_text_id] = get_sub_text_base(sub_text_id)
    return bases


def get_page_span(page_id, g):
    page_start = int(g.value(BDR[page_id], BDO["sliceStartChar"]))
    page_end = int(g.value(BDR[page_id], BDO["sliceEndChar"]))
    page_span = Span(start=page_start, end=page_end)
    return page_span


def get_page_img_num(page_id, g):
    page_img_num = int(g.value(BDR[page_id], BDO["seqNum"]))
    return page_img_num


def get_page_annotation(page_uri, g):
    page_id = parse_uri(page_uri)
    page_span = get_page_span(page_id, g)
    page_img_num = get_page_img_num(page_id, g)
    page_annotation = {
        uuid4().hex: Page(span=page_span, imgnum= page_img_num, reference=page_uri)
    }
    return page_annotation


def get_sub_text_pagination_layer(sub_text_id):
    page_annotations = {}
    g = ConjunctiveGraph()
    g.parse(f'./data/sub_texts/{sub_text_id}.trig', format="trig")
    pages = g.objects(BDR[sub_text_id], BDO["eTextHasPage"])
    for page in pages:
        page_uri = str(page)
        page_annotation = get_page_annotation(page_uri, g)
        page_annotations.update(page_annotation)

    pagination_layer = Layer(
        annotation_type=LayerEnum.pagination, annotations=page_annotations
    )
    return pagination_layer


def get_layers(instance_id, instance_mapping):
    layers = {}
    sub_text_ids = instance_mapping.get(instance_id, [])
    if sub_text_ids:
        for sub_text_id in sub_text_ids:
            layers[sub_text_id] = {
                LayerEnum.pagination:get_sub_text_pagination_layer(sub_text_id)
            }
    return layers


def create_opf(instance_id, instance_mapping, output_path):
    opf = OpenPechaFS(
        meta= get_metadata(instance_id),
        base=get_base_layer(instance_id, instance_mapping),
        layers= get_layers(instance_id, instance_mapping)
        )

    opf.save(output_path=output_path)


if __name__ == "__main__":
    instance_id = "IE00KG08439"
    instance_mapping = from_yaml(Path('./mapping.yml'))
    opf_path = Path('./data/opfs')
    create_opf(instance_id, instance_mapping, opf_path)