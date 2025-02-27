import io
import os
import json
import csv
from REMSG import *
import chardet
import copy

SHORT_LANG_LU : Final[dict[str, int]] = {
    "ja" : 0, # "Japanese",
    "en" : 1, # "English",
    "fr" : 2, # "French",
    "it" : 3, # "Italian",
    "de" : 4, # "German",
    "es" : 5, # "Spanish",
    "ru" : 6, # "Russian",
    "pl" : 7, # "Polish",
    "nl" : 8, # "Dutch",
    "pt" : 9, # "Portuguese",
    "ptbr" : 10, # "PortugueseBr",
    "ko" : 11, # "Korean",
    "zhtw" : 12, # "TraditionalChinese", # only this
    "zhcn" : 13, # "SimplifiedChinese", # and this
    "fi" : 14, # "Finnish",
    "sv" : 15, # "Swedish",
    "da" : 16, # "Danish",
    "no" : 17, # "Norwegian",
    "cs" : 18, # "Czech",
    "hu" : 19, # "Hungarian",
    "sk" : 20, # "Slovak",
    "ar" : 21, # "Arabic",
    "tr" : 22, # "Turkish",
    "bg" : 23, # "Bulgarian",
    "el" : 24, # "Greek",
    "ro" : 25, # "Romanian",
    "th" : 26, # "Thai",
    "ua" : 27, # "Ukrainian",
    "vi" : 28, # "Vietnamese",
    "id" : 29, # "Indonesian",
    "cc" : 30, # "Fiction",
    "hi" : 31, # "Hindi",
    "es419" : 32, # "LatinAmericanSpanish",
    # "" : 33, # "Max",
}


def searchSameGuid(msg: MSG):
    """research use, print out all entry name with same guid in one file"""
    guidset = set()
    for entry in msg.entrys:
        if entry.guid not in guidset:
            guidset.add(entry.guid)
        else:
            print(str(entry.guid)+":"+entry.name)


def searchGuid(msg: MSG, guid: uuid.UUID):
    """research use, print out the entry name with that guid"""
    for entry in msg.entrys:
        if entry.guid.hex == guid.hex:
            print(str(entry.guid)+":"+entry.name)


def getEncoding(filename: str, bufferSize: int = 256*1024) -> str:
    """althoguh I set utf-8 to all output file, but in-case someone copy paste to another file and has diff encoding..."""
    rawdata = open(filename, 'rb').read(bufferSize)
    result = chardet.detect(rawdata)
    encode = result['encoding']
    confidence = result['confidence']
    if encode is None or "ascii" == encode.lower() or (confidence < 0.75 and 'utf' not in encode.lower()):
        encode = 'utf-8'
    if encode.lower() == 'utf-8':
        encode = 'utf-8-sig'
    return encode


def readAttributeFromStr(inValue: str | int | float, vtype: int):
    """return the attribute value with correct data type"""
    value = ""
    match (vtype):
        case -1:    # null wstring
            value = ""
        case 0:     # int64
            value = int(inValue)
        case 1:     # double
            value = float(inValue)
        case 2:     # wstring
            value = str(inValue)
    return value


def printAllAttr(msg: MSG, filenameFull: str):
    """
    Debug: return all attr for debug propose.
    """
    for entry in msg.entrys:
        for j, x in enumerate(entry.attributes):
            name = str(msg.attributeHeaders[j]["name"])
            valueType = str(msg.attributeHeaders[j]["valueType"])
            value = "\""+str(x)+"\""
            yield ",".join((filenameFull,name,valueType,value))


def searchAttrTy(msg: MSG, filenameFull: str, ty: int):
    """
    Debug: search and print all attr's valueType if is ty type
    """
    for entry in msg.entrys:
        for j, x in enumerate(entry.attributes):
            name = str(msg.attributeHeaders[j]["name"])
            valueType = int(msg.attributeHeaders[j]["valueType"])
            if valueType == ty:
                value = "\""+str(x)+"\""
                print(",".join((filenameFull,name,str(valueType),value)))


def searchEntryName(msg: MSG, filename: str, keyword:str):
    """
    Debug: search entry name if keyword in entry name
    """
    for entry in msg.entrys:
        if keyword in entry.name:
            print(filename + "||" + entry.name)


def exportCSV(msg: MSG, filename: str):
    """write csv file from MSG object"""

    # newline = \n, as the original string has \r\n already, set newline as \r\n will replace \r\n to \r\r\n
    with io.open(filename, "w", encoding="utf-8-sig", newline='\n') as csvf:
        writer = csv.writer(csvf, delimiter=',')
        writer.writerow(
            ["guid", "crc?"] +\
            ["<" + x["name"] + ">" for x in msg.attributeHeaders] + \
            ["entry name",] + \
            [LANG_LIST.get(lang, f"lang_{lang}") for lang in msg.languages]
            )
        for entry in msg.entrys:
            writer.writerow(
                [str(x) for x in (entry.guid, entry.crc)] +\
                [str(x) for x in entry.attributes] +\
                [entry.name,] + \
                [entry.langs[lang] for lang in msg.languages]
            )


def importCSV(msgObj: MSG, filename: str, version: int = None, langCount: int = None) -> MSG:
    """read csv file, modify the provided msg object, and return the new MSG object"""
    
    msg = copy.deepcopy(msgObj)
    if version is None:
        if msg is not None:
            version = msg.version

    if langCount is None:
        if msg is not None:
            langCount = len(msg.languages)
        else:
            langCount = helper.VERSION_2_LANG_COUNT[version]

    with io.open(filename, "r", encoding=getEncoding(filename), newline='\n') as csvf:
        rows = list(csv.reader(csvf))
        # for row in rows:
        #     print(row)
        guididx = rows[0].index('guid')
        crcidx = rows[0].index('crc?')
        nameidx = rows[0].index('entry name')
        attridxs = list([i for i, field in enumerate(rows[0]) if field.startswith("<") and field.endswith(">")])
        fAttrList = list([rows[0][idx].removeprefix("<").removesuffix(">") for idx in attridxs])
        langidxs = list([rows[0].index(LANG_LIST.get(i, f"lang_{i}")) for i in range(langCount)])
        # fAttrNum = len(fAttrList)
        fEntrys = list([row for row in rows[1:]])
        # print(fAttrNum)
        # print(len(fEntrys))

    assert sorted(fAttrList) == sorted(list([head["name"] for head in msg.attributeHeaders])), "AttributeList Should be same as original"

    missingEntry = list([str(entry.guid) for entry in msg.entrys if str(entry.guid) not in [fEntry[guididx] for fEntry in fEntrys]])
    if len(missingEntry) > 0:
        print("Missing Entry:")
        print("\n".join(missingEntry))
        raise ValueError("Missing Entry")

    # oldEntrys = dict([(entry.guid, entry) for entry in msg.entrys])
    newEntrys : list[Entry] = list()
    for i, fEntry in enumerate(fEntrys):
        entry = Entry(version) # create a new one.
        attributes = list()
        for ai, header in enumerate(msg.attributeHeaders):
            value = readAttributeFromStr(fEntry[ attridxs[ai] ], header["valueType"])
            attributes.append(value)

        entry.buildEntry(
            guid = fEntry[guididx],
            crc = int(fEntry[crcidx]),
            name = fEntry[nameidx],
            attributeValues = attributes,
            langs = [helper.forceWindowsLineBreak(fEntry[i]) for i in langidxs],
            hash = mmh3.hash(key = fEntry[nameidx].encode('utf-16-le'), seed = -1, signed = False) if isVersionEntryByHash(version) else None,
            index = i if not(isVersionEntryByHash(version)) else None)
        
        # not gonna check, left it to user
        # if entry.guid in oldEntrys.keys():
        #     assert entry.crc == oldEntrys[entry.guid].crc
        #     assert entry.name == oldEntrys[entry.guid].name
        #     if isVersionEntryByHash(version):
        #         assert entry.hash == oldEntrys[entry.guid].hash
        #     else:
        #         assert entry.index == entry.index
        # else:
        #     if isVersionEntryByHash(version):
        #         if entry.hash != mmh3.hash(key = entry.name.encode('utf-16-le'), seed = -1, signed = False):
        #             print(f"Incorrect hash value for {entry.name}, filling a correct one")
        #             entry.hash = mmh3.hash(key = entry.name.encode('utf-16-le'), seed = -1, signed = False)
        #     else:
        #         assert entry.index >= len(oldEntrys)

        newEntrys.append(entry)

    msg.entrys = newEntrys
    return msg


def exportTXT(msg: MSG, filename: str, lang: int, encode="utf-8"):
    """write txt file from MSG object with specified language"""

    with io.open(filename, "w", encoding=encode) as txtf:
        txtf.writelines(['<string>'+entry.langs[lang].replace('\r\n','<lf>')+'\n' for entry in msg.entrys])


def importTXT(msgObj: MSG, filename: str, lang: int) -> MSG:
    """read txt file, modify the provided msg object, and return the new MSG object"""

    msg = copy.deepcopy(msgObj)
    lines = None
    with io.open(filename, mode="r", encoding=getEncoding(filename)) as txtf:
        lines = list([s.rstrip('\n').rstrip('\r').removeprefix("<string>").replace('<lf>','\r\n') for s in txtf.readlines() if s.startswith("<string>")])

    assert len(lines) == len(msg.entrys), "Invalid number of entry"
    for i, entry in enumerate(msg.entrys):
        entry.langs[lang] = lines[i]
    
    return msg


def exportMHRTextDump(msg: MSG, filename: str):
    """export all the content with all the language seperate by folders."""

    folder, file = os.path.split(filename)
    for lang in MHR_SUPPORTED_LANG:
        if not os.path.exists(os.path.join(folder, LANG_LIST.get(lang,f"lang_{lang}"))):
            try:
                os.makedirs(os.path.join(folder, LANG_LIST.get(lang,f"lang_{lang}")))
            except:
                pass

        outputPath = os.path.join(folder, LANG_LIST.get(lang,f"lang_{lang}"), file)
        exportTXT(msg, outputPath, lang, "utf-8-sig")


def valueTypeEnum(ty: int) -> str:
    """use mhrice style"""

    match (ty):
        case -1: return "Unknown"
        case 0: return "Int"
        case 1 : return "Float"
        case 2 : return "String"
        case _: return "Unknown"


def buildmhriceJson(msg: MSG) -> dict:
    """build mhrice style json file from MSG object.
    
    (with some additional info to let json itslef is able to convert to msg object)"""

    infos = {
            "version" : msg.version,
            "attribute_headers" : list([{"ty": attr["valueType"],
                                        "name": attr["name"]}
                                            for attr in msg.attributeHeaders]),
            "entries" : list([{
                "name": entry.name,
                "guid": str(entry.guid),
                "crc?": entry.crc,
                "hash": entry.hash if isVersionEntryByHash(msg.version) else 0xFFFFFFFF,
                "attributes" : list([{valueTypeEnum(attrh["valueType"]): entry.attributes[i]}
                                        for i, attrh in enumerate(msg.attributeHeaders)]),
                "content" : list([entry.langs[lang]
                                        for lang in msg.languages])
            } for entry in msg.entrys])}

    return infos


def exportJson(msg: MSG, filename: str):
    """write mhrice like json file from MSG object."""
    
    with io.open(filename, "w", encoding="utf-8") as jsonf:
        json.dump(buildmhriceJson(msg), jsonf, ensure_ascii=False, indent=2)


def importJson(msgObj: MSG, filename: str):
    """read json file, and return the new MSG object.

    @param msgObj: deprecated parameter, you may pass None for this.
    @param filename: filename string. 
    """

    msg = MSG()
    mhriceJson = ""
    with io.open(filename, "r", encoding=getEncoding(filename)) as jsonf:
        mhriceJson = json.load(jsonf)

    msg.version = int(mhriceJson["version"])
    if len(mhriceJson["entries"]) > 0:
        msg.languages = list(range(len(mhriceJson["entries"][0]["content"])))
    else:
        msg.languages = list(range(helper.VERSION_2_LANG_COUNT[msg.version]))

    # replace Attribute Head
    msg.attributeHeaders = list([{"valueType": head["ty"],
                                    "name": head["name"]}
                                        for head in mhriceJson["attribute_headers"]])
    
    newEntrys : list[Entry] = list()
    for jIndex, jEntry in enumerate(mhriceJson["entries"]):
        entry = Entry(msg.version) # create a new one.
        entry.buildEntry(
            guid=jEntry["guid"],
            crc=jEntry["crc?"],
            name=jEntry["name"],
            attributeValues=list([ readAttributeFromStr(next(iter(attr.values())), msg.attributeHeaders[i]["valueType"])
                                    for i, attr in enumerate(jEntry["attributes"])]),
            langs=list([ helper.forceWindowsLineBreak(content) for content in jEntry["content"] ]),
            hash=mmh3.hash(key = jEntry["name"].encode('utf-16-le'), seed = -1, signed = False) if isVersionEntryByHash(msg.version) else None,
            index = jIndex if not(isVersionEntryByHash(msg.version)) else None
        )

        newEntrys.append(entry)

    msg.entrys = newEntrys
    return msg


def importMSG(filename: str) -> MSG:
    """read a msg file and return a MSG object"""

    with io.open(filename, "rb" ) as filestream:
        msg = MSG()
        msg.readMSG(filestream)
        return msg


def exportMSG(msg: MSG, filename: str):
    """write a msg file from a MSG object"""

    with io.open(filename, 'wb') as outstream:
        outstream.write(msg.writeMSG())
