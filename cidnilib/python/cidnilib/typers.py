import os
import sys
from .main import DataService

def is_pdf(stream) -> bool:
    try:
        header = stream.read(8)
        return header.startswith(b"%PDF-")
    except:
        return False

def is_zip(stream) -> bool:
    try:
        header = stream.read(8)
        return header.startswith(b"PK\x03\x04")
    except:
        return False

def is_jpg(stream) -> bool:
    try:
        header = stream.read(2)
        return header.startswith(b'\xFF\xD8')
    except:
        return False


def is_png(stream) -> bool:
    try:
        header = stream.read(8)
        return header.startswith(b'\x89PNG\r\n\x1a\n')
    except:
        return False

def is_tar(stream) -> bool:
    try:
        stream.seek(257)
        magic = stream.read(8)
        return magic.startswith(b'ustar\x00\x30\x30') or magic.startswith(b'ustar\x20\x20\x00') 
    except:
        return False

def is_gz(stream) -> bool:
    try:
        header = stream.read(2)
        return header.startswith(b'\x1f\x8b')
    except:
        return False


def extract_generic(ds: DataService, cid: str, extension: str, command: str):
    os.mkdir('/tmp/'+cid)
    fin = ds.recall_stream(cid)
    fout = open("/tmp/{cid}/{cid}.{extension}".format(cid=cid,extension=extension), 'wb')
    print("Copying " + cid, flush=True, file=sys.stderr)
    while True:
        data = fin.read(104857600)
        if not data:
            break
        fout.write(data)
        print(".", end="", flush=True, file=sys.stderr)
    fout.close()
    print(command.format(cid=cid,extension=extension))
    os.system(command.format(cid=cid,extension=extension))
    os.system("rm /tmp/{cid}/{cid}.{extension}".format(cid=cid,extension=extension))
    for root, dirs, files in os.walk("/tmp/{cid}".format(cid=cid)):
        for file in files:
            # TODO: handle metadata
            print("Storing " + os.path.join(root,file) + "... ")
            bcid, known = ds.know_file(open(os.path.join(root,file), 'rb')) 
            if not known: print("ALREADY ", end='')
            print("STORED AS " + bcid)
    os.system("rm -rf /tmp/"+cid)

typers = {
    'pdf': is_pdf,
    'zip': is_zip,
    'jpg': is_jpg,
    'png': is_png,
    'tar': is_tar,
    'gz': is_gz
}

archive_typers = {
    'zip': is_zip,
    'tar': is_tar,
    'gz': is_gz
}

extractors = {
    'zip': lambda ds, cid : extract_generic(ds, cid, 'zip', 
                                            "unzip /tmp/{cid}/{cid}.{extension} -d /tmp/{cid}/"),
    'gz': lambda ds, cid : extract_generic(ds, cid, 'gz', 
                                            "zcat /tmp/{cid}/{cid}.{extension} > /tmp/{cid}/{cid}.out"),
    'tar': lambda ds, cid : extract_generic(ds, cid, 'tar', 
                                            "tar -xvf /tmp/{cid}/{cid}.{extension} -C /tmp/{cid}/")
}