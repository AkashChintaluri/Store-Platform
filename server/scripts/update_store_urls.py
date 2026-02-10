import os
from pymongo import MongoClient


def build_host_and_url(store_name: str, base_domain: str, base_port: str) -> tuple[str, str]:
    host = f"{store_name}.{base_domain}" if base_domain else store_name
    url = f"http://{host}:{base_port}" if base_port else f"http://{host}"
    return host, url


def main() -> None:
    mongodb_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("MONGODB_DB", "store_platform")
    base_domain = os.getenv("STORE_BASE_DOMAIN", "localhost").strip()
    base_port = os.getenv("STORE_BASE_PORT", "").strip()

    if not mongodb_uri:
        raise RuntimeError("MONGODB_URI is not set")

    client = MongoClient(mongodb_uri)
    db = client[database_name]
    stores = db.stores

    updated = 0
    for store in stores.find({}, {"_id": 1, "name": 1}):
        store_name = store.get("name")
        if not store_name:
            continue
        host, url = build_host_and_url(store_name, base_domain, base_port)
        result = stores.update_one(
            {"_id": store["_id"]},
            {"$set": {"host": host, "url": url}},
        )
        updated += result.modified_count

    client.close()
    print(f"Updated {updated} store records")


if __name__ == "__main__":
    main()
