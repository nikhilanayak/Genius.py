import lxml
import cchardet
from bs4 import BeautifulSoup
import grequests
import requests
import json

def get_lyrics(page_content):
    if page_content == None:
        return None
    soup = BeautifulSoup(page_content, features="lxml")

    return soup.text.split("\n\n")

class Maybe:
    def __init__(self, value):
        self.value = value

    def __hasattr(self, v):
        if hasattr(self.value, v):
            return True
        if type(self.value) == dict and v in self.value:
            return True
        return False

    def __getattr__(self, name):
        if self.__hasattr(name):
            return Maybe(self.value[name])
        else:
            return Maybe(None)
        
    def __getitem__(self, name):
        return self.__getattr__(name)


def map_kv(l):
    if l == None:
        return {}

    out = {}
    for item in l:
        #item = l[key]
        if "values" in item: item["value"] = item["values"]
        if "name" in item: item["key"] = item["name"]

        out[item["key"]] = item["value"]
    return out


def first(x):
    if x == None:
        return None
    if len(x) == 0:
        return None
    if type(x) != list:
        return None
    return x[0]


def parse_annotation(response):
    data = response.text

    soup = BeautifulSoup(data, features="lxml")

    metas = soup.find_all("meta")

    referent = first([i for i in metas if "property" in i.attrs and i["property"] == "rap_genius:referent"])
    description = first([i for i in metas if "property" in i.attrs and i["property"] == "og:description"])

    if referent == None:
        referent = ""
    else:
        referent = referent["content"]

    if description == None:
        description = ""
    else:
        description = description["content"]


    return {"referent": referent, "description": description}


def parse(id):
    page_content = requests.get(f"https://genius.com/songs/{id}").text


    soup = BeautifulSoup(page_content, "lxml")
      
    lines = page_content.split("\n")
    json_line = [i.strip() for i in lines if i.strip().startswith("window.__PRELOADED_STATE__ =")]
    
    out_data = {}

    if len(json_line) > 0:
        json_data = json_line[0][41:-3].encode("utf-8").decode("unicode_escape")
        json_data = Maybe(json.loads(json_data))
        #json_data = #eval()
    else:
        json_data = Maybe(None)


    kv_data = {**map_kv(json_data.songPage.trackingData.value), **map_kv(json_data.songPage.dfpKv.value)}
    kv_data = Maybe(kv_data)

    out_data["title"] = {"name": kv_data.Title.value, "id": kv_data["Song ID"].value}
    out_data["artist"] = {"name": kv_data["Primary Artist"].value, "id": kv_data["Primary Artist ID"].value}
    out_data["is_music"] = kv_data["Music?"].value
    out_data["release_date"] = kv_data["Release Date"].value
    out_data["language"] = kv_data["Lyrics Language"].value
    out_data["topic"] = first(kv_data.topic.value)
    out_data["url"] = json_data.songPage.path.value
    out_data["page_views"] = first(kv_data.pageviews.value)
    out_data["is_explicit"] = first(kv_data.is_explicit.value)
    out_data["lyrics"] = get_lyrics(json_data.songPage.lyricsData.body.html.value)


    annotation_ids = json_data.songPage.lyricsData.referents.value
    
    annotation_urls = list(map(lambda i: f"https://genius.com/{i}", annotation_ids))
    annotation_responses = list(grequests.map(grequests.get(i) for i in annotation_urls))
    annotations = list(map(parse_annotation, annotation_responses))

    out_data["annotations"] = annotations

    print(id)
    return out_data

