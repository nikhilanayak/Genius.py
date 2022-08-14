import json
from scraper import parse
from multiprocessing import Pool

BATCH_SIZE = 1024
POOL_SIZE = 128

offset = 0


if __name__ == "__main__":
    with Pool(POOL_SIZE) as p:
        while True:
            batch = list(range(offset, offset + BATCH_SIZE))
            res = p.map(parse, batch)

            print(offset)
            offset += BATCH_SIZE
