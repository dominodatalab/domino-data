import sys

from domino_data.featurestore_sync import sync

if __name__ == "__main__":
    try:
        sync()
    except Exception as e:
        print(e)
        sys.exit(-1)
